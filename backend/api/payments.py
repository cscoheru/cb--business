# api/payments.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import Optional

from models.user import User
from models.subscription import Subscription, Payment
from schemas.payment import (
    PaymentCreate,
    PaymentOrderResponse,
    PaymentQueryResponse,
    PaymentMethod,
    PaymentStatus,
)
from config.subscriptions import get_plan_pricing
from config.database import get_db
from api.dependencies import get_current_user
from services.wechat_pay import WeChatPayService

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

# 初始化微信支付服务
wechat_pay = WeChatPayService()


@router.post("/create", response_model=PaymentOrderResponse)
async def create_payment_order(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建支付订单"""
    # 检查是否已有活跃订阅
    if payment_data.plan_tier != "free":
        existing = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == current_user.id,
                    Subscription.status == "active",
                    Subscription.plan_tier == payment_data.plan_tier,
                )
            )
        )
        existing_sub = existing.scalar_one_or_none()

        if existing_sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "ACTIVE_SUBSCRIPTION_EXISTS",
                    "message": f"您已有活跃的{payment_data.plan_tier}订阅"
                }
            )

    # 获取定价
    amount = get_plan_pricing(payment_data.plan_tier, payment_data.billing_cycle)

    if amount is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CUSTOM_PLAN", "message": "企业版需联系销售，请发送邮件至 sales@3strategy.cc"}
        )

    if amount == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "FREE_PLAN", "message": "免费版无需支付"}
        )

    # 创建支付订单
    if payment_data.payment_method == PaymentMethod.WECHAT:
        order_result = await wechat_pay.create_order(
            user_id=str(current_user.id),
            plan_tier=payment_data.plan_tier,
            billing_cycle=payment_data.billing_cycle,
            amount=float(amount),
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"code": "PAYMENT_METHOD_NOT_SUPPORTED", "message": "暂不支持该支付方式"}
        )

    # 创建支付记录
    payment = Payment(
        user_id=current_user.id,
        subscription_id=None,  # 支付成功后创建订阅
        amount=amount,
        currency="CNY",
        payment_method=payment_data.payment_method.value,
        payment_status=PaymentStatus.PENDING.value,
        transaction_id=order_result["order_no"],
        external_order_id=order_result.get("prepay_id"),
        extra_data=f'{{"plan_tier":"{payment_data.plan_tier}","billing_cycle":"{payment_data.billing_cycle}"}}',
    )

    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    # 生成二维码URL
    qrcode_url = f"/api/v1/payments/qrcode/{order_result['order_no']}"

    return PaymentOrderResponse(
        order_no=order_result["order_no"],
        amount=float(amount),
        currency="CNY",
        payment_method=payment_data.payment_method.value,
        code_url=order_result.get("code_url"),
        qrcode_url=qrcode_url,
        expires_at=datetime.utcnow() + timedelta(hours=2),  # 订单2小时过期
    )


@router.get("/{order_no}", response_model=PaymentQueryResponse)
async def query_payment(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询支付状态"""
    # 查找支付记录
    result = await db.execute(
        select(Payment).where(
            and_(
                Payment.transaction_id == order_no,
                Payment.user_id == current_user.id,
            )
        )
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PAYMENT_NOT_FOUND", "message": "支付记录不存在"}
        )

    return PaymentQueryResponse(
        order_no=order_no,
        amount=float(payment.amount),
        status=PaymentStatus(payment.payment_status),
        payment_method=payment.payment_method,
        created_at=payment.created_at,
        completed_at=payment.completed_at,
        transaction_id=payment.external_order_id,
    )


@router.post("/wechat/notify")
async def wechat_notify(request: Request, db: AsyncSession = Depends(get_db)):
    """微信支付回调"""
    xml_data = await request.body()
    xml_str = xml_data.decode()

    # 验证签名
    is_valid, data = wechat_pay.verify_notify(xml_str)

    if not is_valid:
        return wechat_pay.build_notify_response(False, "签名验证失败")

    # 检查支付结果
    if data.get("return_code") == "SUCCESS" and data.get("result_code") == "SUCCESS":
        order_no = data.get("out_trade_no")
        transaction_id = data.get("transaction_id")

        # 查找支付记录
        result = await db.execute(
            select(Payment).where(Payment.transaction_id == order_no)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            return wechat_pay.build_notify_response(False, "支付记录不存在")

        # 避免重复处理
        if payment.payment_status == PaymentStatus.COMPLETED.value:
            return wechat_pay.build_notify_response(True, "OK")

        # 更新支付状态
        payment.payment_status = PaymentStatus.COMPLETED.value
        payment.external_order_id = transaction_id
        payment.completed_at = datetime.utcnow()

        # 解析额外数据
        import json
        try:
            extra_data = json.loads(payment.extra_data) if payment.extra_data else {}
            plan_tier = extra_data.get("plan_tier", "pro")
            billing_cycle = extra_data.get("billing_cycle", "monthly")
        except:
            plan_tier = "pro"
            billing_cycle = "monthly"

        # 计算订阅过期时间
        if billing_cycle == "yearly":
            expires_at = datetime.utcnow() + timedelta(days=365)
        else:
            expires_at = datetime.utcnow() + timedelta(days=30)

        # 创建订阅
        # 先检查是否已有相同计划的订阅
        existing_sub = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == payment.user_id,
                    Subscription.plan_tier == plan_tier,
                )
            )
        )
        subscription = existing_sub.scalar_one_or_none()

        if subscription:
            # 更新现有订阅
            subscription.status = "active"
            subscription.billing_cycle = billing_cycle
            subscription.amount = float(payment.amount)
            subscription.started_at = datetime.utcnow()
            subscription.expires_at = expires_at
            subscription.canceled_at = None
            subscription.auto_renew = True
        else:
            # 创建新订阅
            subscription = Subscription(
                user_id=payment.user_id,
                plan_tier=plan_tier,
                status="active",
                billing_cycle=billing_cycle,
                amount=float(payment.amount),
                started_at=datetime.utcnow(),
                expires_at=expires_at,
                auto_renew=True,
            )
            db.add(subscription)
            await db.flush()

        payment.subscription_id = str(subscription.id)
        await db.commit()

        return wechat_pay.build_notify_response(True, "OK")

    return wechat_pay.build_notify_response(False, "支付失败")


@router.get("/qrcode/{order_no}")
async def get_payment_qrcode(order_no: str):
    """获取支付二维码（前端可直接使用code_url生成）"""
    from fastapi.responses import Response
    import qrcode
    from io import BytesIO

    # 查询支付记录
    # 实际应该查询code_url，这里简化处理
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"PAYMENT:{order_no}")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return Response(content=buffer.read(), media_type="image/png")


@router.post("/mock/{order_no}/complete")
async def mock_payment_complete(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """模拟支付完成（仅开发环境）"""
    # 查找支付记录
    result = await db.execute(
        select(Payment).where(
            and_(
                Payment.transaction_id == order_no,
                Payment.user_id == current_user.id,
            )
        )
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PAYMENT_NOT_FOUND", "message": "支付记录不存在"}
        )

    # 更新为已完成
    payment.payment_status = PaymentStatus.COMPLETED.value
    payment.completed_at = datetime.utcnow()

    # 解析额外数据并创建订阅（与回调处理相同）
    import json
    try:
        extra_data = json.loads(payment.extra_data) if payment.extra_data else {}
        plan_tier = extra_data.get("plan_tier", "pro")
        billing_cycle = extra_data.get("billing_cycle", "monthly")
    except:
        plan_tier = "pro"
        billing_cycle = "monthly"

    # 计算订阅过期时间
    if billing_cycle == "yearly":
        expires_at = datetime.utcnow() + timedelta(days=365)
    else:
        expires_at = datetime.utcnow() + timedelta(days=30)

    # 创建订阅
    existing_sub = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.user_id == payment.user_id,
                Subscription.plan_tier == plan_tier,
            )
        )
    )
    subscription = existing_sub.scalar_one_or_none()

    if subscription:
        subscription.status = "active"
        subscription.billing_cycle = billing_cycle
        subscription.amount = float(payment.amount)
        subscription.started_at = datetime.utcnow()
        subscription.expires_at = expires_at
        subscription.canceled_at = None
        subscription.auto_renew = True
    else:
        subscription = Subscription(
            user_id=payment.user_id,
            plan_tier=plan_tier,
            status="active",
            billing_cycle=billing_cycle,
            amount=float(payment.amount),
            started_at=datetime.utcnow(),
            expires_at=expires_at,
            auto_renew=True,
        )
        db.add(subscription)
        await db.flush()

    payment.subscription_id = str(subscription.id)
    await db.commit()

    return {"success": True, "message": "支付完成"}

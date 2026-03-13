# api/payments.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import Optional
import logging
import uuid

logger = logging.getLogger(__name__)


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
from services.airwallex_service import get_airwallex_service, AirwallexError

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

# 初始化支付服务
wechat_pay = WeChatPayService()
airwallex = get_airwallex_service()


@router.post("/create", response_model=PaymentOrderResponse)
async def create_payment_order(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建支付订单

    支付规则:
    - TRIAL (试用版): 新用户自动获得14天，无需支付
    - FREE (免费版): 永久免费基础功能
    - PRO (专业版): 需要支付，99元/月 或 990元/年
    """
    # 验证目标计划
    if payment_data.plan_tier == "trial":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "TRIAL_AUTO_GRANTED",
                "message": "试用版在注册时自动获得，无需支付"
            }
        )

    if payment_data.plan_tier == "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "FREE_PLAN_AVAILABLE",
                "message": "免费版无需支付，直接使用即可"
            }
        )

    # 只允许升级到 Pro
    if payment_data.plan_tier != "pro":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PLAN", "message": "无效的订阅计划"}
        )

    # 检查是否已有 Pro 订阅
    existing = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.user_id == current_user.id,
                Subscription.status == "active",
                Subscription.plan_tier == "pro",
            )
        )
    )
    existing_sub = existing.scalar_one_or_none()

    if existing_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "ACTIVE_PRO_SUBSCRIPTION",
                "message": "您已有活跃的专业版订阅"
            }
        )

    # 获取定价
    amount = get_plan_pricing(payment_data.plan_tier, payment_data.billing_cycle)

    if amount is None or amount == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PAYMENT_NOT_REQUIRED", "message": "该计划无需支付"}
        )

    # 创建支付订单
    if payment_data.payment_method == PaymentMethod.WECHAT:
        order_result = await wechat_pay.create_order(
            user_id=str(current_user.id),
            plan_tier=payment_data.plan_tier,
            billing_cycle=payment_data.billing_cycle,
            amount=float(amount),
        )
        external_order_id = order_result.get("prepay_id")
        code_url = order_result.get("code_url")
        qrcode_url = f"/api/v1/payments/qrcode/{order_result['order_no']}"

    elif payment_data.payment_method == PaymentMethod.AIRWALLEX:
        # 使用 Airwallex 支付
        from models.user import User

        # 获取用户已有的 Airwallex Customer ID
        airwallex_customer_id = getattr(current_user, 'airwallex_customer_id', None)

        # 如果没有，尝试创建
        if not airwallex_customer_id:
            try:
                customer = await airwallex.create_customer(
                    user_id=str(current_user.id),
                    email=current_user.email,
                    name=getattr(current_user, 'name', current_user.email)
                )
                airwallex_customer_id = customer.get("id")
                # 保存到用户记录
                current_user.airwallex_customer_id = airwallex_customer_id
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to create Airwallex customer: {e}")
                # 即使客户创建失败，仍然可以创建支付意图

        # 创建支付意图（使用已有的客户 ID）
        return_url = f"https://www.zenconsult.top/billing?success=true"
        description = f"{payment_data.plan_tier} 订阅 - {payment_data.billing_cycle}"

        try:
            intent_result = await airwallex.create_payment_intent(
                amount_cny=int(amount),
                user_id=str(current_user.id),
                plan_tier=payment_data.plan_tier,
                billing_cycle=payment_data.billing_cycle,
                description=description,
                return_url=return_url,
                customer_email=current_user.email,
                airwallex_customer_id=airwallex_customer_id
            )
        except AirwallexError as e:
            logger.error(f"Airwallex error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": e.code, "message": e.message, "details": e.details}
            )

        order_result = {
            "order_no": intent_result["request_id"],
            "payment_intent_id": intent_result["payment_intent_id"],
            "customer_id": intent_result.get("customer_id"),
            "client_token": intent_result["client_token"]
        }
        external_order_id = intent_result["payment_intent_id"]
        code_url = None  # Airwallex uses embedded checkout, not QR code
        qrcode_url = None

    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"code": "PAYMENT_METHOD_NOT_SUPPORTED", "message": "暂不支持该支付方式"}
        )

    # 创建支付记录
    payment = Payment(
        id=uuid.uuid4(),
        user_id=current_user.id,
        subscription_id=None,  # 支付成功后创建订阅
        amount=amount,
        currency="CNY",
        payment_method=payment_data.payment_method.value,
        payment_status=PaymentStatus.PENDING.value,
        transaction_id=order_result["order_no"],
        external_order_id=external_order_id,
        extra_data=f'{{"plan_tier":"{payment_data.plan_tier}","billing_cycle":"{payment_data.billing_cycle}"}}',
    )

    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    # 生成响应数据
    response_data = PaymentOrderResponse(
        order_no=order_result["order_no"],
        amount=float(amount),
        currency="CNY",
        payment_method=payment_data.payment_method.value,
        code_url=code_url,
        qrcode_url=qrcode_url,
        client_token=order_result.get("client_token") if payment_data.payment_method == PaymentMethod.AIRWALLEX else None,
        payment_intent_id=order_result.get("payment_intent_id") if payment_data.payment_method == PaymentMethod.AIRWALLEX else None,
        expires_at=datetime.utcnow() + timedelta(hours=2),  # 订单2小时过期
    )

    # Airwallex 额外处理：保存 intent 记录和 client_token
    if payment_data.payment_method == PaymentMethod.AIRWALLEX:
        from models.airwallex import AirwallexPaymentIntent
        import json

        # 创建 AirwallexPaymentIntent 记录
        aw_intent = AirwallexPaymentIntent(
            payment_id=payment.id,
            user_id=current_user.id,
            airwallex_intent_id=intent_result["payment_intent_id"],
            merchant_order_id=intent_result["request_id"],
            amount_minor=int(amount) * 100,  # 转换为 fen
            currency="CNY",
            status="requires_payment_method",
            client_token=intent_result["client_token"],
            description=description,
            return_url=return_url,
            metadata={
                "plan_tier": payment_data.plan_tier,
                "billing_cycle": payment_data.billing_cycle
            }
        )
        db.add(aw_intent)

        # 保存 client_token 到 extra_data（前端兼容）
        extra = json.loads(payment.extra_data or "{}")
        extra["client_token"] = intent_result.get("client_token")
        extra["payment_intent_id"] = intent_result.get("payment_intent_id")
        payment.extra_data = json.dumps(extra)

        await db.commit()

    return response_data


# ============================================================================
# 公开端点（必须在参数化路由之前定义）
# ============================================================================

@router.get("/plans")
async def get_plans():
    """
    获取所有订阅计划信息

    Returns:
        包含 free, trial, pro 三种计划的详情
    """
    from config.subscriptions import get_all_plans_for_display

    plans = get_all_plans_for_display()

    return {
        "success": True,
        "plans": plans
    }


@router.get("/config")
async def get_payment_config(
    current_user: User = Depends(get_current_user),
):
    """
    获取支付配置信息（用于前端显示）

    Returns:
        用户当前订阅状态和可用计划
    """
    from config.subscriptions import get_all_plans_for_display, get_upgrade_target

    # 计算试用剩余天数
    trial_days_remaining = None
    if current_user.trial_ends_at:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if current_user.trial_ends_at > now:
            trial_days_remaining = (current_user.trial_ends_at - now).days
        else:
            trial_days_remaining = 0

    # 获取建议升级目标
    upgrade_target = get_upgrade_target(current_user.plan_tier)

    return {
        "success": True,
        "current_plan": {
            "tier": current_user.plan_tier,
            "status": current_user.plan_status,
            "trial_ends_at": current_user.trial_ends_at.isoformat() if current_user.trial_ends_at else None,
            "trial_days_remaining": trial_days_remaining,
        },
        "upgrade_target": upgrade_target,
        "plans": get_all_plans_for_display()
    }


# ============================================================================
# 参数化路由（必须放在最后）
# ============================================================================

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
    from config.redis import redis_client
    import json

    xml_data = await request.body()
    xml_str = xml_data.decode()

    # 验证签名
    is_valid, data = wechat_pay.verify_notify(xml_str)

    if not is_valid:
        logger.warning(f"Invalid payment notification signature")
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
            logger.warning(f"Payment not found for order: {order_no}")
            return wechat_pay.build_notify_response(False, "支付记录不存在")

        # 添加金额验证
        total_fee = data.get("total_fee")
        if total_fee != int(payment.amount * 100):
            logger.warning(f"Payment amount mismatch: {total_fee} != {payment.amount * 100}")
            return wechat_pay.build_notify_response(False, "金额不匹配")

        # 添加重放攻击防护（使用Redis）
        cache_key = f"payment_notify:{order_no}"
        existing = await redis_client.get(cache_key)
        if existing:
            logger.info(f"Payment already processed: {order_no}")
            return wechat_pay.build_notify_response(True, "OK")  # 已处理

        # 避免重复处理
        if payment.payment_status == PaymentStatus.COMPLETED.value:
            await redis_client.set(cache_key, "1", ex=3600)  # 1小时过期
            return wechat_pay.build_notify_response(True, "OK")

        # 更新支付状态
        payment.payment_status = PaymentStatus.COMPLETED.value
        payment.external_order_id = transaction_id
        payment.completed_at = datetime.utcnow()

        # 解析额外数据
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
                id=uuid.uuid4(),
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

        # 标记为已处理
        await redis_client.set(cache_key, "1", ex=3600)  # 1小时过期

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
            id=uuid.uuid4(),
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


@router.get("/airwallex/customer")
async def get_airwallex_customer(
    customer_id: str,
    current_user: User = Depends(get_current_user),
):
    """获取 Airwallex 客户详情"""
    try:
        customer = await airwallex.get_customer(customer_id)
        return {
            "success": True,
            "data": customer
        }
    except Exception as e:
        logger.error(f"Failed to get Airwallex customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "GET_CUSTOMER_FAILED", "message": str(e)}
        )


@router.post("/airwallex/customer/link")
async def link_airwallex_customer(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """将 Airwallex Customer ID 关联到当前用户"""
    current_user.airwallex_customer_id = customer_id
    await db.commit()

    logger.info(f"Linked Airwallex customer {customer_id} to user {current_user.id}")

    return {
        "success": True,
        "message": "Customer ID linked successfully",
        "customer_id": customer_id
    }


@router.post("/webhooks/airwallex")
async def airwallex_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Airwallex 支付回调"""
    from config.redis import redis_client
    from models.airwallex import AirwallexWebhookEvent
    import json

    # 获取签名头
    signature = request.headers.get("x-webhook-signature", "")
    timestamp = request.headers.get("x-webhook-timestamp", "")

    # 读取原始 payload
    raw_body = await request.body()
    payload_str = raw_body.decode()

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in Airwallex webhook")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # 获取事件信息
    event_id = payload.get("id")
    event_type = payload.get("name")

    if not event_id or not event_type:
        logger.warning("Missing event id or type in webhook")
        raise HTTPException(status_code=400, detail="Missing event data")

    logger.info(f"Received Airwallex webhook: {event_type} - {event_id}")

    # 验证签名
    is_valid = await airwallex.verify_webhook_signature(
        payload=payload_str,
        signature=signature,
        timestamp=timestamp
    )

    if not is_valid:
        logger.warning(f"Invalid Airwallex webhook signature for event {event_id}")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 防重放攻击（使用 Redis 和数据库）
    cache_key = f"airwallex_webhook:{event_id}"

    # 首先检查数据库是否已处理
    existing_event = await db.execute(
        select(AirwallexWebhookEvent).where(
            AirwallexWebhookEvent.event_id == event_id
        )
    )
    event_record = existing_event.scalar_one_or_none()

    if event_record and event_record.status == "processed":
        logger.info(f"Webhook event already processed: {event_id}")
        return {"status": "ok", "message": "already processed"}

    # 检查 Redis 缓存
    existing = await redis_client.get(cache_key)
    if existing:
        logger.info(f"Webhook event in cache: {event_id}")
        return {"status": "ok", "message": "already processed"}

    # 创建 webhook 事件记录
    webhook_event = AirwallexWebhookEvent(
        event_id=event_id,
        event_type=event_type,
        status="pending",
        payload=payload,
        signature=signature,
        timestamp=datetime.utcnow() if timestamp else None
    )
    db.add(webhook_event)
    await db.flush()  # 获取 ID 但不提交

    # 处理支付成功事件
    try:
        if event_type == "payment_intent.succeeded":
            await _process_airwallex_payment_success(payload, db)
        elif event_type == "payment_intent.failed":
            await _process_airwallex_payment_failed(payload, db)
        else:
            logger.info(f"Unhandled Airwallex event type: {event_type}")

        # 标记事件为已处理
        webhook_event.status = "processed"
        webhook_event.processed_at = datetime.utcnow()
        await db.commit()

        # 标记为已处理（1小时过期）
        await redis_client.set(cache_key, "1", ex=3600)

    except Exception as e:
        logger.error(f"Error processing Airwallex webhook {event_id}: {e}")
        webhook_event.status = "failed"
        webhook_event.error_message = str(e)
        await db.commit()
        raise  # Re-raise to trigger retry

    return {"status": "ok", "message": "processed"}


async def _process_airwallex_payment_success(payload: dict, db: AsyncSession):
    """处理 Airwallex 支付成功"""
    from models.airwallex import AirwallexPaymentIntent

    payment_intent_data = payload.get("data", {}).get("object", {})
    airwallex_intent_id = payment_intent_data.get("id")
    merchant_order_id = payment_intent_data.get("merchant_order_id")
    amount_minor = payment_intent_data.get("amount")
    currency = payment_intent_data.get("currency")
    metadata = payment_intent_data.get("metadata", {})

    # 查找或创建 AirwallexPaymentIntent 记录
    existing_intent = await db.execute(
        select(AirwallexPaymentIntent).where(
            AirwallexPaymentIntent.merchant_order_id == merchant_order_id
        )
    )
    intent_record = existing_intent.scalar_one_or_none()

    if intent_record:
        intent_record.status = "succeeded"
        intent_record.updated_at = datetime.utcnow()

    logger.info(f"Processing successful Airwallex payment: {airwallex_intent_id}")

    # 查找支付记录（通过 merchant_order_id）
    result = await db.execute(
        select(Payment).where(Payment.transaction_id == merchant_order_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        logger.warning(f"Payment not found for Airwallex intent: {merchant_order_id}")
        return

    # 避免重复处理
    if payment.payment_status == PaymentStatus.COMPLETED.value:
        logger.info(f"Payment already completed: {merchant_order_id}")
        return

    # 验证金额
    expected_amount = int(payment.amount * 100)  # 转换为 fen
    if int(amount_minor) != expected_amount:
        logger.warning(
            f"Airwallex amount mismatch: {amount_minor} != {expected_amount}"
        )
        payment.payment_status = PaymentStatus.FAILED.value
        await db.commit()
        return

    # 更新支付状态
    payment.payment_status = PaymentStatus.COMPLETED.value
    payment.external_order_id = airwallex_intent_id
    payment.completed_at = datetime.utcnow()

    # 解析元数据
    plan_tier = metadata.get("plan_tier", "pro")
    billing_cycle = metadata.get("billing_cycle", "monthly")

    # 计算订阅过期时间
    if billing_cycle == "yearly":
        expires_at = datetime.utcnow() + timedelta(days=365)
    else:
        expires_at = datetime.utcnow() + timedelta(days=30)

    # 创建或更新订阅
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
        subscription.payment_method = "airwallex"
    else:
        # 创建新订阅
        subscription = Subscription(
            id=uuid.uuid4(),
            user_id=payment.user_id,
            plan_tier=plan_tier,
            status="active",
            billing_cycle=billing_cycle,
            amount=float(payment.amount),
            started_at=datetime.utcnow(),
            expires_at=expires_at,
            auto_renew=True,
            payment_method="airwallex",
        )
        db.add(subscription)
        await db.flush()

    payment.subscription_id = str(subscription.id)
    await db.commit()

    logger.info(f"Airwallex payment processed successfully: {airwallex_intent_id}")


async def _process_airwallex_payment_failed(payload: dict, db: AsyncSession):
    """处理 Airwallex 支付失败"""
    from models.airwallex import AirwallexPaymentIntent

    payment_intent_data = payload.get("data", {}).get("object", {})
    merchant_order_id = payment_intent_data.get("merchant_order_id")
    airwallex_intent_id = payment_intent_data.get("id")
    error_message = payment_intent_data.get("last_payment_error", {}).get("message", "Unknown error")

    logger.warning(f"Processing failed Airwallex payment: {merchant_order_id} - {error_message}")

    # 更新 AirwallexPaymentIntent 状态
    existing_intent = await db.execute(
        select(AirwallexPaymentIntent).where(
            AirwallexPaymentIntent.merchant_order_id == merchant_order_id
        )
    )
    intent_record = existing_intent.scalar_one_or_none()

    if intent_record:
        intent_record.status = "failed"
        intent_record.updated_at = datetime.utcnow()

    # 查找并更新支付记录
    result = await db.execute(
        select(Payment).where(Payment.transaction_id == merchant_order_id)
    )
    payment = result.scalar_one_or_none()

    if payment:
        payment.payment_status = PaymentStatus.FAILED.value
        await db.commit()

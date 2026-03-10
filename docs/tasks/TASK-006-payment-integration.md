# TASK-006: 支付集成实现

> **所属会话**: 会话2（后端开发线）
> **优先级**: P0（最高）
> **预计工期**: 3天
> **依赖任务**: TASK-005（订阅管理系统）
> **创建日期**: 2025-03-10
> **状态**: ⏳ 待开始

---

## 任务目标

集成微信支付和支付宝，实现支付订单创建、支付回调处理、订阅状态更新等支付相关功能。

---

## 验收标准

- [ ] 微信支付统一下单API
- [ ] 支付宝统一下单API
- [ ] 微信支付回调处理
- [ ] 支付宝回调处理
- [ ] 支付成功后自动创建/更新订阅
- [ ] 支付记录查询API
- [ ] Webhook签名验证

---

## API规范

### 创建支付订单
```
POST /api/v1/payments/create
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "plan_tier": "pro",
  "billing_cycle": "monthly",
  "payment_method": "wechat"
}

Response 200:
{
  "success": true,
  "data": {
    "order_no": "CB20250310123456",
    "amount": 99.00,
    "currency": "CNY",
    "payment_method": "wechat",
    "code_url": "weixin://wxpay/bizpayurl?pr=xxxxx",  // 二维码链接
    "qrcode_url": "https://api.cb.3strategy.cc/api/v1/payments/qrcode/CB20250310123456"
  }
}
```

### 微信支付回调
```
POST /api/v1/payments/wechat/notify
Content-Type: application/xml

<xml>
  <return_code><![CDATA[SUCCESS]]></return_code>
  <result_code><![CDATA[SUCCESS]]></result_code>
  <out_trade_no><![CDATA[CB20250310123456]]></out_trade_no>
  <transaction_id><![CDATA[wx_transaction_id]]></transaction_id>
  ...
</xml>

Response:
<xml>
  <return_code><![CDATA[SUCCESS]]></return_code>
  <return_msg><![CDATA[OK]]></return_msg>
</xml>
```

### 查询支付状态
```
GET /api/v1/payments/{order_no}
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "order_no": "CB20250310123456",
    "amount": 99.00,
    "status": "completed",
    "payment_method": "wechat",
    "created_at": "2025-03-10T...",
    "completed_at": "2025-03-10T..."
  }
}
```

---

## 开发要点

### 微信支付服务

```python
# backend/services/wechat_pay.py
import hashlib
import random
import time
from datetime import datetime
from config.settings import settings

class WeChatPayService:
    """微信支付服务"""

    def __init__(self):
        self.app_id = settings.WECHAT_APP_ID
        self.mch_id = settings.WECHAT_MCH_ID
        self.api_key = settings.WECHAT_API_KEY
        self.notify_url = settings.WECHAT_NOTIFY_URL

    def _generate_sign(self, params: dict) -> str:
        """生成签名"""
        # 按字典序排序
        sorted_params = sorted(params.items())
        # 拼接参数字符串
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params if v])
        # 添加key
        param_str += f"&key={self.api_key}"
        # MD5加密并转大写
        return hashlib.md5(param_str.encode()).hexdigest().upper()

    async def create_order(
        self,
        user_id: str,
        plan_tier: str,
        billing_cycle: str,
        amount: float
    ) -> dict:
        """创建微信支付订单"""
        # 生成订单号
        order_no = f"CB{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000,9999)}"

        # 调用统一下单API
        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "nonce_str": self._generate_nonce(),
            "body": f"跨境电商专业版订阅({plan_tier})",
            "out_trade_no": order_no,
            "total_fee": int(amount * 100),  # 转换为分
            "spbill_create_ip": "127.0.0.1",
            "notify_url": self.notify_url,
            "trade_type": "NATIVE",  # 扫码支付
            "product_id": f"{plan_tier}_{billing_cycle}_{user_id}",
        }

        # 生成签名
        params["sign"] = self._generate_sign(params)

        # 调用微信API（使用httpx）
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.mch.weixin.qq.com/pay/unifiedorder",
                data=self._dict_to_xml(params),
                headers={"Content-Type": "application/xml"}
            )
            result = self._xml_to_dict(response.text)

        if result.get("return_code") == "SUCCESS":
            return {
                "order_no": order_no,
                "code_url": result.get("code_url"),
                "prepay_id": result.get("prepay_id")
            }
        else:
            raise Exception(f"微信支付下单失败: {result.get('return_msg')}")

    def verify_notify(self, xml_data: str) -> bool:
        """验证支付回调签名"""
        params = self._xml_to_dict(xml_data)
        sign = params.pop("sign", None)
        calculated_sign = self._generate_sign(params)
        return sign == calculated_sign
```

### 支付回调处理

```python
# backend/api/payments.py
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models.payments import Payment
from models.subscriptions import Subscription
from models.user import User
from services.wechat_pay import WeChatPayService
from config.database import get_db
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

wechat_pay = WeChatPayService()

@router.post("/wechat/notify")
async def wechat_notify(request: Request, db: AsyncSession = Depends(get_db)):
    """微信支付回调"""
    xml_data = await request.body()

    # 验证签名
    if not wechat_pay.verify_notify(xml_data.decode()):
        return {"return_code": "FAIL", "return_msg": "签名验证失败"}

    # 解析回调数据
    data = wechat_pay._xml_to_dict(xml_data.decode())

    if data.get("return_code") == "SUCCESS" and data.get("result_code") == "SUCCESS":
        order_no = data.get("out_trade_no")
        transaction_id = data.get("transaction_id")

        # 查找支付记录
        result = await db.execute(
            select(Payment).where(Payment.transaction_id == order_no)
        )
        payment = result.scalar_one_or_none()

        if payment and payment.payment_status != "completed":
            # 更新支付状态
            payment.payment_status = "completed"
            payment.transaction_id = transaction_id
            payment.completed_at = datetime.utcnow()

            # 创建或更新订阅
            subscription = Subscription(
                user_id=payment.user_id,
                plan_tier=payment.metadata["plan_tier"],
                status="active",
                billing_cycle=payment.metadata["billing_cycle"],
                amount=payment.amount,
                payment_method="wechat"
            )

            db.add(subscription)
            await db.commit()

        return {"return_code": "SUCCESS", "return_msg": "OK"}

    return {"return_code": "FAIL", "return_msg": "支付失败"}
```

---

## 测试要求

- [ ] 微信支付沙箱环境测试
- [ ] 支付回调签名验证测试
- [ ] 支付成功后订阅创建测试
- [ ] 订单状态查询测试

---

## 提交规范

```bash
git commit -m "feat(TASK-006): 集成微信支付

- 实现微信支付统一下单
- 实现支付回调处理
- 实现签名验证
- 支付成功自动创建订阅
- 添加支付记录查询API

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

*本任务书由主会话（项目经理）创建和维护*

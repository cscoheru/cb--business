# schemas/payment.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class PaymentMethod(str, Enum):
    """支付方式"""
    WECHAT = "wechat"
    ALIPAY = "alipay"
    AIRWALLEX = "airwallex"


class PaymentStatus(str, Enum):
    """支付状态"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentCreate(BaseModel):
    """创建支付订单请求"""
    plan_tier: str = Field(..., description="订阅计划层级", pattern="^(free|pro|enterprise)$")
    billing_cycle: str = Field(default="monthly", description="计费周期", pattern="^(monthly|yearly)$")
    payment_method: PaymentMethod = Field(default=PaymentMethod.WECHAT, description="支付方式")


class PaymentResponse(BaseModel):
    """支付响应"""
    id: str
    order_no: str
    user_id: str
    subscription_id: Optional[str] = None
    amount: float
    currency: str = "CNY"
    payment_method: str
    payment_status: str
    transaction_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreatePaymentResponse(BaseModel):
    """创建支付订单响应"""
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None


class PaymentOrderResponse(BaseModel):
    """支付订单响应"""
    order_no: str
    amount: float
    currency: str
    payment_method: str
    code_url: Optional[str] = None  # 微信支付二维码链接
    qrcode_url: Optional[str] = None  # 二维码图片URL
    client_token: Optional[str] = None  # Airwallex 前端 checkout token
    payment_intent_id: Optional[str] = None  # Airwallex 支付意图 ID
    expires_at: Optional[datetime] = None


class PaymentNotifyResponse(BaseModel):
    """支付回调响应"""
    return_code: str
    return_msg: str = "OK"


class PaymentQueryResponse(BaseModel):
    """支付查询响应"""
    order_no: str
    amount: float
    status: PaymentStatus
    payment_method: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    transaction_id: Optional[str] = None

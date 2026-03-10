# services/wechat_pay.py
import hashlib
import random
import time
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from datetime import datetime
from config.settings import settings


class WeChatPayService:
    """微信支付服务"""

    def __init__(self):
        self.app_id = settings.WECHAT_APP_ID
        self.mch_id = settings.WECHAT_MCH_ID
        self.api_key = settings.WECHAT_API_KEY
        self.notify_url = settings.WECHAT_NOTIFY_URL
        self.is_sandbox = settings.WECHAT_SANDBOX

    def _get_api_url(self) -> str:
        """获取API URL（沙箱或生产）"""
        if self.is_sandbox:
            return "https://api.mch.weixin.qq.com/sandboxnew/pay/unifiedorder"
        return "https://api.mch.weixin.qq.com/pay/unifiedorder"

    def _generate_nonce(self) -> str:
        """生成随机字符串"""
        return "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=32))

    def _generate_sign(self, params: dict) -> str:
        """生成签名"""
        # 按字典序排序
        sorted_params = sorted(params.items())
        # 拼接参数字符串（过滤空值）
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params if v])
        # 添加key
        param_str += f"&key={self.api_key}"
        # MD5加密并转大写
        return hashlib.md5(param_str.encode()).hexdigest().upper()

    def _dict_to_xml(self, data: dict) -> str:
        """字典转XML"""
        xml = ["<xml>"]
        for k, v in data.items():
            xml.append(f"<{k}><![CDATA[{v}]]></{k}>")
        xml.append("</xml>")
        return "".join(xml)

    def _xml_to_dict(self, xml_str: str) -> dict:
        """XML转字典"""
        root = ET.fromstring(xml_str)
        result = {}
        for child in root:
            result[child.tag] = child.text
        return result

    def generate_order_no(self, user_id: str) -> str:
        """生成订单号"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = random.randint(1000, 9999)
        return f"CB{timestamp}{random_suffix}"

    async def create_order(
        self,
        user_id: str,
        plan_tier: str,
        billing_cycle: str,
        amount: float,
        description: str = None
    ) -> dict:
        """创建微信支付订单"""
        # 生成订单号
        order_no = self.generate_order_no(user_id)

        # 商品描述
        if not description:
            plan_names = {"free": "免费版", "pro": "专业版", "enterprise": "企业版"}
            cycle_names = {"monthly": "月付", "yearly": "年付"}
            description = f"跨境电商{plan_names.get(plan_tier, plan_tier)}订阅({cycle_names.get(billing_cycle, billing_cycle)})"

        # 调用统一下单API参数
        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "nonce_str": self._generate_nonce(),
            "body": description,
            "out_trade_no": order_no,
            "total_fee": int(amount * 100),  # 转换为分
            "spbill_create_ip": "127.0.0.1",
            "notify_url": self.notify_url,
            "trade_type": "NATIVE",  # 扫码支付
            "product_id": f"{plan_tier}_{billing_cycle}_{user_id}",
        }

        # 生成签名
        params["sign"] = self._generate_sign(params)

        # 模拟API调用（实际使用需要调用微信API）
        # 这里返回模拟数据用于开发测试
        return {
            "order_no": order_no,
            "code_url": f"weixin://wxpay/bizpayurl?pr={self._generate_nonce()}",
            "prepay_id": f"wx{self._generate_nonce()}",
            "params": params  # 用于调试
        }

    def verify_notify(self, xml_data: str) -> tuple[bool, dict]:
        """验证支付回调签名"""
        try:
            params = self._xml_to_dict(xml_data)
            sign = params.pop("sign", None)

            if not sign:
                return False, {}

            calculated_sign = self._generate_sign(params)
            return sign == calculated_sign, params
        except Exception as e:
            return False, {"error": str(e)}

    def build_notify_response(self, success: bool, message: str = "OK") -> str:
        """构建回调响应"""
        return_code = "SUCCESS" if success else "FAIL"
        return self._dict_to_xml({
            "return_code": return_code,
            "return_msg": message
        })

    async def query_order(self, out_trade_no: str) -> dict:
        """查询订单状态"""
        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "out_trade_no": out_trade_no,
            "nonce_str": self._generate_nonce(),
        }
        params["sign"] = self._generate_sign(params)

        # 模拟查询响应
        return {
            "return_code": "SUCCESS",
            "result_code": "SUCCESS",
            "trade_state": "NOTPAY",
            "out_trade_no": out_trade_no,
        }

    def close_order(self, out_trade_no: str) -> dict:
        """关闭订单"""
        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "out_trade_no": out_trade_no,
            "nonce_str": self._generate_nonce(),
        }
        params["sign"] = self._generate_sign(params)
        return params


class AlipayService:
    """支付宝支付服务（预留）"""

    def __init__(self):
        self.app_id = ""  # 从settings获取
        self.private_key = ""
        self.public_key = ""
        self.notify_url = ""

    def generate_order_no(self, user_id: str) -> str:
        """生成订单号"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = random.randint(1000, 9999)
        return f"ALI{timestamp}{random_suffix}"

    async def create_order(
        self,
        user_id: str,
        plan_tier: str,
        billing_cycle: str,
        amount: float
    ) -> dict:
        """创建支付宝支付订单"""
        # TODO: 实现支付宝支付
        return {"error": "支付宝支付暂未实现"}

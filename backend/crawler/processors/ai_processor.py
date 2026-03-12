# crawler/processors/ai_processor.py
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# 可选导入 zhipuai
try:
    from zhipuai import ZhipuAI
    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False
    ZhipuAI = None

logger = logging.getLogger(__name__)


class AIProcessor:
    """AI内容分析处理器 - 使用智谱AI"""

    def __init__(self, api_key: str = ""):
        if not ZHIPUAI_AVAILABLE:
            raise ImportError("zhipuai 模块未安装。请运行: pip install zhipuai")
        if not api_key:
            raise ValueError("api_key 不能为空")
        self.client = ZhipuAI(api_key=api_key)
        self.model = "glm-4-flash"  # 使用快速响应模型

    async def analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """分析文章内容"""
        try:
            # 准备分析内容
            title = article.get("title", "")
            content = article.get("summary", "")[:500]
            full_content = article.get("full_content", "")[:500]

            # 构建分析提示词
            prompt = f"""你是跨境电商信息分析专家。请分析以下文章并返回JSON格式结果。

文章标题：{title}

文章摘要：{content}

文章内容：{full_content}

请按照以下JSON格式返回分析结果（只返回JSON，不要其他内容）：
{{
    "content_theme": "opportunity/risk/policy/guide/market/platform",
    "region": "southeast_asia/north_america/europe/latin_america/global",
    "platform": "amazon/shopee/lazada/shopify/tiktok/other",
    "tags": ["tag1", "tag2", "tag3"],
    "risk_level": "low/medium/high/critical",
    "opportunity_score": 0.0,
    "summary_cn": "简短的中文摘要（50字以内）"
}}

判断标准：
- content_theme: 根据内容判断主题类型
- region: 涉及的主要地区
- platform: 提到的电商平台
- risk_level: 对跨境电商的风险程度
- opportunity_score: 商机潜力评分（0-1之间的浮点数）
- summary_cn: 中文摘要

只返回JSON，不要其他说明文字。"""

            # 调用智谱AI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是跨境电商信息分析专家，擅长分析电商相关文章并提供结构化分析结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 降低温度以获得更稳定的结果
            )

            # 解析响应
            content = response.choices[0].message.content.strip()

            # 移除可能的markdown代码块标记
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            # 解析JSON
            analysis = json.loads(content)

            # 验证必要字段
            required_fields = ["content_theme", "region", "platform", "tags", "risk_level", "opportunity_score"]
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = self._get_default_value(field)

            logger.info(f"Successfully analyzed article: {title[:50]}")
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return self._get_default_analysis()

        except Exception as e:
            logger.error(f"Error analyzing article: {e}")
            return self._get_default_analysis()

    def _get_default_analysis(self) -> Dict[str, Any]:
        """获取默认分析结果"""
        return {
            "content_theme": "guide",
            "region": "global",
            "platform": "other",
            "tags": ["跨境电商"],
            "risk_level": "low",
            "opportunity_score": 0.5,
            "summary_cn": "待分析"
        }

    def _get_default_value(self, field: str) -> Any:
        """获取字段默认值"""
        defaults = {
            "content_theme": "guide",
            "region": "global",
            "platform": "other",
            "tags": [],
            "risk_level": "low",
            "opportunity_score": 0.5,
            "summary_cn": ""
        }
        return defaults.get(field)


class MockAIProcessor:
    """模拟AI处理器（用于开发测试）"""

    # 来源与地区的映射关系
    SOURCE_REGION_MAP = {
        "Tech in Asia": "southeast_asia",
        "e27": "southeast_asia",
        "雨果网": "southeast_asia",
        "亿恩网": "north_america",
        "Mercopress": "latin_america",
        "Retail Dive": "north_america",
        "Digital Commerce 360": "north_america",
        "EcommerceBytes": "north_america",
        "PYMNTS": "north_america",
        "Amazon Seller News": "north_america",
        "eBay Seller News": "north_america",
        "PayPal Blog": "north_america",
        "Stripe Blog": "north_america",
        "eMarketer": "global",
        "TechCrunch": "global",
    }

    # 来源与国家的映射关系
    SOURCE_COUNTRY_MAP = {
        "Tech in Asia": "sg",  # 新加坡
        "e27": "sg",  # 新加坡
        "雨果网": "cn",  # 中国
        "亿恩网": "cn",  # 中国
        "Mercopress": "br",  # 巴西
        "Retail Dive": "us",  # 美国
        "Digital Commerce 360": "us",  # 美国
        "EcommerceBytes": "us",  # 美国
        "PYMNTS": "us",  # 美国
        "Amazon Seller News": "us",  # 美国
        "eBay Seller News": "us",  # 美国
        "PayPal Blog": "us",  # 美国
        "Stripe Blog": "us",  # 美国
        "eMarketer": "us",  # 美国
        "TechCrunch": "us",  # 美国
    }

    # 区域内的国家关键词映射
    REGION_COUNTRY_KEYWORDS = {
        "southeast_asia": {
            "thailand": "th", "thai": "th", "bangkok": "th",
            "vietnam": "vn", "viet": "vn", "hanoi": "vn", "ho chi minh": "vn",
            "singapore": "sg", "singaporean": "sg",
            "malaysia": "my", "malaysian": "my", "kuala lumpur": "my",
            "indonesia": "id", "indonesian": "id", "jakarta": "id",
            "philippines": "ph", "philippine": "ph", "manila": "ph",
        },
        "north_america": {
            "united states": "us", "usa": "us", "u.s.": "us", "america": "us", "us-market": "us",
            "canada": "ca", "canadian": "ca",
            "mexico": "mx", "mexican": "mx",
        },
        "latin_america": {
            "brazil": "br", "brazilian": "br", "brasil": "br", "são paulo": "br", "rio": "br",
            "mexico": "mx", "mexican": "mx",
            "colombia": "co", "colombian": "co",
            "argentina": "ar", "argentinian": "ar",
            "chile": "cl",
            "peru": "pe",
        }
    }

    # 扩展的关键词列表
    SOUTHEAST_ASIA_KEYWORDS = [
        "southeast asia", "sea", "asean",
        "thailand", "vietnam", "viet", "singapore", "singaporean",
        "malaysia", "indonesia", "philippines", "philippine",
        "jakarta", "bangkok", "ho chi minh", "hanoi", "kuala lumpur",
        "shopee", "lazada", "tokopedia", "bukalapak",
        "tiktok shop southeast", "shopee "
    ]

    NORTH_AMERICA_KEYWORDS = [
        "north america", "usa", "us", "united states", "america", "american",
        "canada", "canadian", "mexico", "us-based", "u.s.", "us-market",
        "amazon us", "walmart", "target", "costco",
        "federal trade commission", "ftc", "fcc"
    ]

    LATIN_AMERICA_KEYWORDS = [
        "latin america", "latam", "latin american",
        "brazil", "brazilian", "brasil", "são paulo", "rio",
        "mexico", "mexican", "colombia", "colombian",
        "argentina", "chile", "peru", "mercado libre", "mercadolibre"
    ]

    async def analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """模拟分析文章内容"""
        # 根据标题和来源进行分类
        title = article.get("title", "").lower()
        summary = article.get("summary", "").lower()
        source = article.get("source", "")

        # 合并标题和摘要进行分析
        text_content = title + " " + summary

        # 首先根据来源推断地区
        region = self.SOURCE_REGION_MAP.get(source, "global")

        # 如果来源无法确定，通过关键词判断
        if region == "global":
            region = self._detect_region(text_content)

        # 推断国家代码
        country = self.SOURCE_COUNTRY_MAP.get(source)
        if not country and region != "global":
            # 如果来源没有映射，通过关键词推断国家
            country = self._detect_country(text_content, region)

        # 主题判断 - 扩展关键词
        if any(word in text_content for word in ["risk", "warning", "alert", "danger", "ban", "fraud", "scam", "lawsuit", "crime"]):
            content_theme = "risk"
            risk_level = "medium"
        elif any(word in text_content for word in ["opportunity", "growth", "expand", "launch", "new market", "emerging", "trend"]):
            content_theme = "opportunity"
            risk_level = "low"
        elif any(word in text_content for word in ["policy", "regulation", "law", "tax", "tariff", "compliance", "legal", "bill"]):
            content_theme = "policy"
            risk_level = "medium"
        elif any(word in text_content for word in ["platform", "amazon", "shopee", "lazada", "marketplace"]):
            content_theme = "platform"
            risk_level = "low"
        elif any(word in text_content for word in ["logistics", "shipping", "fulfillment", "warehouse", "delivery", "supply chain"]):
            content_theme = "logistics"
            risk_level = "low"
        else:
            content_theme = "guide"
            risk_level = "low"

        # 平台判断
        if any(word in text_content for word in ["amazon", "aws", "fba"]):
            platform = "amazon"
        elif any(word in text_content for word in ["shopee"]):
            platform = "shopee"
        elif any(word in text_content for word in ["lazada"]):
            platform = "lazada"
        elif any(word in text_content for word in ["shopify"]):
            platform = "shopify"
        elif any(word in text_content for word in ["tiktok shop", "tiktok"]):
            platform = "tiktok"
        elif any(word in text_content for word in ["mercado libre", "mercadolibre"]):
            platform = "mercadolibre"
        else:
            platform = "other"

        # 生成标签
        tags = ["跨境电商"]
        if region != "global":
            tags.append(region.replace("_", " "))
        if platform != "other":
            tags.append(platform)
        tags.append(content_theme)

        return {
            "content_theme": content_theme,
            "region": region,
            "country": country,  # ✅ 添加country字段
            "platform": platform,
            "tags": list(set(tags)),  # 去重
            "risk_level": risk_level,
            "opportunity_score": 0.7 if content_theme == "opportunity" else (0.6 if region != "global" else 0.4),
            "summary_cn": summary[:100] if summary else title[:100]
        }

    def _detect_country(self, text: str, region: str) -> Optional[str]:
        """通过关键词检测国家代码"""
        if region not in self.REGION_COUNTRY_KEYWORDS:
            return None

        country_keywords = self.REGION_COUNTRY_KEYWORDS[region]
        for keyword, code in country_keywords.items():
            if keyword in text:
                return code

        # 如果没有检测到具体国家，返回区域的默认国家
        defaults = {
            "southeast_asia": "th",  # 泰国作为东南亚默认
            "north_america": "us",  # 美国作为北美默认
            "latin_america": "br",  # 巴西作为拉美默认
        }
        return defaults.get(region)

    def _detect_region(self, text: str) -> str:
        """通过关键词检测地区"""
        # 检查东南亚关键词
        if any(word in text for word in self.SOUTHEAST_ASIA_KEYWORDS):
            return "southeast_asia"

        # 检查北美关键词
        if any(word in text for word in self.NORTH_AMERICA_KEYWORDS):
            return "north_america"

        # 检查拉美关键词
        if any(word in text for word in self.LATIN_AMERICA_KEYWORDS):
            return "latin_america"

        # 默认返回 global
        return "global"

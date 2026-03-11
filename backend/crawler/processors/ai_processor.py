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

    async def analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """模拟分析文章内容"""
        # 根据标题进行简单分类
        title = article.get("title", "").lower()
        summary = article.get("summary", "")

        # 简单规则判断
        if any(word in title for word in ["risk", "warning", "alert", "danger", "ban"]):
            content_theme = "risk"
            risk_level = "medium"
        elif any(word in title for word in ["opportunity", "growth", "expand", "launch"]):
            content_theme = "opportunity"
            risk_level = "low"
        elif any(word in title for word in ["policy", "regulation", "law", "tax"]):
            content_theme = "policy"
            risk_level = "medium"
        else:
            content_theme = "guide"
            risk_level = "low"

        # 地区判断
        if any(word in title for word in ["southeast asia", "sea", "thailand", "vietnam", "singapore"]):
            region = "southeast_asia"
        elif any(word in title for word in ["north america", "usa", "canada", "us"]):
            region = "north_america"
        elif any(word in title for word in ["europe", "uk", "germany", "france"]):
            region = "europe"
        elif any(word in title for word in ["latin america", "brazil", "mexico"]):
            region = "latin_america"
        else:
            region = "global"

        # 平台判断
        if any(word in title for word in ["amazon", "aws"]):
            platform = "amazon"
        elif any(word in title for word in ["shopee", "shopee"]):
            platform = "shopee"
        elif any(word in title for word in ["lazada"]):
            platform = "lazada"
        elif any(word in title for word in ["shopify"]):
            platform = "shopify"
        else:
            platform = "other"

        return {
            "content_theme": content_theme,
            "region": region,
            "platform": platform,
            "tags": ["电商", "跨境电商"],
            "risk_level": risk_level,
            "opportunity_score": 0.6 if content_theme == "opportunity" else 0.4,
            "summary_cn": summary[:100] if summary else title[:100]
        }

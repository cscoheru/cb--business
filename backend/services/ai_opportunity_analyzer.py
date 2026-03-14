# services/ai_opportunity_analyzer.py
"""AI商机分析器 - 智能商机发现与验证"""

import os
import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timezone

from zhipuai import ZhipuAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.business_opportunity import BusinessOpportunity, OpportunityStatus, OpportunityType
from models.article import Article

logger = logging.getLogger(__name__)


class AIOpportunityAnalyzer:
    """
    AI商机分析器

    职责：
    1. 分析信号，判断是否为商机
    2. 生成数据采集需求
    3. 评估新数据的质量
    4. 更新商机置信度
    """

    def __init__(self):
        """初始化AI分析器"""
        from config.settings import settings

        self.api_key = settings.ZHIPU_AI_KEY or os.getenv("ZHIPUAI_API_KEY")
        if not self.api_key:
            logger.warning("ZHIPUAI_API_KEY not set, using mock mode")
            self.mock_mode = True
        else:
            self.client = ZhipuAI(api_key=self.api_key)
            self.mock_mode = False
            logger.info("✅ ZHIPUAI_API_KEY configured, AI analysis enabled")

        # 加载Prompt模板
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        self.analysis_prompt = self._load_prompt("opportunity_analysis.txt")
        self.data_planning_prompt = self._load_prompt("data_request_planning.txt")

    def _load_prompt(self, filename: str) -> str:
        """加载Prompt模板"""
        prompt_path = self.prompts_dir / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        else:
            logger.warning(f"Prompt file not found: {filename}")
            return ""

    async def analyze_signal(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        分析信号，判断是否为商机

        Args:
            signal: 原始信号数据

        Returns:
            商机数据字典，如果不是商机则返回None
        """
        if self.mock_mode:
            return self._mock_analyze_signal(signal)

        try:
            # 构建完整的Prompt
            prompt = self._build_analysis_prompt(signal)

            # 调用GLM-4 Plus
            response = self.client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个跨境电商商机发现专家。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            # 解析响应
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            # 检查是否为商机
            if not result.get("is_opportunity"):
                logger.info(f"AI判断不是商机: {signal.get('title', 'N/A')}")
                return None

            # 转换为标准格式
            return self._normalize_opportunity_data(result, signal)

        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            # Fallback: 使用mock分析
            return self._mock_analyze_signal(signal)

    def _build_analysis_prompt(self, signal: Dict[str, Any]) -> str:
        """构建分析Prompt"""
        signal_json = json.dumps(signal, ensure_ascii=False, indent=2)

        prompt = f"""
{self.analysis_prompt}

## 请分析以下信号

```json
{signal_json}
```

请严格按照上述JSON格式输出分析结果。
"""
        return prompt

    def _normalize_opportunity_data(self, ai_result: Dict, signal: Dict) -> Dict[str, Any]:
        """标准化商机数据"""
        return {
            "title": ai_result.get("title", signal.get("title", "新商机")),
            "description": ai_result.get("description", ""),
            "opportunity_type": ai_result.get("opportunity_type", "product"),
            "elements": self._filter_null_elements(ai_result.get("elements", {})),
            "ai_insights": {
                "why_opportunity": ai_result.get("ai_insights", {}).get("why_opportunity", ""),
                "key_assumptions": ai_result.get("ai_insights", {}).get("key_assumptions", []),
                "verification_needs": ai_result.get("ai_insights", {}).get("verification_questions", []),
                "missing_information": ai_result.get("ai_insights", {}).get("missing_information", []),
                "data_requirements": ai_result.get("ai_insights", {}).get("data_requirements", []),
                "signal_source": signal.get("source", "unknown"),
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            },
            "confidence_score": ai_result.get("initial_confidence", 0.5),
            "status": OpportunityStatus.POTENTIAL.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    def _filter_null_elements(self, elements: Dict) -> Dict:
        """过滤掉null的elements"""
        return {k: v for k, v in elements.items() if v is not None}

    async def generate_data_requirements(
        self,
        opportunity: Dict[str, Any],
        verification_questions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        生成数据采集需求

        Args:
            opportunity: 商机数据
            verification_questions: 需要验证的问题列表

        Returns:
            数据采集任务列表
        """
        if self.mock_mode:
            return opportunity.get("ai_insights", {}).get("data_requirements", [])

        try:
            # 构建Prompt
            prompt = f"""
{self.data_planning_prompt}

## 请规划以下商机的数据采集需求

商机ID: {opportunity.get('id', 'N/A')}
当前置信度: {opportunity.get('confidence_score', 0.5)}
需要验证的问题:
{json.dumps(verification_questions, ensure_ascii=False, indent=2)}

请严格按照上述JSON格式输出数据采集计划。
"""

            response = self.client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {"role": "system", "content": "你是一个智能数据采集规划专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            return result.get("data_collection_plan", [])

        except Exception as e:
            logger.error(f"数据需求规划失败: {e}")
            return []

    async def update_with_new_data(
        self,
        opportunity: Dict[str, Any],
        new_data: Dict[str, Any],
        task_description: str
    ) -> Dict[str, Any]:
        """
        基于新数据更新商机判断

        Args:
            opportunity: 当前商机数据
            new_data: 新采集的数据
            task_description: 数据采集任务描述

        Returns:
            更新后的商机数据
        """
        old_confidence = opportunity.get("confidence_score", 0.5)

        # 评估新数据质量
        quality_assessment = await self._evaluate_data_quality(new_data)

        # 更新置信度
        confidence_change = self._calculate_confidence_change(
            old_confidence,
            quality_assessment
        )

        new_confidence = max(0.0, min(1.0, old_confidence + confidence_change))

        # 更新AI洞察
        ai_insights = opportunity.get("ai_insights", {})
        ai_insights["confidence_history"] = ai_insights.get("confidence_history", [])
        ai_insights["confidence_history"].append({
            "from": old_confidence,
            "to": new_confidence,
            "change": confidence_change,
            "data_source": task_description,
            "data_quality": quality_assessment.get("overall_score", 0.5),
            "reasoning": self._generate_confidence_reasoning(confidence_change, quality_assessment),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # 判断是否需要更多数据
        if new_confidence < 0.8 and quality_assessment.get("overall_score", 0) > 0.6:
            # 置信度不够且数据质量尚可，可能需要更多数据
            next_needs = await self._propose_next_data_collection(opportunity, new_data)
        else:
            next_needs = []

        ai_insights["data_requirements"] = next_needs

        # 更新商机
        opportunity["confidence_score"] = new_confidence
        opportunity["ai_insights"] = ai_insights
        opportunity["last_verification_at"] = datetime.now(timezone.utc)
        opportunity["updated_at"] = datetime.now(timezone.utc)

        return opportunity

    async def _evaluate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """评估采集数据的质量"""
        if self.mock_mode:
            return {"overall_score": 0.8, "completeness": 0.9, "relevance": 0.85}

        try:
            prompt = f"""
请评估以下数据的质量：

```json
{json.dumps(data, ensure_ascii=False, indent=2)}
```

请以JSON格式返回评估结果：
{{
    "overall_score": 0.0-1.0,
    "completeness": 0.0-1.0,
    "relevance": 0.0-1.0,
    "timeliness": 0.0-1.0,
    "limitations": ["限制1", "限制2"],
    "usefulness": "这个数据对验证商机的帮助程度"
}}
"""

            response = self.client.chat.completions.create(
                model="glm-4-flash",  # 用更快的模型
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            return json.loads(result_text)

        except Exception as e:
            logger.error(f"数据质量评估失败: {e}")
            return {"overall_score": 0.5, "completeness": 0.5, "relevance": 0.5}

    def _calculate_confidence_change(self, old_confidence: float, quality: Dict) -> float:
        """计算置信度变化"""
        quality_score = quality.get("overall_score", 0.5)

        # 数据质量高 → 增加置信度
        # 数据质量低 → 减少置信度
        if quality_score > 0.7:
            change = 0.1 * quality_score
        elif quality_score > 0.5:
            change = 0.05 * quality_score
        elif quality_score > 0.3:
            change = -0.05
        else:
            change = -0.1

        return change

    def _generate_confidence_reasoning(self, change: float, quality: Dict) -> str:
        """生成置信度变化说明"""
        if change > 0:
            return f"新数据验证了关键假设，数据质量评分{quality.get('overall_score', 0):.0%}"
        elif change < 0:
            return f"新数据与预期不符或质量不足，数据质量评分{quality.get('overall_score', 0):.0%}"
        else:
            return "新数据对判断无显著影响"

    async def _propose_next_data_collection(
        self,
        opportunity: Dict[str, Any],
        current_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """提出下一轮数据采集需求"""
        # 简化实现：返回已有的数据需求
        # 实际可以让AI分析当前数据缺口
        return opportunity.get("ai_insights", {}).get("data_requirements", [])

    async def generate_feasibility_report(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """生成可行性研究报告"""
        if self.mock_mode:
            return {
                "summary": "Mock可行性报告",
                "market_size": {"estimate": "中等", "reasoning": "基于产品销量"},
                "competition": {"level": "中等", "top_competitors": []},
                "entry_barriers": [],
                "roi_estimate": {"range": "6-18个月", "confidence": 0.6}
            }

        try:
            prompt = f"""
基于以下商机信息，生成一份可行性研究报告：

```json
{json.dumps(opportunity, ensure_ascii=False, indent=2)}
```

报告应包括：
1. 市场规模评估
2. 竞争格局分析
3. 进入壁垒
4. ROI预估
5. 风险因素
6. 建议

请以JSON格式返回。
"""

            response = self.client.chat.completions.create(
                model="glm-4-plus",
                messages=[
                    {"role": "system", "content": "你是一位资深的商业分析师。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            return json.loads(result_text)

        except Exception as e:
            logger.error(f"可行性报告生成失败: {e}")
            return {}

    # Mock模式实现（用于测试）
    def _mock_analyze_signal(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mock分析（用于无API密钥时）- 使用关键词匹配和规则引擎"""
        title = signal.get("title", "")
        content = signal.get("content", signal.get("summary", signal.get("description", "")))
        source = signal.get("source", "")

        # 合并文本进行分析
        text = (title + " " + content).lower()

        # 商机判断关键词
        opportunity_keywords = {
            "高": ["新政策", "降低成本", "增长", "机会", "进入", "推出", "扩张", "launch", "growth", "enter", "expand"],
            "中": ["平台", "品牌", "产品", "市场", "trend", "platform", "brand", "product", "market"],
            "低": ["新闻", "报道", "发布", "announce", "report"]
        }

        # 计算商机得分
        opportunity_score = 0
        for level, keywords in opportunity_keywords.items():
            for kw in keywords:
                if kw.lower() in text:
                    if level == "高":
                        opportunity_score += 2
                    elif level == "中":
                        opportunity_score += 1
                    else:
                        opportunity_score -= 1

        # 如果得分太低，不是商机
        if opportunity_score < 2:
            logger.info(f"Mock模式: 信号不是商机 (得分: {opportunity_score}) - {title[:50]}")
            return None

        # 确定商机类型
        opp_type = self._determine_opportunity_type(text, title)

        # 构建商机要素
        elements = self._build_elements_from_signal(text, opp_type, source)

        # 计算初始置信度 (基于关键词得分)
        initial_confidence = min(0.9, max(0.4, opportunity_score * 0.1))

        return {
            "title": title[:100] if len(title) > 100 else title,
            "description": content[:500] if len(content) > 500 else content,
            "opportunity_type": opp_type,
            "elements": elements,
            "ai_insights": {
                "why_opportunity": f"基于关键词分析，信号包含 {opportunity_score} 个商机指标",
                "key_assumptions": self._extract_key_assumptions(text, opp_type),
                "verification_needs": self._generate_verification_questions(opp_type),
                "missing_information": self._identify_missing_info(text, opp_type),
                "data_requirements": self._generate_initial_data_requirements(opp_type),
                "signal_source": source,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "analysis_mode": "mock_keyword_matching"
            },
            "confidence_score": initial_confidence,
            "status": OpportunityStatus.POTENTIAL.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    def _determine_opportunity_type(self, text: str, title: str) -> str:
        """确定商机类型"""
        type_keywords = {
            OpportunityType.PRODUCT: ["产品", "product", "爆款", "热销", "需求", "demand", "销量", "sales"],
            OpportunityType.POLICY: ["政策", "policy", "税收", "tax", "法规", "regulation", "关税", "tariff", "自贸", "fta"],
            OpportunityType.PLATFORM: ["平台", "platform", "tiktok", "shopee", "lazada", "amazon", "算法", "algorithm"],
            OpportunityType.BRAND: ["品牌", "brand", "anker", "小米", "samsung", "apple", "进入", "enter"],
            OpportunityType.REGION: ["东南亚", "southeast asia", "泰国", "thailand", "越南", "vietnam", "马来西亚", "malaysia"],
            OpportunityType.INDUSTRY: ["行业", "industry", "趋势", "trend", "电商", "ecommerce"]
        }

        max_score = 0
        best_type = OpportunityType.PRODUCT

        for opp_type, keywords in type_keywords.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            if score > max_score:
                max_score = score
                best_type = opp_type

        return best_type.value

    def _build_elements_from_signal(self, text: str, opp_type: str, source: str) -> Dict[str, Any]:
        """从信号构建商机要素"""
        elements = {}

        # 地区识别
        regions = {
            "东南亚": ["southeast asia", "sea", "asean", "东南亚", "泰国", "越南", "马来西亚", "印尼"],
            "北美": ["north america", "usa", "us", "united states", "美国", "加拿大"],
            "拉美": ["latin america", "latam", "巴西", "brazil", "墨西哥", "mexico"],
            "欧洲": ["europe", "欧盟", "european"]
        }

        for region, keywords in regions.items():
            if any(kw in text for kw in keywords):
                elements["region"] = {
                    "focus": region,
                    "opportunity_reason": "信号提及该地区"
                }
                break

        # 平台识别
        platforms = ["tiktok shop", "shopee", "lazada", "amazon", "shopify"]
        for platform in platforms:
            if platform in text:
                elements["platform"] = {
                    "focus": platform.title(),
                    "opportunity_reason": "信号提及该平台"
                }
                break

        # 产品/行业识别
        if opp_type == OpportunityType.PRODUCT.value:
            elements["product"] = {
                "focus": "待AI分析确定具体品类",
                "opportunity_reason": "信号提及产品相关机会"
            }
        elif opp_type == OpportunityType.INDUSTRY.value:
            elements["industry"] = {
                "focus": "跨境电商",
                "opportunity_reason": "信号涉及行业趋势"
            }

        return elements

    def _extract_key_assumptions(self, text: str, opp_type: str) -> List[str]:
        """提取关键假设"""
        assumptions = []

        if "增长" in text or "growth" in text:
            assumptions.append("市场将持续增长")
        if "降低成本" in text or "reduce cost" in text:
            assumptions.append("政策会降低运营成本")
        if "新" in text or "new" in text:
            assumptions.append("这是新的机会窗口")

        return assumptions if assumptions else ["需要验证市场反应"]

    def _generate_verification_questions(self, opp_type: str) -> List[str]:
        """生成验证问题"""
        questions = {
            OpportunityType.PRODUCT.value: [
                "目标市场的需求规模如何？",
                "竞争格局是否饱和？",
                "价格是否有竞争力？"
            ],
            OpportunityType.POLICY.value: [
                "政策的具体实施细节是什么？",
                "哪些品类最受益？",
                "申请门槛是什么？"
            ],
            OpportunityType.PLATFORM.value: [
                "平台流量红利期有多长？",
                "入驻门槛是什么？",
                "现有卖家反馈如何？"
            ]
        }

        return questions.get(opp_type, ["需要进一步验证商机的可行性"])

    def _identify_missing_info(self, text: str, opp_type: str) -> List[str]:
        """识别缺失信息"""
        missing = []

        # 检查关键信息是否存在
        if "价格" not in text and "price" not in text:
            missing.append("价格信息")
        if "时间" not in text and "when" not in text and "日期" not in text:
            missing.append("具体时间")
        if "数据" not in text and "data" not in text:
            missing.append("市场数据")

        return missing if missing else ["需要更多市场数据"]

    def _generate_initial_data_requirements(self, opp_type: str) -> List[Dict[str, Any]]:
        """生成初始数据需求"""
        requirements = []

        if opp_type == OpportunityType.PRODUCT.value:
            requirements.append({
                "priority": "high",
                "question": "目标市场的用户反馈如何？",
                "data_needed": {
                    "type": "product_reviews",
                    "scope": {"region": "待确定", "category": "待确定"},
                    "constraints": {"sample_size": 50}
                },
                "source_suggestion": "Amazon/Shopee评论数据",
                "expected_outcome": "用户满意度、主要优缺点"
            })
        elif opp_type == OpportunityType.POLICY.value:
            requirements.append({
                "priority": "high",
                "question": "政策的详细条款是什么？",
                "data_needed": {
                    "type": "policy_details",
                    "scope": {"policy": "待确定"},
                    "constraints": {}
                },
                "source_suggestion": "官方公告",
                "expected_outcome": "政策细则、申请条件"
            })

        return requirements

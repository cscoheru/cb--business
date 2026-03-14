# services/task_generation.py
"""数据采集任务生成器 - AI分析需要采集什么数据

这是OpenClaw+AI智能协同系统的第二层：
分析C-P-I分数，识别需要验证的数据点，生成有针对性的数据采集任务
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from models.business_opportunity import DataCollectionTask, TaskPriority

logger = logging.getLogger(__name__)


class DataCollectionTaskGenerator:
    """数据采集任务生成器"""

    # 类目关键词映射
    CATEGORY_KEYWORDS = {
        'wireless_earbuds': ['无线耳机', 'earbuds', 'TWS', '蓝牙耳机'],
        'phone_chargers': ['充电器', 'charger', 'fast charging', '充电头'],
        'phone_cases': ['手机壳', 'phone case', 'case', '保护壳'],
        'bluetooth_speakers': ['蓝牙音箱', 'speakers', '便携音箱'],
        'desk_lamps': ['台灯', 'desk lamp', 'LED lamp'],
        'smart_plugs': ['智能插座', 'smart plug', '插座'],
        'keyboards': ['键盘', 'keyboard', '机械键盘'],
        'mouse': ['鼠标', 'mouse', '无线鼠标'],
        'fitness_trackers': ['健身手环', 'fitness tracker', '智能手环'],
        'yoga_mats': ['瑜伽垫', 'yoga mat', '运动垫'],
        'coffee_makers': ['咖啡机', 'coffee maker', '咖啡'],
        'webcams': ['摄像头', 'webcam', '网络摄像头']
    }

    async def generate_tasks(
        self,
        lead: Dict[str, Any],
        opportunity_id: str
    ) -> List[DataCollectionTask]:
        """
        为单个线索生成数据采集任务

        根据C-P-I三维度分数，智能判断需要采集哪些验证数据：

        竞争度(C)低 → 需要验证品牌分布、CPC、新品速度
        增长潜力(P)波动 → 需要验证关键词趋势、社交媒体声量
        信息差(I)高 → 需要深度分析竞品差评、痛点集中度

        Args:
            lead: 包含card和cpi_score的字典
            opportunity_id: 关联的商机ID

        Returns:
            数据采集任务列表
        """
        try:
            card = lead['card']
            cpi_score = lead['cpi_score']
            tasks = []

            # 任务1: 竞争度深度分析 (C值 < 65时需要)
            competition_score = cpi_score['competition']['score']
            if competition_score < 65:
                task = DataCollectionTask(
                    opportunity_id=opportunity_id,
                    task_type='competition_analysis',
                    priority=TaskPriority.HIGH if competition_score < 50 else TaskPriority.MEDIUM,
                    ai_request={
                        'question': f'{card.category}类目的竞争格局如何？是否有新进入者机会？',
                        'data_needed': [
                            'Top10品牌的市场份额及其变化趋势',
                            '近30天新上架产品数量和速度',
                            '平均CPC出价和广告竞争度',
                            '价格区间分布'
                        ],
                        'constraints': {
                            'time_range': 'last_30_days',
                            'sample_size': 'top_50_products'
                        },
                        'outcome_format': {
                            'brand_concentration': 'float (0-1)',  # 0=分散, 1=垄断
                            'new_product_velocity': 'int (products/week)',
                            'estimated_cpc': 'float (USD)',
                            'price_distribution': 'dict'
                        }
                    },
                    channel_name='oxylabs-competition-monitor',
                    execution_params={
                        'category': card.category,
                        'search_query': self._get_search_query(card.category),
                        'depth': 'top_50_products',
                        'analyze_brand_shares': True,
                        'analyze_new_products': True,
                        'estimate_cpc': True
                    },
                    expected_outcome={
                        'will_improve': 'competition_score',
                        'expected_impact': 'high' if competition_score < 50 else 'medium'
                    }
                )
                tasks.append(task)
                logger.info(f"生成竞争度验证任务: {card.category} (当前C值: {competition_score})")

            # 任务2: 增长潜力验证 (P值在50-85之间需要验证)
            potential_score = cpi_score['potential']['score']
            if 50 < potential_score < 85:
                task = DataCollectionTask(
                    opportunity_id=opportunity_id,
                    task_type='potential_analysis',
                    priority=TaskPriority.MEDIUM,
                    ai_request={
                        'question': f'{card.category}的增长趋势是否可持续？是否有季节性波动？',
                        'data_needed': [
                            '近30天关键词搜索量变化趋势',
                            '社交媒体(Instagram/TikTok)声量趋势',
                            '竞品评论增长速度',
                            '是否有季节性或事件驱动因素'
                        ],
                        'constraints': {
                            'time_range': '30d',
                            'sources': ['google_trends', 'social_media', 'amazon_reviews']
                        },
                        'outcome_format': {
                            'keyword_growth_rate': 'float (%)',
                            'social_mentions_trend': 'str (rising/stable/declining)',
                            'review_velocity': 'float (reviews/day)',
                            'seasonality_detected': 'bool'
                        }
                    },
                    channel_name='google-trends-monitor',
                    execution_params={
                        'keywords': self.CATEGORY_KEYWORDS.get(card.category, [card.category]),
                        'time_range': '30d',
                        'granularity': 'daily'
                    },
                    expected_outcome={
                        'will_improve': 'potential_score',
                        'expected_impact': 'medium'
                    }
                )
                tasks.append(task)
                logger.info(f"生成增长潜力验证任务: {card.category} (当前P值: {potential_score})")

            # 任务3: 信息差深度分析 (I值 > 75时重点验证，这是AI的核心战场)
            intelligence_score = cpi_score['intelligence_gap']['score']
            if intelligence_score > 75:
                # 获取Top产品的ASIN列表
                top_asins = self._extract_top_asins(card, limit=10)

                task = DataCollectionTask(
                    opportunity_id=opportunity_id,
                    task_type='intelligence_gap_analysis',
                    priority=TaskPriority.HIGH if intelligence_score > 85 else TaskPriority.MEDIUM,
                    ai_request={
                        'question': f'用户在{card.category}产品中最不满意的是什么？有哪些未被满足的需求？',
                        'data_needed': [
                            '竞品3星以下评论的文本内容和情感分析',
                            '高频负面关键词和短语统计',
                            '痛点集中度计算（是否存在共性痛点）',
                            '用户提出的改进建议和期望功能'
                        ],
                        'constraints': {
                            'rating_filter': 'below_3_stars',
                            'sample_size': 'min_100_reviews',
                            'asins': top_asins
                        },
                        'outcome_format': {
                            'top_pain_points': 'List[str]',  # 痛点列表
                            'pain_point_concentration': 'float (0-1)',  # 集中度
                            'improvement_opportunities': 'List[str]',  # 改进机会
                            'sentiment_keywords': 'Dict[str, int]',  # 负面词频
                            'user_suggestions': 'List[str]'  # 用户建议
                        }
                    },
                    channel_name='amazon-review-scraper',
                    execution_params={
                        'asins': top_asins,
                        'filter': 'rating_below_3',
                        'max_reviews_per_asin': 50,
                        'sentiment_analysis': True,
                        'keyword_extraction': True
                    },
                    expected_outcome={
                        'will_improve': 'intelligence_gap_score',
                        'expected_impact': 'critical' if intelligence_score > 85 else 'high'
                    }
                )
                tasks.append(task)
                logger.info(f"生成信息差深度分析任务: {card.category} (当前I值: {intelligence_score})")

            # 任务4: 价格追踪 (如果C值和P值都中等，补充价格数据)
            if 50 < competition_score < 70 and 50 < potential_score < 75:
                task = DataCollectionTask(
                    opportunity_id=opportunity_id,
                    task_type='price_tracking',
                    priority=TaskPriority.LOW,
                    ai_request={
                        'question': f'{card.category}的价格分布和利润空间如何？',
                        'data_needed': [
                            'Top20产品的价格分布',
                            '最低价和最高价的差距',
                            '是否存在价格战迹象'
                        ],
                        'outcome_format': {
                            'price_range': 'dict {min, max, avg}',
                            'price_distribution': 'dict',
                            'margin_estimate': 'float (%)'
                        }
                    },
                    channel_name='oxylabs-price-tracker',
                    execution_params={
                        'category': card.category,
                        'sample_size': 20
                    },
                    expected_outcome={
                        'will_improve': 'competition_score',
                        'expected_impact': 'low'
                    }
                )
                tasks.append(task)

            logger.info(f"为商机 {opportunity_id} 生成了 {len(tasks)} 个数据采集任务")
            return tasks

        except Exception as e:
            logger.error(f"生成数据采集任务失败: {e}")
            return []

    def _get_search_query(self, category: str) -> str:
        """获取品类的搜索查询"""
        queries = {
            'wireless_earbuds': 'wireless earbuds bluetooth',
            'phone_chargers': 'phone charger fast charging',
            'phone_cases': 'phone case protective',
            'bluetooth_speakers': 'bluetooth speaker portable',
            'desk_lamps': 'LED desk lamp',
            'smart_plugs': 'smart plug outlet',
            'keyboards': 'mechanical keyboard wireless',
            'mouse': 'wireless mouse ergonomic',
            'fitness_trackers': 'fitness tracker watch',
            'yoga_mats': 'yoga mat non slip',
            'coffee_makers': 'coffee maker programmable',
            'webcams': 'HD webcam 1080p'
        }
        return queries.get(category, category)

    def _extract_top_asins(self, card: Dict[str, Any], limit: int = 10) -> List[str]:
        """从Card的amazon_data中提取Top ASIN列表"""
        products = card.get('amazon_data', {}).get('products', [])
        asins = []

        for product in products[:limit]:
            asin = product.get('asin')
            if asin:
                asins.append(asin)

        return asins


# 全局单例
task_generator = DataCollectionTaskGenerator()

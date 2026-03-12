# api/keywords.py
"""关键词 API - 从文章中动态提取关键词"""
from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Dict, Any
import logging
import json
from collections import Counter

from models.article import Article
from config.database import get_db

router = APIRouter(prefix="/api/v1/keywords", tags=["keywords"])
logger = logging.getLogger(__name__)


def extract_keywords_from_text(text: str, min_length: int = 2) -> List[str]:
    """从文本中提取关键词"""
    if not text:
        return []

    # 常见停用词
    stop_words = {
        '的', '了', '是', '在', '和', '与', '或', '但', '而', '等', '对', '就', '都', '要',
        '可以', '这', '那', '这个', '那个', '一个', '一些', '如何', '什么', '为什么',
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'and', 'or', 'but', 'in', 'on',
        'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'be', 'this', 'that'
    }

    # 从tags中提取（如果存在）
    # 从title中提取中文/英文关键词
    import re

    # 匹配中文词汇（2-4个字符）
    chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)

    # 匹配英文单词
    english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)

    all_words = chinese_words + english_words

    # 过滤停用词和短词
    keywords = [w for w in all_words if w not in stop_words and len(w) >= min_length]

    return keywords


@router.get("/categories")
async def get_keyword_categories(
    region: str = Query(None, description="区域筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取文章分类关键词统计（基于真实文章数据）"""

    # 构建查询条件
    conditions = [Article.is_processed == True]
    if region:
        conditions.append(Article.region == region)

    # 获取所有文章
    result = await db.execute(
        select(Article).where(and_(*conditions))
    )
    articles = result.scalars().all()

    # 预定义分类映射
    category_mapping = {
        # 中文分类
        '电子': ['电子', '数码', '手机', '电脑', '智能', '科技', '芯片', '硬件'],
        '美妆': ['美妆', '化妆品', '护肤', '彩妆', '美容', '时尚'],
        '家居': ['家居', '家具', '家电', '生活', '厨具', '装饰'],
        '服饰': ['服饰', '服装', '鞋', '包包', '配饰', '时尚'],
        '食品': ['食品', '饮料', '零食', '生鲜', '餐饮', '美食'],
        '母婴': ['母婴', '婴儿', '儿童', '玩具', '奶粉', '尿布'],
        '运动': ['运动', '健身', '户外', '体育', '瑜伽', '跑步'],
        '宠物': ['宠物', '狗', '猫', '宠物用品', '饲料'],
        # 英文分类
        'electronics': ['electronics', 'digital', 'smartphone', 'laptop', 'tech', 'gadget'],
        'beauty': ['beauty', 'cosmetic', 'skincare', 'makeup', 'fashion'],
        'home': ['home', 'furniture', 'appliance', 'kitchen', 'decor'],
        'fashion': ['fashion', 'clothing', 'shoes', 'accessories'],
        'food': ['food', 'beverage', 'snack', 'restaurant'],
        'baby': ['baby', 'infant', 'toy', 'formula'],
        'sports': ['sports', 'fitness', 'outdoor', 'yoga'],
        'pets': ['pets', 'dog', 'cat', 'pet'],
    }

    # 统计每个分类的文章数
    category_counts = {}
    for article in articles:
        # 组合文本用于关键词匹配
        text = f"{article.title or ''} {article.summary or ''} {article.content_theme or ''}"
        text_lower = text.lower()

        matched = False
        for category, keywords in category_mapping.items():
            if any(kw in text_lower for kw in keywords):
                category_counts[category] = category_counts.get(category, 0) + 1
                matched = True
                break

        # 如果没有匹配到任何分类，使用content_theme作为分类
        if not matched and article.content_theme:
            theme = article.content_theme.lower()
            if 'policy' in theme:
                category_counts['policy'] = category_counts.get('policy', 0) + 1
            elif 'opportunity' in theme:
                category_counts['opportunity'] = category_counts.get('opportunity', 0) + 1
            elif 'risk' in theme:
                category_counts['risk'] = category_counts.get('risk', 0) + 1

    # 转换为响应格式
    categories = []
    emoji_map = {
        '电子': '📱', 'electronics': '📱',
        '美妆': '💄', 'beauty': '💄',
        '家居': '🏠', 'home': '🏠',
        '服饰': '👗', 'fashion': '👗',
        '食品': '🍜', 'food': '🍜',
        '母婴': '👶', 'baby': '👶',
        '运动': '⚽', 'sports': '⚽',
        '宠物': '🐕', 'pets': '🐕',
        'policy': '📜',
        'opportunity': '💡',
        'risk': '⚠️',
    }

    name_map = {
        'electronics': '电子', 'beauty': '美妆', 'home': '家居',
        'fashion': '服饰', 'food': '食品', 'baby': '母婴',
        'sports': '运动', 'pets': '宠物',
        'policy': '政策', 'opportunity': '机会', 'risk': '风险',
    }

    for cat_id, count in category_counts.items():
        categories.append({
            "id": cat_id,
            "name": name_map.get(cat_id, cat_id),
            "emoji": emoji_map.get(cat_id, "📁"),
            "count": count
        })

    # 按数量排序
    categories.sort(key=lambda x: x["count"], reverse=True)

    return {"categories": categories}


@router.get("/trending")
async def get_trending_keywords(
    region: str = Query(None, description="区域筛选"),
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取热门关键词（基于文章频率统计）"""

    # 构建查询条件
    conditions = [Article.is_processed == True]
    if region:
        conditions.append(Article.region == region)

    # 获取所有文章
    result = await db.execute(
        select(Article).where(and_(*conditions))
    )
    articles = result.scalars().all()

    # 提取所有关键词
    all_keywords = []
    for article in articles:
        # 从tags提取
        if article.tags:
            try:
                tags = json.loads(article.tags) if isinstance(article.tags, str) else article.tags
                all_keywords.extend(tags)
            except:
                pass

        # 从title提取
        title_keywords = extract_keywords_from_text(article.title or "")
        all_keywords.extend(title_keywords)

    # 统计关键词频率
    keyword_counter = Counter(all_keywords)

    # 转换为响应格式
    trending = []
    for keyword, count in keyword_counter.most_common(limit):
        trending.append({
            "keyword": keyword,
            "count": count
        })

    return {"keywords": trending}


@router.get("/by-region")
async def get_keywords_by_region(
    db: AsyncSession = Depends(get_db)
):
    """按区域获取关键词统计"""

    # 获取所有已处理的文章
    result = await db.execute(
        select(Article.region, Article.content_theme, Article.tags)
        .where(Article.is_processed == True)
    )
    articles = result.all()

    # 按区域统计
    region_keywords = {}
    for region, theme, tags in articles:
        if not region:
            continue

        if region not in region_keywords:
            region_keywords[region] = {
                "total": 0,
                "themes": Counter(),
                "tags": Counter()
            }

        region_keywords[region]["total"] += 1

        if theme:
            region_keywords[region]["themes"][theme] += 1

        if tags:
            try:
                tag_list = json.loads(tags) if isinstance(tags, str) else tags
                for tag in tag_list:
                    region_keywords[region]["tags"][tag] += 1
            except:
                pass

    # 转换为响应格式
    result_data = []
    for region, data in region_keywords.items():
        result_data.append({
            "region": region,
            "total_articles": data["total"],
            "top_themes": [
                {"theme": theme, "count": count}
                for theme, count in data["themes"].most_common(5)
            ],
            "top_tags": [
                {"tag": tag, "count": count}
                for tag, count in data["tags"].most_common(10)
            ]
        })

    return {"regions": result_data}

# Freemium变现策略设计

> **核心问题**：如何让用户在试用期内持续使用、留下痕迹，到期后不得不购买？
> **解决方案**：投资循环 + 渐进式价值披露 + 损失厌恶触发

---

## 用户心理分析

### 免费用户的行为模式

```
第一天：注册 → 探索 → 发现价值
   ↓
第2-7天：持续使用 → 开始投入时间 → 建立习惯
   ↓
第8-14天：深度使用 → 收藏机会 → 建立数据资产
   ↓
第15-30天：依赖形成 → 日常决策依赖平台 → 试用到期
   ↓
决策点：放弃已投入的数据 OR 继续订阅？
```

### 关键洞察

**用户的痛点不是"没有价值"，而是"失去已积累的价值"**

- ❌ 错误思维：限制功能，让用户感到不便
- ✅ 正确思维：让用户建立数据资产，到期后失去这些资产会痛

---

## Freemium层级设计

### 三层模型

```
┌─────────────────────────────────────────────────────────┐
│  Free Tier (永久免费)                                    │
│  目标：让用户体验核心价值，建立使用习惯                   │
├─────────────────────────────────────────────────────────┤
│  ✓ 每天3个机会卡片（AI精选，价值高）                      │
│  ✓ 基础市场趋势数据（7天内）                             │
│  ✓ 单个产品详情查看                                      │
│  ✓ 保存最多5个机会到收藏夹                               │
│  ✗ AI深度分析报告                                        │
│  ✗ 竞品对比                                              │
│  ✗ 历史数据追踪                                          │
│  ✗ 导出功能                                              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Trial Tier (14天免费试用)                               │
│  目标：让用户深度使用，积累数据资产                       │
├─────────────────────────────────────────────────────────┤
│  ✓ Free所有功能                                          │
│  ✓ 无限机会卡片                                          │
│  ✓ AI深度分析报告（每天10份）                            │
│  ✓ 竞品对比（每天5次）                                   │
│  ✓ 保存无限机会                                          │
│  ✓ 个人仪表盘（使用统计、收藏管理）                       │
│  ✓ 市场趋势（90天历史数据）                              │
│  ✓ 价格追踪（收藏产品价格变化提醒）                       │
│  ✓ 邮件周报（个性化机会推荐）                            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Pro Tier (付费订阅 - $29/月 或 $299/年)                 │
│  目标：专业卖家全功能工具                                │
├─────────────────────────────────────────────────────────┤
│  ✓ Trial所有功能                                         │
│  ✓ 无限AI分析                                            │
│  ✓ 供应链信息（供应商匹配）                               │
│  ✓ 利润计算器（成本、物流、税费）                         │
│  ✓ 竞品监控（实时价格、库存变化）                         │
│  ✓ 数据导出（CSV、Excel、API）                           │
│  ✓ 团队协作（多用户、权限管理）                           │
│  ✓ 优先客服                                              │
│  ✓ 新功能优先体验                                        │
└─────────────────────────────────────────────────────────┘
```

---

## 投资循环设计（核心创新）

### 原理：让用户的时间投入变成不可放弃的资产

### 循环1：收藏积累循环

```
用户行为：收藏机会
   ↓
系统记录：
  • 收藏时间
  • 收藏原因（用户可选标签）
  • 产品信息快照
  • 市场数据快照
  • AI分析报告
   ↓
持续价值：
  • 价格变化提醒（降价通知）
  • 市场趋势更新（需求上升/下降）
  • 新竞争者进入提醒
  • 相关机会推荐
   ↓
用户依赖：每天查看收藏夹的变化
   ↓
资产积累：7天后收藏夹有10-20个机会
   ↓
损失痛点：试用到期，失去这些追踪数据
```

**技术实现：**

```python
# models/user_favorite.py

class UserFavorite(Base):
    __tablename__ = 'user_favorites'

    id = UUID(primary_key=True)
    user_id = UUID(foreign_key='users.id')
    opportunity_id = UUID(foreign_key='opportunities.id')

    # 投资记录：用户为什么收藏
    saved_at = DateTime(default=func.now())
    save_reason = String(100)  # 用户选择的标签
    user_notes = Text()  # 用户的个人笔记

    # 数据快照：收藏时的市场状态
    price_snapshot = Decimal(10, 2)
    rating_snapshot = Float
    demand_score_snapshot = Integer
    market_trend_snapshot = String(20)

    # 持续价值：追踪变化
    price_change_alerts = JSONB  # [{date, old_price, new_price}]
    market_update_events = JSONB  # [{date, event_type, description}]

    # 元数据
    last_viewed_at = DateTime()
    view_count = Integer(default=0)
    engagement_score = Float(default=0)  # 基于查看频率

    # 关系
    opportunity = relationship('Opportunity', back_populates='favorited_by')
```

### 循环2：分析报告积累循环

```
用户行为：请求AI分析报告
   ↓
系统生成：
  • 20+页深度分析PDF
  • 个性化建议
  • 数据可视化图表
  • 行动计划清单
   ↓
系统保存：
  • 报告永久存储在用户账户
  • 可随时查看历史报告
  • 报告之间可以关联对比
   ↓
用户行为：
  • 下载报告到本地
  • 分享给团队
  • 基于报告做决策
   ↓
资产积累：
  • 14天试用期内生成10-20份报告
  • 形成个人的知识库
  • 团队协作依赖这些报告
   ↓
损失痛点：
  • 试用到期，无法查看历史报告
  • 无法生成新报告
  • 团队协作中断
```

**技术实现：**

```python
# models/ai_report.py

class AIReport(Base):
    __tablename__ = 'ai_reports'

    id = UUID(primary_key=True)
    user_id = UUID(foreign_key='users.id')
    opportunity_id = UUID(foreign_key='opportunities.id')

    # 报告元数据
    title = String(200)
    generated_at = DateTime(default=func.now())
    report_type = String(50)  # 'deep_analysis', 'competitor_comparison', 'profit_calculation'

    # 报告内容（长文本存储）
    content = JSONB  # 结构化的报告内容
    pdf_url = String(500)  # 生成的PDF文件链接

    # 投资追踪
    view_count = Integer(default=0)
    last_viewed_at = DateTime()
    shared_with = Array(UUID)  # 分享给其他用户

    # 关联数据
    related_reports = Array(UUID)  # 相关的其他报告
    action_items = JSONB  # 从报告提取的行动清单

    # 转化触发点
    is_starred = Boolean(default=False)  # 用户标记重要
    export_count = Integer(default=0)  # 导出次数
```

### 循环3：价格追踪依赖循环

```
用户行为：开启价格追踪
   ↓
系统服务：
  • 每天检查价格变化
  • 降价立即邮件/微信通知
  • 价格趋势图表更新
  • 历史价格数据积累
   ↓
用户价值：
  • 及时捕获降价机会
  • 了解价格波动规律
  • 判断最佳采购时机
   ↓
使用习惯：
  • 每天查看价格更新
  • 收到通知立即查看
  • 基于价格数据做决策
   ↓
数据积累：
  • 30-60天的价格历史
  • 多产品对比数据
  • 市场价格趋势判断
   ↓
损失痛点：
  • 失去实时监控
  • 历史数据无法查看
  • 错过最佳采购时机
```

---

## 渐进式价值披露设计

### 原理：价值随使用时间递增，越用越有价值

### 价值披露时间线

```
Day 1: 注册 → 立即价值
  ✅ 看到3个高质量机会卡片
  ✅ 每个卡片都有清晰的行动建议
  ✅ 立即可以验证信息准确性（对比Amazon）

Day 3: 探索 → 发现更多价值
  ✅ 发现可以收藏机会
  ✅ 收藏后开始收到价格更新
  ✅ 第一次感受到"系统在帮我工作"

Day 7: 习惯 → 日常使用
  ✅ 每天早上查看更新成为习惯
  ✅ 收藏夹有10+个机会
  ✅ 开始信赖AI分析

Day 14: 深度使用 → 依赖形成
  ✅ 生成5-10份AI报告
  ✅ 团队开始协作使用
  ✅ 决策依赖平台数据

Day 15: 试用预警 → 损失厌恶
  ⚠️ "您的试用还剩7天，升级后可保留："
     • 12个收藏机会的持续追踪
     • 8份AI深度分析报告
     • 30天的价格历史数据
     • 团队协作设置

Day 30: 试用到期 → 痛点触发
  ❌ 收藏夹锁定（只能看，不能更新）
  ❌ 历史报告只显示前3页
  ❌ 价格追踪停止
  ❌ 团队协作暂停
  ✅ "升级Pro，立即恢复所有功能"
```

### 功能解锁时间表

| 功能 | Free | Trial (Day 1-14) | Pro |
|------|------|------------------|-----|
| 每日机会卡片 | 3个 | 无限 | 无限 |
| AI分析报告 | ✗ | 10份/天 | 无限 |
| 保存收藏 | 5个 | 无限 | 无限 |
| 价格追踪 | ✗ | ✅ | ✅ |
| 历史数据 | 7天 | 90天 | 永久 |
| 竞品对比 | ✗ | 5次/天 | 无限 |
| 数据导出 | ✗ | ✗ | ✅ |
| 供应链信息 | ✗ | ✗ | ✅ |
| 团队协作 | ✗ | ✗ | ✅ |
| 邮件通知 | ✗ | 周报 | 实时 |

---

## 转化触发器设计

### 触发器1：资产盘点提醒（Day 15）

```
┌─────────────────────────────────────────────────────┐
│  📊 您的试用资产盘点                                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  💼 收藏机会：12个                                   │
│     • 3个产品最近7天降价                             │
│     • 2个市场需求上升20%                             │
│     • 1个新竞争者进入                                │
│                                                     │
│  📈 AI报告：8份                                      │
│     • 总阅读时长：2.5小时                            │
│     • 最常查看：无线耳机市场分析                      │
│                                                     │
│  💰 价格追踪：23天数据                               │
│     • 捕获3次降价机会（节省$估算）                    │
│                                                     │
│  ⚠️ 15天后，这些数据将停止更新                        │
│                                                     │
│  [立即升级Pro - 保留所有数据]                        │
│  [查看详细资产报告]                                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 触发器2：实时价值损失提醒（Day 25-29）

```
┌─────────────────────────────────────────────────────┐
│  ⚠️ 试用还剩X天                                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  今天发生的您可能错过的事件：                         │
│                                                     │
│  📉 Anker Soundcore Life 2 降价 $10                 │
│     您收藏了这个产品，但没有Pro将不再收到降价通知      │
│     → [开启价格追踪]                                 │
│                                                     │
│  📈 "无线耳机"类目搜索量上升 15%                     │
│     您收藏了3个相关产品，市场需求在增长               │
│     → [查看AI分析]                                  │
│                                                     │
│  🆕 新竞争者进入：TaoTronic                          │
│     您关注的耳机市场出现新竞争者                     │
│     → [查看竞品对比]                                 │
│                                                     │
│  ─────────────────────────────────────────────────   │
│  升级Pro，不再错过任何机会：                          │
│  • 实时价格追踪 + 降价通知                           │
│  • 市场变化监控 + AI分析                             │
│  • 竞品动态追踪 + 对比报告                           │
│                                                     │
│  [立即升级 - $29/月]                                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 触发器3：部分功能锁定（Day 30到期）

```
┌─────────────────────────────────────────────────────┐
│  🔒 试用已到期                                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  您的数据被安全保存，但部分功能已锁定：               │
│                                                     │
│  ✅ 可以继续使用：                                   │
│     • 查看已收藏的机会（只读）                       │
│     • 查看历史AI报告（前3页预览）                     │
│     • 每日3个新的机会卡片                            │
│                                                     │
│  🔒 已锁定功能：                                     │
│     • ❌ 价格追踪（停止更新）                         │
│     • ❌ 新建AI分析报告                              │
│     • ❌ 竞品对比                                    │
│     • ❌ 数据导出                                    │
│     • ❌ 邮件通知                                    │
│                                                     │
│  📊 您即将失去：                                     │
│     • 12个收藏机会的实时追踪                         │
│     • 8份完整AI报告                                  │
│     • 23天的价格历史数据                             │
│     • 持续的市场更新                                 │
│                                                     │
│  ─────────────────────────────────────────────────   │
│  立即解锁，恢复所有功能：                             │
│                                                     │
│  [升级Pro - $29/月]  [升级Pro - $299/年 (省$49)]    │
│                                                     │
│  ✨ 限时优惠：年付用户免费获得供应链匹配功能          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 用户留存机制

### 留存Hook 1：每日价值推送

```python
# 每天早上8点发送邮件

def daily_value_email(user_id):
    """发送每日价值邮件"""

    # 获取用户收藏
    favorites = get_user_favorites(user_id)

    # 检查变化
    changes = []
    for fav in favorites:
        # 价格变化
        if fav.price_change:
            changes.append({
                'type': 'price_drop',
                'product': fav.opportunity.title,
                'old_price': fav.price_snapshot,
                'new_price': fav.current_price,
                'saving': fav.price_snapshot - fav.current_price
            })

        # 需求上升
        if fav.demand_increase > 0.1:
            changes.append({
                'type': 'demand_up',
                'product': fav.opportunity.title,
                'increase': f"{fav.demand_increase*100}%"
            })

    # 生成邮件
    email = {
        'subject': f'📊 每日更新：发现{len(changes)}个机会变化',
        'body': f'''
        Hi {user.name},

        今天您的收藏夹发生了以下变化：

        {format_changes(changes)}

        [查看详情] (链接回网站)

        ---
        您已累计收藏 {len(favorites)} 个机会
        试用还剩 {trial_days_left} 天
        '''
    }

    send_email(user.email, email)
```

### 留存Hook 2：智能推荐

```
用户行为：查看"无线耳机"机会卡片
   ↓
系统记录：用户兴趣标签 = [电子产品, 音频, 高利润]
   ↓
AI推荐：
  • 相关机会："蓝牙音箱市场"（相似类目）
  • 互补机会："充电器市场"（配套产品）
  • 趋势机会："降噪技术趋势"（技术洞察）
   ↓
推送方式：
  • 网站横幅："为您推荐3个相关机会"
  • 邮件推送："基于您的阅读，推荐..."
   ↓
用户行为：点击推荐 → 查看更多 → 收藏
   ↓
循环：使用越多，推荐越准，价值越高
```

### 留存Hook 3：社交证明

```
在机会卡片上显示：

┌──────────────────────────────────────┐
│  🎯 高利润机会：无线耳机市场          │
├──────────────────────────────────────┤
│  👥 1,234人收藏了这个机会             │
│  📈 过去7天收藏量 +45%                │
│  💬 23条用户评论（查看讨论）          │
│                                      │
│  [收藏] [查看分析]                    │
└──────────────────────────────────────┘

心理效应：
• 从众心理：大家都在收藏，说明有价值
• 错失恐惧：收藏量在上升，现在要参与
• 社交验证：有评论，说明真实用户在用
```

---

## 数据追踪设计

### 必须追踪的用户行为指标

```python
# models/user_analytics.py

class UserAnalytics(Base):
    """用户行为追踪 - 用于计算转化率"""

    __tablename__ = 'user_analytics'

    # 基础指标
    user_id = UUID(foreign_key='users.id')
    date = Date()

    # 使用指标（投资证明）
    page_views = Integer(default=0)  # 页面浏览
    session_duration = Integer(default=0)  # 会话时长（秒）
    opportunity_views = Integer(default=0)  # 查看机会详情
    favorites_added = Integer(default=0)  # 新增收藏
    favorites_removed = Integer(default=0)  # 取消收藏

    # 深度使用指标（依赖证明）
    ai_reports_generated = Integer(default=0)  # 生成AI报告
    ai_reports_viewed = Integer(default=0)  # 查看AI报告
    competitor_comparisons = Integer(default=0)  # 竞品对比
    price_tracking_enabled = Integer(default=0)  # 开启价格追踪
    exports_performed = Integer(default=0)  # 数据导出

    # 参与度指标（习惯证明）
    emails_opened = Integer(default=0)  # 打开邮件
    email_clicks = Integer(default=0)  # 邮件点击
    push_notifications_clicked = Integer(default=0)  # 通知点击
    shares = Integer(default=0)  # 分享

    # 社交指标（网络效应证明）
    comments_posted = Integer(default=0)  # 发表评论
    likes_given = Integer(default=0)  # 点赞
    team_invites = Integer(default=0)  # 邀请队友

    # 转化指标
    trial_started = Boolean(default=False)
    trial_converted = Boolean(default=False)
    conversion_date = DateTime()
```

### 转化预测模型

```python
def predict_conversion_probability(user_id):
    """预测用户转化概率"""

    analytics = get_user_analytics(user_id, last_30_days)

    # 特征工程
    features = {
        # 使用频率
        'avg_daily_sessions': analytics.total_sessions / 30,
        'avg_session_duration': analytics.total_duration / analytics.total_sessions,

        # 投资深度
        'favorites_count': get_user_favorites_count(user_id),
        'ai_reports_count': analytics.ai_reports_generated,
        'data_accumulation_days': days_since_first_save(user_id),

        # 参与度
        'email_open_rate': analytics.emails_opened / analytics.emails_sent,
        'return_visit_rate': analytics.days_visited / 30,

        # 社交
        'has_shared': analytics.shares > 0,
        'team_members': get_team_size(user_id)
    }

    # 转化信号（基于经验阈值）
    signals = {
        'high_probability': 0.7,  # 70%+ 转化率
        'medium_probability': 0.3,  # 30-70% 转化率
        'low_probability': 0.1,  # <30% 转化率
    }

    # 判断
    if (features['favorites_count'] >= 10 and
        features['ai_reports_count'] >= 5 and
        features['data_accumulation_days'] >= 7):
        return signals['high_probability']

    elif (features['favorites_count'] >= 5 and
          features['avg_daily_sessions'] >= 3):
        return signals['medium_probability']

    else:
        return signals['low_probability']
```

---

## 定价心理学

### 价格锚定

```
网站定价页面设计：

┌─────────────────────────────────────────────────────────┐
│  选择您的计划                                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Free                    Trial                     Pro   │
│  ┌─────────┐           ┌─────────┐           ┌───────────┐
│  │ $0/月   │           │ 限时免费 │           │ $29/月    │
│  │         │           │ 14天    │           │           │
│  ├─────────┤           ├─────────┤           ├───────────┤
│  │ 3个卡片 │           │ 无限    │           │ 无限      │
│  │ 基础数据 │           │ AI报告  │           │ 全部功能  │
│  │ 5个收藏 │           │ 价格追踪 │           │ 供应链    │
│  │         │           │ 团队协作 │           │ 数据导出  │
│  │         │           │         │           │           │
│  │ [当前]  │           │ [试用中]│           │ [升级]    │
│  └─────────┘           └─────────┘           └───────────┘
│                                                         │
│  💡 推荐：年付 $299 (省 $49) + 免费供应链匹配           │
│                                                         │
└─────────────────────────────────────────────────────────┘

锚定效应：
• Free vs Trial: 价值对比明显（3个 vs 无限）
• Trial vs Pro: $29/月感觉便宜（相比价值）
• 月付 vs 年付: 年付看起来划算（省$49 + 赠品）
```

### 损失厌恶定价

```
试用期最后3天弹窗：

┌─────────────────────────────────────────────────────────┐
│  ⏰ 试用还剩3天                                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  您现在有两种选择：                                      │
│                                                         │
│  ❌ 放弃：                                              │
│     • 失去12个收藏机会的实时追踪                        │
│     • 无法查看8份完整AI报告                             │
│     • 停止接收价格变化通知                              │
│     • 已投入的30天使用时间浪费                          │
│                                                         │
│  ✅ 升级Pro ($29/月)：                                   │
│     • 保留所有数据和功能                                │
│     • 持续接收更新和通知                                │
│     • 解锁供应链、数据导出等专业功能                    │
│     • 投资回报：每月只需1个成功机会即可回本             │
│                                                         │
│  [立即升级]  [稍后提醒我]                                │
│                                                         │
└─────────────────────────────────────────────────────────┘

心理触发：
• 强调"失去"而非"不能获得"
• 具体化损失（12个机会、8份报告）
• 时间投资浪费（沉没成本）
• ROI论证（1个机会回本）
```

---

## 技术实现架构

### 数据库Schema扩展

```sql
-- 用户表扩展
ALTER TABLE users ADD COLUMN subscription_tier VARCHAR(20) DEFAULT 'free';
ALTER TABLE users ADD COLUMN trial_started_at TIMESTAMP;
ALTER TABLE users ADD COLUMN trial_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN subscription_expires_at TIMESTAMP;

-- 用户收藏表
CREATE TABLE user_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,

    -- 投资记录
    saved_at TIMESTAMP DEFAULT NOW(),
    save_reason VARCHAR(100),
    user_notes TEXT,

    -- 数据快照
    price_snapshot DECIMAL(10,2),
    rating_snapshot FLOAT,
    demand_score_snapshot INTEGER,
    market_trend_snapshot VARCHAR(20),

    -- 持续价值
    price_change_alerts JSONB DEFAULT '[]',
    market_update_events JSONB DEFAULT '[]',

    -- 元数据
    last_viewed_at TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    engagement_score FLOAT DEFAULT 0,

    UNIQUE(user_id, opportunity_id)
);

CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX idx_user_favorites_engagement ON user_favorites(user_id, engagement_score DESC);

-- AI报告表
CREATE TABLE ai_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,

    -- 报告元数据
    title VARCHAR(200),
    generated_at TIMESTAMP DEFAULT NOW(),
    report_type VARCHAR(50),

    -- 报告内容
    content JSONB NOT NULL,
    pdf_url VARCHAR(500),

    -- 投资追踪
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP,
    shared_with UUID[],

    -- 转化触发
    is_starred BOOLEAN DEFAULT FALSE,
    export_count INTEGER DEFAULT 0,

    -- 关联
    related_reports UUID[],
    action_items JSONB
);

CREATE INDEX idx_ai_reports_user_id ON ai_reports(user_id);
CREATE INDEX idx_ai_reports_generated_at ON ai_reports(user_id, generated_at DESC);

-- 价格追踪表
CREATE TABLE price_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,

    enabled BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP DEFAULT NOW(),

    -- 价格历史
    price_history JSONB DEFAULT '[]',  -- [{date, price}]

    -- 阈值设置
    alert_on_drop_above_percent INTEGER DEFAULT 10,

    -- 最新状态
    last_price DECIMAL(10,2),
    last_checked_at TIMESTAMP,

    UNIQUE(user_id, opportunity_id)
);

CREATE INDEX idx_price_tracking_user_id ON price_tracking(user_id);
CREATE INDEX idx_price_tracking_enabled ON price_tracking(user_id, enabled);

-- 用户行为分析表
CREATE TABLE user_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,

    -- 使用指标
    page_views INTEGER DEFAULT 0,
    session_duration INTEGER DEFAULT 0,
    opportunity_views INTEGER DEFAULT 0,
    favorites_added INTEGER DEFAULT 0,
    favorites_removed INTEGER DEFAULT 0,

    -- 深度使用
    ai_reports_generated INTEGER DEFAULT 0,
    ai_reports_viewed INTEGER DEFAULT 0,
    competitor_comparisons INTEGER DEFAULT 0,
    price_tracking_enabled INTEGER DEFAULT 0,
    exports_performed INTEGER DEFAULT 0,

    -- 参与度
    emails_opened INTEGER DEFAULT 0,
    email_clicks INTEGER DEFAULT 0,
    push_notifications_clicked INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,

    -- 社交
    comments_posted INTEGER DEFAULT 0,
    likes_given INTEGER DEFAULT 0,
    team_invites INTEGER DEFAULT 0,

    -- 转化
    trial_started BOOLEAN DEFAULT FALSE,
    trial_converted BOOLEAN DEFAULT FALSE,
    conversion_date TIMESTAMP,

    UNIQUE(user_id, date)
);

CREATE INDEX idx_user_analytics_user_date ON user_analytics(user_id, date DESC);
```

### 后端API端点

```python
# api/subscriptions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])

class TrialStartRequest(BaseModel):
    user_id: UUID

class TrialStatusResponse(BaseModel):
    is_trial: bool
    days_remaining: int
    assets_summary: dict
    can_extend: bool

@router.post("/trial/start")
async def start_trial(
    request: TrialStartRequest,
    db: AsyncSession = Depends(get_db)
):
    """开始14天试用"""

    # 检查是否已经试用过
    user = await get_user(db, request.user_id)
    if user.trial_expires_at:
        raise HTTPException(400, "Already used trial")

    # 开启试用
    user.subscription_tier = 'trial'
    user.trial_started_at = datetime.now()
    user.trial_expires_at = datetime.now() + timedelta(days=14)

    await db.commit()

    # 发送欢迎邮件
    send_trial_welcome_email(user.email)

    return {"message": "Trial started", "expires_at": user.trial_expires_at}

@router.get("/trial/status", response_model=TrialStatusResponse)
async def get_trial_status(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取试用状态和资产摘要"""

    user = await get_user(db, request.user_id)

    if not user.trial_expires_at:
        return TrialStatusResponse(
            is_trial=False,
            days_remaining=0,
            assets_summary={},
            can_extend=True
        )

    days_left = (user.trial_expires_at - datetime.now()).days

    # 获取资产摘要
    favorites = await get_user_favorites_count(db, user_id)
    reports = await get_ai_reports_count(db, user_id)
    tracking = await get_price_tracking_count(db, user_id)

    assets = {
        "favorites": favorites,
        "ai_reports": reports,
        "price_tracking": tracking,
        "total_investment_days": (datetime.now() - user.trial_started_at).days
    }

    return TrialStatusResponse(
        is_trial=True,
        days_remaining=days_left,
        assets_summary=assets,
        can_extend=False
    )

@router.post("/checkout/create")
async def create_checkout_session(
    user_id: UUID,
    plan: str,  # 'monthly' or 'yearly'
    db: AsyncSession = Depends(get_db)
):
    """创建支付会话（Stripe）"""

    user = await get_user(db, user_id)

    # 创建Stripe checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_xxx' if plan == 'monthly' else 'price_yyy',
            'quantity': 1,
        }],
        mode='subscription',
        success_url=f'{settings.FRONTEND_URL}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=f'{settings.FRONTEND_URL}/subscription/cancel',
        customer_email=user.email,
        metadata={
            'user_id': str(user_id),
            'plan': plan
        }
    )

    return {"checkout_url": session.url}

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Stripe webhook处理"""

    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = UUID(session['metadata']['user_id'])

        # 升级用户
        await upgrade_user_to_pro(db, user_id, session['subscription'])

    return {"status": "ok"}

async def upgrade_user_to_pro(
    db: AsyncSession,
    user_id: UUID,
    subscription: dict
):
    """升级用户到Pro"""

    user = await get_user(db, user_id)

    user.subscription_tier = 'pro'
    user.subscription_expires_at = datetime.fromtimestamp(
        subscription['current_period_end']
    )
    user.stripe_subscription_id = subscription['id']
    user.trial_converted = True
    user.conversion_date = datetime.now()

    await db.commit()

    # 发送欢迎邮件
    send_pro_welcome_email(user.email)

    # 记录转化事件
    await track_conversion_event(db, user_id, 'trial_to_pro')
```

---

## 转化率优化策略

### A/B测试框架

```python
# 转化率测试点

1. 试用开始触发器
   A: 注册后立即弹窗
   B: 浏览3个卡片后弹窗
   C: 收藏第1个机会后弹窗

2. 试用长度
   A: 7天
   B: 14天
   C: 30天

3. 转化提醒频率
   A: 剩余7天、3天、1天
   B: 剩余3天、1天、当天
   C: 剩余14天、7天、3天、1天

4. 价格展示
   A: $29/月
   B: $1/天（拆解价格）
   C: $29/月 + 强调ROI

5. 资产盘点提醒
   A: 只显示数量
   B: 显示数量 + 预估价值
   C: 显示数量 + 预估价值 + 损失场景
```

---

## 成功指标

### North Star Metric

**定义**: "付费转化率" (Trial → Paid Conversion)

### 目标

| 阶段 | 目标转化率 | 时间线 |
|------|-----------|--------|
| MVP上线 | 5% | 第1个月 |
| 优化迭代 | 10% | 第3个月 |
| 成熟期 | 15%+ | 第6个月 |

### 分层指标

| 漏斗阶段 | 指标 | 目标值 |
|---------|------|--------|
| 注册 → 试用 | 试用开始率 | 40% |
| 试用第1天 | 次日留存 | 60% |
| 试用第7天 | 7日留存 | 40% |
| 试用第14天 | 14日留存 | 25% |
| 试用 → 付费 | 转化率 | 10% |

### 预警指标

| 指标 | 预警线 | 行动 |
|------|--------|------|
| 试用开始率 | <30% | 优化注册流程 |
| 次日留存 | <40% | 检查onboarding |
| 7日留存 | <20% | 检查产品价值 |
| 转化率 | <5% | 检查资产积累机制 |

---

## 实施路线图

### Phase 1: 基础功能（2周）

- [ ] 用户收藏系统
- [ ] 试用开始/结束逻辑
- [ ] 基础订阅管理（Stripe集成）
- [ ] 试用状态API

### Phase 2: 投资循环（3周）

- [ ] AI报告生成和存储
- [ ] 价格追踪系统
- [ ] 用户行为分析追踪
- [ ] 资产盘点提醒

### Phase 3: 转化优化（2周）

- [ ] 试用到期提醒
- [ ] 实时价值损失提醒
- [ ] 定价页面设计
- [ ] Stripe checkout流程

### Phase 4: 留存机制（2周）

- [ ] 每日价值邮件
- [ ] 智能推荐系统
- [ ] 社交证明显示
- [ ] 仪表盘页面

### Phase 5: 数据分析（持续）

- [ ] 转化漏斗追踪
- [ ] A/B测试框架
- [ ] 画像分析
- [ ] 预测模型

---

## 风险与缓解

### 风险1：用户不开始试用

**原因**: 免费版太"好用"，没有升级动力

**缓解**:
- Free限制3个卡片，触发"想看更多"
- Free不提供AI分析，展示报告预览（前3页）
- 试用提醒在收藏第1个机会后立即出现

### 风险2：用户试用后不转化

**原因**: 资产积累不够，失去不痛

**缓解**:
- 确保试用期内至少生成5份AI报告
- 推荐收藏，至少10个机会
- 强调"失去"而非"不能获得"
- 展示ROI计算器

### 风险3：用户试用结束后继续用Free

**原因**: Free版3个卡片足够用

**缓解**:
- Free卡片随机，Trial卡片个性化
- Free不保存历史，Trial保存
- Trial到期后，收藏夹锁定（只读）
- 强调"失去已积累的数据"

---

## 总结：完整的转化链路

```
1. 用户注册 → 立即看到3个高质量卡片（价值证明）
   ↓
2. 浏览更多 → "收藏第1个机会" → 弹窗："开始14天免费试用，无限收藏"
   ↓ (触发试用开始)
3. 试用第1-7天 → 每天查看机会 → 收藏增加到5-10个 → 开始收到价格变化通知
   ↓ (习惯形成)
4. 试用第7-14天 → 生成AI报告 → 团队开始协作 → 深度使用功能
   ↓ (依赖形成)
5. 试用第15天 → "您的资产盘点"邮件 → 显示已投入的时间、数据
   ↓ (损失意识)
6. 试用第25-29天 → 每日"正在错过"提醒 → 实时价值损失展示
   ↓ (紧迫感)
7. 试用第30天 → 功能锁定 → "失去12个收藏追踪、8份AI报告..."
   ↓ (痛点触发)
8. 决策点 → 放弃已投入的资产 OR $29/月继续 → 70%+选择继续
   ↓ (转化完成)
9. 付费用户 → 持续价值 → 续费
```

---

**文档版本**: 1.0
**创建日期**: 2026-03-12
**核心创新**: 投资循环 + 渐进式价值披露 + 损失厌恶触发
**预期转化率**: 10-15% (Trial → Paid)

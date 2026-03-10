# ZenConsult 跨境电商资讯平台 - 需求文档

**版本**: v1.0
**最后更新**: 2025-03-10
**状态**: 开发中

---

## 项目概述

ZenConsult 是一个为国内跨境电商创业者提供市场资讯、政策解读、机会发现的专业信息平台。

### 核心定位

- **目标用户**: 国内潜在跨境电商创业者（小白用户，非专业卖家）
- **目标市场**: 东南亚、欧美、拉美
- **服务模式**: Freemium工具型 SaaS
- **核心价值**: 陪伴式成长 + 决策支持 + 实操工具

---

## 首页设计规范

### 设计理念

采用 **SellerSprite 风格**的专业设计：
- 灰色背景 (`bg-gray-100`)
- 白色卡片 (`bg-white` + `border-gray-200`)
- 信息密集型布局
- 无营销导向的 CTA

### 首页结构

```
┌─────────────────────────────────────────────────────────────┐
│  全局导航栏 (sticky top-0)                                    │
│  Logo | 首页 | 东南亚 | 欧美 | 拉美 | 搜索 | 登录 | 注册         │
├─────────────────────────────────────────────────────────────┤
│  有趣的功能模块 (4个横排卡片)                                 │
│  🪞 个人能力照妖镜 | 📦 资源盘点 | 🧭 兴趣探索 | 📖 成长指南    │
├─────────────────────────────────────────────────────────────┤
│  三大区域资讯流 (3列横排)                                     │
│  🌏 东南亚 | 🇺🇸 欧美 | 🇧🇷 拉美                              │
│  每列显示该区域的最新资讯标题列表                              │
├─────────────────────────────────────────────────────────────┤
│  专业信息门户 (6个网格卡片)                                   │
│  📜 政策中心 | 💡 机会发现 | ⚠️ 风险预警                      │
│  📊 实操指南 | 🛒 平台指南 | 🚚 物流参考                      │
├─────────────────────────────────────────────────────────────┤
│  CTA 卡片                                                     │
│  "想要更深入的数据分析？"                                     │
├─────────────────────────────────────────────────────────────┤
│  页脚                                                         │
└─────────────────────────────────────────────────────────────┘
```

### 设计规范

- **背景色**: `bg-gray-100` (浅灰色)
- **卡片样式**: `bg-white` + `border border-gray-200`
- **圆角**: `rounded-lg` 或 `rounded-xl`
- **阴影**: `shadow-sm` 或 `hover:shadow-lg`
- **间距**: 标准化使用 Tailwind 间距 scale (4, 6, 8)

---

## 国家门户设计

### URL 结构

```
/th  - 泰国
/vn  - 越南
/my  - 马来西亚
/us  - 美国
/br  - 巴西
/mx  - 墨西哥
```

### 国家门户布局

```
┌─────────────────────────────────────────────────────────────────┐
│  国家门户头部 - 带地区特色渐变                                    │
│  🇹🇭 泰国 Thailand | 人口7100万 | GDP $5490亿 | 电商$190亿        │
├──────────────────────────┬──────────────────────────────────────┤
│  【主要内容区】(2/3宽)    │  【右侧边栏】(1/3宽)                   │
│                          │                                      │
│  📊 市场概览卡片(4个)      │  🛒 平台指南                          │
│  📰 最新资讯(流式)        │  🔥 热销产品TOP5                      │
│  💰 机会发现(网格)        │  💵 成本参考                          │
│  ⚠️ 风险预警(警告卡片)    │  🚀 开始泰国之旅                      │
└──────────────────────────┴──────────────────────────────────────┘
```

---

## 技术架构

### 前端

**框架**: Next.js 16.1.6 (App Router + Turbopack)

**技术栈**:
- TypeScript
- Tailwind CSS
- shadcn/ui (UI 组件库)

**关键配置**:
```typescript
// 动态渲染（用于获取实时数据的页面）
export const dynamic = 'force-dynamic';

// 服务器组件（默认）
export default async function Page() {
  // 在服务端获取数据
}
```

### 后端

**框架**: FastAPI (Python)

**技术栈**:
- SQLAlchemy (Async ORM)
- PostgreSQL (数据库)
- Pydantic (数据验证)

**API 端点**:

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/api/v1/crawler/articles` | GET | 否 | 获取文章列表 |
| `/api/v1/crawler/articles/{id}` | GET | 否 | 获取文章详情 |
| `/api/v1/crawler/trigger/{source}` | POST | 是 | 触发爬取 |
| `/health` | GET | 否 | 健康检查 |

---

## 数据模型

### Article (文章)

```typescript
interface Article {
  id: string;
  title: string;
  summary: string | null;
  full_content: string | null;
  link: string;
  source: string;
  language: string;
  published_at: string | null;
  crawled_at: string | null;
  region: string | null;        // southeast_asia, north_america, latin_america
  platform: string | null;       // shopee, lazada, amazon, etc.
  content_theme: string | null;  // opportunity, risk, policy, guide
  tags: string[];
  risk_level: string | null;     // low, medium, high, critical
  opportunity_score: number | null;  // 0-1
  author: string | null;
  is_processed: boolean;
  is_published: boolean;
}
```

---

## 内容主题分类

| 主题 | 英文 | Emoji | 说明 |
|------|------|-------|------|
| 政策 | policy | 📜 | 各国电商政策法规解读 |
| 机会 | opportunity | 💡 | 市场机会、选品建议 |
| 风险 | risk | ⚠️ | 市场风险、运营陷阱 |
| 指南 | guide | 📊 | 开店流程、运营技巧 |

---

## 地区分类

| 地区 | 代码 | Emoji | 国家 |
|------|------|-------|------|
| 东南亚 | southeast_asia | 🌏 | 泰国、越南、马来西亚 |
| 欧美 | north_america | 🇺🇸 | 美国 |
| 拉美 | latin_america | 🇧🇷 | 巴西、墨西哥 |

---

## 平台支持

- Shopee
- Lazada
- TikTok Shop
- Amazon
- Mercado Libre
- 其他区域性平台

---

## 待完成功能

### 高优先级

1. **爬虫系统**: SSL 证书问题需要修复
2. **认证流程**: 登录/注册功能需要完善
3. **国家筛选**: 后端需要支持按国家筛选文章
4. **文章详情页**: 需要美化格式化内容显示

### 中优先级

1. **搜索功能**: 全文搜索文章
2. **订阅管理**: Freemium 模式实现
3. **用户仪表盘**: 个人数据看板
4. **成本计算器**: 辅助工具

### 低优先级

1. **评论系统**: 文章评论互动
2. **收藏功能**: 用户收藏文章
3. **邮件订阅**: 定期推送资讯
4. **移动端优化**: PWA 支持

---

## 域名规划

- 主站: `www.zenconsult.top`
- 国家页面: `www.zenconsult.top/th`, `www.zenconsult.top/us`, etc.
- API: `api.zenconsult.top` (未来)

---

## 部署计划

### 前端

- **平台**: Vercel
- **构建命令**: `npm run build`
- **环境变量**: `NEXT_PUBLIC_API_URL`

### 后端

- **平台**: Railway
- **启动命令**: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
- **数据库**: PostgreSQL (Railway 提供的托管数据库)

---

## 成功指标

### 技术指标

- API 响应时间: P95 < 200ms
- 爬虫成功率: > 90%
- 系统可用性: > 99%
- 页面加载: < 2秒

### 业务指标

- 首月注册用户: 200+
- 首月付费转化率: > 5%
- 用户留存: 30天 > 30%
- 月度经常性收入(MRR): 3个月内达到 ¥10,000+

---

## 变更日志

### 2025-03-10

- ✅ 前后端数据类型统一
- ✅ 文章 API 公开访问
- ✅ 首页 SellerSprite 风格设计
- ✅ 国家门户页面开发
- ✅ 动态渲染配置
- ✅ 测试数据创建
- ⏳ 爬虫 SSL 证书问题
- ⏳ 认证流程完善

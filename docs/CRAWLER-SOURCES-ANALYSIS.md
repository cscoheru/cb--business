# 爬虫信息源配置分析报告

## 📊 总览

**配置信息源数量**: 16个（15个已启用，1个已禁用）

| 状态 | 数量 |
|------|------|
| ✅ 已启用 | 15 |
| ❌ 已禁用 | 1 (Shopify Blog) |
| 🔄 调度中 | 15 (每30分钟) |
| 🧹 清理任务 | 1 (每天凌晨3点) |

---

## 🌍 信息源详情

### 东南亚市场 (Southeast Asia)

| 信息源 | 类型 | 语言 | 预期Region | 预期Country | 状态 |
|--------|------|------|-----------|-------------|------|
| Tech in Asia | RSS | en | southeast_asia | sg (新加坡) | ✅ |
| e27 | RSS | en | southeast_asia | sg (新加坡) | ✅ |
| 雨果网 | HTTP | zh | southeast_asia | cn (中国) | ✅ |

### 北美市场 (North America)

| 信息源 | 类型 | 语言 | 预期Region | 预期Country | 状态 |
|--------|------|------|-----------|-------------|------|
| Retail Dive | RSS | en | north_america | us (美国) | ✅ |
| Digital Commerce 360 | RSS | en | north_america | us (美国) | ✅ |
| EcommerceBytes | RSS | en | north_america | us (美国) | ✅ |
| PYMNTS | RSS | en | north_america | us (美国) | ✅ |
| Amazon Seller News | RSS | en | north_america | us (美国) | ✅ |
| eBay Seller News | RSS | en | north_america | us (美国) | ✅ |
| PayPal Blog | RSS | en | north_america | us (美国) | ✅ |
| Stripe Blog | RSS | en | north_america | us (美国) | ✅ |
| 亿恩网 | RSS | zh | north_america | cn (中国) | ✅ |

### 拉美市场 (Latin America)

| 信息源 | 类型 | 语言 | 预期Region | 预期Country | 状态 |
|--------|------|------|-----------|-------------|------|
| Mercopress | RSS | en | latin_america | br (巴西) | ✅ |

### 全球市场 (Global)

| 信息源 | 类型 | 语言 | 预期Region | 预期Country | 状态 |
|--------|------|------|-----------|-------------|------|
| TechCrunch | RSS | en | global | us (美国) | ✅ |
| eMarketer | RSS | en | global | us (美国) | ✅ |
| Shopify Blog | RSS | en | global | - | ❌ 已禁用 |

---

## 🤖 AI分析规则详解

### MockAIProcessor 分类逻辑

#### 1. 地区推断 (Region Detection)

**优先级**:
1. 来源映射 (`SOURCE_REGION_MAP`)
2. 关键词检测 (`_detect_region()`)

**来源映射表**:
```python
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
```

#### 2. 国家推断 (Country Detection)

**优先级**:
1. 来源映射 (`SOURCE_COUNTRY_MAP`)
2. 关键词检测 (`_detect_country()`)

**来源映射表**:
```python
SOURCE_COUNTRY_MAP = {
    "Tech in Asia": "sg",  # 新加坡
    "e27": "sg",           # 新加坡
    "雨果网": "cn",        # 中国
    "亿恩网": "cn",        # 中国
    "Mercopress": "br",    # 巴西
    "Retail Dive": "us",   # 美国
    "Digital Commerce 360": "us",
    "EcommerceBytes": "us",
    "PYMNTS": "us",
    "Amazon Seller News": "us",
    "eBay Seller News": "us",
    "PayPal Blog": "us",
    "Stripe Blog": "us",
    "eMarketer": "us",
    "TechCrunch": "us",
}
```

**关键词检测规则** (当来源映射不存在时):

**东南亚国家关键词**:
- `th`, `thai`, `bangkok` → `th` (泰国)
- `vietnam`, `viet`, `hanoi`, `ho chi minh` → `vn` (越南)
- `singapore`, `singaporean` → `sg` (新加坡)
- `malaysia`, `malaysian`, `kuala lumpur` → `my` (马来西亚)
- `indonesia`, `indonesian`, `jakarta` → `id` (印尼)
- `philippines`, `philippine`, `manila` → `ph` (菲律宾)

**北美国家关键词**:
- `united states`, `usa`, `u.s.`, `america`, `us-market` → `us` (美国)
- `canada`, `canadian` → `ca` (加拿大)
- `mexico`, `mexican` → `mx` (墨西哥)

**拉美国家关键词**:
- `brazil`, `brazilian`, `brasil`, `são paulo`, `rio` → `br` (巴西)
- `mexico`, `mexican` → `mx` (墨西哥)
- `colombia`, `colombian` → `co` (哥伦比亚)
- `argentina`, `argentinian` → `ar` (阿根廷)
- `chile` → `cl` (智利)
- `peru` → `pe` (秘鲁)

#### 3. 主题分类 (Content Theme)

| 主题 | 关键词示例 | risk_level |
|------|----------|-----------|
| `risk` | risk, warning, alert, danger, ban, fraud, scam, lawsuit, crime | medium |
| `opportunity` | opportunity, growth, expand, launch, new market, emerging, trend | low |
| `policy` | policy, regulation, law, tax, tariff, compliance, legal, bill | medium |
| `platform` | platform, amazon, shopee, lazada, marketplace | low |
| `logistics` | logistics, shipping, fulfillment, warehouse, delivery, supply chain | low |
| `guide` | (默认) | low |

#### 4. 平台检测 (Platform)

| 平台代码 | 关键词 |
|---------|--------|
| `amazon` | amazon, aws, fba |
| `shopee` | shopee |
| `lazada` | lazada |
| `shopify` | shopify |
| `tiktok` | tiktok shop, tiktok |
| `mercadolibre` | mercado libre, mercadolibre |
| `other` | (默认) |

---

## 🏷️ 关键词云配置

### 前端配置 (`keyword-cloud.tsx`)

**平台关键词配置**:
```typescript
const PLATFORMS_BY_REGION = {
  southeast_asia: ['Shopee', 'Lazada', 'TikTok Shop', 'Amazon'],
  north_america: ['Amazon', 'Shopify', 'eBay', 'Walmart'],
  latin_america: ['Mercado Libre', 'Amazon', 'Shopee', 'AliExpress'],
};
```

**品类关键词**:
```typescript
const CATEGORIES = [
  { label: '美妆', emoji: '💄' },
  { label: '电子', emoji: '📱' },
  { label: '家居', emoji: '🏠' },
  { label: '服饰', emoji: '👗' },
  { label: '食品', emoji: '🍜' },
  { label: '母婴', emoji: '👶' },
  { label: '运动', emoji: '⚽' },
  { label: '宠物', emoji: '🐕' },
];
```

**国家配置** (`config/countries/index.ts`):
```typescript
export const countriesByRegion = {
  southeast_asia: [thailand, vietnam, malaysia],  // th, vn, my
  north_america: [usa],                            // us
  latin_america: [brazil, mexico],                 // br, mx
};
```

**国家代码映射**:
| 国家 | slug (URL) | code (ISO) | 文章查询 |
|------|-----------|-----------|---------|
| 泰国 | `th` | `TH` | `country=th` |
| 越南 | `vn` | `VN` | `country=vn` |
| 马来西亚 | `my` | `MY` | `country=my` |
| 美国 | `us` | `US` | `country=us` |
| 巴西 | `br` | `BR` | `country=br` |
| 墨西哥 | `mx` | `MX` | `country=mx` |

---

## 📈 当前数据统计

**文章总数**: 134篇

**地区分布**:
- 北美: 84篇
- 拉美: 19篇
- 东南亚: 11篇
- 全球: 20篇

**待处理**:
- 缺少country字段: 14篇
- region为global: 20篇
- 合计需要重新处理: 34篇

---

## 🎯 改进建议

### 1. 信息源覆盖优化

**当前问题**:
- 东南亚市场文章偏少 (11篇 vs 北美84篇)
- 缺少印尼、菲律宾等国家的专门信息源
- 拉美市场只有1个信息源

**建议新增信息源**:

#### 东南亚补充
```
- Tech in Asia Indonesia (印尼)
- e27 Vietnam (越南)
- DealStreetAsia SEA
- KrASIA (东南亚科技)
- vnExpress (越南)
- Kompas (印尼)
- Philippine Daily Inquirer (菲律宾)
```

#### 拉美补充
```
- Neobiz (巴西电商)
- Webcapitalista (拉美电商)
- E-commerce Brasil (巴西)
- Tienda Pago (秘鲁)
- Compras Colombianas (哥伦比亚)
```

### 2. 国家代码映射完善

**当前问题**:
- AI处理器返回的国家代码 (`sg`, `cn`) 与前端国家slug不匹配
- 前端只有6个国家 (th, vn, my, us, br, mx)
- 新加坡 (`sg`)、中国 (`cn`) 文章无法正确展示

**解决方案**:

**选项A**: 扩展前端国家配置
```typescript
// 新增国家
- singapore (sg)
- indonesia (id)
- philippines (ph)
```

**选项B**: 在AI处理器中映射国家代码到slug
```python
# 当检测到sg时，随机分配到东南亚国家之一
if country == "sg":
    country = random.choice(["th", "vn", "my"])
```

### 3. 关键词云 + 信息源关联

**当前问题**:
- 关键词云是静态配置
- 没有显示每个关键词对应的信息来源
- 用户不知道文章来自哪里

**建议实现**:

在前端显示每个关键词+国家的信息来源统计:
```typescript
// 例子: 泰国 + Shopee 的文章来源
{
  "th": {
    "shopee": {
      "sources": ["Tech in Asia", "雨果网"],
      "article_count": 5
    }
  }
}
```

### 4. AI分析规则增强

**当前问题**:
- 品类分类缺失 (美妆、电子、家居等)
- 品类关键词没有用于文章分类

**建议增强**:

在 `MockAIProcessor.analyze_article()` 中添加品类检测:
```python
CATEGORY_KEYWORDS = {
    "beauty": ["beauty", "cosmetic", "makeup", "skincare", "lipstick"],
    "electronics": ["electronics", "phone", "laptop", "gadget", "tech"],
    "home": ["home", "furniture", "decor", "kitchen", "living"],
    "fashion": ["fashion", "clothing", "apparel", "shoes", "jewelry"],
    "food": ["food", "grocery", "beverage", "snack", "organic"],
    "baby": ["baby", "infant", "diaper", "formula", "toy"],
    "sports": ["sports", "fitness", "outdoor", "equipment", "gear"],
    "pet": ["pet", "dog", "cat", "pet food", "veterinary"],
}
```

---

## 🔧 实施优先级

### P0 - 立即修复
1. ✅ 修复调度器 (已完成 - 改用MemoryJobStore)
2. ✅ 修复country字段 (已完成 - 120/134篇文章已补充)

### P1 - 高优先级
1. 扩展前端国家配置 (添加 sg, id, ph)
2. 在API中添加"信息来源统计"端点
3. 在国家页面显示"文章来源"列表

### P2 - 中优先级
1. 添加新信息源 (印尼、菲律宾、拉美)
2. 增强AI分析规则 (添加品类检测)
3. 关键词云显示信息来源

### P3 - 低优先级
1. 信息源健康监控
2. 自动去重优化
3. 爬虫性能优化

# Lazada Open Platform API Registration Guide

## 概述

Lazada Open Platform API 是获取东南亚电商数据的**最佳选择**：
- ✅ 官方API，稳定可靠
- ✅ 公开访问，无需ERP资质（相比Shopee的严格限制）
- ✅ 支持泰国、越南、马来西亚、新加坡、印尼、菲律宾
- ✅ 提供商品、评论、订单等数据接口

## 注册步骤

### 1. 创建开发者账号
访问: https://open.lazada.com/

1. 点击 "Create Account" 创建账号
2. 使用邮箱注册 UAC (统一账户中心)
3. 验证邮箱

### 2. 成为 Lazada 开发者
1. 登录后，完善开发者资料
2. 选择开发者类型（个人/企业）
3. 提交审核（通常很快）

### 3. 创建应用获取API密钥
1. 进入 APP Console
2. 点击 "Create" 创建新应用
3. 填写应用信息：
   - 应用名称: ZenConsult E-commerce Analytics
   - 应用类型: 选择数据分析类
   - 网站: https://www.zenconsult.top
4. 提交后获取：
   - **App Key** (应用唯一标识)
   - **App Secret** (用于签名)

## 关键API端点

### 商品相关
| 端点 | 描述 | 文档 |
|------|------|------|
| `/products/get` | 获取商品详情 | https://open.lazada.com/apps/doc/api?path=%2Fproducts%2Fget |
| `/product/item/get` | 获取单个商品信息 | https://open.lazada.com/apps/doc/api?path=%2Fproduct%2Fitem%2Fget |
| `/product/search` | 搜索商品 | 待确认 |

### 评论相关
| 端点 | 描述 | 文档 |
|------|------|------|
| `/product/review/list` | 获取商品评论列表 | 根据Alibaba文档提及 |
| `/product/review/get` | 获取单个评论详情 | 待确认 |

## API认证

Lazada API 使用标准 OAuth 2.0 流程：

1. **生成授权URL** (使用 App Key)
2. **卖家授权** - 获取 `code`
3. **换取 Access Token** - 使用 `code` + `App Secret`

参考: https://developer.alibaba.com/docs/doc.htm?treeId=499&articleId=120248

## 服务端点

不同国家使用不同端点：

| 国家 | 端点 |
|------|------|
| 泰国 | https://api.lazada.co.th |
| 越南 | https://api.lazada.vn |
| 马来西亚 | https://api.lazada.com.my |
| 新加坡 | https://api.lazada.sg |
| 印尼 | https://api.lazada.co.id |
| 菲律宾 | https://api.lazada.ph |

## 开发计划

### Phase 1: 注册与认证 (用户操作)
- [ ] 注册 Lazada 开发者账号
- [ ] 创建应用获取 App Key/App Secret
- [ ] 实现 OAuth 认证流程

### Phase 2: 基础数据获取 (我来实现)
- [ ] 实现商品搜索接口
- [ ] 实现商品详情获取
- [ ] 实现热销商品排行榜

### Phase 3: 评论分析 (我来实现)
- [ ] 实现评论获取接口
- [ ] 集成 AI 情感分析
- [ ] 生成洞察报告

## 参考资源

- Lazada Open Platform: https://open.lazada.com/
- API文档: https://open.lazada.com/apps/doc/api
- GitHub SDK (Node.js): https://github.com/branch8/lazada-open-platform-sdk
- Rutter集成指南: https://docs.rutter.com/platforms/commerce/lazada

## 与Shopee对比

| 特性 | Shopee | Lazada |
|------|--------|--------|
| 注册门槛 | ❌ 需要ERP资质 | ✅ 开放注册 |
| API稳定性 | ⚠️ 公共页面易变 | ✅ 官方API |
| 反爬虫 | ❌ 强 | ✅ 无需担心 |
| 评论数据 | ❌ 需要爬虫 | ✅ API提供 |
| 维护成本 | 高 | 低 |

**结论**: Lazada API 是目前获取东南亚电商数据的最佳途径。

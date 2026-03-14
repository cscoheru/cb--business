# 商机等级动态跟踪系统 - 实施完成

## 实施时间
2026-03-14

## 系统概述

基于C-P-I算法的商机动态等级系统，当用户收藏线索后自动进入商机跟踪系统，根据C-P-I分数动态升级和降级。

### 等级定义

| 等级 | 分数范围 | 描述 |
|------|----------|------|
| LEAD (线索) | < 60分 | 需进一步验证市场潜力 |
| NORMAL (普通) | 60-69分 | 保持关注，定期评估 |
| PRIORITY (重点) | 70-84分 | 优先验证，重点关注 |
| LANDABLE (落地) | ≥ 85分 | 可执行落地，启动项目 |

---

## 已完成的工作

### 1. 数据库模型 ✅
**文件**: `models/business_opportunity.py`

**新增内容**:
- `OpportunityGrade` 枚举 (LEAD, NORMAL, PRIORITY, LANDABLE)
- 7个新字段:
  - `grade` (SQLEnum) - 当前等级
  - `grade_history` (JSONB) - 等级变更历史
  - `last_grade_change_at` (DateTime) - 最后等级变更时间
  - `last_cpi_recalc_at` (DateTime) - 最后CPI重算时间
  - `cpi_total_score` (Float) - C-P-I总分
  - `cpi_competition_score` (Float) - 竞争度分数 (40%权重)
  - `cpi_potential_score` (Float) - 增长潜力分数 (40%权重)
  - `cpi_intelligence_gap_score` (Float) - 信息差分数 (20%权重)

### 2. 等级计算服务 ✅
**文件**: `services/grade_calculator.py`

**功能**:
- `calculate_grade()` - 根据CPI分数计算等级
- `should_upgrade()` / `should_downgrade()` - 判断升降级
- `get_grade_change_reason()` - 生成变更原因
- `create_grade_history_entry()` - 创建历史记录
- `get_next_target_scores()` - 获取上下目标分数
- `get_grade_description()` - 获取等级描述

### 3. 等级管理服务 ✅
**文件**: `services/grade_manager.py`

**功能**:
- `update_opportunity_grade()` - 更新商机等级
- `recalculate_and_update()` - 重新计算CPI并更新等级
- `batch_update_grades()` - 批量更新（用于调度器）
- `get_grade_summary()` - 获取等级摘要

### 4. 收藏API集成 ✅
**文件**: `api/favorites.py`

**功能**:
- 用户收藏卡片时自动创建商机记录
- 调用CPI算法计算初始分数
- 根据分数确定初始等级
- 关联商机到收藏记录

### 5. 定时调度任务 ✅
**文件**: `scheduler/opportunity_tasks.py`

**功能**:
- `grade_monitoring_job()` - 等级监控任务
- 每6小时执行一次
- 重新计算所有用户收藏商机的CPI分数
- 自动升级和降级
- 记录等级变更历史

### 6. 数据库迁移脚本 ✅
**文件**: `migrations/add_grading_system.py`

**待部署**: 需要在HK服务器执行

---

## 工作流程

```
用户收藏卡片
    ↓
api/favorites.py: add_favorite()
    ↓
创建 BusinessOpportunity
    ├─ 调用 opportunity_scorer.calculate_opportunity_score()
    ├─ 计算 C-P-I 三维度分数
    ├─ GradeCalculator.calculate_grade() 确定等级
    └─ 存入数据库
    ↓
定时任务 (每6小时)
    ├─ grade_monitoring_job()
    ├─ GradeManager.batch_update_grades()
    ├─ 重新计算CPI分数
    ├─ 检查是否需要升降级
    └─ 记录等级变更历史
```

---

## 部署步骤

### Step 1: 部署代码到HK服务器

```bash
# 1. 提交代码
git add models/business_opportunity.py \
        services/grade_calculator.py \
        services/grade_manager.py \
        api/favorites.py \
        scheduler/opportunity_tasks.py \
        migrations/add_grading_system.py
git commit -m "feat: add dynamic opportunity grading system based on CPI score"
git push origin main

# 2. 在HK服务器拉取代码
ssh hk-jump "cd /root/cb-business-repo/backend && git pull"

# 3. 重启FastAPI容器
ssh hk-jump "docker restart cb-business-api-fixed"
```

### Step 2: 执行数据库迁移

```bash
ssh hk-jump "cd /root/cb-business-repo/backend && PYTHONPATH=/root/cb-business-repo/backend python3 migrations/add_grading_system.py"
```

**预期输出**:
```
✓ 添加 grade 列
✓ 添加 grade_history 列
✓ 添加 last_grade_change_at 列
✓ 添加 last_cpi_recalc_at 列
✓ 添加 cpi_total_score 列
✓ 添加 cpi_competition_score 列
✓ 添加 cpi_potential_score 列
✓ 添加 cpi_intelligence_gap_score 列
✓ 添加 grade 索引
✓ 添加 cpi_total_score 索引
✓ 添加列注释

✅ 迁移成功：business_opportunities 表已添加等级系统字段
```

### Step 3: 验证部署

```bash
# 1. 测试收藏卡片API
curl -X POST "https://api.zenconsult.top/api/v1/favorites" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"card_id": "SOME_CARD_ID"}'

# 2. 检查商机是否创建
curl -X GET "https://api.zenconsult.top/api/v1/opportunities?user_id=YOUR_USER_ID"

# 3. 查看日志确认调度器运行
ssh hk-jump "docker logs cb-business-api-fixed --tail 50 | grep '等级监控'"
```

---

## API示例

### 收藏卡片创建商机

**请求**:
```http
POST /api/v1/favorites
Authorization: Bearer <token>
Content-Type: application/json

{
  "card_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**响应**:
```json
{
  "id": "...",
  "user_id": "...",
  "card_id": "...",
  "opportunity_id": "...",  // 新创建的商机ID
  "created_at": "2026-03-14T12:00:00Z"
}
```

### 查询商机等级

**请求**:
```http
GET /api/v1/opportunities/<opportunity_id>
Authorization: Bearer <token>
```

**响应**:
```json
{
  "id": "...",
  "title": "收藏商机: wireless_earbuds",
  "grade": "priority",
  "cpi_total_score": 78.5,
  "cpi_competition_score": 65.0,
  "cpi_potential_score": 82.0,
  "cpi_intelligence_gap_score": 75.0,
  "grade_history": [
    {
      "from_grade": "normal",
      "to_grade": "priority",
      "old_score": 68.0,
      "new_score": 78.5,
      "timestamp": "2026-03-14T18:00:00Z"
    }
  ],
  "last_grade_change_at": "2026-03-14T18:00:00Z",
  "last_cpi_recalc_at": "2026-03-14T18:00:00Z"
}
```

---

## 测试清单

- [ ] 代码部署到HK服务器
- [ ] 数据库迁移执行成功
- [ ] 收藏卡片能创建商机
- [ ] 商机初始等级正确计算
- [ ] 调度器正常运行
- [ ] 等级能自动升降
- [ ] 等级历史正确记录
- [ ] API返回包含新字段

---

## 故障排查

### 问题1: 迁移失败 - table does not exist

**原因**: 本地数据库没有business_opportunities表

**解决**: 必须在HK服务器执行迁移

### 问题2: 收藏卡片后商机未创建

**检查**:
1. 查看日志: `docker logs cb-business-api-fixed`
2. 确认CPI算法能正常计算
3. 检查数据库连接

### 问题3: 等级监控未运行

**检查**:
1. 确认调度器已启动: 查看日志 "商机定时任务调度器已启动"
2. 查看调度任务: `docker logs cb-business-api-fixed | grep '等级监控'`
3. 手动触发: 在代码中调用 `grade_monitoring_job()`

---

## 相关文件

### 代码文件
- `models/business_opportunity.py` - 数据模型
- `services/grade_calculator.py` - 等级计算
- `services/grade_manager.py` - 等级管理
- `services/opportunity_algorithm.py` - C-P-I算法
- `api/favorites.py` - 收藏API
- `scheduler/opportunity_tasks.py` - 定时任务
- `migrations/add_grading_system.py` - 数据库迁移

### 文档
- `/Users/kjonekong/.claude/plans/jazzy-stargazing-hickey.md` - 完整计划
- `/Users/kjonekong/Documents/Obsidian Vault/zenconsult跨境电商/商机潜力计算公式.md` - C-P-I公式

---

**版本**: 1.0
**创建日期**: 2026-03-14
**状态**: 代码完成，待部署HK服务器

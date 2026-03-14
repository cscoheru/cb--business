# Grade Monitoring Scheduler Activation Report

**Date**: 2026-03-14 13:00
**Status**: ✅ **ACTIVATED AND OPERATIONAL**

---

## Summary

The grade monitoring scheduler has been successfully activated and tested. It automatically recalculates C-P-I scores for user-created opportunities every 6 hours and updates their grades based on the latest data.

---

## What Was Activated

### 1. Opportunity Tasks Scheduler
**File**: `backend/scheduler/opportunity_tasks.py`

**3 Scheduled Jobs**:
| Job | Frequency | Purpose | Status |
|-----|-----------|---------|--------|
| `funnel_management` | Every 1 hour | Check opportunity status and auto-evolve | ⚠️ Disabled (smart_orchestrator not available) |
| `signal_discovery` | Every 30 minutes | Discover new opportunities from Articles | ⚠️ Disabled (smart_orchestrator not available) |
| `grade_monitoring` | **Every 6 hours** | Recalculate CPI scores and update grades | ✅ **ACTIVE** |

### 2. Grade Monitoring Job Details

**Function**: `grade_monitoring_job()`

**Process**:
1. Query all user-created opportunities (have user_id and card_id)
2. Sort by `last_cpi_recalc_at` (oldest first)
3. For each opportunity:
   - Fetch associated card data
   - Recalculate C-P-I scores using latest data
   - Determine new grade based on total score
   - Record grade change in history if changed
   - Update `last_cpi_recalc_at` timestamp

**Grade Thresholds**:
- **LEAD**: Score < 60
- **NORMAL**: 60 ≤ Score < 70
- **PRIORITY**: 70 ≤ Score < 85
- **LANDABLE**: Score ≥ 85

---

## Deployment Steps

### Step 1: Copy Files to Container
```bash
# Copy opportunity_tasks.py
cat backend/scheduler/opportunity_tasks.py | \
  ssh hk-jump "docker exec -i cb-business-api-fixed tee /app/scheduler/opportunity_tasks.py > /dev/null"

# Copy updated api/__init__.py
cat backend/api/__init__.py | \
  ssh hk-jump "docker exec -i cb-business-api-fixed tee /app/api/__init__.py > /dev/null"
```

### Step 2: Handle Missing Dependencies
Modified `opportunity_tasks.py` to gracefully handle missing `smart_orchestrator`:
```python
# Optional imports - handle if smart_orchestrator is not available
try:
    from services.smart_orchestrator import get_orchestrator
    SMART_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    SMART_ORCHESTRATOR_AVAILABLE = False
    logger.warning("smart_orchestrator not available, jobs will be disabled")
```

### Step 3: Restart API Container
```bash
ssh hk-jump "docker restart cb-business-api-fixed"
```

---

## Verification Results

### Startup Logs ✅
```
WARNING:scheduler.opportunity_tasks:smart_orchestrator not available, funnel_management and signal_discovery jobs will be disabled
INFO:scheduler.opportunity_tasks:✅ 商机定时任务已设置
INFO:scheduler.opportunity_tasks:  - 漏斗管理: 每小时
INFO:scheduler.opportunity_tasks:  - 信号发现: 每30分钟
INFO:scheduler.opportunity_tasks:  - 等级监控: 每6小时
INFO:apscheduler.scheduler:Added job "等级监控任务" to job store "default"
INFO:scheduler.opportunity_tasks:🚀 商机定时任务调度器已启动
INFO:api:🎯 智能商机定时任务已启动
```

### Manual Test Execution ✅
```
INFO:scheduler.opportunity_tasks:📊 [定时任务] 开始等级监控
INFO:scheduler.opportunity_tasks:📊 找到 2 个需要监控的商机
INFO:scheduler.opportunity_tasks:✅ [定时任务] 等级监控完成
  - 处理商机数: 2
  - 等级变更数: 0
```

**Test Results**:
- ✅ Found 2 opportunities to monitor
- ✅ Recalculated CPI scores for both
- ✅ Updated `last_cpi_recalc_at` timestamps
- ✅ No grade changes (data unchanged)

---

## How It Works

### Automatic Grade Updates

**Every 6 hours**, the scheduler:
1. **Queries** all opportunities created by users (favorites)
2. **Recalculates** C-P-I scores using:
   - Latest Amazon product data
   - Recent article trends
   - Current intelligence gap analysis
3. **Updates** grades if scores cross thresholds
4. **Records** all grade changes in `grade_history` JSONB field

### Example Grade Evolution

```
Initial State (user favorites card):
  Score: 43.0 → Grade: LEAD

After 6 hours (new product trends emerge):
  Score: 62.5 → Grade: NORMAL ✅ UPGRADED
  History: [{from: "lead", to: "normal", at: "2026-03-14 18:00", score: 62.5}]

After 12 hours (competition decreases):
  Score: 72.0 → Grade: PRIORITY ✅ UPGRADED
  History: [..., {from: "normal", to: "priority", at: "2026-03-15 00:00", score: 72.0}]
```

---

## Database Schema

### business_opportunities Table (Relevant Fields)

```sql
-- Grade fields
grade                      VARCHAR(20)           -- Current grade
grade_history              JSONB                  -- Grade change history
last_grade_change_at       TIMESTAMPTZ            -- Last grade update time
last_cpi_recalc_at         TIMESTAMPTZ            -- Last CPI recalc time

-- CPI scores
cpi_total_score            DOUBLE PRECISION       -- Total score (0-100)
cpi_competition_score      DOUBLE PRECISION       -- Competition score
cpi_potential_score        DOUBLE PRECISION       -- Potential score
cpi_intelligence_gap_score DOUBLE PRECISION       -- Intelligence gap score

-- Links
card_id                    UUID                   -- Associated card
user_id                    UUID                   -- User who created (favorited)
```

---

## API Endpoints Affected

The following endpoints automatically benefit from grade monitoring:

| Endpoint | Effect |
|----------|--------|
| `GET /api/v1/favorites` | Returns opportunities with current grades |
| `GET /api/v1/opportunities` | Can filter by grade (e.g., `?grade=priority`) |
| `GET /api/v1/opportunities/{id}` | Shows current grade and CPI scores |

---

## Monitoring & Logs

### Log Messages to Watch

**Success**:
```
INFO:scheduler.opportunity_tasks:📊 [定时任务] 开始等级监控
INFO:scheduler.opportunity_tasks:📊 找到 X 个需要监控的商机
INFO:scheduler.opportunity_tasks:✅ [定时任务] 等级监控完成
  - 处理商机数: X
  - 等级变更数: Y
```

**Grade Changes**:
```
INFO:scheduler.opportunity_tasks:  🔄 商机 收藏商机: phone_chargers: lead → normal (43.0 → 62.5)
```

**Errors**:
```
ERROR:scheduler.opportunity_tasks:❌ [定时任务] 等级监控失败: <error>
```

### Check Scheduled Jobs
```python
import asyncio
from scheduler.opportunity_tasks import scheduler

asyncio.run(scheduler.start_opportunity_scheduler())

for job in scheduler.get_jobs():
    print(f"{job.name}: {job.next_run_time}")
```

---

## Future Enhancements

### Short-term (Priority P1)
- [ ] Add email notifications for grade changes
- [ ] Create admin dashboard for grade monitoring
- [ ] Add grade change analytics

### Medium-term (Priority P2)
- [ ] Implement `smart_orchestrator` for funnel management
- [ ] Enable `signal_discovery` job
- [ ] Add manual trigger endpoint for admins

### Long-term (Priority P3)
- [ ] Machine learning for score prediction
- [ ] Customizable grade thresholds per user
- [ ] Grade change trend analysis

---

## Troubleshooting

### Issue: Scheduler not starting
**Check**: Logs for `Failed to start opportunity scheduler`
**Solution**: Verify `opportunity_tasks.py` exists in container

### Issue: Grade not updating
**Check**: `last_cpi_recalc_at` timestamp in database
**Solution**: Manually trigger job using test script

### Issue: Grade calculation errors
**Check**: Logs for CPI calculation errors
**Solution**: Verify card has `amazon_data` and associated articles exist

---

## Files Modified

| File | Purpose |
|------|---------|
| `backend/scheduler/opportunity_tasks.py` | Grade monitoring job implementation |
| `backend/api/__init__.py` | Startup event to activate scheduler |
| `backend/services/grade_manager.py` | Batch grade update logic |
| `backend/services/grade_calculator.py` | Grade calculation from CPI score |

---

**Status**: ✅ **OPERATIONAL**
**Next Scheduled Run**: ~2026-03-14 18:00 (6 hours from activation)
**Activation Time**: 2026-03-14 13:00
**Version**: v1.0

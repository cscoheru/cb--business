# Phase 1 Card System - Deployment Checklist

## Pre-Deployment Verification ✅

### Backend Tests (2026-03-13)
- [✅] Oxylabs API Integration - Working (16 products fetched)
- [✅] Card Generation Logic - Working (Score: 90, Price: $20-30)
- [⚠️] Database Connection - Fixed config (`connect_timeout` → `timeout`)
- [⚠️] Redis Cache - Infrastructure config (credentials in production env)

### Frontend Tests
- [✅] TypeScript Compilation - No errors in app code
- [✅] Production Build - Successful (34 pages)
- [✅] Card Display Components - Created
- [✅] Favorites System - Implemented with localStorage

---

## Deployment Steps

### 1. Backend Deployment (HK Server)

```bash
# SSH to HK server
ssh hk-jump

# Navigate to project
cd /path/to/cb-Business/backend

# Pull latest code
git pull origin frontend

# Install dependencies (if needed)
pip install -r requirements.txt

# Run database migration (if cards table doesn't exist)
psql -h $DB_HOST -U cbuser -d cbdb -f migrations/create_cards_table.sql

# Restart the API service
docker-compose restart api
# or
systemctl restart cb-business-api
```

**Environment Variables Required:**
```bash
DATABASE_URL=postgresql://cbuser:cbuser123@host:5432/cbdb
REDIS_URL=redis://host:6379
ZHIPU_AI_KEY=your_key  # Optional for AI analysis
OXYLABS_USERNAME=your_username
OXYLABS_PASSWORD=your_password
```

### 2. Frontend Deployment (Vercel)

```bash
# From frontend directory
cd /Users/kjonekong/Documents/cb-Business/frontend

# Deploy to production
npx vercel --prod

# Or through Vercel dashboard:
# https://vercel.com/dashboard
```

**Environment Variables (Vercel):**
```
NEXT_PUBLIC_API_URL=https://api.zenconsult.top
```

---

## Post-Deployment Testing

### API Endpoints to Verify

```bash
# Health check
curl https://api.zenconsult.top/health

# Daily cards
curl https://api.zenconsult.top/api/v1/cards/daily

# Latest cards
curl https://api.zenconsult.top/api/v1/cards/latest?limit=3

# Card stats
curl https://api.zenconsult.top/api/v1/cards/stats/overview
```

### Frontend Pages to Test

1. **Cards Listing**: https://www.zenconsult.top/cards
   - Tab switching (Today, Latest, History)
   - Category filter
   - Pagination

2. **Card Detail**: Click any card
   - All 4 tabs (Overview, Market Data, Insights, Top Products)
   - Like button functionality
   - Share button

3. **Favorites**: https://www.zenconsult.top/favorites
   - Empty state
   - Favorite list
   - Header badge count

---

## Scheduled Task Verification

### Check Scheduler Status

```bash
# SSH to server and check logs
ssh hk-jump
tail -f /var/log/cb-business/scheduler.log

# Or check APScheduler jobs table
psql -h $DB_HOST -U cbuser -d cbdb
SELECT * FROM apscheduler_jobs;
```

**Expected Jobs:**
- `generate_daily_cards` - Daily 8:00 AM
- `*_crawl` jobs - Every 30 minutes per source
- `cleanup_old_data` - Daily 3:00 AM

### Manual Card Generation Test

```bash
# SSH to server
ssh hk-jump

# Activate Python environment
cd /path/to/cb-Business/backend
source venv/bin/activate  # or use your env

# Run card generation
python -c "
import asyncio
from services.card_generator import generate_daily_cards
result = asyncio.run(generate_daily_cards())
print(result)
"
```

---

## Monitoring

### Key Metrics to Watch

1. **API Response Times**
   - `/api/v1/cards/daily` - Target: < 500ms
   - `/api/v1/cards/latest` - Target: < 300ms

2. **Oxylabs API Usage**
   - Check remaining credits
   - Monitor rate limits

3. **Database Performance**
   - Card table size
   - Query times

4. **Error Rates**
   - 404s on card details
   - 500s on card generation

### Log Locations

```bash
# Backend logs (HK server)
tail -f /var/log/cb-business/api.log
tail -f /var/log/cb-business/scheduler.log

# Vercel logs (Dashboard)
https://vercel.com/dashboard → Project → Logs
```

---

## Rollback Plan

If issues occur after deployment:

```bash
# Backend - Revert to previous commit
git log --oneline -5  # Find previous commit
git reset --hard <commit-hash>
docker-compose restart api

# Frontend - Rollback in Vercel
# Vercel Dashboard → Deployments → Click previous deployment → Promote to Production
```

---

## Known Issues & Workarounds

### 1. Redis Authentication Error
**Issue**: "invalid username-password pair or user is disabled"
**Workaround**: Card generation works without cache (slower but functional)
**Fix**: Verify REDIS_URL and credentials in production env

### 2. Database Connection Timeout
**Issue**: `connect_timeout` parameter error
**Fixed**: Changed to `timeout` in config/database.py

### 3. Oxylabs Rate Limits
**Issue**: May hit rate limits during testing
**Workaround**: Use cache=true, cache_ttl=1800 (30 min)

---

## Success Criteria

✅ **Deployment Successful When:**
- [ ] All API endpoints return 200 OK
- [ ] Frontend loads without errors
- [ ] Can view cards at /cards
- [ ] Can like/unlike cards
- [ ] Favorites page works
- [ ] Share button copies link
- [ ] Header shows favorite count
- [ ] Scheduler is running (check logs)
- [ ] Manual card generation works

---

## Next Steps After Deployment

1. **Day 11-14**: Monitor card generation for 3 days
2. **Collect user feedback** on card quality
3. **Analyze metrics**: Which cards get most likes?
4. **Iterate**: Adjust opportunity scoring, sweet spot pricing

---

## Support Contacts

- **Backend Issues**: Check logs → Fix code → Restart service
- **Frontend Issues**: Vercel logs → Fix code → Redeploy
- **Oxylabs API**: Check dashboard → Verify credits
- **Database**: Check connection → Verify credentials

---

*Deployment Checklist v1.0*
*Generated: 2026-03-13*
*Status: Ready for deployment*

# CB Business Deployment Guide

Complete guide for deploying CB Business to production.

---

## 📋 Prerequisites

### Required Accounts

| Service | Account | Purpose |
|---------|---------|---------|
| Vercel | https://vercel.com | Frontend hosting (cb.3strategy.cc, admin.cb.3strategy.cc) |
| Railway | https://railway.app | Backend API hosting (api.cb.3strategy.cc) |
| Vercel DNS | Included | Domain management |
| GitHub | https://github.com | Code repository |

### Required Tools

```bash
# Install CLI tools
npm install -g vercel
npm install -g railway

# Verify installation
vercel --version
railway --version
```

---

## 🚀 Part 1: Backend Deployment (Railway)

### Step 1: Railway Login

```bash
railway login
```

### Step 2: Create New Project

```bash
cd /Users/kjonekong/Documents/cb-Business/backend
railway init
```

Select: **Create New Project**

### Step 3: Configure Project

```bash
# Set project name
railway variables set APP_NAME="Cross-Border Business API"

# Add environment variables from deploy/railway/.env.example
railway variables set DATABASE_URL="postgresql://postgres:changeme-postgres-password-123@139.224.42.111:5432/crawler_db"
railway variables set REDIS_URL="redis://:FWD4D75OKyQS7HOluA6J@139.224.42.111:6379"
railway variables set SECRET_KEY="$(openssl rand -hex 32)"
railway variables set APP_ENV="production"
railway variables set DEBUG="false"
railway variables set ALLOWED_ORIGINS="https://cb.3strategy.cc,https://admin.cb.3strategy.cc"
railway variables set PORT="8000"
```

### Step 4: Add PostgreSQL (Optional - Railway Managed)

```bash
railway add postgresql
# Get connection string
railway variables get DATABASE_URL
```

### Step 5: Add Redis (Optional - Railway Managed)

```bash
railway add redis
# Get connection string
railway variables get REDIS_URL
```

### Step 6: Deploy

```bash
railway up
```

### Step 7: Configure Custom Domain

```bash
# Get your production URL
railway domain

# Add custom domain (in Railway Dashboard)
# Settings → Domains → Add Domain → api.cb.3strategy.cc
```

### Step 8: Verify Deployment

```bash
# Get deployment URL
railway domain

# Test health endpoint
curl https://your-production-url.up.railway.app/health
curl https://api.cb.3strategy.cc/health
```

---

## 🌐 Part 2: Frontend Deployment (Vercel)

### Step 1: Vercel Login

```bash
cd /Users/kjonekong/Documents/cb-Business/frontend
vercel login
```

### Step 2: Link Project

```bash
vercel link
```

Follow prompts:
- **Set up and deploy**: `Y`
- **Scope**: Select your account
- **Link to existing**: `N` (new project)
- **Project name**: `cb-business-frontend`
- **Directory**: `./`
- **Override settings**: `N`

### Step 3: Configure Environment Variables

```bash
# Add API URL
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://api.cb.3strategy.cc
```

Or via Vercel Dashboard:
1. Go to Project → Settings → Environment Variables
2. Add `NEXT_PUBLIC_API_URL` = `https://api.cb.3strategy.cc`

### Step 4: Deploy to Production

```bash
vercel --prod
```

### Step 5: Configure Custom Domain

In Vercel Dashboard:
1. Go to Settings → Domains
2. Add `cb.3strategy.cc`
3. Follow DNS instructions (A record to `76.76.21.21`)

### Step 6: Verify Deployment

```bash
# Test frontend
curl https://cb.3strategy.cc
curl https://cb.3strategy.cc/api/health  # Should proxy to Railway
```

---

## 🔧 Part 3: Admin Panel Deployment (Vercel)

### Step 1: Link Admin Project

```bash
cd /Users/kjonekong/Documents/cb-Business/admin
vercel link
```

Follow prompts (same as frontend):
- **Project name**: `cb-business-admin`

### Step 2: Configure Environment Variables

```bash
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://api.cb.3strategy.cc
```

### Step 3: Deploy to Production

```bash
vercel --prod
```

### Step 4: Configure Custom Domain

In Vercel Dashboard:
1. Go to Settings → Domains
2. Add `admin.cb.3strategy.cc`
3. Follow DNS instructions (A record to `76.76.21.21`)

### Step 5: Verify Deployment

```bash
# Test admin
curl https://admin.cb.3strategy.cc
```

---

## 🌍 Part 4: DNS Configuration

### Vercel DNS Configuration

Since your domain is managed by Vercel:

1. Go to Vercel Dashboard → Domains → `3strategy.cc`
2. Add the following records:

| Type | Name | Value |
|------|------|-------|
| A | `cb` | `76.76.21.21` |
| A | `admin` | `76.76.21.21` |
| CNAME | `api` | `[your-railway-domain].up.railway.app` |
| CNAME | `www` | `cb.3strategy.cc` |

### Verify DNS Propagation

```bash
# Check propagation
dig cb.3strategy.cc
dig admin.cb.3strategy.cc
dig api.cb.3strategy.cc

# Online tools
# https://dnschecker.org
# https://www.whatsmydns.net
```

---

## 🔒 Part 5: SSL Certificate Setup

Vercel and Railway automatically provision SSL certificates via Let's Encrypt. No manual setup required.

### Verify SSL

```bash
# Check certificate
openssl s_client -connect cb.3strategy.cc:443 -servername cb.3strategy.cc </dev/null 2>/dev/null | openssl x509 -noout -dates

# Test SSL Labs
# https://www.ssllabs.com/ssltest/analyze.html?d=cb.3strategy.cc
```

---

## ✅ Part 6: Post-Deployment Verification

### Health Checks

```bash
# Frontend
curl -I https://cb.3strategy.cc

# Admin
curl -I https://admin.cb.3strategy.cc

# API
curl https://api.cb.3strategy.cc/health

# API Documentation
curl -I https://api.cb.3strategy.cc/docs
```

### Functional Tests

1. **Frontend Accessibility**
   - Open https://cb.3strategy.cc
   - Check page loads correctly
   - Check navigation works

2. **Admin Panel Accessibility**
   - Open https://admin.cb.3strategy.cc
   - Check login page displays
   - Check admin dashboard accessible

3. **API Functionality**
   - Open https://api.cb.3strategy.cc/docs
   - Test `/api/v1/health` endpoint
   - Test user registration endpoint

4. **Cross-Origin Communication**
   - Frontend can call API
   - Admin can call API
   - CORS headers correct

---

## 📊 Part 7: Monitoring Setup

### Application Monitoring

1. **Sentry (Error Tracking)**
   ```bash
   vercel env add SENTRY_DSN production
   vercel env add NEXT_PUBLIC_SENTRY_DSN production
   ```

2. **Vercel Analytics**
   - Enable in Vercel Dashboard
   - Add to project settings

### Railway Monitoring

1. **Railway Metrics**
   - Available in Railway Dashboard
   - CPU, Memory, Response time

2. **Logs**
   ```bash
   railway logs
   railway logs --filter "ERROR"
   ```

---

## 🔄 Part 8: CI/CD Setup

### Automatic Deployments

**Vercel**: Automatic on push to `main` branch

**Railway**: Automatic on push to `main` branch (if connected to GitHub)

### GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: '--prod'
          working-directory: ./frontend

  deploy-admin:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.ADMIN_PROJECT_ID }}
          vercel-args: '--prod'
          working-directory: ./admin
```

---

## 🆘 Troubleshooting

### Common Issues

#### 1. Vercel Deployment Fails

```bash
# Check build logs
vercel logs

# Redeploy
vercel --force
```

#### 2. Railway Deployment Fails

```bash
# Check logs
railway logs

# Restart service
railway up
```

#### 3. DNS Not Propagating

- Wait 5-30 minutes for DNS propagation
- Check with `dig cb.3strategy.cc`
- Verify DNS records in Vercel Dashboard

#### 4. SSL Certificate Issues

- Wait up to 24 hours for Let's Encrypt
- Verify DNS records point correctly
- Check certificate at https://www.ssllabs.com/ssltest/

#### 5. API CORS Errors

- Verify `ALLOWED_ORIGINS` in Railway env
- Check frontend uses `https://api.cb.3strategy.cc`
- Verify CORS headers in API response

#### 6. Database Connection Errors

- Verify `DATABASE_URL` in Railway env
- Check database server is accessible
- Test connection string locally

---

## 📝 Environment Variables Checklist

### Vercel (Frontend & Admin)

- [ ] `NEXT_PUBLIC_API_URL=https://api.cb.3strategy.cc`
- [ ] `NEXT_PUBLIC_APP_NAME=Cross-Border Business`
- [ ] `NEXT_PUBLIC_GA_ID=` (optional)
- [ ] `NEXT_PUBLIC_SENTRY_DSN=` (optional)

### Railway (Backend)

- [ ] `DATABASE_URL` - PostgreSQL connection
- [ ] `REDIS_URL` - Redis connection
- [ ] `SECRET_KEY` - JWT secret (generate with `openssl rand -hex 32`)
- [ ] `APP_ENV=production`
- [ ] `DEBUG=false`
- [ ] `ALLOWED_ORIGINS=https://cb.3strategy.cc,https://admin.cb.3strategy.cc`
- [ ] `PORT=8000`

---

## 🎯 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Environment variables documented
- [ ] Database migrations tested
- [ ] API documentation complete

### Deployment
- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] Admin deployed to Vercel
- [ ] DNS records configured
- [ ] SSL certificates issued

### Post-Deployment
- [ ] All endpoints accessible
- [ ] API health check passing
- [ ] Frontend loads correctly
- [ ] Admin panel accessible
- [ ] User registration works
- [ ] Login/logout works
- [ ] Payment integration tested

### Monitoring
- [ ] Error tracking configured (Sentry)
- [ ] Analytics configured (GA/Vercel)
- [ ] Logging configured
- [ ] Uptime monitoring set up

---

*Last Updated: 2025-03-10*

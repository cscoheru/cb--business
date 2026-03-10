# CB Business Deployment Preparation

This directory contains all configuration files and scripts for deploying CB Business to production.

---

## 📁 Directory Structure

```
deploy/
├── nginx/                    # Nginx configuration files
│   ├── cb.3strategy.conf      # Frontend reverse proxy
│   ├── admin.cb.3strategy.conf # Admin panel reverse proxy
│   └── api.cb.3strategy.conf   # Backend API reverse proxy
├── vercel/                   # Vercel deployment configs
│   ├── vercel.json            # Frontend & Admin Vercel config
│   ├── project.json           # Project settings
│   └── .env.example           # Environment variables template
├── railway/                  # Railway deployment configs
│   ├── railway.json           # Railway project config
│   ├── Dockerfile             # Docker configuration
│   └── .env.example           # Environment variables template
├── scripts/                  # Deployment automation scripts
│   ├── deploy-all.sh          # Deploy all services
│   ├── rollback.sh            # Rollback deployments
│   └── health-check.sh        # Health check monitoring
└── docs/                     # Documentation
    ├── DEPLOYMENT_GUIDE.md    # Complete deployment guide
    └── DNS_CONFIGURATION.md   # DNS setup guide
```

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install CLI tools
npm install -g vercel railway

# Verify installation
vercel --version
railway --version
```

### 2. One-Command Deployment

```bash
# Deploy all services
./deploy/scripts/deploy-all.sh
```

### 3. Verify Deployment

```bash
# Run health checks
./deploy/scripts/health-check.sh
```

---

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] API documentation complete
- [ ] SSL certificates ready

### Backend (Railway)

- [ ] Railway project created
- [ ] Environment variables set
- [ ] PostgreSQL configured
- [ ] Redis configured
- [ ] Health check accessible
- [ ] API docs accessible

### Frontend (Vercel)

- [ ] Vercel project linked
- [ ] Custom domain configured
- [ ] Environment variables set
- [ ] Build successful
- [ ] Production accessible

### Admin Panel (Vercel)

- [ ] Vercel project linked
- [ ] Custom domain configured
- [ ] Environment variables set
- [ ] Build successful
- [ ] Production accessible

### DNS & SSL

- [ ] A records configured
- [ ] CNAME records configured
- [ ] DNS propagated
- [ ] SSL certificates issued
- [ ] HTTPS redirect working

### Post-Deployment

- [ ] All endpoints tested
- [ ] User registration works
- [ ] Login/logout works
- [ ] API calls successful
- [ ] Monitoring configured

---

## 🔧 Configuration Files

### Nginx Configuration

Each service has its own Nginx configuration:

| Service | Config File | Purpose |
|---------|-------------|---------|
| Frontend | `cb.3strategy.conf` | Reverse proxy to Vercel |
| Admin | `admin.cb.3strategy.conf` | Reverse proxy to Vercel with stricter security |
| API | `api.cb.3strategy.conf` | Reverse proxy to Railway with rate limiting |

**Key Features**:
- SSL termination with Let's Encrypt
- HTTP/2 support
- Security headers
- Rate limiting for API
- CORS configuration

### Vercel Configuration

- **vercel.json**: Build settings, headers, rewrites
- **project.json**: Project metadata
- **.env.example**: Environment variable template

### Railway Configuration

- **railway.json**: Build and deploy settings
- **Dockerfile**: Container configuration
- **.env.example**: Environment variable template

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | Complete step-by-step deployment guide |
| [DNS_CONFIGURATION.md](docs/DNS_CONFIGURATION.md) | DNS setup and SSL configuration |

---

## 🛠️ Scripts

### deploy-all.sh

Deploys all services in sequence:
1. Backend to Railway
2. Frontend to Vercel
3. Admin Panel to Vercel
4. Runs health checks

```bash
./deploy/scripts/deploy-all.sh
```

### rollback.sh

Rolls back all services to previous deployment:
```bash
./deploy/scripts/rollback.sh
```

### health-check.sh

Checks all services and reports status:
```bash
./deploy/scripts/health-check.sh
```

**Output includes**:
- DNS resolution
- SSL certificate status
- Service availability
- API endpoint checks

---

## 🌐 Domain Configuration

| Subdomain | Service | Platform | URL |
|-----------|---------|----------|-----|
| `cb.3strategy.cc` | Frontend | Vercel | https://cb.3strategy.cc |
| `admin.cb.3strategy.cc` | Admin Panel | Vercel | https://admin.cb.3strategy.cc |
| `api.cb.3strategy.cc` | Backend API | Railway | https://api.cb.3strategy.cc |

---

## 🔐 Security Considerations

### Environment Variables

**Never commit** actual values to Git. Use:
- `.env.example` as template
- Vercel/Railway dashboards for production values
- Railway secrets for sensitive data

### SSL Certificates

- **Vercel**: Automatic via Let's Encrypt
- **Railway**: Automatic via Let's Encrypt
- **Nginx**: Manual via Certbot (if using reverse proxy)

### Rate Limiting

API endpoints have rate limiting:
- Auth endpoints: 10 req/sec
- General API: 100 req/sec
- Webhooks: No limit

---

## 📊 Monitoring

### Application Monitoring

1. **Vercel Analytics**
   - Built-in analytics
   - Performance metrics
   - Deployment status

2. **Railway Metrics**
   - CPU/Memory usage
   - Response times
   - Error rates

3. **Sentry** (optional)
   - Error tracking
   - Performance monitoring
   - Release tracking

### Health Check Endpoints

- Frontend: `https://cb.3strategy.cc`
- Admin: `https://admin.cb.3strategy.cc`
- API Health: `https://api.cb.3strategy.cc/health`
- API Docs: `https://api.cb.3strategy.cc/docs`

---

## 🆘 Troubleshooting

### Deployment Fails

1. Check logs:
   ```bash
   vercel logs                    # Vercel
   railway logs                   # Railway
   ```

2. Verify environment variables:
   ```bash
   vercel env ls                  # Vercel
   railway variables              # Railway
   ```

3. Redeploy:
   ```bash
   vercel --prod --force          # Vercel
   railway up                     # Railway
   ```

### DNS Issues

1. Check propagation:
   ```bash
   dig cb.3strategy.cc
   ```

2. Verify records in Vercel Dashboard

3. Wait 5-30 minutes for propagation

### SSL Issues

1. Check certificate:
   ```bash
   openssl s_client -connect cb.3strategy.cc:443
   ```

2. Wait up to 24 hours for Let's Encrypt

3. Verify DNS records point correctly

### API Connection Errors

1. Check CORS settings in API
2. Verify `ALLOWED_ORIGINS` environment variable
3. Check API health endpoint

---

## 📝 Maintenance

### Regular Tasks

- **Daily**: Check health status
- **Weekly**: Review logs and metrics
- **Monthly**: Update dependencies
- **Quarterly**: Review SSL certificates

### Update Deployment

```bash
# Pull latest code
git pull origin main

# Deploy all services
./deploy/scripts/deploy-all.sh
```

### Backup Strategy

- Database: Daily automatic backups
- Code: Git version control
- Configuration: Documented in this directory

---

*Last Updated: 2025-03-10*

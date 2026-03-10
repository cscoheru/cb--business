# CB Business DNS Configuration Guide

## Domain Overview

**Primary Domain**: `3strategy.cc`
**DNS Provider**: Vercel (for main domain)

---

## DNS Records Configuration

### A Records (Vercel DNS)

| Name | Value | TTL | Purpose |
|------|-------|-----|---------|
| `cb` | `76.76.21.21` | Auto | User Frontend (Vercel) |
| `admin` | `76.76.21.21` | Auto | Admin Panel (Vercel) |
| `api` | Custom | Auto | Backend API (Railway) |

### CNAME Records (Vercel DNS)

| Name | Value | TTL | Purpose |
|------|-------|-----|---------|
| `www` | `cb.3strategy.cc` | Auto | WWW redirect |
| `api` | `<railway-domain>.up.railway.app` | Auto | API proxy |

---

## Vercel DNS Setup

### Step 1: Add Domain to Vercel

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add `cb.3strategy.cc`
3. Choose the recommended configuration
4. Repeat for `admin.cb.3strategy.cc`

### Step 2: Configure DNS Records

In Vercel Dashboard:

```
Domain: cb.3strategy.cc
Type: A Record
Name: @
Value: 76.76.21.21 (Vercel's IPv4)
```

```
Domain: admin.cb.3strategy.cc
Type: A Record
Name: admin
Value: 76.76.21.21 (Vercel's IPv4)
```

### Step 3: Verify Domain Ownership

Vercel will provide a TXT record to add:

```
Type: TXT
Name: _vercel
Value: verification-code-here
```

---

## Railway Domain Setup

### Option A: Use Railway-provided Domain

Railway provides a free subdomain:
```
your-project.up.railway.app
```

### Option B: Custom Domain

1. In Railway Dashboard → Your Project → Settings → Domains
2. Add `api.cb.3strategy.cc`
3. Railway will provide a CNAME target

**Vercel DNS Configuration for Railway:**

```
Type: CNAME
Name: api
Value: your-production-project.up.railway.app
Proxy: False
```

---

## Complete DNS Configuration (Vercel DNS)

```
; A Records
@           A    76.76.21.21          ; cb.3strategy.cc (Vercel)
admin       A    76.76.21.21          ; admin.cb.3strategy.cc (Vercel)
www         A    76.76.21.21          ; www.cb.3strategy.cc

; CNAME Records
api         CNAME cb-api.up.railway.app ; api.cb.3strategy.cc (Railway)

; TXT Records
@           TXT  "v=spf1 include:_spf.mx.cloudflare.net ~all"
_dmarc      TXT  "v=DMARC1; p=quarantine; rua=mailto:dmarc@3strategy.cc"
_vercel     TXT  "verify-code-here"
google-site-verification TXT  "your-verification-code"

; MX Records (Cloudflare)
@           MX   route1.mx.cloudflare.net (priority: 91)
@           MX   route2.mx.cloudflare.net (priority: 100)
@           MX   route3.mx.cloudflare.net (priority: 46)
```

---

## SSL Certificate Setup

### Vercel Automatic SSL

Vercel automatically provisions SSL certificates via Let's Encrypt:
- ✅ No manual configuration needed
- ✅ Auto-renewal
- ✅ Supports HTTP/2

### Railway SSL

Railway also provides automatic SSL for custom domains:
- ✅ Let's Encrypt integration
- ✅ Auto-renewal
- ✅ Supports HTTP/2

### Alternative: Nginx SSL Termination

If using Nginx reverse proxy on your server:

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificates
sudo certbot --nginx -d cb.3strategy.cc \
                      -d admin.cb.3strategy.cc \
                      -d api.cb.3strategy.cc

# Auto-renewal (cron)
sudo crontab -e
# Add: 0 0 * * * certbot renew --quiet
```

---

## Verification Commands

### Check DNS Propagation

```bash
# Check A record
dig cb.3strategy.cc A +short
dig admin.cb.3strategy.cc A +short

# Check CNAME record
dig api.cb.3strategy.cc CNAME +short

# Check all records
dig 3strategy.cc ANY +short
```

### Check SSL Certificate

```bash
# Check certificate
openssl s_client -connect cb.3strategy.cc:443 -servername cb.3strategy.cc </dev/null 2>/dev/null | openssl x509 -noout -dates

# Check HTTP/2 support
nghttp https://cb.3strategy.cc

# Full SSL test
curl -I https://cb.3strategy.cc
```

### Test Endpoints

```bash
# Frontend
curl https://cb.3strategy.cc

# Admin
curl https://admin.cb.3strategy.cc

# API Health
curl https://api.cb.3strategy.cc/health

# API Docs
curl https://api.cb.3strategy.cc/docs
```

---

## Troubleshooting

### DNS Not Propagating

```bash
# Check global propagation
dig cb.3strategy.cc @8.8.8.8
dig cb.3strategy.cc @1.1.1.1

# Check local cache
sudo dscacheutil -flushcache  # macOS
sudo systemd-resolve --flush-caches  # Linux
```

### SSL Certificate Issues

```bash
# Check certificate chain
openssl s_client -connect cb.3strategy.cc:443 -showcerts

# Verify certificate
curl -vI https://cb.3strategy.cc 2>&1 | grep -i ssl
```

### Mixed Content Warnings

Ensure all resources use HTTPS:
- Update `NEXT_PUBLIC_API_URL` to `https://`
- Check for hardcoded `http://` in code
- Verify CSP headers allow HTTPS resources

---

## Migration Checklist

- [ ] Add domains to Vercel
- [ ] Configure A records for cb.3strategy.cc and admin.cb.3strategy.cc
- [ ] Configure CNAME record for api.cb.3strategy.cc
- [ ] Verify domain ownership (TXT records)
- [ ] Deploy Railway backend and get custom domain
- [ ] Wait for DNS propagation (5-30 minutes)
- [ ] Verify SSL certificates are issued
- [ ] Test all endpoints (frontend, admin, API)
- [ ] Configure email SPF/DMARC records
- [ ] Set up monitoring for SSL expiry

---

*Last Updated: 2025-03-10*

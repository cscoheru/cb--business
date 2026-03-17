# API Quick Reference Card

## Authentication

```bash
curl -H "X-API-Key: cb_live_xxx" https://api.zenconsult.top/api/v1/public/...
```

## Endpoints Summary

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| `GET` | `/cpi/weights` | Dev+ | Get CPI weight configuration |
| `POST` | `/cpi/calculate` | Dev+ | Calculate CPI score |
| `POST` | `/cpi/calculate/advanced` | Biz+ | Advanced CPI with full details |
| `GET` | `/orchestrator/status` | Dev+ | Service status |
| `POST` | `/orchestrator/analyze` | Dev+ | AI-powered analysis |
| `POST` | `/orchestrator/analyze/batch` | Biz+ | Batch analysis (max 10) |
| `GET` | `/openclaw/skills` | Dev+ | List available skills |
| `POST` | `/openclaw/invoke` | Dev+ | Invoke OpenClaw skill |
| `GET` | `/openclaw/health` | Dev+ | MCP health check |

## CPI Scoring Weights

```
CPI Total = C × 40% + P × 40% + I × 20%

C (Competition):
  - Price Dispersion: 37.5%
  - Seller Density: 37.5%
  - Review Growth: 25%

P (Potential):
  - Google Trends: 50%
  - Regional Comparison: 50%

I (Intelligence):
  - AI Insights: 100%
```

## Quick Examples

### Calculate CPI

```bash
curl -X POST https://api.zenconsult.top/api/v1/public/cpi/calculate \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"amazon_data": {"price": {"min": 10, "max": 50, "avg": 25}}}'
```

### Analyze Opportunity

```bash
curl -X POST https://api.zenconsult.top/api/v1/public/orchestrator/analyze \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"category": "phone_cases"}'
```

### Scan Market

```bash
curl -X POST https://api.zenconsult.top/api/v1/public/openclaw/invoke \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"skill": "deep_market_scan", "params": {"category": "phone_cases"}}'
```

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Invalid API Key |
| 403 | Tier Not Allowed |
| 429 | Rate Limited |
| 500 | Server Error |

## Rate Limits

| Tier | Per Minute | Per Day |
|------|------------|---------|
| Developer | 60 | 1,000 |
| Business | 300 | 10,000 |
| Enterprise | 1,000 | 100,000 |

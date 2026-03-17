# Public API Documentation

> **Version**: 1.0.0
> **Base URL**: `https://api.zenconsult.top`
> **Last Updated**: 2026-03-17

---

## Overview

The CB-Business Public API provides programmatic access to our AI-powered market analysis tools. Third-party developers can integrate CPI scoring, AI orchestration, and OpenClaw data collection into their applications.

### Key Features

- **CPI Algorithm API** - Competition-Potential-Intelligence scoring for market opportunities
- **AI Orchestrator API** - AI-driven analysis with automatic data gap detection
- **OpenClaw Integration** - Direct access to e-commerce data collection tools

---

## Authentication

All API requests require authentication via an API Key.

### Getting an API Key

1. Sign up at [zenconsult.top](https://www.zenconsult.top)
2. Navigate to Dashboard → API Keys
3. Click "Create New Key"
4. Select your subscription tier
5. Copy and securely store your key

### Using the API Key

Include your API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: cb_live_your_api_key_here" \
  https://api.zenconsult.top/api/v1/public/cpi/weights
```

### Security Notes

- **Never expose your API key in client-side code**
- Store keys in environment variables or secure vaults
- Rotate keys periodically via the dashboard
- Each key is hashed with SHA256 - we never store the raw key

---

## Rate Limiting

Rate limits are enforced per API key using Redis sliding windows.

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 45
X-RateLimit-Limit-Day: 1000
X-RateLimit-Remaining-Day: 856
```

### Rate Limit Response

When rate limited, you'll receive a `429 Too Many Requests` response:

```json
{
  "detail": {
    "error": "rate_limit_exceeded",
    "message": "API rate limit exceeded",
    "rate_info": {
      "minute_count": 61,
      "minute_limit": 60,
      "day_count": 1001,
      "day_limit": 1000
    }
  }
}
```

---

## Subscription Tiers

| Tier | Price | Requests/Day | Requests/Minute | Features |
|------|-------|--------------|-----------------|----------|
| **Developer** | ¥299/mo | 1,000 | 60 | CPI Basic, Orchestrator Basic, OpenClaw Basic |
| **Business** | ¥999/mo | 10,000 | 300 | All Developer + CPI Advanced, Batch Analysis, Mock Orders |
| **Enterprise** | ¥2,999/mo | 100,000 | 1,000 | All Business + Priority Support, Custom Limits |

### Tier Feature Access

| Endpoint | Developer | Business | Enterprise |
|----------|-----------|----------|------------|
| `GET /cpi/weights` | ✅ | ✅ | ✅ |
| `POST /cpi/calculate` | ✅ | ✅ | ✅ |
| `POST /cpi/calculate/advanced` | ❌ | ✅ | ✅ |
| `POST /orchestrator/analyze` | ✅ | ✅ | ✅ |
| `POST /orchestrator/analyze/batch` | ❌ | ✅ | ✅ |
| `POST /openclaw/invoke` (deep_market_scan) | ✅ | ✅ | ✅ |
| `POST /openclaw/invoke` (mock_order_analysis) | ❌ | ✅ | ✅ |
| `POST /openclaw/invoke` (competitor_watch) | ❌ | ✅ | ✅ |

---

## API Endpoints

### CPI Algorithm API

#### Calculate CPI Score

```http
POST /api/v1/public/cpi/calculate
```

Calculate the Competition-Potential-Intelligence score for a product or market.

**Request Body:**

```json
{
  "amazon_data": {
    "price": {
      "min": 10.0,
      "max": 50.0,
      "avg": 25.0
    },
    "competition": {
      "total_sellers": 100
    },
    "total_products": 500,
    "rating": {
      "avg": 4.2,
      "count": 1500
    }
  },
  "google_trends_data": {
    "score": 75,
    "growth_rate": 0.15
  },
  "article_insights": [
    {"title": "Market trend article", "relevance": 0.8}
  ]
}
```

**Response:**

```json
{
  "success": true,
  "c_score": 61.75,
  "p_score": 63.25,
  "i_score": 62.5,
  "total_score": 62.5,
  "confidence": 0.63,
  "data_quality": "medium",
  "recommendation": "建议进一步分析具体品类和价格区间",
  "risk_level": "low",
  "details": {
    "competition": {
      "price_dispersion": 1.6,
      "price_score": 0,
      "seller_density": 0.2,
      "seller_score": 98.0,
      "review_count": 1500,
      "review_score": 100,
      "weighted_score": 61.8
    },
    "potential": {
      "google_trends_score": 76.5,
      "growth_rate": 0.15,
      "regional_score": "single_region",
      "weighted_score": 63.2
    },
    "intelligence": {
      "articles_analyzed": 1,
      "base_score": 62.5,
      "insight_bonus": 5,
      "final_score": 67.5
    },
    "is_multi_platform": false
  },
  "tier": "developer"
}
```

#### Get CPI Weights

```http
GET /api/v1/public/cpi/weights
```

Returns the CPI algorithm weight configuration.

**Response:**

```json
{
  "competition": {
    "weight": 0.4,
    "description": "竞争度 - 衡量市场竞争激烈程度",
    "components": {
      "price_dispersion": {"weight": 0.375, "description": "价格离散度"},
      "seller_density": {"weight": 0.375, "description": "卖家密度"},
      "review_growth": {"weight": 0.25, "description": "评论增长趋势"}
    }
  },
  "potential": {
    "weight": 0.4,
    "description": "潜力 - 衡量市场增长空间",
    "components": {
      "google_trends": {"weight": 0.5, "description": "Google Trends 增长趋势"},
      "regional_comparison": {"weight": 0.5, "description": "区域市场对比"}
    }
  },
  "intelligence": {
    "weight": 0.2,
    "description": "智能洞察 - AI 综合分析和建议",
    "components": {
      "ai_insights": {"weight": 1.0, "description": "基于 C 和 P 分数的 AI 综合判断"}
    }
  }
}
```

---

### AI Orchestrator API

#### Analyze Opportunity

```http
POST /api/v1/public/orchestrator/analyze
```

AI-driven analysis that automatically detects data gaps and recommends actions.

**Request Body:**

```json
{
  "category": "phone_cases",
  "amazon_data": {
    "products": [...],
    "price": {"min": 10, "max": 50, "avg": 25}
  },
  "google_trends_data": {
    "score": 75,
    "growth_rate": 0.15
  },
  "depth_level": "standard"
}
```

**Response:**

```json
{
  "success": true,
  "category": "phone_cases",
  "initial_score": {
    "total_score": 43.0,
    "competition": {"score": 40.0},
    "potential": {"score": 45.0},
    "intelligence_gap": {"score": 50.0}
  },
  "data_gaps": [
    {
      "type": "competition_deep_scan",
      "priority": "high",
      "reason": "竞争度分数40较低，需要验证品牌分布和CPC",
      "skill": "deep_market_scan"
    },
    {
      "type": "potential_trend_verification",
      "priority": "medium",
      "reason": "增长潜力分数45处于中等区间，需要验证趋势持续性"
    }
  ],
  "data_gaps_filled": [...],
  "final_score": {
    "total_score": 61.0,
    "data_enhanced": true
  },
  "confidence_improvement": 18.0,
  "execution_time_ms": 1250,
  "tier": "developer"
}
```

#### Get Orchestrator Status

```http
GET /api/v1/public/orchestrator/status
```

**Response:**

```json
{
  "status": "active",
  "version": "1.0.0",
  "capabilities": [
    "cpi_scoring",
    "data_gap_detection",
    "openclaw_integration",
    "batch_analysis"
  ],
  "uptime_seconds": 3600
}
```

---

### OpenClaw Integration API

#### List Available Skills

```http
GET /api/v1/public/openclaw/skills
```

**Response:**

```json
{
  "skills": [
    {
      "name": "deep_market_scan",
      "description": "深度市场扫描 - 获取竞争度、价格分布、评论趋势",
      "params": {
        "category": "string - 产品类目 (必填)",
        "anomaly_detected": "boolean - 是否检测异常 (可选)",
        "depth_level": "string - deep/standard/intensive (可选)"
      }
    },
    {
      "name": "mock_order_analysis",
      "description": "模拟订单分析 - 获取真实成本、物流信息",
      "params": {
        "asin": "string - Amazon ASIN (必填)",
        "quantity": "integer - 购买数量 (可选)"
      }
    },
    {
      "name": "competitor_watch",
      "description": "竞争对手监控 - 跟踪价格变化、新品上架",
      "params": {
        "category": "string - 产品类目 (必填)",
        "competitors": "array - 竞争对手列表 (可选)"
      }
    }
  ],
  "total": 3
}
```

#### Invoke OpenClaw Skill

```http
POST /api/v1/public/openclaw/invoke
```

**Request Body:**

```json
{
  "skill": "deep_market_scan",
  "params": {
    "category": "phone_cases",
    "depth_level": "deep"
  }
}
```

**Response:**

```json
{
  "success": true,
  "skill": "deep_market_scan",
  "data": {
    "category": "phone_cases",
    "brand_concentration": 0.65,
    "price_range": {
      "min": 10,
      "max": 50,
      "avg": 25
    },
    "new_product_count": 15,
    "competition_level": "medium",
    "top_brands": ["Anker", "Spigen", "OtterBox"],
    "sample_size": 100
  },
  "execution_time_ms": 45,
  "tier": "developer"
}
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": {
    "error": "error_code",
    "message": "Human readable error message"
  },
  "code": "HTTP_ERROR"
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `invalid_request` | Malformed request body |
| 400 | `invalid_skill` | Unknown OpenClaw skill name |
| 401 | `missing_api_key` | No X-API-Key header provided |
| 401 | `invalid_api_key` | API key not found or inactive |
| 403 | `api_key_expired` | Subscription has expired |
| 403 | `tier_not_allowed` | Endpoint requires higher tier |
| 429 | `rate_limit_exceeded` | Too many requests |
| 500 | `internal_error` | Server error |

### Example: Tier Not Allowed

```json
{
  "detail": {
    "error": "tier_not_allowed",
    "message": "Skill 'mock_order_analysis' requires business tier or higher",
    "current_tier": "developer",
    "required_tier": "business"
  }
}
```

---

## SDK Examples

### Python

```python
import requests

class CBBusinessClient:
    def __init__(self, api_key: str):
        self.base_url = "https://api.zenconsult.top/api/v1/public"
        self.headers = {"X-API-Key": api_key}

    def calculate_cpi(self, amazon_data: dict, trends_data: dict = None):
        """Calculate CPI score"""
        response = requests.post(
            f"{self.base_url}/cpi/calculate",
            headers=self.headers,
            json={
                "amazon_data": amazon_data,
                "google_trends_data": trends_data
            }
        )
        return response.json()

    def analyze_opportunity(self, category: str, amazon_data: dict = None):
        """AI-powered opportunity analysis"""
        response = requests.post(
            f"{self.base_url}/orchestrator/analyze",
            headers=self.headers,
            json={
                "category": category,
                "amazon_data": amazon_data,
                "depth_level": "standard"
            }
        )
        return response.json()

    def invoke_openclaw(self, skill: str, params: dict):
        """Invoke OpenClaw skill"""
        response = requests.post(
            f"{self.base_url}/openclaw/invoke",
            headers=self.headers,
            json={"skill": skill, "params": params}
        )
        return response.json()


# Usage
client = CBBusinessClient("cb_live_your_api_key")

# Calculate CPI
result = client.calculate_cpi({
    "price": {"min": 10, "max": 50, "avg": 25},
    "competition": {"total_sellers": 100},
    "total_products": 500,
    "rating": {"avg": 4.2, "count": 1500}
})

print(f"CPI Score: {result['total_score']}")
print(f"Risk Level: {result['risk_level']}")
```

### JavaScript / TypeScript

```typescript
interface CPIRequest {
  amazon_data?: {
    price?: { min: number; max: number; avg: number };
    competition?: { total_sellers: number };
    total_products?: number;
    rating?: { avg: number; count: number };
  };
  google_trends_data?: {
    score: number;
    growth_rate: number;
  };
}

interface CPIResponse {
  success: boolean;
  c_score: number;
  p_score: number;
  i_score: number;
  total_score: number;
  confidence: number;
  data_quality: string;
  recommendation: string;
  risk_level: string;
}

class CBBusinessClient {
  private baseUrl = 'https://api.zenconsult.top/api/v1/public';
  private headers: HeadersInit;

  constructor(apiKey: string) {
    this.headers = {
      'X-API-Key': apiKey,
      'Content-Type': 'application/json',
    };
  }

  async calculateCPI(data: CPIRequest): Promise<CPIResponse> {
    const response = await fetch(`${this.baseUrl}/cpi/calculate`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(data),
    });
    return response.json();
  }

  async analyzeOpportunity(category: string, amazonData?: object): Promise<any> {
    const response = await fetch(`${this.baseUrl}/orchestrator/analyze`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        category,
        amazon_data: amazonData,
        depth_level: 'standard',
      }),
    });
    return response.json();
  }

  async invokeOpenClaw(skill: string, params: object): Promise<any> {
    const response = await fetch(`${this.baseUrl}/openclaw/invoke`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ skill, params }),
    });
    return response.json();
  }
}

// Usage
const client = new CBBusinessClient('cb_live_your_api_key');

const result = await client.calculateCPI({
  amazon_data: {
    price: { min: 10, max: 50, avg: 25 },
    competition: { total_sellers: 100 },
    total_products: 500,
    rating: { avg: 4.2, count: 1500 },
  },
});

console.log(`CPI Score: ${result.total_score}`);
```

### cURL Examples

```bash
# Calculate CPI
curl -X POST https://api.zenconsult.top/api/v1/public/cpi/calculate \
  -H "X-API-Key: cb_live_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "amazon_data": {
      "price": {"min": 10, "max": 50, "avg": 25},
      "competition": {"total_sellers": 100},
      "total_products": 500,
      "rating": {"avg": 4.2, "count": 1500}
    }
  }'

# Get weights
curl -H "X-API-Key: cb_live_your_api_key" \
  https://api.zenconsult.top/api/v1/public/cpi/weights

# Analyze opportunity
curl -X POST https://api.zenconsult.top/api/v1/public/orchestrator/analyze \
  -H "X-API-Key: cb_live_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "phone_cases",
    "depth_level": "standard"
  }'

# Invoke OpenClaw
curl -X POST https://api.zenconsult.top/api/v1/public/openclaw/invoke \
  -H "X-API-Key: cb_live_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "deep_market_scan",
    "params": {"category": "phone_cases", "depth_level": "deep"}
  }'
```

---

## Best Practices

### 1. Handle Rate Limits Gracefully

```python
import time

def call_api_with_retry(client, max_retries=3):
    for attempt in range(max_retries):
        response = client.calculate_cpi(data)

        if response.status_code == 429:
            # Wait and retry
            wait_time = 60  # seconds
            time.sleep(wait_time)
            continue

        return response

    raise Exception("Max retries exceeded")
```

### 2. Cache Results

CPI scores for the same product data won't change frequently. Cache results to reduce API calls:

```python
import hashlib
import json

def get_cached_cpi(client, data, cache):
    # Create cache key from data
    key = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    if key in cache:
        return cache[key]

    result = client.calculate_cpi(data)
    cache[key] = result
    return result
```

### 3. Use Batch Endpoints

For multiple analyses, use batch endpoints to reduce API calls:

```python
# Instead of multiple individual calls
results = client.batch_analyze([
    {"category": "phone_cases"},
    {"category": "laptop_stands"},
    {"category": "wireless_chargers"},
])
```

### 4. Secure Key Storage

```python
# Use environment variables
import os
api_key = os.environ.get("CB_BUSINESS_API_KEY")

# Or use a secrets manager
from aws_secretsmanager import get_secret
api_key = get_secret("cb-business-api-key")
```

---

## Support

- **Documentation**: [docs.zenconsult.top](https://docs.zenconsult.top)
- **API Status**: [status.zenconsult.top](https://status.zenconsult.top)
- **Email**: api-support@zenconsult.top
- **GitHub Issues**: [github.com/cscoheru/cb-business/issues](https://github.com/cscoheru/cb-business/issues)

---

## Changelog

### v1.0.0 (2026-03-17)
- Initial public API release
- CPI Algorithm API
- AI Orchestrator API
- OpenClaw Integration API
- Developer, Business, Enterprise tiers

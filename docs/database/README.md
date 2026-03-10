# CB Business Database Documentation

**Database**: `crawler_db`
**Host**: 139.224.42.111:5432
**User**: postgres
**Last Updated**: 2025-03-10

---

## Connection Information

### Development
```
Host: 139.224.42.111
Port: 5432
Database: crawler_db
User: postgres
Password: changeme-postgres-password-123
```

### Connection String
```
postgresql://postgres:changeme-postgres-password-123@139.224.42.111:5432/crawler_db
```

### Connection via Docker (from server)
```bash
docker exec -it postgres psql -U postgres -d crawler_db
```

---

## Table Overview

| # | Table Name | Purpose | Rows (Est.) |
|---|------------|---------|-------------|
| 1 | `users` | User accounts and profiles | 0 |
| 2 | `subscriptions` | User subscription plans | 0 |
| 3 | `payments` | Payment transactions | 0 |
| 4 | `user_usage` | Usage tracking for billing | 0 |
| 5 | `articles` | Cross-border business articles | 0 |
| 6 | `opportunities` | Business opportunities | 0 |
| 7 | `risk_alerts` | Risk warnings for sellers | 0 |
| 8 | `cost_references` | Platform and cost references | 0 |

---

## Table Schemas

### 1. users (用户表)

User account information and subscription status.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | User unique identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User email (login) |
| `password_hash` | VARCHAR(255) | | Bcrypt hashed password |
| `name` | VARCHAR(100) | | Display name |
| `phone` | VARCHAR(20) | | Phone number |
| `avatar_url` | TEXT | | Profile avatar URL |
| `plan_tier` | VARCHAR(20) | DEFAULT 'free' | free, pro, enterprise |
| `plan_status` | VARCHAR(20) | DEFAULT 'active' | active, canceled, expired, suspended |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Account creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update (auto-trigger) |
| `last_login_at` | TIMESTAMPTZ | | Last successful login |
| `region_preference` | VARCHAR(50) | | Preferred market region |
| `currency_preference` | VARCHAR(10) | DEFAULT 'CNY' | Preferred currency |

**Indexes**:
- `idx_users_email` on (email)
- `idx_users_plan_tier` on (plan_tier)
- `idx_users_plan_status` on (plan_status)
- `idx_users_created_at` on (created_at)

---

### 2. subscriptions (订阅表)

User subscription plan records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Subscription ID |
| `user_id` | UUID | FK → users(id), NOT NULL | User reference |
| `plan_tier` | VARCHAR(20) | NOT NULL | free, pro, enterprise |
| `status` | VARCHAR(20) | DEFAULT 'active' | active, canceled, expired, pending |
| `billing_cycle` | VARCHAR(10) | | monthly, quarterly, annual |
| `amount` | DECIMAL(10,2) | | Subscription amount |
| `currency` | VARCHAR(10) | DEFAULT 'CNY' | Currency code |
| `started_at` | TIMESTAMPTZ | DEFAULT NOW() | Subscription start |
| `expires_at` | TIMESTAMPTZ | | Subscription expiry |
| `canceled_at` | TIMESTAMPTZ | | Cancellation timestamp |
| `auto_renew` | BOOLEAN | DEFAULT TRUE | Auto-renewal flag |
| `payment_method` | VARCHAR(50) | | wechat, alipay, stripe |
| `external_subscription_id` | VARCHAR(255) | | Payment gateway ID |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation |

**Indexes**:
- `idx_subscriptions_user_id` on (user_id)
- `idx_subscriptions_status` on (status)
- `idx_subscriptions_expires_at` on (expires_at)

---

### 3. payments (支付记录表)

Payment transaction records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Payment ID |
| `user_id` | UUID | FK → users(id), NOT NULL | User reference |
| `subscription_id` | UUID | FK → subscriptions(id) | Related subscription |
| `amount` | DECIMAL(10,2) | NOT NULL | Payment amount |
| `currency` | VARCHAR(10) | DEFAULT 'CNY' | Currency code |
| `payment_method` | VARCHAR(50) | NOT NULL | wechat, alipay, stripe, paypal |
| `payment_status` | VARCHAR(20) | DEFAULT 'pending' | pending, processing, completed, failed, refunded |
| `transaction_id` | VARCHAR(255) | UNIQUE | Payment gateway transaction ID |
| `external_order_id` | VARCHAR(255) | | Gateway order ID |
| `metadata` | JSONB | | Additional payment data |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Payment initiation |
| `completed_at` | TIMESTAMPTZ | | Payment completion |

**Indexes**:
- `idx_payments_user_id` on (user_id)
- `idx_payments_status` on (payment_status)
- `idx_payments_transaction_id` on (transaction_id)
- `idx_payments_created_at` on (created_at)

---

### 4. user_usage (用户使用记录表)

Track user usage for billing and limits.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Usage record ID |
| `user_id` | UUID | FK → users(id), NOT NULL | User reference |
| `usage_type` | VARCHAR(50) | NOT NULL | api_call, article_view, opportunity_access, report_download, search_query |
| `quantity` | INTEGER | DEFAULT 1 | Usage count |
| `period_date` | DATE | DEFAULT CURRENT_DATE | Billing period date |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record timestamp |

**Indexes**:
- `idx_user_usage_user_date` on (user_id, period_date)
- `idx_user_usage_type` on (usage_type)

---

### 5. articles (文章表)

Cross-border business articles and insights.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Article ID |
| `title` | TEXT | NOT NULL | Article title |
| `summary` | TEXT | | Article summary |
| `content` | TEXT | | Full article content |
| `source` | VARCHAR(50) | | Content source |
| `url` | TEXT | UNIQUE | Source URL |
| `published_at` | TIMESTAMPTZ | | Original publish date |
| `crawled_at` | TIMESTAMPTZ | DEFAULT NOW() | Crawling timestamp |
| `region` | VARCHAR(50) | | Target region |
| `country` | VARCHAR(50) | | Target country |
| `platform` | VARCHAR(50) | | Related platform |
| `content_theme` | VARCHAR(20) | | market_insight, policy_update, case_study, tutorial, news |
| `subcategory` | VARCHAR(50) | | Content subcategory |
| `tags` | TEXT[] | | Content tags (array) |
| `risk_level` | VARCHAR(20) | | low, medium, high, critical |
| `opportunity_score` | DECIMAL(3,2) | | AI-calculated score (0.00-1.00) |
| `slug` | TEXT | UNIQUE | URL-friendly identifier |
| `meta_description` | TEXT | | SEO meta description |
| `is_published` | BOOLEAN | DEFAULT FALSE | Publication status |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation |

**Indexes**:
- `idx_articles_region` on (region)
- `idx_articles_theme` on (content_theme)
- `idx_articles_published` on (published_at DESC)
- `idx_articles_is_published` on (is_published)
- `idx_articles_slug` on (slug)
- `idx_articles_tags` on (tags) using GIN

---

### 6. opportunities (机会表)

Business opportunities for cross-border sellers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Opportunity ID |
| `region` | VARCHAR(50) | NOT NULL | Target region |
| `country` | VARCHAR(50) | | Target country |
| `product_category` | VARCHAR(50) | | Product category |
| `opportunity_type` | VARCHAR(50) | | product, market, platform, niche |
| `title` | TEXT | | Opportunity title |
| `description` | TEXT | | Detailed description |
| `opportunity_score` | DECIMAL(3,2) | | AI-calculated score (0.00-1.00) |
| `estimated_market_size` | BIGINT | | Market size in CNY |
| `competition_level` | VARCHAR(20) | | low, medium, high, saturated |
| `growth_potential` | VARCHAR(20) | | low, moderate, high, explosive |
| `entry_difficulty` | INTEGER | | Difficulty 1-10 |
| `data_sources` | JSONB | | Source references |
| `valid_until` | TIMESTAMPTZ | | Opportunity expiry |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation |

**Indexes**:
- `idx_opportunities_region` on (region)
- `idx_opportunities_type` on (opportunity_type)
- `idx_opportunities_score` on (opportunity_score DESC)
- `idx_opportunities_valid` on (valid_until)

---

### 7. risk_alerts (风险预警表)

Risk warnings for cross-border sellers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Alert ID |
| `alert_type` | VARCHAR(50) | | policy, tariff, platform, logistics, payment |
| `severity` | VARCHAR(20) | | info, warning, critical |
| `title` | TEXT | | Alert title |
| `description` | TEXT | | Detailed description |
| `affected_regions` | TEXT[] | | Affected regions (array) |
| `affected_platforms` | TEXT[] | | Affected platforms (array) |
| `affected_categories` | TEXT[] | | Affected categories (array) |
| `mitigation_actions` | JSONB | | Recommended actions |
| `source_url` | TEXT | | Information source |
| `is_active` | BOOLEAN | DEFAULT TRUE | Active status |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Alert creation |
| `resolved_at` | TIMESTAMPTZ | | Resolution timestamp |

**Indexes**:
- `idx_risk_alerts_active` on (is_active)
- `idx_risk_alerts_severity` on (severity)
- `idx_risk_alerts_regions` on (affected_regions) using GIN

---

### 8. cost_references (成本参考表)

Platform and operational cost references.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Cost reference ID |
| `region` | VARCHAR(50) | NOT NULL | Region |
| `country` | VARCHAR(50) | | Country |
| `platform` | VARCHAR(50) | | Platform name |
| `cost_type` | VARCHAR(50) | | platform_fee, shipping, storage, advertising, payment, tax, other |
| `cost_item` | TEXT | | Cost item name |
| `amount` | DECIMAL(10,2) | | Cost amount |
| `currency` | VARCHAR(10) | | Currency code |
| `frequency` | VARCHAR(20) | | one_time, monthly, quarterly, annual, per_transaction, per_order |
| `effective_date` | TIMESTAMPTZ | | Effective from |
| `valid_until` | TIMESTAMPTZ | | Valid until |

**Indexes**:
- `idx_cost_references_region` on (region)
- `idx_cost_references_type` on (cost_type)
- `idx_cost_references_effective` on (effective_date)

---

## Indexes Summary

**Total Indexes**: 41

| Table | Index Count |
|-------|-------------|
| users | 4 |
| subscriptions | 3 |
| payments | 4 |
| user_usage | 2 |
| articles | 6 |
| opportunities | 4 |
| risk_alerts | 3 |
| cost_references | 3 |

---

## Triggers

### `update_users_updated_at`
Automatically updates the `updated_at` column on `users` table when a row is updated.

```sql
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

---

## Enums and Constraints

### Plan Tier (users.subscriptions)
- `free`
- `pro`
- `enterprise`

### Plan Status (users.subscriptions)
- `active`
- `canceled`
- `expired`
- `suspended`

### Payment Method (payments)
- `wechat`
- `alipay`
- `stripe`
- `paypal`

### Payment Status (payments)
- `pending`
- `processing`
- `completed`
- `failed`
- `refunded`

### Usage Type (user_usage)
- `api_call`
- `article_view`
- `opportunity_access`
- `report_download`
- `search_query`

### Content Theme (articles)
- `market_insight`
- `policy_update`
- `case_study`
- `tutorial`
- `news`

### Risk Level (articles)
- `low`
- `medium`
- `high`
- `critical`

---

## Common Queries

### Get Active Users Count
```sql
SELECT COUNT(*) FROM users WHERE plan_status = 'active';
```

### Get User with Latest Subscription
```sql
SELECT u.*, s.plan_tier, s.expires_at
FROM users u
LEFT JOIN LATERAL (
  SELECT * FROM subscriptions
  WHERE user_id = u.id
  ORDER BY created_at DESC
  LIMIT 1
) s ON true
WHERE u.email = 'user@example.com';
```

### Get User Usage for Current Month
```sql
SELECT usage_type, SUM(quantity) as total
FROM user_usage
WHERE user_id = 'user-uuid'
  AND period_date >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY usage_type;
```

### Get Published Articles by Region
```sql
SELECT * FROM articles
WHERE is_published = true
  AND region = 'Southeast Asia'
ORDER BY published_at DESC
LIMIT 20;
```

### Get Active Risk Alerts
```sql
SELECT * FROM risk_alerts
WHERE is_active = true
  AND severity IN ('warning', 'critical')
ORDER BY
  CASE severity
    WHEN 'critical' THEN 1
    WHEN 'warning' THEN 2
    ELSE 3
  END,
  created_at DESC;
```

### Get Opportunities by Score
```sql
SELECT * FROM opportunities
WHERE valid_until > NOW()
ORDER BY opportunity_score DESC
LIMIT 10;
```

---

## Maintenance

### Backup Database
```bash
# From server
docker exec postgres pg_dump -U postgres crawler_db > backup.sql

# From local with SSH
ssh root@139.224.42.111 "docker exec postgres pg_dump -U postgres crawler_db" > backup.sql
```

### Restore Database
```bash
# From server
docker exec -i postgres psql -U postgres crawler_db < backup.sql
```

### Analyze Tables (update statistics)
```sql
ANALYZE users;
ANALYZE subscriptions;
ANALYZE payments;
ANALYZE user_usage;
ANALYZE articles;
ANALYZE opportunities;
ANALYZE risk_alerts;
ANALYZE cost_references;
```

### Vacuum (reclaim storage)
```sql
VACUUM ANALYZE;
```

---

## Notes

1. **Redis Password**: The Redis password in infrastructure documentation (`FWD4D75OKyQS7HOluA6J`) doesn't match the actual password. SSH access to server is currently blocked, preventing password verification. Update the `REDIS_URL` in `.env` when access is restored.

2. **UUID Generation**: Uses PostgreSQL's `gen_random_uuid()` from the `pgcrypto` extension for all primary keys.

3. **Time Zones**: All timestamps use `TIMESTAMPTZ` (timezone-aware) and are stored in UTC.

4. **JSONB Fields**: Several tables use `JSONB` for flexible metadata storage (payments.metadata, opportunities.data_sources, risk_alerts.mitigation_actions).

---

*This documentation is automatically generated. Update it when schema changes occur.*

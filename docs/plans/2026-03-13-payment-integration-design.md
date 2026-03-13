# Payment Integration Design Document
**CB-Business (ZenConsult) SaaS Platform**

**Document Version**: 1.0
**Date**: 2026-03-13
**Author**: Claude Code
**Status**: Design Proposal

---

## Executive Summary

This document outlines a comprehensive payment integration strategy for CB-Business, a SaaS platform targeting Chinese entrepreneurs. The recommended approach uses **Stripe as the primary payment gateway** with plans to migrate to WeChat Pay/Alipay once the business obtains proper licensing.

**Key Recommendation**: Start with Stripe (via Hong Kong/Singapore entity) for immediate revenue generation, then transition to native Chinese payment methods as the business matures.

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Payment Gateway Research](#payment-gateway-research)
3. [Recommended Solution](#recommended-solution)
4. [Architecture Design](#architecture-design)
5. [API Specifications](#api-specifications)
6. [Implementation Plan](#implementation-plan)
7. [Risk Mitigation](#risk-mitigation)
8. [Migration Strategy](#migration-strategy)

---

## 1. Current State Analysis

### 1.1 Existing Infrastructure

**Backend Architecture**:
- **Framework**: FastAPI running on Docker (HK server)
- **Database**: PostgreSQL with async SQLAlchemy
- **Cache**: Redis for session management and rate limiting
- **Current Payment Implementation**: WeChat Pay stub (not production-ready)

**Existing Payment Models** (`/Users/kjonekong/Documents/cb-Business/backend/models/subscription.py`):
```python
- Subscription model (plan tiers, billing cycles, auto-renew)
- Payment model (transaction tracking, status management)
- UserUsage model (usage tracking for quota management)
```

**Current Pricing Plans** (`/Users/kjonekong/Documents/cb-Business/backend/config/subscriptions.py`):
- **Free**: ¥0/month (5 API calls/day, limited features)
- **Pro**: ¥99/month or ¥990/year (unlimited API calls, full features)
- **Enterprise**: Custom pricing (dedicated support, API access)

### 1.2 Technical Gaps

1. **No Production Payment Gateway**: Current WeChat Pay implementation is a mock
2. **No Webhook Infrastructure**: Missing secure webhook handling
3. **No Subscription Management**: No automated billing cycles or renewal logic
4. **No Payment Method UI**: Frontend lacks payment flow components

---

## 2. Payment Gateway Research

### 2.1 WeChat Pay (微信支付)

**Requirements**:
- ✅ Chinese business license (营业执照) OR
- ✅ Cross-border business license (跨境营业执照)
- ✅ ICP license for websites hosted in China
- ✅ Merchant qualification review

**Pros**:
- 900M+ monthly active users in China
- Native mobile payment experience
- Highest conversion rate for Chinese users
- ~0.6% transaction fee

**Cons**:
- ❌ Requires business license (project doesn't have yet)
- ❌ Complex approval process (2-4 weeks)
- ❌ Strict compliance requirements
- ❌ Daily settlement limits for new merchants

**Verdict**: **Phase 2** - Implement after obtaining business license

---

### 2.2 Alipay (支付宝)

**Requirements**:
- ✅ Chinese business license OR
- ✅ Cross-border merchant registration (Alipay Cross-border)
- ✅ Business registration documents
- ✅ Bank account information

**Pros**:
- 1.3B+ users worldwide
- Cross-border solution available WITHOUT Chinese business license
- Supports international card settlements
- ~1-2% transaction fee for cross-border

**Cons**:
- ⚠️ Cross-border fees higher than domestic
- ⚠️ Currency conversion fees apply
- ⚠️ Longer settlement cycles (3-5 days)

**Verdict**: **Phase 2** - Implement alongside WeChat Pay

---

### 2.3 Stripe

**Requirements**:
- ✅ Business entity in Stripe-supported country (46 countries)
- ✅ Bank account in supported country
- ✅ Basic business information

**Availability in China**:
- ❌ Stripe is NOT available for mainland China businesses
- ✅ Available in Hong Kong, Singapore, and most other countries

**Stripe + WeChat Pay Integration**:
- ✅ Stripe offers WeChat Pay as a payment method
- ✅ merchants in supported countries can accept WeChat Pay
- ✅ No need for separate WeChat Pay merchant account
- ✅ Unified dashboard and reporting

**Pros**:
- ✅ Fast setup (1-2 days)
- ✅ Excellent developer experience and documentation
- ✅ Built-in subscription management
- ✅ Supports 135+ payment methods including WeChat Pay
- ✅ Advanced fraud protection (Radar)
- ✅ Automated billing and invoicing

**Cons**:
- ⚠️ Requires Hong Kong/Singapore business entity (or use payment facilitator)
- ⚠️ Higher transaction fees (2.9% + $0.30 for international cards)
- ⚠️ Currency conversion fees apply
- ⚠️ WeChat Pay via Stripe has limited functionality vs native integration

**Verdict**: **Phase 1 (Recommended)** - Start with Stripe via HK entity

---

### 2.4 Airwallex

**Requirements**:
- ✅ Business registration (any jurisdiction)
- ✅ KYC verification

**Pros**:
- ✅ Specializes in cross-border payments
- ✅ Supports Alipay and WeChat Pay
- ✅ Competitive FX rates (near interbank)
- ✅ Multi-currency accounts
- ✅ Lower fees (~0.5% + £0.20 per transaction)

**Cons**:
- ⚠️ Less mature than Stripe
- ⚠️ Smaller developer community
- ⚠️ Fewer integrations

**Verdict**: **Alternative** - Consider if FX optimization is critical

---

## 3. Recommended Solution

### 3.1 Phase 1: MVP Launch (Months 1-3)

**Primary Gateway**: Stripe (Hong Kong entity)

**Rationale**:
1. **Fastest Path to Revenue**: Setup in 1-2 days vs 4-8 weeks for WeChat Pay
2. **Lowest Barrier**: No Chinese business license required
3. **Comprehensive Features**: Built-in subscription management, invoicing, dunning
4. **WeChat Pay Support**: Can accept WeChat Pay through Stripe
5. **Proven Reliability**: Used by thousands of SaaS companies

**Entity Structure Options**:
- **Option A**: Register Hong Kong Limited Company (HK$10K-20K, 2-3 weeks)
- **Option B**: Use existing Hong Kong entity if available
- **Option C**: Partner with payment facilitator (higher fees, faster setup)

**Supported Payment Methods**:
- International credit/debit cards (Visa, Mastercard, Amex)
- WeChat Pay (via Stripe)
- Alipay (via Stripe - coming 2026)
- China UnionPay (via Stripe)

**Pricing**:
- Card payments: 3.4% + HK$2.30 per transaction
- WeChat Pay: ~2.5% per transaction
- Currency conversion: 1-2% (if charging in CNY)

---

### 3.2 Phase 2: Local Payment Methods (Months 4-6)

**Add Native WeChat Pay + Alipay**

**Trigger**: When monthly recurring revenue (MRR) reaches $5,000+

**Approach**:
1. Register Chinese business entity (or use parent company)
2. Apply for WeChat Pay merchant account
3. Apply for Alipay cross-border merchant account
4. Implement direct integrations
5. Migrate existing Chinese customers to native methods

**Benefits**:
- Lower transaction fees (0.6-1.2% vs 2.5-3.4%)
- Better user experience for Chinese customers
- Faster settlement (T+1 vs T+2-3)
- Higher conversion rates

---

### 3.3 Phase 3: Optimization (Months 7-12)

**Payment Method Routing**

Implement intelligent routing to optimize costs and conversion:

```
┌─────────────────────────────────────────────────────────────┐
│                    Payment Router                           │
├─────────────────────────────────────────────────────────────┤
│  User Detection → IP, Browser Language, Phone Number       │
│  Decision Logic → Cost vs Conversion Optimization           │
│  Fallback Chain → Preferred Method → Backup → Stripe        │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   Chinese Users      International Users     Enterprise
        │                   │                   │
   WeChat Pay            Stripe Cards       Bank Transfer
   Alipay               Apple Pay           Custom Invoicing
```

---

## 4. Architecture Design

### 4.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Frontend (Next.js)                           │
│                        www.zenconsult.top (Vercel)                      │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐              │
│  │  Pricing Page │  │  Checkout UI  │  │ Billing Portal│              │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘              │
│          │                  │                  │                       │
│          └──────────────────┴──────────────────┘                       │
│                              │                                         │
└──────────────────────────────┼─────────────────────────────────────────┘
                               │ HTTPS (Stripe.js + Custom API)
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Backend API (FastAPI)                              │
│                   api.zenconsult.top (HK Docker)                        │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Payment Service Layer                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │   │
│  │  │ Stripe Svc  │  │ Alipay Svc  │  │ WeChat Pay Svc          │ │   │
│  │  │ (Phase 1)   │  │ (Phase 2)   │  │ (Phase 2)               │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Subscription Manager                         │   │
│  │  - Plan activation/deactivation                                 │   │
│  │  - Usage quota enforcement                                      │   │
│  │  - Billing cycle management                                     │   │
│  │  - Dunning and retry logic                                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Webhook Handler                              │   │
│  │  - Signature verification                                       │   │
│  │  - Idempotency checks (Redis)                                   │   │
│  │  - Async event processing                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│    Stripe     │    │   Alipay      │    │ WeChat Pay    │
│    API        │    │   API         │    │   API         │
└───────────────┘    └───────────────┘    └───────────────┘
        │                      │                      │
        └──────────────────────┴──────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Payment Gateway    │
                    │  Settlement Bank    │
                    └─────────────────────┘
```

### 4.2 Data Flow: Payment Creation

```
User                 Frontend              Backend              Stripe
 │                      │                    │                    │
 ├──Select Plan────────▶│                    │                    │
 │                      │                    │                    │
 │◀──Show Pricing───────┤                    │                    │
 │                      │                    │                    │
 ├──Click Subscribe────▶│                    │                    │
 │                      │                    │                    │
 │                      ├──POST /api/v1/payments/create──────────▶│
 │                      │                    │                    │
 │                      │                    │  Create Intent     │
 │                      │                    │  (Amount, Plan)    │
 │                      │                    │                    │
 │                      │◀──clientSecret─────┤◀───────────────────┤
 │                      │                    │                    │
 │                      │                    │                    │
 │                      │──Stripe.js Confirm▶│                    │
 │                      │  (3D Secure)       │                    │
 │                      │                    │                    │
 │◀──Payment Success───┤                    │                    │
 │                      │                    │                    │
 │                      ├──GET /api/v1/subscriptions/me───────────▶│
 │                      │                    │                    │
 │◀──Show Dashboard────┤◀───────────────────┤◀───────────────────┤
```

### 4.3 Data Flow: Webhook Processing

```
Stripe                Backend               Database              Redis
  │                      │                     │                     │
  │──Webhook Event──────▶│                     │                     │
  │  (payment.succeeded) │                     │                     │
  │                      │                     │                     │
  │                      ├──Verify Signature──▶│                     │
  │                      │  (Stripe Sig)       │                     │
  │                      │                     │                     │
  │                      ├──Check Idempotency──────────────────────▶│
  │                      │  (event_id)         │                     │
  │                      │                     │                     │
  │                      │◀────Not Exists──────┤                     │
  │                      │                     │                     │
  │                      ├──Process Payment──▶│                     │
  │                      │  - Update status    │                     │
  │                      │  - Create/Update    │                     │
  │                      │    subscription      │                     │
  │                      │                     │                     │
  │                      ├──Mark Processed──────────────────────────▶│
  │                      │  (event_id)         │                     │
  │                      │                     │                     │
  │◀─200 OK──────────────┤                     │                     │
```

### 4.4 Database Schema Updates

**New Tables**:

```sql
-- Stripe-specific data (optional, can use Stripe dashboard)
CREATE TABLE stripe_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE stripe_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_price_id VARCHAR(255) NOT NULL,
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payment_intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID REFERENCES payments(id) ON DELETE CASCADE,
    stripe_intent_id VARCHAR(255) UNIQUE NOT NULL,
    client_secret VARCHAR(500),
    amount INTEGER NOT NULL,  -- in cents/fen
    currency VARCHAR(3) DEFAULT 'cny',
    status VARCHAR(50),
    payment_method_type VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Webhook event log for idempotency
CREATE TABLE webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processing_attempts INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. API Specifications

### 5.1 New Endpoints

#### 5.1.1 Create Payment Intent

```http
POST /api/v1/payments/create-intent
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
  "plan_tier": "pro",
  "billing_cycle": "monthly",
  "payment_method": "stripe",  // future: "wechat", "alipay"
  "success_url": "https://www.zenconsult.top/billing?success=true",
  "cancel_url": "https://www.zenconsult.top/billing?canceled=true"
}

Response (200):
{
  "client_secret": "pi_1234567890_secret_xxxxx",
  "intent_id": "pi_1234567890",
  "amount": 9900,  // in cents/fen
  "currency": "cny",
  "publishable_key": "pk_live_xxxxx"
}

Response (400):
{
  "detail": "Active subscription already exists",
  "code": "ACTIVE_SUBSCRIPTION_EXISTS"
}
```

#### 5.1.2 Get Payment Methods

```http
GET /api/v1/payments/methods
Authorization: Bearer <token>

Response (200):
{
  "methods": [
    {
      "id": "pm_123456",
      "type": "card",
      "card": {
        "brand": "visa",
        "last4": "4242",
        "exp_month": 12,
        "exp_year": 2026
      },
      "is_default": true
    }
  ]
}
```

#### 5.1.3 Webhook Endpoint

```http
POST /api/v1/payments/webhooks/stripe
Content-Type: application/json
Stripe-Signature: t=123456,v1=abcdef...

Headers:
- Stripe-Signature: Required for verification

Request Body:
{
  "id": "evt_123456",
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_123456",
      "amount": 9900,
      "currency": "cny",
      "metadata": {
        "user_id": "uuid",
        "plan_tier": "pro",
        "billing_cycle": "monthly"
      }
    }
  }
}

Response (200):
{
  "received": true
}

Response (400):
{
  "error": "Invalid signature"
}
```

#### 5.1.4 Update Payment Method

```http
PUT /api/v1/payments/methods/default
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
  "payment_method_id": "pm_123456"
}

Response (200):
{
  "success": true,
  "message": "Default payment method updated"
}
```

#### 5.1.5 Get Invoices

```http
GET /api/v1/payments/invoices?limit=10
Authorization: Bearer <token>

Response (200):
{
  "invoices": [
    {
      "id": "in_123456",
      "amount_due": 9900,
      "currency": "cny",
      "status": "paid",
      "created": 1678892800,
      "hosted_invoice_url": "https://pay.stripe.com/invoice/..."
    }
  ],
  "total": 25
}
```

### 5.2 Updated Endpoints

#### 5.2.1 Get Subscription (Enhanced)

```http
GET /api/v1/subscriptions/me
Authorization: Bearer <token>

Response (200):
{
  "id": "uuid",
  "plan_tier": "pro",
  "status": "active",
  "billing_cycle": "monthly",
  "amount": 99.00,
  "currency": "CNY",
  "current_period_start": "2026-03-01T00:00:00Z",
  "current_period_end": "2026-04-01T00:00:00Z",
  "cancel_at_period_end": false,
  "payment_method": {
    "type": "card",
    "card": {
      "brand": "visa",
      "last4": "4242"
    }
  },
  "usage": {
    "api_calls_today": 45,
    "api_calls_limit": -1
  }
}
```

---

## 6. Implementation Plan

### 6.1 Phase 1: Stripe Integration (Weeks 1-4)

**Week 1: Setup & Configuration**
- [ ] Register Hong Kong business entity (if needed)
- [ ] Create Stripe account
- [ ] Complete KYC verification
- [ ] Configure webhook endpoints
- [ ] Set up API keys in environment variables
- [ ] Update `.env.prod` with Stripe keys

**Estimated Time**: 5-10 hours

**Week 2: Backend Implementation**
- [ ] Install Stripe Python SDK: `pip install stripe`
- [ ] Create payment service module: `services/stripe_service.py`
- [ ] Implement payment intent creation
- [ ] Implement webhook handler with signature verification
- [ ] Add webhook idempotency checks (Redis)
- [ ] Update database schema (add stripe-specific tables)
- [ ] Implement subscription activation logic
- [ ] Add unit tests for payment flows

**Files to Create/Modify**:
- `/Users/kjonekong/Documents/cb-Business/backend/services/stripe_service.py`
- `/Users/kjonekong/Documents/cb-Business/backend/api/payments.py` (update)
- `/Users/kjonekong/Documents/cb-Business/backend/models/subscription.py` (add tables)
- `/Users/kjonekong/Documents/cb-Business/backend/tests/test_stripe_payments.py`

**Estimated Time**: 20-30 hours

**Week 3: Frontend Implementation**
- [ ] Install Stripe.js: `npm install @stripe/stripe-js`
- [ ] Create pricing page component
- [ ] Create checkout modal/component
- [ ] Implement Stripe Elements integration
- [ ] Add payment success/error handling
- [ ] Create billing portal page
- [ ] Add subscription management UI
- [ ] Implement usage metering display

**Files to Create/Modify**:
- `/Users/kjonekong/Documents/cb-Business/frontend/components/pricing/pricing-table.tsx`
- `/Users/kjonekong/Documents/cb-Business/frontend/components/payment/checkout-modal.tsx`
- `/Users/kjonekong/Documents/cb-Business/frontend/components/billing/portal.tsx`
- `/Users/kjonekong/Documents/cb-Business/frontend/lib/stripe.ts`
- `/Users/kjonekong/Documents/cb-Business/frontend/app/billing/page.tsx`

**Estimated Time**: 15-20 hours

**Week 4: Testing & Deployment**
- [ ] Set up Stripe test mode
- [ ] Test payment flows with test cards
- [ ] Test webhook processing locally (ngrok)
- [ ] Test subscription activation
- [ ] Test payment failures and retries
- [ ] Test 3D Secure authentication
- [ ] Deploy to staging
- [ ] Conduct end-to-end testing
- [ ] Deploy to production
- [ ] Monitor first live transactions

**Estimated Time**: 10-15 hours

**Total Phase 1 Effort**: 50-75 hours (6-10 business days)

---

### 6.2 Phase 2: WeChat Pay & Alipay (Weeks 5-12)

**Prerequisites**:
- Business license obtained
- MRR > $5,000 (to justify investment)

**Week 5-6: Business Registration**
- [ ] Register Chinese business entity
- [ ] Obtain business license
- [ ] Open Chinese bank account
- [ ] Register for ICP license (if needed)

**Estimated Time**: 40-60 hours (mostly waiting for approvals)

**Week 7-8: Payment Provider Registration**
- [ ] Apply for WeChat Pay merchant account
- [ ] Apply for Alipay cross-border account
- [ ] Complete KYC for both providers
- [ ] Configure API credentials

**Estimated Time**: 10-20 hours

**Week 9-10: Backend Implementation**
- [ ] Complete WeChat Pay service implementation
- [ ] Implement Alipay service
- [ ] Add QR code generation
- [ ] Implement payment status polling
- [ ] Add webhook handlers for both providers
- [ ] Implement payment method router
- [ ] Add unit and integration tests

**Estimated Time**: 30-40 hours

**Week 11-12: Frontend & Testing**
- [ ] Add WeChat Pay QR code display
- [ ] Add Alipay payment button
- [ ] Implement payment method selection
- [ ] Test all payment flows
- [ ] Deploy to production
- [ ] Monitor conversion rates

**Estimated Time**: 20-30 hours

**Total Phase 2 Effort**: 100-150 hours (12-19 business days)

---

### 6.3 Phase 3: Optimization (Weeks 13-16)

**Week 13-14: Smart Routing**
- [ ] Implement payment method router
- [ ] Add user preference detection
- [ ] Implement cost optimization logic
- [ ] Add A/B testing framework

**Estimated Time**: 20-30 hours

**Week 15-16: Advanced Features**
- [ ] Implement Stripe Billing for complex pricing
- [ ] Add Stripe Radar for fraud prevention
- [ ] Implement automated dunning
- [ ] Add advanced analytics and reporting

**Estimated Time**: 15-25 hours

**Total Phase 3 Effort**: 35-55 hours (4-7 business days)

---

## 7. Risk Mitigation

### 7.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| Webhook delivery failures | High | Medium | Implement idempotency, retry logic, and monitoring |
| Payment method downtime | High | Low | Multi-provider strategy from Phase 2 |
| Data consistency issues | High | Medium | Use database transactions, implement reconciliation jobs |
| API rate limits | Medium | Medium | Implement caching, queue for bulk operations |
| Security breaches | Critical | Low | PCI compliance, encryption, regular audits |

### 7.2 Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| Low conversion with Stripe | High | Medium | Phase 2 native payment methods |
| Higher transaction costs | Medium | High | Phase 3 smart routing, negotiate volume discounts |
| Currency conversion losses | Medium | Medium | Price in local currencies, use multi-currency accounts |
| Regulatory changes | High | Low | Stay compliant, work with legal advisors |
| Business license delays | Medium | High | Start with Stripe, parallel license application |

### 7.3 Security Considerations

**PCI DSS Compliance**:
- ✅ Use Stripe.js for card data collection (SAQ A compliance)
- ✅ Never store raw card data
- ✅ Use HTTPS for all payment endpoints
- ✅ Implement webhook signature verification
- ✅ Regular security audits

**Data Protection**:
- ✅ Encrypt sensitive data at rest
- ✅ Use secure environment variable management
- ✅ Implement proper access controls
- ✅ Log all payment operations for audit trail
- ✅ Comply with GDPR and Chinese data protection laws

---

## 8. Migration Strategy

### 8.1 From Stripe to Native WeChat Pay/Alipay

**Approach**: Gradual migration with user consent

**Steps**:

1. **Phase 2a: Dual Operation**
   - Keep Stripe as default for international users
   - Offer WeChat Pay/Alipay as options for Chinese users
   - Allow users to choose preferred method

2. **Phase 2b: Smart Routing**
   - Automatically route Chinese users to native methods
   - Keep Stripe as fallback
   - Track conversion rates

3. **Phase 2c: Full Migration**
   - Migrate existing Chinese users to native methods
   - Send notification emails with migration incentives
   - Maintain Stripe for international users

**Migration Timeline**: 3-6 months

### 8.2 Data Migration Plan

**No data migration required** - all customer and subscription data stays in PostgreSQL. Only the payment method changes.

**Migration Process**:
1. User clicks "Switch to WeChat Pay"
2. System creates new subscription via WeChat Pay
3. System cancels Stripe subscription at period end
4. User has uninterrupted service

---

## 9. Cost Analysis

### 9.1 Phase 1 Costs (Stripe)

**Setup Costs**:
- Hong Kong company registration: HK$10,000-20,000 (one-time)
- Bank account opening: HK$500-1,000
- Legal fees: HK$5,000-10,000

**Transaction Fees** (per transaction):
- International cards: 3.4% + HK$2.30
- WeChat Pay via Stripe: ~2.5%
- Currency conversion: 1-2% (if applicable)

**Monthly Costs** (estimated for 100 customers at ¥99/month):
- Transaction fees: ¥9,900 × 3.4% = ¥336/month
- Stripe subscription: Free
- Total: ~¥336/month (3.4% of revenue)

### 9.2 Phase 2 Costs (Native Methods)

**Setup Costs**:
- Chinese company license: ¥0 (if using existing entity)
- ICP license: ¥1,000-3,000
- Merchant application: Free

**Transaction Fees** (per transaction):
- WeChat Pay: 0.6%
- Alipay: 0.6-1.2%
- Total: 0.6-1.2%

**Monthly Costs** (same 100 customers):
- Transaction fees: ¥9,900 × 0.6% = ¥59/month
- Total: ~¥59/month (0.6% of revenue)

**Savings**: ¥277/month or ¥3,324/year

**Break-even Point**: Phase 2 pays for itself in ~2-3 months

---

## 10. Success Metrics

### 10.1 Key Performance Indicators (KPIs)

**Phase 1 (Months 1-3)**:
- [ ] Payment success rate > 95%
- [ ] Checkout completion rate > 70%
- [ ] Time to first payment < 5 minutes
- [ ] Webhook processing time < 1 second
- [ ] Payment-related support tickets < 5%

**Phase 2 (Months 4-6)**:
- [ ] Chinese user payment conversion > 85%
- [ ] Transaction cost reduction > 60%
- [ ] Payment method preference: WeChat Pay > 70%
- [ ] Average revenue per user (ARPU) increase > 20%

**Phase 3 (Months 7-12)**:
- [ ] Payment routing efficiency > 95%
- [ ] Churn rate < 5% monthly
- [ ] Expansion revenue (upsells) > 15% of new revenue
- [ ] Payment method coverage for target markets = 100%

---

## 11. Next Steps

### 11.1 Immediate Actions (This Week)

1. **Stakeholder Approval**
   - [ ] Review and approve this design document
   - [ ] Confirm budget for Phase 1 implementation
   - [ ] Assign development team members

2. **Entity Setup**
   - [ ] Determine if Hong Kong entity is needed
   - [ ] Begin company registration process (if needed)
   - [ ] Open business bank account

3. **Developer Setup**
   - [ ] Create Stripe account (test mode)
   - [ ] Get API keys
   - [ ] Set up local development environment
   - [ ] Clone Stripe sample code

### 11.2 Phase 1 Kickoff (Week 1)

1. **Project Planning**
   - [ ] Create detailed task list in project management tool
   - [ ] Assign tasks to developers
   - [ ] Set up milestones and deadlines

2. **Environment Setup**
   - [ ] Configure Stripe in staging environment
   - [ ] Set up webhook endpoint (ngrok for local)
   - [ ] Prepare test cards and test scenarios

3. **Development Sprint**
   - [ ] Start backend implementation
   - [ ] Set up continuous integration

---

## 12. Appendix

### 12.1 Stripe Resources

- **Documentation**: https://stripe.com/docs
- **Python SDK**: https://stripe.com/docs/libraries#python
- **Webhooks**: https://stripe.com/docs/webhooks
- **Subscriptions**: https://stripe.com/docs/billing/subscriptions/overview
- **WeChat Pay via Stripe**: https://stripe.com/zh-sg/payment-method/wechat-pay

### 12.2 WeChat Pay Resources

- **Official Documentation**: https://pay.weixin.qq.com/wiki/doc/api/index.html
- **Cross-border Payments**: https://pay.weixin.qq.com/static/applyment_guide/applyment_detail_crossborder.shtml
- **SDK Repository**: https://pay.weixin.qq.com/wiki/doc/api/download/WxPayAPI_JAVA_v3.zip

### 12.3 Alipay Resources

- **Global Documentation**: https://global.alipay.com/docs
- **Cross-border Integration**: https://global.alipay.com/docs/ac/overview
- **Developer Portal**: https://open.alipay.com/

### 12.4 Test Cards (Stripe Test Mode)

```
Success: 4242 4242 4242 4242
Require 3D Secure: 4000 0025 0000 3155
Decline: 4000 0000 0000 0002
Insufficient Funds: 4000 0000 0000 9995
Expired Card: 4000 0000 0000 0069
```

### 12.5 Environment Variables

Add to `/Users/kjonekong/Documents/cb-Business/backend/.env.prod`:

```bash
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
STRIPE_PRICE_ID_PRO_MONTHLY=price_xxxxx
STRIPE_PRICE_ID_PRO_YEARLY=price_xxxxx
STRIPE_PRICE_ID_ENTERPRISE=price_xxxxx

# WeChat Pay Configuration (Phase 2)
WECHAT_PAY_APP_ID=wxcbxxxxx
WECHAT_PAY_MCH_ID=1xxxxx
WECHAT_PAY_API_KEY=xxxxx
WECHAT_PAY_CERT_PATH=/path/to/cert.pem
WECHAT_PAY_NOTIFY_URL=https://api.zenconsult.top/api/v1/payments/webhooks/wechat

# Alipay Configuration (Phase 2)
ALIPAY_APP_ID=2021xxxxx
ALIPAY_PRIVATE_KEY=xxxxx
ALIPAY_PUBLIC_KEY=xxxxx
ALIPAY_NOTIFY_URL=https://api.zenconsult.top/api/v1/payments/webhooks/alipay
```

---

## 13. Conclusion

This payment integration design provides a **pragmatic, phased approach** to monetizing the CB-Business SaaS platform:

1. **Phase 1 (Recommended)**: Launch with Stripe in 1 month for immediate revenue
2. **Phase 2**: Add native WeChat Pay/Alipay once business license is obtained
3. **Phase 3**: Optimize with intelligent payment routing

The recommended approach balances **speed to market** with **long-term cost efficiency**, allowing the platform to start generating revenue quickly while preparing for scale with native Chinese payment methods.

**Estimated Timeline to First Payment**: 4-6 weeks
**Estimated Development Effort**: 50-75 hours (Phase 1)
**Estimated Setup Costs**: HK$15,000-30,000 (one-time)
**Expected ROI**: Positive within 2-3 months

---

**Document End**

For questions or clarifications, please refer to:
- Stripe Integration Guide: https://stripe.com/docs
- WeChat Pay Documentation: https://pay.weixin.qq.com/wiki/doc/api/index.html
- Alipay Global: https://global.alipay.com/docs

---

**Sources**:
- [Stripe Global Availability](https://stripe.com/global)
- [Stripe WeChat Pay Integration](https://stripe.com/zh-sg/payment-method/wechat-pay)
- [Integrating Alipay and WeChat Pay Guide](https://sesamedisk.com/integrating-alipay-wechat-pay-guide/)
- [Airwallex Chinese Payment Gateways](https://www.airwallex.com/uk/blog/best-chinese-payment-gateways-for-uk-businesses)
- [Airwallex 2026 Cross-Border Collection Trends](https://www.airwallex.com/cn/blog/2026-cross-border-collection-trends)
- [Alipay Global Documentation](https://global-pre.alipay.com/help/integration/49)

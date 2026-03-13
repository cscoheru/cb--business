# Airwallex Payment Gateway Setup

## Overview

Airwallex is implemented as the primary payment gateway for cross-border payments. It supports:
- Credit/Debit card payments (international)
- Alipay cross-border
- WeChat Pay cross-border
- Multiple currencies with CNY as primary

## Environment Variables

Add the following to your `.env` file:

```bash
# Airwallex API Configuration
AIRWALLEX_API_KEY=your_api_key_here
AIRWALLEX_API_URL=https://api-airwallex.com

# Airwallex Webhook Configuration
AIRWALLEX_WEBHOOK_SECRET=your_webhook_secret_here
AIRWALLEX_WEBHOOK_URL=https://api.zenconsult.top/api/v1/payments/webhooks/airwallex
```

## Getting Airwallex Credentials

### 1. Create Airwallex Account

1. Sign up at https://www.airwallex.com
2. Complete business verification (Chinese domestic entity supported)
3. Enable API access in dashboard

### 2. Generate API Key

1. Go to Settings → API Management
2. Create new API key
3. Copy the key to `AIRWALLEX_API_KEY`

### 3. Configure Webhook

1. Go to Settings → Webhooks
2. Add webhook URL: `https://api.zenconsult.top/api/v1/payments/webhooks/airwallex`
3. Copy webhook signing secret to `AIRWALLEX_WEBHOOK_SECRET`
4. Enable events:
   - `payment_intent.succeeded`
   - `payment_intent.failed`

## Database Migration

Run the migration to create Airwallex tables:

```bash
# Via SSH to HK server
ssh hk-jump
docker exec -it cb-business-api psql -U cbuser -d cbdb -f /app/migrations/003_create_airwallex_tables.sql
```

## Testing

### Test Mode

Airwallex provides test mode for development:
1. Use test API keys (prefixed with `test_`)
2. Use test card numbers from documentation
3. Webhooks can be tested via dashboard

### Test Cards

Use these card numbers for testing (in test mode):
- Successful payment: `4242 4242 4242 4242`
- Requires authentication: `4000 0025 0000 3155`
- Card declined: `4000 0000 0000 0002`

## API Endpoints

### Create Payment

```bash
POST /api/v1/payments/create
{
  "plan_tier": "pro",
  "billing_cycle": "monthly",
  "payment_method": "airwallex"
}
```

Response:
```json
{
  "order_no": "uuid",
  "amount": 99.0,
  "currency": "CNY",
  "payment_method": "airwallex",
  "client_token": "token_for_frontend",
  "payment_intent_id": "airwallex_intent_id",
  "expires_at": "2024-01-01T12:00:00Z"
}
```

### Webhook Endpoint

```bash
POST /api/v1/payments/webhooks/airwallex
Headers:
  x-webhook-signature: hmac_signature
  x-webhook-timestamp: unix_timestamp
```

## Frontend Integration

The frontend can use the `client_token` to embed Airwallex checkout:

```javascript
import { loadAirwallex } from 'airwallex-payment-elements';

const airwallex = loadAirwallex({
  env: 'demo', // or 'prod'
  origin: 'https://www.zenconsult.top'
});

// Use the client_token from API response
airwallex.createElement('card', {
  client_token: response.client_token
}).mount('card-element');
```

## Security Notes

1. **Signature Verification**: Webhook signatures are verified using HMAC-SHA256
2. **Idempotency**: Webhook events are tracked in database to prevent duplicate processing
3. **Redis Cache**: Additional cache layer for replay attack prevention
4. **Amount Validation**: Webhook amounts are validated against original payment amount

## Troubleshooting

### Webhook Signature Fails
- Verify `AIRWALLEX_WEBHOOK_SECRET` matches Airwallex dashboard
- Check timestamp is within tolerance (Airwallex allows 5 minutes)

### Payment Intent Creation Fails
- Verify API key is valid
- Check account has sufficient permissions
- Ensure `CNY` is enabled as a currency

### Webhook Not Received
- Check webhook URL is publicly accessible
- Verify webhook events are enabled in Airwallex dashboard
- Check server logs for errors

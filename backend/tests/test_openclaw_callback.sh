#!/bin/bash
# test_openclaw_callback.sh
# 测试OpenClaw回调端点的完整流程

echo "🧪 测试OpenClaw回调端点"
echo "============================"

# API基础URL
API_BASE="https://api.zenconsult.top"
# API_BASE="http://127.0.0.1:8000"  # 本地测试

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 测试1: 发送成功回调
echo ""
echo "📤 测试1: 发送成功回调"
echo "----------------------------"
TIMESTAMP=$(date +%s)
CALLBACK_DATA=$(cat <<EOF
{
  "channel_id": "rss-crawler",
  "execution_id": "exec-test-$TIMESTAMP",
  "status": "success",
  "started_at": "2026-03-14T10:00:00Z",
  "completed_at": "2026-03-14T10:05:00Z",
  "duration_ms": 300000,
  "result": {
    "total_fetched": 70,
    "total_pushed": 70,
    "sources": 5
  },
  "stats": {
    "sources": 5,
    "successful": 4,
    "failed": 1
  }
}
EOF
)

RESPONSE=$(curl -s -X POST \
  "$API_BASE/api/v1/openclaw/callback/channel" \
  -H "Content-Type: application/json" \
  -d "$CALLBACK_DATA")

echo "响应: $RESPONSE"
if echo "$RESPONSE" | grep -q '"success": true'; then
  echo -e "${GREEN}✅ 测试1通过${NC}"
else
  echo -e "${RED}❌ 测试1失败${NC}"
fi

# 测试2: 发送失败回调
echo ""
echo "📤 测试2: 发送失败回调"
echo "----------------------------"
TIMESTAMP=$(date +%s)
CALLBACK_DATA=$(cat <<EOF
{
  "channel_id": "oxylabs-monitor",
  "execution_id": "exec-test-$TIMESTAMP",
  "status": "failed",
  "started_at": "2026-03-14T11:00:00Z",
  "completed_at": "2026-03-14T11:02:00Z",
  "duration_ms": 120000,
  "error": {
    "message": "Connection timeout",
    "code": "TIMEOUT"
  },
  "stats": {
    "sources": 1,
    "successful": 0,
    "failed": 1
  }
}
EOF
)

RESPONSE=$(curl -s -X POST \
  "$API_BASE/api/v1/openclaw/callback/channel" \
  -H "Content-Type: application/json" \
  -d "$CALLBACK_DATA")

echo "响应: $RESPONSE"
if echo "$RESPONSE" | grep -q '"success": true'; then
  echo -e "${GREEN}✅ 测试2通过${NC}"
else
  echo -e "${RED}❌ 测试2失败${NC}"
fi

# 测试3: 查询回调历史
echo ""
echo "📥 测试3: 查询回调历史"
echo "----------------------------"
RESPONSE=$(curl -s "$API_BASE/api/v1/openclaw/callback/history?limit=5")
echo "响应: $RESPONSE" | head -20

# 测试4: 查询特定Channel的历史
echo ""
echo "📥 测试4: 查询特定Channel历史"
echo "----------------------------"
RESPONSE=$(curl -s "$API_BASE/api/v1/openclaw/callback/history?channel_id=rss-crawler&limit=3")
echo "响应: $RESPONSE" | head -20

echo ""
echo "============================"
echo "✅ 测试完成"
echo ""
echo "💡 提示："
echo "  - 查看数据库: docker exec cb-business-postgres psql -U cbuser -d cbdb -c 'SELECT * FROM crawl_logs ORDER BY completed_at DESC LIMIT 10;'"
echo "  - 查看容器日志: docker logs cb-business-api-fixed --tail 50 | grep callback"

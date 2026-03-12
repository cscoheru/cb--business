#!/bin/bash
# 检查 HK 服务器部署状态

echo "🔍 检查 HK 服务器状态..."
echo "================================"

ssh hk << 'ENDSSH'
echo ""
echo "📊 Docker 容器状态:"
if [ -f /root/cb-business/docker-compose.prod.yml ]; then
    cd /root/cb-business
    docker-compose -f docker-compose.prod.yml ps 2>/dev/null || echo "Docker Compose 服务未运行"
else
    echo "docker-compose.prod.yml 不存在"
fi

echo ""
echo "🌐 端口监听状态:"
ss -tlnp | grep -E '8000|5432|6379|80|443|18789' || echo "未发现相关端口"

echo ""
echo "💾 磁盘空间:"
df -h | grep -E '^/dev/|Filesystem'

echo ""
echo "🧠 内存使用:"
free -h

echo ""
echo "📋 OpenClaw 服务状态:"
systemctl is-active openclaw || echo "OpenClaw 服务未运行"
ENDSSH

echo ""
echo "🌐 API 测试:"
echo "  - HTTP: curl -s http://103.59.103.85:8000/"
echo "  - HTTPS: curl -s https://api.zenconsult.top/"

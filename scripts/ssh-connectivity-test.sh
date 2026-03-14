#!/bin/bash
# SSH Connectivity Test Script for HK Node
# 用于测试和验证SSH连接优化的效果

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

HK_IP="103.59.103.85"
ALIYUN_IP="139.224.42.111"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  HK节点SSH连接性测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 基础网络测试
echo -e "${BLUE}[1/6] 基础网络测试${NC}"
echo -e "  测试目标: ${HK_IP}"
echo ""

# Ping测试
echo -n "  ICMP Ping (30次)... "
PING_RESULT=$(ping -c 30 -i 0.5 -q $HK_IP 2>&1 | tail -2)
PACKET_LOSS=$(echo "$PING_RESULT" | grep "packet loss" | grep -oE "[0-9]+%" || echo "N/A")
AVG_LATENCY=$(echo "$PING_RESULT" | grep "round-trip" | awk -F'/' '{print $5}' || echo "N/A")
echo -e "${GREEN}完成${NC}"
echo -e "    丢包率: ${YELLOW}$PACKET_LOSS${NC}"
echo -e "    平均延迟: ${YELLOW}${AVG_LATENCY}ms${NC}"
echo ""

# TCP端口测试
echo -n "  TCP端口22连通性 (5次)... "
SUCCESS=0
for i in {1..5}; do
    if nc -zv -w 5 $HK_IP 22 2>&1 | grep -q "succeeded\|open"; then
        ((SUCCESS++))
    fi
    sleep 0.5
done
echo -e "${GREEN}完成${NC}"
echo -e "    成功率: ${YELLOW}$SUCCESS/5${NC}"
echo ""

# 2. SSH直连测试
echo -e "${BLUE}[2/6] SSH直连测试${NC}"
echo -n "  测试连接hk主机... "
if ssh -o ConnectTimeout=10 -o BatchMode=yes hk "echo 'OK'; uptime" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 成功${NC}"
else
    echo -e "${RED}✗ 失败${NC}"
fi
echo ""

# 3. SSH跳板连接测试
echo -e "${BLUE}[3/6] SSH跳板连接测试${NC}"
echo -n "  测试连接hk-jump主机... "
if ssh -o ConnectTimeout=15 -o BatchMode=yes hk-jump "echo 'OK'; uptime" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 成功${NC}"
else
    echo -e "${RED}✗ 失败${NC}"
fi
echo ""

# 4. 长连接稳定性测试
echo -e "${BLUE}[4/6] 长连接稳定性测试${NC}"
echo -n "  保持SSH连接60秒... "
START_TIME=$(date +%s)
(
    ssh hk "while true; do echo \$(date +%T); sleep 5; done" > /dev/null 2>&1 &
    SSH_PID=$!
    sleep 60
    if ps -p $SSH_PID > /dev/null 2>&1; then
        kill $SSH_PID 2>/dev/null
        echo "SUCCESS"
    else
        echo "FAILED"
    fi
) &
LONG_TEST_PID=$!

# 等待测试完成
WAIT_COUNT=0
while kill -0 $LONG_TEST_PID 2>/dev/null; do
    if [ $WAIT_COUNT -lt 65 ]; then
        sleep 1
        ((WAIT_COUNT++))
        echo -n "."
    else
        kill $LONG_TEST_PID 2>/dev/null
        break
    fi
done

LONG_TEST_RESULT=$(wait $LONG_TEST_PID 2>/dev/null || echo "FAILED")
if echo "$LONG_TEST_RESULT" | grep -q "SUCCESS"; then
    echo -e " ${GREEN}✓ 60秒连接稳定${NC}"
else
    echo -e " ${RED}✗ 连接中断${NC}"
fi
echo ""

# 5. 传输测试（小文件）
echo -e "${BLUE}[5/6] 文件传输测试${NC}"
TEST_FILE="/tmp/ssh-test-$(date +%s).txt"
echo "Test file for SSH transfer - $(date)" > $TEST_FILE
echo -n "  上传测试文件... "
if scp $TEST_FILE hk:/tmp/ 2>/dev/null; then
    echo -e "${GREEN}✓ 成功${NC}"
    rm -f $TEST_FILE
    ssh hk "rm -f /tmp/ssh-test-*.txt" 2>/dev/null
else
    echo -e "${RED}✗ 失败${NC}"
    rm -f $TEST_FILE
fi
echo ""

# 6. 连接复用状态
echo -e "${BLUE}[6/6] SSH连接复用状态${NC}"
SOCKET_DIR="$HOME/.ssh/sockets"
if [ -d "$SOCKET_DIR" ]; then
    SOCKET_COUNT=$(ls -1 "$SOCKET_DIR"/*@${HK_IP}-* 2>/dev/null | wc -l)
    if [ $SOCKET_COUNT -gt 0 ]; then
        echo -e "  ${GREEN}✓ 发现 ${SOCKET_COUNT} 个活跃的连接复用socket${NC}"
        ls -lh "$SOCKET_DIR"/*@${HK_IP}-* 2>/dev/null | awk '{print "    " $9 " (" $5 ")"}'
    else
        echo -e "  ${YELLOW}⚠ 未发现连接复用socket${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Socket目录不存在${NC}"
fi
echo ""

# 总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  测试完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "建议:"
if [ "$PACKET_LOSS" != "0%"" ] && [ "$PACKET_LOSS" != "N/A" ]; then
    echo -e "  ${YELLOW}• 网络存在丢包，建议使用跳板模式 (hk-jump)${NC}"
fi
if [ $SUCCESS -lt 5 ]; then
    echo -e "  ${RED}• TCP连接不稳定，建议检查网络或使用跳板模式${NC}"
fi
echo -e "  ${GREEN}• 直连使用: ssh hk${NC}"
echo -e "  ${GREEN}• 跳板使用: ssh hk-jump (推荐)${NC}"
echo -e "  ${GREEN}• 传输使用: ssh hk-transfer${NC}"
echo ""

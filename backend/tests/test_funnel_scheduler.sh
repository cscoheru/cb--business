#!/bin/bash
# test_funnel_scheduler.sh
# 测试商机漏斗管理调度器

echo "🧪 测试商机漏斗管理调度器"
echo "================================"

# API基础URL
API_BASE="https://api.zenconsult.top"

echo ""
echo "1️⃣ 漏斗管理任务"
echo "----------------------------"
echo "说明: 自动检查所有商机状态并执行自动演进"
echo "执行频率: 每小时"
echo "功能:"
echo "  - 检查verifying和assessing状态的商机"
echo "  - 根据置信度自动演进到下一状态"
echo "  - 处理超时商机"

echo ""
echo "2️⃣ 信号发现任务"
echo "----------------------------"
echo "说明: 从文章流自动发现商业机会"
echo "执行频率: 每30分钟"
echo "功能:"
echo "  - 扫描最近已处理的20篇文章"
echo "  - AI分析识别商业信号"
echo "  - 自动创建BusinessOpportunity记录"

echo ""
echo "3️⃣ 等级监控任务"
echo "----------------------------"
echo "说明: 动态更新用户收藏商机的等级"
echo "执行频率: 每6小时"
echo "功能:"
echo "  - 重新计算C-P-I分数"
echo "  - 自动升降级"
echo "  - 记录等级变更历史"

echo ""
echo "================================"
echo "📊 查看调度器状态"
echo "================================"

echo ""
echo "查看调度器日志:"
echo "docker logs cb-business-api-fixed | grep -E '(定时任务|商机)' | tail -20"

echo ""
echo "查看商机统计:"
curl -s "$API_BASE/api/v1/opportunities/funnel" | jq '.'

echo ""
echo "================================"
echo "💡 提示:"
echo "  - 所有任务已自动启动，无需手动触发"
echo "  - 查看实时日志: docker logs -f cb-business-api-fixed"
echo "  - 测试等级更新: 收藏一个商机，6小时内自动更新等级"
echo ""

#!/bin/bash
# tests/run_tests.sh
# CB-Business 后端 API 测试运行脚本

set -e

echo "🧪 CB-Business Backend API 测试"
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在 Docker 容器内
if [ -f /.dockerenv ]; then
    echo -e "${GREEN}✅ 检测到 Docker 容器环境${NC}"
    IS_DOCKER=true
else
    echo -e "${YELLOW}⚠️  本地环境（可能需要 PostgreSQL）${NC}"
    IS_DOCKER=false
fi

# 检查 pytest
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest 未安装${NC}"
    echo "安装: pip install pytest pytest-asyncio pytest-cov httpx"
    exit 1
fi

echo -e "${GREEN}✅ pytest 已安装${NC}"

# 测试列表
TESTS=(
    "tests/test_auth.py::TestAuthFlow"
    "tests/test_cards.py::TestCardsAPI"
    "tests/test_cards.py::TestCardsAPIIntegration"
    "tests/test_products.py::TestProductsAPI"
    "tests/test_products.py::TestProductsAPIIntegration"
    "tests/test_favorites.py::TestFavoritesAPI"
    "tests/test_opportunities.py::TestOpportunitiesAPI"
    "tests/test_opportunities.py::TestOpportunityCPIAlgorithm"
)

# 运行测试
echo ""
echo "🚀 开始运行测试..."
echo ""

FAILED_TESTS=()
PASSED_TESTS=0
TOTAL_TESTS=0

for test in "${TESTS[@]}"; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}测试: ${test}${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if pytest "$test" -v --tb=line -x 2>&1 | tee /tmp/test_output.log; then
        echo -e "${GREEN}✅ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ FAILED${NC}"
        FAILED_TESTS+=("$test")
    fi

    echo ""
done

# 输出摘要
echo "================================"
echo "📊 测试摘要"
echo "================================"
echo -e "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}✅ 通过: $PASSED_TESTS${NC}"
echo -e "${RED}❌ 失败: ${#FAILED_TESTS[@]}${NC}"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo ""
    echo "失败的测试:"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  - ${RED}$test${NC}"
    done
fi

# 覆盖率报告
echo ""
echo "📈 生成覆盖率报告..."
if pytest tests/ --cov=api --cov-report=term-missing --quiet 2>&1 | tee /tmp/coverage.log; then
    echo -e "${GREEN}✅ 覆盖率报告已生成${NC}"
else
    echo -e "${YELLOW}⚠️  覆盖率报告生成失败${NC}"
fi

# 最终结果
echo ""
if [ ${#FAILED_TESTS[@]} -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}⚠️  部分测试失败${NC}"
    exit 1
fi

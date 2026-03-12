#!/bin/bash
# OpenClaw 迁移部署脚本
# 用途: 将代码同步到 HK 服务器并部署

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数: 打印带颜色的消息
print_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

print_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 检查必需命令
check_requirements() {
    print_info "检查系统依赖..."

    if ! command -v rsync &> /dev/null; then
        print_error "rsync 未安装"
        exit 1
    fi

    if ! command -v ssh &> /dev/null; then
        print_error "ssh 未安装"
        exit 1
    fi

    # 检查 SSH 别名 'hk' 是否配置
    if ! ssh hk "echo 'HK 服务器连接成功'" &> /dev/null; then
        print_error "无法连接到 HK 服务器 (请检查 ~/.ssh/config 中 hk 别名配置)"
        exit 1
    fi

    print_success "依赖检查通过"
}

# 加载环境变量
load_env() {
    print_info "加载环境变量..."

    if [ ! -f .env.prod ]; then
        print_error ".env.prod 文件不存在"
        exit 1
    fi

    set -a  # 自动导出所有变量
    source .env.prod
    set +a

    print_success "环境变量已加载"
}

# 同步代码到 HK 服务器
sync_code() {
    print_info "同步代码到 HK 服务器..."

    rsync -avz --delete \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.pytest_cache' \
        --exclude='logs' \
        --exclude='*.db' \
        --exclude='*.sqlite' \
        --exclude='railway_backup_*.sql' \
        --exclude='.DS_Store' \
        --exclude='backups' \
        --exclude='ssl' \
        . hk:/root/cb-business/

    print_success "代码同步完成"
}

# 在 HK 服务器上执行部署
deploy_on_server() {
    print_info "在 HK 服务器上启动部署..."

    ssh hk << 'ENDSSH'
set -e

echo "📦 进入项目目录..."
cd /root/cb-business

echo "🛑 停止旧服务..."
docker-compose -f docker-compose.prod.yml down

echo "🔧 清理旧镜像（可选）..."
# docker system prune -f

echo "🏗️  构建新镜像..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo "🚀 启动新服务..."
docker-compose -f docker-compose.prod.yml up -d

echo "⏳ 等待服务启动..."
sleep 10

echo "📊 服务状态:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📋 最近日志 (API):"
docker-compose -f docker-compose.prod.yml logs --tail=30 api

ENDSSH

    print_success "部署完成"
}

# 显示服务状态
show_status() {
    print_info "检查服务状态..."

    ssh hk << 'ENDSSH'
cd /root/cb-business
echo ""
echo "🔍 容器状态:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "🌐 端口监听:"
ss -tlnp | grep -E '8000|5432|6379|80|443' || echo "未发现端口监听"
ENDSSH
}

# 测试 API 连接
test_api() {
    print_info "测试 API 连接..."

    # 等待服务完全启动
    sleep 5

    # 测试健康检查
    if curl -s -f http://103.59.103.85:8000/health > /dev/null; then
        print_success "健康检查通过"
    else
        print_warn "健康检查失败 - 服务可能还在启动中"
    fi

    # 测试根路径
    if curl -s -f http://103.59.103.85:8000/ > /dev/null; then
        print_success "根路径访问正常"
    else
        print_warn "根路径访问失败"
    fi
}

# 主函数
main() {
    echo "🚀 OpenClaw 迁移部署脚本"
    echo "================================"
    echo ""

    check_requirements
    load_env
    sync_code
    deploy_on_server
    show_status
    test_api

    echo ""
    print_success "部署流程完成！"
    echo ""
    echo "📌 后续命令:"
    echo "  查看日志: ssh hk \"cd /root/cb-business && docker-compose -f docker-compose.prod.yml logs -f api\""
    echo "  重启服务: ssh hk \"cd /root/cb-business && docker-compose -f docker-compose.prod.yml restart api\""
    echo "  停止服务: ssh hk \"cd /root/cb-business && docker-compose -f docker-compose.prod.yml down\""
}

# 执行主函数
main "$@"

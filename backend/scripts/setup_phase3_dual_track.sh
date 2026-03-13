#!/bin/bash
###############################################################################
# Phase 3: 双轨运行环境设置脚本
#
# 功能:
# 1. 创建数据库监控表
# 2. 配置OpenClaw Channels调度 (影子模式)
# 3. 设置数据监控定时任务
# 4. 验证环境配置
#
# 使用方法:
#   bash backend/scripts/setup_phase3_dual_track.sh
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否在HK服务器上
check_hk_server() {
    log_info "检查服务器环境..."

    if [ ! -d "/root/.openclaw" ]; then
        log_error "未检测到OpenClaw目录，请在HK服务器上运行此脚本"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi

    if ! command -v node &> /dev/null; then
        log_error "Node.js未安装"
        exit 1
    fi

    log_success "服务器环境检查通过"
}

# 步骤1: 创建数据库监控表
setup_database_monitoring() {
    log_info "步骤1: 创建数据库监控表..."

    local db_container="cb-business-postgres"
    local migration_file="/opt/cb-business-repo/backend/migrations/004_create_dual_track_monitoring.sql"

    # 检查容器是否运行
    if ! docker ps | grep -q "$db_container"; then
        log_error "PostgreSQL容器未运行"
        return 1
    fi

    # 执行迁移
    docker exec -i "$db_container" psql -U cbuser -d cbdb < "$migration_file"

    log_success "数据库监控表创建完成"
}

# 步骤2: 配置OpenClaw Channels (影子模式)
setup_openclaw_channels() {
    log_info "步骤2: 配置OpenClaw Channels调度..."

    local openclaw_dir="/root/.openclaw"
    local channels_dir="$openclaw_dir/channels"
    local cron_dir="$openclaw_dir/cron"

    # 检查channels是否存在
    if [ ! -d "$channels_dir" ]; then
        log_error "Channels目录不存在: $channels_dir"
        return 1
    fi

    # 验证所有channel文件
    local required_channels=(
        "rss-crawler.js"
        "oxylabs-monitor.js"
        "bright-data-monitor.js"
        "content-classifier.js"
        "trend-discovery.js"
    )

    for channel in "${required_channels[@]}"; do
        if [ ! -f "$channels_dir/$channel" ]; then
            log_warning "Channel文件不存在: $channel"
        else
            log_info "✓ $channel"
        fi
    done

    # 创建OpenClaw crontab配置
    local crontab_file="$cron_dir/dual_track_crontab"

    cat > "$crontab_file" << 'CRONTAB_EOF'
# OpenClaw Channels - 双轨运行测试 (影子模式)
# 所有OpenClaw任务使用 'openclaw-' 作为数据源标记
# 与APScheduler并行运行，不干扰生产系统

# RSS Crawler - 每30分钟 (影子模式)
*/30 * * * * cd /root/.openclaw/channels && node rss-crawler.js >> /root/.openclaw/logs/rss-shadow.log 2>&1

# Bright Data Monitor - 每小时 (影子模式)
0 * * * * cd /root/.openclaw/channels && node bright-data-monitor.js >> /root/.openclaw/logs/brightdata-shadow.log 2>&1

# Content Classifier - 每30分钟 (影子模式)
*/30 * * * * cd /root/.openclaw/channels && node content-classifier.js >> /root/.openclaw/logs/classifier-shadow.log 2>&1

# Trend Discovery - 每6小时 (影子模式)
0 */6 * * * cd /root/.openclaw/channels && node trend-discovery.js >> /root/.openclaw/logs/trend-shadow.log 2>&1

# Oxylabs Monitor - 每小时 (影子模式，作为备用)
0 * * * * cd /root/.openclaw/channels && node oxylabs-monitor.js >> /root/.openclaw/logs/oxylabs-shadow.log 2>&1
CRONTAB_EOF

    # 创建日志目录
    mkdir -p "$openclaw_dir/logs"

    # 显示当前crontab
    log_info "当前crontab配置:"
    crontab -l 2>/dev/null | grep -v "^#" | grep openclaw || echo "无现有OpenClaw任务"

    log_success "OpenClaw Channels配置完成"
    log_info "Crontab文件: $crontab_file"
    log_warning "请手动审核后使用 'crontab $crontab_file' 安装"
}

# 步骤3: 设置数据监控定时任务
setup_monitoring_jobs() {
    log_info "步骤3: 设置数据监控定时任务..."

    local api_container="cb-business-api-fixed"

    # 创建监控脚本crontab
    local monitor_cron="/tmp/monitor_cron"

    cat > "$monitor_cron" << 'MONITOR_EOF'
# 双轨运行监控任务

# 每小时运行数据对比监控
0 * * * * docker exec $api_container python /app/scripts/dual_track_monitor.py >> /var/log/dual_track_monitor.log 2>&1

# 每天凌晨3点清理旧日志
0 3 * * * docker exec $api_container python -c "from config.database import engine; import asyncio; async def cleanup(): result = await engine.execute('SELECT cleanup_old_comparison_logs()'); print(f'Cleaned {result.scalar()} logs'); asyncio.run(cleanup())"
MONITOR_EOF

    log_success "监控任务配置完成"
    log_info "监控Crontab文件: $monitor_cron"
}

# 步骤4: 验证配置
verify_setup() {
    log_info "步骤4: 验证环境配置..."

    # 4.1 检查数据库表
    log_info "检查数据库表..."
    local db_check=$(docker exec cb-business-postgres psql -U cbuser -d cbdb -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'data_comparison_log'" 2>/dev/null || echo "0")

    if [ "$db_check" -eq "1" ]; then
        log_success "✓ 监控表已创建"
    else
        log_error "✗ 监控表创建失败"
        return 1
    fi

    # 4.2 检查OpenClaw Channels
    log_info "检查OpenClaw Channels..."
    local channels_dir="/root/.openclaw/channels"
    local channel_count=$(ls -1 "$channels_dir"/*.js 2>/dev/null | wc -l)

    if [ "$channel_count" -ge 4 ]; then
        log_success "✓ 发现 $channel_count 个Channels"
    else
        log_warning "仅发现 $channel_count 个Channels (预期5个)"
    fi

    # 4.3 测试Channel运行
    log_info "测试Channel运行..."
    cd "$channels_dir"

    local test_output=$(node oxylabs-monitor.js 2>&1)
    if echo "$test_output" | grep -q "success.*true"; then
        log_success "✓ Channel测试通过"
    else
        log_warning "Channel测试返回非成功状态"
    fi

    # 4.4 测试监控脚本
    log_info "测试监控脚本..."
    local api_container="cb-business-api-fixed"
    local monitor_test=$(docker exec "$api_container" python /app/scripts/dual_track_monitor.py 2>&1 || true)

    if echo "$monitor_test" | grep -q "双轨运行监控报告"; then
        log_success "✓ 监控脚本工作正常"
    else
        log_warning "监控脚本测试失败"
    fi

    log_success "环境验证完成"
}

# 步骤5: 显示下一步操作
show_next_steps() {
    cat << 'NEXT_STEPS'

═══════════════════════════════════════════════════════════════
                   Phase 3 双轨运行 - 下一步操作
═══════════════════════════════════════════════════════════════

1. 安装OpenClaw Channels调度:

   crontab -l > /tmp/current_crontab
   cat /root/.openclaw/cron/dual_track_crontab >> /tmp/current_crontab
   crontab /tmp/current_crontab

2. 验证APScheduler仍在运行:

   docker logs cb-business-api-fixed | grep "Scheduler"

3. 启动首次数据对比:

   docker exec cb-business-api-fixed python /app/scripts/dual_track_monitor.py

4. 查看监控数据:

   docker exec cb-business-postgres psql -U cbuser -d cbdb -c "SELECT * FROM v_comparison_summary_24h;"

5. 监控日志:

   tail -f /root/.openclaw/logs/*.log

═══════════════════════════════════════════════════════════════

NEXT_STEPS
}

# 主函数
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║          Phase 3: 双轨运行环境设置                        ║"
    echo "║          Dual Track Monitoring Setup                       ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    check_hk_server
    setup_database_monitoring
    setup_openclaw_channels
    setup_monitoring_jobs
    verify_setup
    show_next_steps

    log_success "Phase 3 环境设置完成！"
}

# 运行主函数
main "$@"

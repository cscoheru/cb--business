#!/bin/bash
#
# 设置Trial到期检查cron任务
#
# 使用方法:
#   ./setup_trial_cron.sh [install|uninstall|status]
#

CRON_JOB="0 2 * * * cd /app && python scripts/check_trial_expiry.py >> logs/trial_expiry.log 2>&1"
CRON_MARKER="# TRIAL_EXPIRY_CHECK"

case "$1" in
  install)
    echo "安装Trial到期检查cron任务..."

    # 检查是否已存在
    if crontab -l 2>/dev/null | grep -q "$CRON_MARKER"; then
      echo "⚠️  Cron任务已存在，跳过安装"
      exit 0
    fi

    # 添加cron任务
    (crontab -l 2>/dev/null; echo "$CRON_MARKER") | crontab -
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

    echo "✅ Cron任务已安装: 每天凌晨2点执行"
    echo "📋 查看日志: tail -f logs/trial_expiry.log"
    ;;

  uninstall)
    echo "卸载Trial到期检查cron任务..."

    # 删除cron任务
    crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | grep -v "check_trial_expiry.py" | crontab -

    echo "✅ Cron任务已卸载"
    ;;

  status)
    echo "检查Cron任务状态..."
    if crontab -l 2>/dev/null | grep -q "$CRON_MARKER"; then
      echo "✅ Cron任务已安装"
      crontab -l 2>/dev/null | grep "$CRON_MARKER" -A 1
    else
      echo "❌ Cron任务未安装"
    fi
    ;;

  test)
    echo "执行测试运行 (dry-run)..."
    cd /app
    python scripts/check_trial_expiry.py --dry-run
    ;;

  *)
    echo "使用方法: $0 {install|uninstall|status|test}"
    echo ""
    echo "命令:"
    echo "  install   - 安装cron任务"
    echo "  uninstall - 卸载cron任务"
    echo "  status    - 查看任务状态"
    echo "  test      - 测试运行 (dry-run模式)"
    exit 1
    ;;
esac

#!/bin/bash
# Railway 数据库导出脚本
# 用途: 从 Railway 导出 PostgreSQL 数据

echo "📤 Railway 数据库导出工具"
echo "================================"

# 检查 Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI 未安装"
    echo "安装命令: npm install -g @railway/cli"
    exit 1
fi

# 登录检查
echo "🔐 检查 Railway 登录状态..."
if ! railway status &> /dev/null; then
    echo "需要登录 Railway..."
    railway login
fi

# 获取项目和服务
echo ""
echo "📋 当前 Railway 项目:"
railway status

echo ""
echo "正在获取 DATABASE_URL..."
DATABASE_URL=$(railway variables get DATABASE_URL 2>/dev/null)

if [ -z "$DATABASE_URL" ]; then
    echo "❌ 无法获取 DATABASE_URL"
    echo "请确保:"
    echo "  1. 已登录正确的 Railway 项目"
    echo "  2. 项目中有 DATABASE_URL 变量"
    exit 1
fi

# 创建备份目录
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR

# 生成备份文件名
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/railway_backup_$DATE.sql"

echo ""
echo "📦 开始导出数据库..."
echo "目标文件: $BACKUP_FILE"

# 导出选项
echo ""
echo "请选择导出选项:"
echo "  1) 完整导出 (所有数据)"
echo "  2) 仅导出关键表 (users, subscriptions, assessments, usage_logs)"
echo "  3) 仅导出结构 (不包含数据)"
read -p "请输入选项 [1-3]: " option

case $option in
    1)
        echo "导出完整数据库..."
        pg_dump "$DATABASE_URL" > "$BACKUP_FILE"
        ;;
    2)
        echo "导出关键表..."
        pg_dump -t users -t subscriptions -t assessments -t usage_logs "$DATABASE_URL" > "$BACKUP_FILE"
        ;;
    3)
        echo "仅导出结构..."
        pg_dump --schema-only "$DATABASE_URL" > "$BACKUP_FILE"
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

# 检查导出结果
if [ $? -eq 0 ]; then
    # 压缩备份文件
    gzip "$BACKUP_FILE"
    BACKUP_FILE_ZIP="${BACKUP_FILE}.gz"

    # 显示文件大小
    SIZE=$(du -h "$BACKUP_FILE_ZIP" | cut -f1)
    echo ""
    echo "✅ 导出成功!"
    echo "文件: $BACKUP_FILE_ZIP ($SIZE)"

    echo ""
    echo "📋 导出文件列表:"
    ls -lh "$BACKUP_DIR/"

    echo ""
    echo "💡 提示:"
    echo "  上传到 HK 服务器: scp $BACKUP_FILE_ZIP hk:/root/cb-business/backups/"
    echo "  在 HK 服务器导入: gunzip -c $BACKUP_FILE_ZIP | docker exec -i cb-business-postgres-1 psql -U cbuser -d cbdb"
else
    echo "❌ 导出失败"
    exit 1
fi

#!/bin/bash
# HK 服务器数据库备份脚本
# 用途: 备份 PostgreSQL 数据库到本地

BACKUP_DIR="/root/cb-business/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/postgres_$DATE.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

echo "💾 开始备份数据库..."

# 备份 PostgreSQL
docker exec cb-business-postgres-1 \
    pg_dump -U cbuser cbdb > $BACKUP_FILE 2>/dev/null || {
    echo "❌ 备份失败！"
    echo "提示: 检查容器名称是否正确"
    docker ps | grep postgres
    exit 1
}

# 压缩备份
gzip $BACKUP_FILE
BACKUP_FILE_ZIP="${BACKUP_FILE}.gz"

# 显示备份文件大小
BACKUP_SIZE=$(du -h $BACKUP_FILE_ZIP | cut -f1)
echo "✅ 备份完成: $BACKUP_FILE_ZIP ($BACKUP_SIZE)"

# 清理 7 天前的备份
find $BACKUP_DIR -name "postgres_*.sql.gz" -mtime +7 -delete
echo "🧹 已清理 7 天前的旧备份"

# 列出所有备份文件
echo ""
echo "📁 当前备份文件:"
ls -lh $BACKUP_DIR/

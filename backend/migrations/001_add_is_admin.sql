-- 添加 is_admin 字段到 users 表
-- 执行前请备份数据库

-- PostgreSQL
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE NOT NULL;

-- SQLite (SQLite不支持IF NOT EXISTS语法，需要分开执行)
-- 首先检查列是否存在的逻辑需要在应用层处理

-- 添加 is_admin 字段 (SQLite)
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE NOT NULL;

-- 设置默认管理员（可选）
UPDATE users SET is_admin = TRUE WHERE email = 'admin@3strategy.cc';

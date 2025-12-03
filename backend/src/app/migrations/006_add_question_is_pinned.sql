-- 迁移: 添加问题的 is_pinned 字段（保留题目，随机抽题时始终出现）
-- 日期: 2025-12-03

-- 添加 is_pinned 列
ALTER TABLE questions ADD COLUMN is_pinned BOOLEAN DEFAULT FALSE;

-- 更新现有记录的默认值
UPDATE questions SET is_pinned = FALSE WHERE is_pinned IS NULL;

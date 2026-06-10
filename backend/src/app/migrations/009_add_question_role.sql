-- 009: 题目语义标记
-- 给 questions 加 role 列: 把某道普通题标记为系统字段 (player_name / qq),
-- 提交时其答案抽取到 Submission 结构化列。NULL=普通题。
-- 新库由模型 create_all 直接含此列; 已有库执行本迁移。

ALTER TABLE questions ADD COLUMN role VARCHAR(20);

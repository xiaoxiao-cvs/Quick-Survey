-- 添加条件显示字段
-- 用于实现条件分支逻辑：根据某道题的答案决定是否显示当前题目
-- 格式: {"depends_on": 问题ID, "show_when": "答案值" 或 ["值1", "值2"]}

ALTER TABLE questions ADD COLUMN condition JSON DEFAULT NULL;

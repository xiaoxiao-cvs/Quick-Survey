-- 迁移: 修复 answers 表的 question_id 外键约束
-- 日期: 2025-12-03
-- 问题: 删除问题时，关联的答案应该级联删除

-- SQLite 不支持直接修改外键约束，需要重建表

-- 1. 创建临时表
CREATE TABLE answers_new (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    content JSON NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- 2. 复制数据
INSERT INTO answers_new (id, submission_id, question_id, content, created_at)
SELECT id, submission_id, question_id, content, created_at FROM answers;

-- 3. 删除旧表
DROP TABLE answers;

-- 4. 重命名新表
ALTER TABLE answers_new RENAME TO answers;

-- 5. 重建索引（如果有的话）

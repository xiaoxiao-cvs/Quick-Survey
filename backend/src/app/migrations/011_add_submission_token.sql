-- 011: 提交自助凭据 token 与注册码领取标记
-- token: 提交时生成的不可枚举随机串, 玩家凭此查询审核进度并在通过后自助领取注册码,
--        取代按明文玩家名查询 (堵掉枚举/越权探测)。
-- code_issued_at: 非空即"已领取", 每个提交仅放码一次。
-- 新库由模型 create_all 直接含这两列; 已有库执行本迁移。
-- SQLite 在唯一索引下允许多个 NULL, 故历史无 token 的行不冲突。

ALTER TABLE submissions ADD COLUMN token VARCHAR(43);
ALTER TABLE submissions ADD COLUMN code_issued_at DATETIME;
CREATE UNIQUE INDEX IF NOT EXISTS ix_submissions_token ON submissions (token);

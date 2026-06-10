-- 010: 提交联系 QQ
-- 给 submissions 加 qq 列: 提交时从 role=qq 的题目抽取, 供审核展示与加白带入。
-- 新库由模型 create_all 直接含此列; 已有库执行本迁移。

ALTER TABLE submissions ADD COLUMN qq VARCHAR(20);

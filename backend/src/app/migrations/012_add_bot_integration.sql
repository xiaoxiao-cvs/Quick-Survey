-- 012: QQ 机器人集成 (审核群通知 + 主群自动准入)
-- submissions.in_review_group: 提交时该 QQ 是否在审核群 (bot 回填), True/False/NULL, 面板标记"未在审核群"。
-- bot_notifications: 待 bot 发送的审核群通知队列, 插件轮询消费。
-- 新库由模型 create_all 直接含这些; 已有库执行本迁移。

ALTER TABLE submissions ADD COLUMN in_review_group BOOLEAN;

CREATE TABLE IF NOT EXISTS bot_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    qq VARCHAR(20) NOT NULL,
    type VARCHAR(20) NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME,
    sent_at DATETIME
);
CREATE INDEX IF NOT EXISTS ix_bot_notifications_status ON bot_notifications (status);
CREATE INDEX IF NOT EXISTS ix_bot_notifications_created_at ON bot_notifications (created_at);

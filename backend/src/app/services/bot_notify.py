"""
QQ 机器人通知队列服务。

提交/审核时入队一条 BotNotification; NapCat 插件轮询取 pending、在审核群 @ 后回调 ack。
入队是审核/提交主流程的"尽力而为"副作用 —— 入队失败不应让提交/审核失败 (调用方 try 包裹)。
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BotNotification, Submission

# 通知类型
SUBMIT = "submit"
APPROVED = "approved"
REJECTED = "rejected"


async def enqueue(
    db: AsyncSession,
    submission: Submission,
    type_: str,
    reason: Optional[str] = None,
) -> None:
    """入队一条通知。qq 缺失则跳过 (无对象可通知)。"""
    if not submission.qq:
        return
    db.add(BotNotification(
        submission_id=submission.id,
        qq=submission.qq,
        type=type_,
        reason=reason,
        status="pending",
    ))
    await db.commit()


async def list_pending(db: AsyncSession, limit: int = 20) -> list[BotNotification]:
    """取待发送通知 (按入队顺序)。"""
    result = await db.execute(
        select(BotNotification)
        .where(BotNotification.status == "pending")
        .order_by(BotNotification.created_at.asc(), BotNotification.id.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def ack(db: AsyncSession, notification_id: int, in_group: Optional[bool] = None) -> bool:
    """
    插件回调: 标记通知已处理 (done)。

    submit 类型且带 in_group 时, 回填对应 Submission.in_review_group (面板据此标记"未在审核群")。
    返回是否命中该 pending 通知。
    """
    notif = await db.get(BotNotification, notification_id)
    if not notif or notif.status != "pending":
        return False

    notif.status = "done"
    notif.sent_at = datetime.now(timezone.utc)

    if notif.type == SUBMIT and in_group is not None:
        submission = await db.get(Submission, notif.submission_id)
        if submission is not None:
            submission.in_review_group = in_group

    await db.commit()
    return True

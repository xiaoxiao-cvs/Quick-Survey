"""
机器人通知队列 + 按 QQ 查过审 的单元测试。
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db import Base
from app.models import Survey
from app.schemas import SubmissionCreate
from app.services import SubmissionService
from app.services import bot_notify


async def _make_session(tmp_path) -> AsyncSession:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)()


async def _make_survey(session: AsyncSession) -> Survey:
    survey = Survey(title="测试问卷", code="testcode", is_active=True)
    session.add(survey)
    await session.commit()
    await session.refresh(survey)
    return survey


async def _make_submission(session, survey, player_name, qq, status="pending"):
    sub = await SubmissionService.create_submission(
        session, survey, SubmissionCreate(answers=[]), player_name=player_name, qq=qq
    )
    if status != "pending":
        sub.status = status
        sub.reviewed_at = datetime.now(timezone.utc)
        await session.commit()
    return sub


async def test_get_approved_by_qq(tmp_path):
    session = await _make_session(tmp_path)
    survey = await _make_survey(session)
    await _make_submission(session, survey, "Alice", "10001", status="approved")
    await _make_submission(session, survey, "Bob", "10002", status="pending")
    await _make_submission(session, survey, "Carol", "10003", status="rejected")

    hit = await SubmissionService.get_approved_by_qq(session, "10001")
    assert hit is not None and hit.player_name == "Alice"
    # pending / rejected / 不存在 都不算命中
    assert await SubmissionService.get_approved_by_qq(session, "10002") is None
    assert await SubmissionService.get_approved_by_qq(session, "10003") is None
    assert await SubmissionService.get_approved_by_qq(session, "99999") is None
    await session.close()


async def test_enqueue_list_ack_flow_and_in_review_group(tmp_path):
    session = await _make_session(tmp_path)
    survey = await _make_survey(session)
    sub = await _make_submission(session, survey, "Dave", "20001")

    await bot_notify.enqueue(session, sub, bot_notify.SUBMIT)
    pending = await bot_notify.list_pending(session)
    assert len(pending) == 1 and pending[0].type == "submit" and pending[0].qq == "20001"

    # ack 回填 in_review_group=False
    nid = pending[0].id
    assert await bot_notify.ack(session, nid, in_group=False) is True
    await session.refresh(sub)
    assert sub.in_review_group is False
    # 已处理 -> 不再 pending; 重复 ack 返回 False
    assert await bot_notify.list_pending(session) == []
    assert await bot_notify.ack(session, nid, in_group=True) is False
    await session.close()


async def test_enqueue_rejected_carries_reason_and_skips_when_no_qq(tmp_path):
    session = await _make_session(tmp_path)
    survey = await _make_survey(session)

    sub = await _make_submission(session, survey, "Eve", "20002")
    await bot_notify.enqueue(session, sub, bot_notify.REJECTED, reason="刷屏")
    pending = await bot_notify.list_pending(session)
    assert len(pending) == 1 and pending[0].type == "rejected" and pending[0].reason == "刷屏"

    # 无 QQ 的提交不入队
    no_qq = await _make_submission(session, survey, "Frank", None)
    await bot_notify.enqueue(session, no_qq, bot_notify.SUBMIT)
    assert len(await bot_notify.list_pending(session)) == 1  # 仍是 1, 没新增
    await session.close()

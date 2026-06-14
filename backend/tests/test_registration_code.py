"""
问卷自助凭据 token 与领码状态机的单元测试。

覆盖安全关键不变量 (删掉对应闸门后必挂):
- 提交生成不可枚举 token, 可凭 token 精确查回、错码查不到。
- 领码必须 status=approved 才放码 (未过审不调 mod、不标记)。
- 每个提交仅放码一次 (已领取不再调 mod)。
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db import Base
from app.models import Survey
from app.schemas import SubmissionCreate
from app.services import SubmissionService


async def _make_session(tmp_path) -> AsyncSession:
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return maker()


async def _make_survey(session: AsyncSession) -> Survey:
    survey = Survey(title="测试问卷", code="testcode", is_active=True)
    session.add(survey)
    await session.commit()
    await session.refresh(survey)
    return survey


async def test_create_submission_generates_lookupable_token(tmp_path):
    session = await _make_session(tmp_path)
    survey = await _make_survey(session)

    sub = await SubmissionService.create_submission(
        session, survey, SubmissionCreate(answers=[]), player_name="Alice"
    )
    assert sub.token and len(sub.token) >= 40, "提交应生成足够长的不可枚举 token"

    found = await SubmissionService.get_submission_by_token(session, sub.token)
    assert found is not None and found.id == sub.id, "应能凭 token 精确查回本条提交"

    miss = await SubmissionService.get_submission_by_token(session, "definitely-not-a-real-token")
    assert miss is None, "错误 token 不应命中任何提交"

    await session.close()


async def test_redeem_requires_approved(tmp_path):
    session = await _make_session(tmp_path)
    survey = await _make_survey(session)
    sub = await SubmissionService.create_submission(
        session, survey, SubmissionCreate(answers=[]), player_name="Bob"
    )

    calls: list[str] = []

    async def provider(name: str) -> dict:
        calls.append(name)
        return {"registration_code": "ABCD-2345", "code_expires_minutes": 1440}

    status, data = await SubmissionService.issue_registration_code(session, sub, provider)

    assert status == "not_approved", "pending 提交不应放码"
    assert data is None
    assert sub.code_issued_at is None, "未过审不应标记已领取"
    assert calls == [], "未过审绝不应调用 mod 发码"

    await session.close()


async def test_redeem_is_once_only(tmp_path):
    session = await _make_session(tmp_path)
    survey = await _make_survey(session)
    sub = await SubmissionService.create_submission(
        session, survey, SubmissionCreate(answers=[]), player_name="Carol"
    )
    sub.status = "approved"
    await session.commit()

    calls: list[str] = []

    async def provider(name: str) -> dict:
        calls.append(name)
        return {"registration_code": "WXYZ-6789", "code_expires_minutes": 1440}

    status, data = await SubmissionService.issue_registration_code(session, sub, provider)
    assert status == "ok"
    assert data["registration_code"] == "WXYZ-6789"
    assert sub.code_issued_at is not None, "首次领取应标记已领取"
    assert calls == ["Carol"], "应以提交者玩家名向 mod 取码一次"

    status2, data2 = await SubmissionService.issue_registration_code(session, sub, provider)
    assert status2 == "already_issued", "再次领取应返回已领取"
    assert data2 is None
    assert calls == ["Carol"], "已领取不应再次调用 mod"

    await session.close()

"""活动日志服务"""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog


class ActivityService:
    """活动日志服务"""
    
    @staticmethod
    async def log_submit(
        db: AsyncSession,
        player_name: str,
        submission_id: int,
    ) -> ActivityLog:
        """记录问卷提交"""
        log = ActivityLog(
            action="submit",
            player_name=player_name,
            submission_id=submission_id,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log
    
    @staticmethod
    async def log_review(
        db: AsyncSession,
        player_name: str,
        submission_id: int,
        status: str,  # approved 或 rejected
        operator: Optional[str] = None,
        note: Optional[str] = None,
    ) -> ActivityLog:
        """记录审核操作"""
        log = ActivityLog(
            action=status,  # approved 或 rejected
            player_name=player_name,
            submission_id=submission_id,
            operator=operator,
            note=note,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log
    
    @staticmethod
    async def get_recent_activities(
        db: AsyncSession,
        limit: int = 10,
        offset: int = 0,
        action: Optional[str] = None,
    ) -> tuple[list[ActivityLog], int]:
        """获取最近活动"""
        query = select(ActivityLog)
        count_query = select(func.count(ActivityLog.id))
        
        if action:
            query = query.where(ActivityLog.action == action)
            count_query = count_query.where(ActivityLog.action == action)
        
        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页
        query = query.order_by(desc(ActivityLog.created_at))
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return list(logs), total

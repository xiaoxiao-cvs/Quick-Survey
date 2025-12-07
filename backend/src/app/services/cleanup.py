"""
定时清理服务 - 清理已审核的问卷答案和图片文件
保留提交记录的元数据（状态、审核时间等）用于日志查询
"""

import os
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import async_session_maker
from app.models import Submission, Answer, UploadedFile
from app.core.config import get_settings


class CleanupService:
    """清理服务"""
    
    _task: Optional[asyncio.Task] = None
    _running: bool = False
    
    @classmethod
    async def cleanup_reviewed_submissions(cls, db: AsyncSession) -> dict:
        """
        清理已审核的提交数据
        
        保留:
        - submissions 表的记录（元数据：状态、审核时间、审核备注等）
        
        删除:
        - answers 表中的答案数据
        - uploaded_files 表中的文件记录
        - uploads/ 目录中的实际图片文件
        """
        settings = get_settings()
        upload_dir = Path(settings.upload.path)
        
        stats = {
            "submissions_cleaned": 0,
            "answers_deleted": 0,
            "files_deleted": 0,
            "bytes_freed": 0,
        }
        
        # 查找已审核的提交（状态为 approved 或 rejected）
        # 使用 selectinload 预加载 answers 关系，避免异步懒加载问题
        query = select(Submission).options(
            selectinload(Submission.answers)
        ).where(
            and_(
                Submission.status.in_(["approved", "rejected"]),
                Submission.reviewed_at.isnot(None),
            )
        )
        result = await db.execute(query)
        submissions = result.scalars().all()
        
        for submission in submissions:
            # 检查是否还有答案（可能已经被清理过）
            if not submission.answers:
                continue
            
            # 收集需要删除的图片文件
            for answer in submission.answers:
                content = answer.content or {}
                images = content.get("images", [])
                
                for image_path in images:
                    # 图片路径格式: /uploads/xxx.jpg
                    filename = image_path.replace("/uploads/", "")
                    file_path = upload_dir / filename
                    
                    if file_path.exists():
                        try:
                            file_size = file_path.stat().st_size
                            os.remove(file_path)
                            stats["files_deleted"] += 1
                            stats["bytes_freed"] += file_size
                        except Exception as e:
                            print(f"[Cleanup] 删除文件失败: {file_path}, 错误: {e}")
            
            # 删除答案记录
            answers_count = len(submission.answers)
            for answer in list(submission.answers):
                await db.delete(answer)
            
            stats["answers_deleted"] += answers_count
            stats["submissions_cleaned"] += 1
        
        # 删除关联的上传文件记录
        file_query = select(UploadedFile).where(
            UploadedFile.submission_id.in_([s.id for s in submissions])
        )
        file_result = await db.execute(file_query)
        uploaded_files = file_result.scalars().all()
        
        for uploaded_file in uploaded_files:
            # 如果文件还存在，也删除
            file_path = Path(uploaded_file.file_path)
            if file_path.exists():
                try:
                    file_size = file_path.stat().st_size
                    os.remove(file_path)
                    stats["files_deleted"] += 1
                    stats["bytes_freed"] += file_size
                except Exception:
                    pass
            await db.delete(uploaded_file)
        
        await db.commit()
        
        return stats
    
    @classmethod
    async def cleanup_orphan_files(cls) -> dict:
        """
        清理孤立的上传文件（没有关联到任何提交的文件）
        超过配置时间的未关联文件会被删除
        """
        settings = get_settings()
        upload_dir = Path(settings.upload.path)
        
        stats = {
            "orphan_files_deleted": 0,
            "bytes_freed": 0,
        }
        
        if not upload_dir.exists():
            return stats
        
        now = datetime.now(timezone.utc)
        threshold_seconds = settings.cleanup.orphan_file_hours * 60 * 60  # 从配置读取
        
        async with async_session_maker() as db:
            # 获取所有数据库中记录的文件名
            query = select(UploadedFile.stored_name)
            result = await db.execute(query)
            db_filenames = set(row[0] for row in result.fetchall())
            
            # 同时从答案中获取引用的图片
            answer_query = select(Answer.content)
            answer_result = await db.execute(answer_query)
            
            for row in answer_result.fetchall():
                content = row[0] or {}
                images = content.get("images", [])
                for image_path in images:
                    filename = image_path.replace("/uploads/", "")
                    db_filenames.add(filename)
        
        # 遍历上传目录
        for file_path in upload_dir.iterdir():
            if not file_path.is_file():
                continue
            
            filename = file_path.name
            
            # 如果文件在数据库中有记录，跳过
            if filename in db_filenames:
                continue
            
            # 检查文件年龄
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
            age_seconds = (now - file_mtime).total_seconds()
            
            if age_seconds > threshold_seconds:
                try:
                    file_size = file_path.stat().st_size
                    os.remove(file_path)
                    stats["orphan_files_deleted"] += 1
                    stats["bytes_freed"] += file_size
                except Exception as e:
                    print(f"[Cleanup] 删除孤立文件失败: {file_path}, 错误: {e}")
        
        return stats
    
    @classmethod
    async def run_cleanup(cls) -> dict:
        """执行一次完整清理"""
        print(f"[Cleanup] 开始清理任务 - {datetime.now()}")
        
        total_stats = {
            "submissions_cleaned": 0,
            "answers_deleted": 0,
            "files_deleted": 0,
            "orphan_files_deleted": 0,
            "bytes_freed": 0,
        }
        
        try:
            # 清理已审核的提交数据
            async with async_session_maker() as db:
                stats = await cls.cleanup_reviewed_submissions(db)
                for key, value in stats.items():
                    total_stats[key] = total_stats.get(key, 0) + value
            
            # 清理孤立文件
            orphan_stats = await cls.cleanup_orphan_files()
            total_stats["orphan_files_deleted"] = orphan_stats["orphan_files_deleted"]
            total_stats["bytes_freed"] += orphan_stats["bytes_freed"]
            
            # 格式化释放的空间
            bytes_freed = total_stats["bytes_freed"]
            if bytes_freed >= 1024 * 1024:
                freed_str = f"{bytes_freed / (1024 * 1024):.2f} MB"
            elif bytes_freed >= 1024:
                freed_str = f"{bytes_freed / 1024:.2f} KB"
            else:
                freed_str = f"{bytes_freed} bytes"
            
            print(f"[Cleanup] 清理完成:")
            print(f"  - 清理提交: {total_stats['submissions_cleaned']}")
            print(f"  - 删除答案: {total_stats['answers_deleted']}")
            print(f"  - 删除文件: {total_stats['files_deleted']}")
            print(f"  - 孤立文件: {total_stats['orphan_files_deleted']}")
            print(f"  - 释放空间: {freed_str}")
            
        except Exception as e:
            print(f"[Cleanup] 清理任务失败: {e}")
            import traceback
            traceback.print_exc()
        
        return total_stats
    
    @classmethod
    async def _cleanup_loop(cls):
        """后台清理循环 - 根据配置的间隔执行"""
        settings = get_settings()
        
        while cls._running:
            try:
                now = datetime.now()
                run_hour = settings.cleanup.run_hour
                interval_days = settings.cleanup.interval_days
                
                # 计算到下一个执行时间点的秒数
                next_run = now.replace(hour=run_hour, minute=0, second=0, microsecond=0)
                if now.hour >= run_hour:
                    # 如果已经过了今天的执行时间，等到下一个周期
                    from datetime import timedelta
                    next_run = next_run + timedelta(days=interval_days)
                
                wait_seconds = (next_run - now).total_seconds()
                print(f"[Cleanup] 清理间隔: {interval_days}天, 执行时间: {run_hour}:00")
                print(f"[Cleanup] 下次清理时间: {next_run}, 等待 {wait_seconds/3600:.1f} 小时")
                
                await asyncio.sleep(wait_seconds)
                
                if cls._running:
                    await cls.run_cleanup()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Cleanup] 清理循环错误: {e}")
                # 出错后等待 1 小时再重试
                await asyncio.sleep(3600)
    
    @classmethod
    def start_background_task(cls):
        """启动后台清理任务"""
        settings = get_settings()
        
        if not settings.cleanup.enabled:
            print("[Cleanup] 自动清理已禁用")
            return
        
        if cls._task is None or cls._task.done():
            cls._running = True
            cls._task = asyncio.create_task(cls._cleanup_loop())
            print(f"[Cleanup] 后台清理任务已启动 (间隔: {settings.cleanup.interval_days}天, 时间: {settings.cleanup.run_hour}:00)")
    
    @classmethod
    def stop_background_task(cls):
        """停止后台清理任务"""
        cls._running = False
        if cls._task and not cls._task.done():
            cls._task.cancel()
            print("[Cleanup] 后台清理任务已停止")

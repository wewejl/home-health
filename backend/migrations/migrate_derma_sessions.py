"""
迁移脚本：将 derma_sessions 表的数据迁移到 sessions 表

执行前请先备份数据库：
    pg_dump -U postgres home_health > backup_before_migration.sql

执行方式：
    cd backend
    python -m migrations.migrate_derma_sessions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models.session import Session as SessionModel
from app.models.derma_session import DermaSession
from app.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def migrate_derma_sessions(dry_run: bool = False):
    """
    将 derma_sessions 表的数据迁移到 sessions 表
    
    Args:
        dry_run: 如果为True，只打印迁移计划不实际执行
    """
    db = SessionLocal()
    
    try:
        # 获取所有皮肤科会话
        derma_sessions = db.query(DermaSession).all()
        logger.info(f"Found {len(derma_sessions)} derma sessions to migrate")
        
        if dry_run:
            logger.info("=== DRY RUN MODE - No changes will be made ===")
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for derma in derma_sessions:
            try:
                # 检查是否已迁移
                existing = db.query(SessionModel).filter(
                    SessionModel.id == derma.id
                ).first()
                
                if existing:
                    logger.debug(f"Session {derma.id} already exists, skipping")
                    skipped_count += 1
                    continue
                
                # 构建 agent_state JSON
                agent_state = {
                    "stage": derma.stage,
                    "progress": derma.progress,
                    "questions_asked": derma.questions_asked,
                    "chief_complaint": derma.chief_complaint,
                    "symptoms": derma.symptoms or [],
                    "symptom_details": derma.symptom_details or {},
                    "skin_location": derma.skin_location,
                    "duration": derma.duration,
                    "skin_analyses": derma.skin_analyses or [],
                    "latest_analysis": derma.latest_analysis,
                    "report_interpretations": derma.report_interpretations or [],
                    "latest_interpretation": derma.latest_interpretation,
                    "possible_conditions": derma.possible_conditions or [],
                    "risk_level": derma.risk_level or "low",
                    "care_advice": derma.care_advice,
                    "need_offline_visit": derma.need_offline_visit,
                    "current_task": derma.current_task,
                    "awaiting_image": derma.awaiting_image,
                    # 保留原始消息历史
                    "original_messages": derma.messages or []
                }
                
                # 确定会话状态
                status = "completed" if derma.stage == "completed" else "active"
                
                if dry_run:
                    logger.info(f"Would migrate: {derma.id} (user_id={derma.user_id}, stage={derma.stage})")
                else:
                    # 创建新的 Session 记录
                    new_session = SessionModel(
                        id=derma.id,
                        user_id=derma.user_id,
                        doctor_id=None,  # derma_sessions 没有 doctor_id
                        agent_type="dermatology",
                        agent_state=agent_state,
                        last_message=derma.current_response,
                        status=status,
                        created_at=derma.created_at,
                        updated_at=derma.updated_at
                    )
                    
                    db.add(new_session)
                
                migrated_count += 1
                
                # 每100条提交一次
                if not dry_run and migrated_count % 100 == 0:
                    db.commit()
                    logger.info(f"Progress: migrated {migrated_count} derma sessions")
                    
            except Exception as e:
                logger.error(f"Error migrating session {derma.id}: {e}")
                error_count += 1
                continue
        
        if not dry_run:
            db.commit()
        
        logger.info("=" * 50)
        logger.info("Migration Summary:")
        logger.info(f"  - Total found: {len(derma_sessions)}")
        logger.info(f"  - Migrated: {migrated_count}")
        logger.info(f"  - Skipped (already exists): {skipped_count}")
        logger.info(f"  - Errors: {error_count}")
        logger.info("=" * 50)
        
        return {
            "total": len(derma_sessions),
            "migrated": migrated_count,
            "skipped": skipped_count,
            "errors": error_count
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate derma_sessions to sessions table")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be migrated")
    args = parser.parse_args()
    
    migrate_derma_sessions(dry_run=args.dry_run)

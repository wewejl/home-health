"""
迁移脚本：将 diagnosis_sessions 表的数据迁移到 sessions 表

执行前请先备份数据库：
    pg_dump -U postgres home_health > backup_before_migration.sql

执行方式：
    cd backend
    python -m migrations.migrate_diagnosis_sessions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models.session import Session as SessionModel
from app.models.diagnosis_session import DiagnosisSession
from app.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def migrate_diagnosis_sessions(dry_run: bool = False):
    """
    将 diagnosis_sessions 表的数据迁移到 sessions 表
    
    Args:
        dry_run: 如果为True，只打印迁移计划不实际执行
    """
    db = SessionLocal()
    
    try:
        # 获取所有全科诊室会话
        diagnosis_sessions = db.query(DiagnosisSession).all()
        logger.info(f"Found {len(diagnosis_sessions)} diagnosis sessions to migrate")
        
        if dry_run:
            logger.info("=== DRY RUN MODE - No changes will be made ===")
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for diagnosis in diagnosis_sessions:
            try:
                # 检查是否已迁移
                existing = db.query(SessionModel).filter(
                    SessionModel.id == diagnosis.id
                ).first()
                
                if existing:
                    logger.debug(f"Session {diagnosis.id} already exists, skipping")
                    skipped_count += 1
                    continue
                
                # 构建 agent_state JSON
                agent_state = {
                    "stage": diagnosis.stage,
                    "progress": diagnosis.progress,
                    "questions_asked": diagnosis.questions_asked,
                    "chief_complaint": diagnosis.chief_complaint,
                    "symptoms": diagnosis.symptoms or [],
                    "symptom_details": diagnosis.symptom_details or {},
                    "possible_diseases": diagnosis.possible_diseases or [],
                    "risk_level": diagnosis.risk_level or "low",
                    "recommendations": diagnosis.recommendations or {},
                    "can_conclude": diagnosis.can_conclude,
                    "reasoning": diagnosis.reasoning,
                    # 保留原始消息历史
                    "original_messages": diagnosis.messages or []
                }
                
                # 确定会话状态
                status = "completed" if diagnosis.stage == "completed" else "active"
                
                if dry_run:
                    logger.info(f"Would migrate: {diagnosis.id} (user_id={diagnosis.user_id}, stage={diagnosis.stage})")
                else:
                    # 创建新的 Session 记录
                    new_session = SessionModel(
                        id=diagnosis.id,
                        user_id=diagnosis.user_id,
                        doctor_id=None,
                        agent_type="general",  # diagnosis 映射到 general
                        agent_state=agent_state,
                        last_message=diagnosis.current_question,
                        status=status,
                        created_at=diagnosis.created_at,
                        updated_at=diagnosis.updated_at
                    )
                    
                    db.add(new_session)
                
                migrated_count += 1
                
                # 每100条提交一次
                if not dry_run and migrated_count % 100 == 0:
                    db.commit()
                    logger.info(f"Progress: migrated {migrated_count} diagnosis sessions")
                    
            except Exception as e:
                logger.error(f"Error migrating session {diagnosis.id}: {e}")
                error_count += 1
                continue
        
        if not dry_run:
            db.commit()
        
        logger.info("=" * 50)
        logger.info("Migration Summary:")
        logger.info(f"  - Total found: {len(diagnosis_sessions)}")
        logger.info(f"  - Migrated: {migrated_count}")
        logger.info(f"  - Skipped (already exists): {skipped_count}")
        logger.info(f"  - Errors: {error_count}")
        logger.info("=" * 50)
        
        return {
            "total": len(diagnosis_sessions),
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
    
    parser = argparse.ArgumentParser(description="Migrate diagnosis_sessions to sessions table")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be migrated")
    args = parser.parse_args()
    
    migrate_diagnosis_sessions(dry_run=args.dry_run)

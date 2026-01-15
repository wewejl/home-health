"""
迁移脚本：将 derma_sessions 和 diagnosis_sessions 中的 messages JSON 字段迁移到 messages 表

执行前请先备份数据库：
    pg_dump -U postgres home_health > backup_before_migration.sql

执行方式：
    cd backend
    python -m migrations.migrate_messages
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlalchemy.orm import Session
from app.models.message import Message, SenderType
from app.models.derma_session import DermaSession
from app.models.diagnosis_session import DiagnosisSession
from app.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_timestamp(timestamp_str):
    """解析时间戳字符串"""
    if not timestamp_str:
        return None
    
    if isinstance(timestamp_str, datetime):
        return timestamp_str
    
    # 尝试多种格式
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse timestamp: {timestamp_str}")
    return None


def migrate_derma_messages(db, dry_run: bool = False):
    """
    将 derma_sessions.messages (JSON) 迁移到 messages 表
    """
    logger.info("Starting derma messages migration...")
    
    derma_sessions = db.query(DermaSession).all()
    migrated_count = 0
    skipped_count = 0
    
    for derma in derma_sessions:
        if not derma.messages:
            continue
        
        for idx, msg_data in enumerate(derma.messages):
            content = msg_data.get("content", "")
            if not content:
                continue
            
            timestamp = parse_timestamp(msg_data.get("timestamp"))
            
            # 检查是否已存在（基于 session_id + content + 序号近似判断）
            existing = db.query(Message).filter(
                Message.session_id == derma.id,
                Message.content == content
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # 确定发送者
            role = msg_data.get("role", "user")
            sender = SenderType.ai if role in ("assistant", "ai", "system") else SenderType.user
            
            # 消息类型
            task_type = msg_data.get("task_type", "text")
            message_type = "text"
            if task_type in ("skin_analysis", "analyze_skin"):
                message_type = "image"
            elif task_type == "report_interpret":
                message_type = "report"
            
            if dry_run:
                logger.debug(f"Would migrate message: {derma.id} - {content[:50]}...")
            else:
                message = Message(
                    session_id=derma.id,
                    sender=sender,
                    content=content,
                    message_type=message_type,
                    created_at=timestamp or derma.created_at
                )
                db.add(message)
            
            migrated_count += 1
        
        # 每处理10个会话提交一次
        if not dry_run and migrated_count > 0 and migrated_count % 500 == 0:
            db.commit()
            logger.info(f"Progress: migrated {migrated_count} derma messages")
    
    if not dry_run:
        db.commit()
    
    logger.info(f"Derma messages: migrated={migrated_count}, skipped={skipped_count}")
    return migrated_count, skipped_count


def migrate_diagnosis_messages(db, dry_run: bool = False):
    """
    将 diagnosis_sessions.messages (JSON) 迁移到 messages 表
    """
    logger.info("Starting diagnosis messages migration...")
    
    diagnosis_sessions = db.query(DiagnosisSession).all()
    migrated_count = 0
    skipped_count = 0
    
    for diagnosis in diagnosis_sessions:
        if not diagnosis.messages:
            continue
        
        for idx, msg_data in enumerate(diagnosis.messages):
            content = msg_data.get("content", "")
            if not content:
                continue
            
            timestamp = parse_timestamp(msg_data.get("timestamp"))
            
            # 检查是否已存在
            existing = db.query(Message).filter(
                Message.session_id == diagnosis.id,
                Message.content == content
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # 确定发送者
            role = msg_data.get("role", "user")
            sender = SenderType.ai if role in ("assistant", "ai", "system") else SenderType.user
            
            if dry_run:
                logger.debug(f"Would migrate message: {diagnosis.id} - {content[:50]}...")
            else:
                message = Message(
                    session_id=diagnosis.id,
                    sender=sender,
                    content=content,
                    message_type="text",
                    created_at=timestamp or diagnosis.created_at
                )
                db.add(message)
            
            migrated_count += 1
        
        # 每处理500条消息提交一次
        if not dry_run and migrated_count > 0 and migrated_count % 500 == 0:
            db.commit()
            logger.info(f"Progress: migrated {migrated_count} diagnosis messages")
    
    if not dry_run:
        db.commit()
    
    logger.info(f"Diagnosis messages: migrated={migrated_count}, skipped={skipped_count}")
    return migrated_count, skipped_count


def migrate_all_messages(dry_run: bool = False):
    """迁移所有消息"""
    db = SessionLocal()
    
    try:
        if dry_run:
            logger.info("=== DRY RUN MODE - No changes will be made ===")
        
        derma_migrated, derma_skipped = migrate_derma_messages(db, dry_run)
        diag_migrated, diag_skipped = migrate_diagnosis_messages(db, dry_run)
        
        logger.info("=" * 50)
        logger.info("Messages Migration Summary:")
        logger.info(f"  Derma messages - Migrated: {derma_migrated}, Skipped: {derma_skipped}")
        logger.info(f"  Diagnosis messages - Migrated: {diag_migrated}, Skipped: {diag_skipped}")
        logger.info(f"  Total - Migrated: {derma_migrated + diag_migrated}, Skipped: {derma_skipped + diag_skipped}")
        logger.info("=" * 50)
        
        return {
            "derma_migrated": derma_migrated,
            "derma_skipped": derma_skipped,
            "diagnosis_migrated": diag_migrated,
            "diagnosis_skipped": diag_skipped
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate messages from old session tables to messages table")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be migrated")
    args = parser.parse_args()
    
    migrate_all_messages(dry_run=args.dry_run)

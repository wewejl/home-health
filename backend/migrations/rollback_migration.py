"""
回滚脚本：回滚会话数据迁移

⚠️ 警告：此脚本会删除迁移的数据，请谨慎使用！

执行方式：
    cd backend
    python -m migrations.rollback_migration
    
    # 或者指定只回滚某类数据
    python -m migrations.rollback_migration --type derma
    python -m migrations.rollback_migration --type diagnosis
    python -m migrations.rollback_migration --type messages
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func
from app.models.session import Session as SessionModel
from app.models.message import Message
from app.models.derma_session import DermaSession
from app.models.diagnosis_session import DiagnosisSession
from app.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def rollback_derma_sessions(db, dry_run: bool = False):
    """
    回滚皮肤科会话迁移
    删除从 derma_sessions 迁移过来的 sessions 记录
    """
    logger.info("Rolling back derma sessions migration...")
    
    # 获取原始 derma_sessions 的 ID 列表
    derma_ids = [d.id for d in db.query(DermaSession.id).all()]
    
    if not derma_ids:
        logger.info("No derma sessions to rollback")
        return 0
    
    # 查找这些 ID 在 sessions 表中的记录
    sessions_to_delete = db.query(SessionModel).filter(
        SessionModel.id.in_(derma_ids)
    ).all()
    
    count = len(sessions_to_delete)
    logger.info(f"Found {count} sessions to rollback")
    
    if dry_run:
        logger.info(f"[DRY RUN] Would delete {count} sessions")
        return count
    
    for session in sessions_to_delete:
        db.delete(session)
    
    db.commit()
    logger.info(f"Rolled back {count} derma sessions")
    return count


def rollback_diagnosis_sessions(db, dry_run: bool = False):
    """
    回滚全科会话迁移
    删除从 diagnosis_sessions 迁移过来的 sessions 记录
    """
    logger.info("Rolling back diagnosis sessions migration...")
    
    # 获取原始 diagnosis_sessions 的 ID 列表
    diag_ids = [d.id for d in db.query(DiagnosisSession.id).all()]
    
    if not diag_ids:
        logger.info("No diagnosis sessions to rollback")
        return 0
    
    # 查找这些 ID 在 sessions 表中的记录
    sessions_to_delete = db.query(SessionModel).filter(
        SessionModel.id.in_(diag_ids)
    ).all()
    
    count = len(sessions_to_delete)
    logger.info(f"Found {count} sessions to rollback")
    
    if dry_run:
        logger.info(f"[DRY RUN] Would delete {count} sessions")
        return count
    
    for session in sessions_to_delete:
        db.delete(session)
    
    db.commit()
    logger.info(f"Rolled back {count} diagnosis sessions")
    return count


def rollback_messages(db, dry_run: bool = False):
    """
    回滚消息迁移
    删除从旧会话表迁移过来的消息
    """
    logger.info("Rolling back messages migration...")
    
    # 获取所有旧会话的 ID
    derma_ids = [d.id for d in db.query(DermaSession.id).all()]
    diag_ids = [d.id for d in db.query(DiagnosisSession.id).all()]
    old_session_ids = derma_ids + diag_ids
    
    if not old_session_ids:
        logger.info("No messages to rollback")
        return 0
    
    # 查找这些会话的消息
    messages_to_delete = db.query(Message).filter(
        Message.session_id.in_(old_session_ids)
    ).all()
    
    count = len(messages_to_delete)
    logger.info(f"Found {count} messages to rollback")
    
    if dry_run:
        logger.info(f"[DRY RUN] Would delete {count} messages")
        return count
    
    for msg in messages_to_delete:
        db.delete(msg)
    
    db.commit()
    logger.info(f"Rolled back {count} messages")
    return count


def rollback_all(dry_run: bool = False, rollback_type: str = None):
    """
    执行回滚
    
    Args:
        dry_run: 如果为True，只打印计划不实际执行
        rollback_type: 指定回滚类型 (derma, diagnosis, messages, 或 None 表示全部)
    """
    db = SessionLocal()
    
    try:
        if dry_run:
            logger.info("=== DRY RUN MODE - No changes will be made ===")
        
        results = {}
        
        if rollback_type is None or rollback_type == "messages":
            # 先回滚消息（因为有外键约束）
            results["messages"] = rollback_messages(db, dry_run)
        
        if rollback_type is None or rollback_type == "derma":
            results["derma"] = rollback_derma_sessions(db, dry_run)
        
        if rollback_type is None or rollback_type == "diagnosis":
            results["diagnosis"] = rollback_diagnosis_sessions(db, dry_run)
        
        logger.info("=" * 50)
        logger.info("Rollback Summary:")
        for key, count in results.items():
            logger.info(f"  {key}: {count} records")
        logger.info("=" * 50)
        
        return results
        
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def confirm_rollback():
    """确认回滚操作"""
    print("\n" + "=" * 60)
    print("⚠️  警告：此操作将删除已迁移的数据！")
    print("=" * 60)
    print("\n请确认您已经：")
    print("1. 备份了数据库")
    print("2. 确认需要回滚")
    print("3. 了解回滚的影响")
    print("\n")
    
    confirm = input("输入 'YES' 确认执行回滚: ")
    return confirm.strip().upper() == "YES"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Rollback session data migration")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be rolled back")
    parser.add_argument("--type", choices=["derma", "diagnosis", "messages"], 
                        help="Only rollback specific type")
    parser.add_argument("--force", action="store_true", help="Skip confirmation")
    args = parser.parse_args()
    
    if not args.dry_run and not args.force:
        if not confirm_rollback():
            print("回滚已取消")
            sys.exit(0)
    
    rollback_all(dry_run=args.dry_run, rollback_type=args.type)

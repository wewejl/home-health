"""
验证脚本：验证会话数据迁移的完整性

执行方式：
    cd backend
    python -m migrations.verify_migration
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


def verify_migration():
    """
    验证迁移数据完整性
    
    检查项:
    1. derma_sessions 中的所有记录都已迁移到 sessions
    2. diagnosis_sessions 中的所有记录都已迁移到 sessions
    3. agent_state 字段包含必要的数据
    4. 消息数量一致性检查
    """
    db = SessionLocal()
    
    try:
        results = {
            "derma_sessions": {"status": "unknown", "details": {}},
            "diagnosis_sessions": {"status": "unknown", "details": {}},
            "messages": {"status": "unknown", "details": {}},
            "overall": "unknown"
        }
        
        # ========== 1. 验证 derma_sessions 迁移 ==========
        logger.info("=" * 50)
        logger.info("Verifying derma_sessions migration...")
        
        derma_total = db.query(func.count(DermaSession.id)).scalar()
        derma_migrated = db.query(func.count(SessionModel.id)).filter(
            SessionModel.agent_type == "dermatology"
        ).scalar()
        
        # 检查每条 derma_session 是否都有对应的 session
        missing_derma = []
        derma_sessions = db.query(DermaSession).all()
        for derma in derma_sessions:
            exists = db.query(SessionModel).filter(SessionModel.id == derma.id).first()
            if not exists:
                missing_derma.append(derma.id)
        
        results["derma_sessions"] = {
            "status": "pass" if len(missing_derma) == 0 else "fail",
            "details": {
                "total_in_old_table": derma_total,
                "migrated_to_sessions": derma_migrated,
                "missing_count": len(missing_derma),
                "missing_ids": missing_derma[:10]  # 只显示前10个
            }
        }
        
        logger.info(f"  Old table count: {derma_total}")
        logger.info(f"  Migrated count: {derma_migrated}")
        logger.info(f"  Missing: {len(missing_derma)}")
        
        # ========== 2. 验证 diagnosis_sessions 迁移 ==========
        logger.info("=" * 50)
        logger.info("Verifying diagnosis_sessions migration...")
        
        diag_total = db.query(func.count(DiagnosisSession.id)).scalar()
        diag_migrated = db.query(func.count(SessionModel.id)).filter(
            SessionModel.agent_type == "general"
        ).scalar()
        
        missing_diag = []
        diagnosis_sessions = db.query(DiagnosisSession).all()
        for diag in diagnosis_sessions:
            exists = db.query(SessionModel).filter(SessionModel.id == diag.id).first()
            if not exists:
                missing_diag.append(diag.id)
        
        results["diagnosis_sessions"] = {
            "status": "pass" if len(missing_diag) == 0 else "fail",
            "details": {
                "total_in_old_table": diag_total,
                "migrated_to_sessions": diag_migrated,
                "missing_count": len(missing_diag),
                "missing_ids": missing_diag[:10]
            }
        }
        
        logger.info(f"  Old table count: {diag_total}")
        logger.info(f"  Migrated count: {diag_migrated}")
        logger.info(f"  Missing: {len(missing_diag)}")
        
        # ========== 3. 验证 agent_state 数据完整性 ==========
        logger.info("=" * 50)
        logger.info("Verifying agent_state data integrity...")
        
        sessions_with_state = db.query(func.count(SessionModel.id)).filter(
            SessionModel.agent_state.isnot(None)
        ).scalar()
        
        sessions_total = db.query(func.count(SessionModel.id)).scalar()
        
        # 抽样检查 agent_state 内容
        sample_sessions = db.query(SessionModel).limit(10).all()
        state_issues = []
        for session in sample_sessions:
            state = session.agent_state or {}
            if session.agent_type == "dermatology":
                # 皮肤科应该有的字段
                if "chief_complaint" not in state and "symptoms" not in state:
                    state_issues.append(f"{session.id}: missing key fields")
        
        logger.info(f"  Total sessions: {sessions_total}")
        logger.info(f"  Sessions with agent_state: {sessions_with_state}")
        logger.info(f"  State issues found: {len(state_issues)}")
        
        # ========== 4. 验证消息迁移 ==========
        logger.info("=" * 50)
        logger.info("Verifying messages migration...")
        
        messages_total = db.query(func.count(Message.id)).scalar()
        
        # 计算原始消息数
        original_derma_msg_count = 0
        for derma in derma_sessions:
            if derma.messages:
                original_derma_msg_count += len(derma.messages)
        
        original_diag_msg_count = 0
        for diag in diagnosis_sessions:
            if diag.messages:
                original_diag_msg_count += len(diag.messages)
        
        original_total = original_derma_msg_count + original_diag_msg_count
        
        results["messages"] = {
            "status": "pass" if messages_total >= original_total * 0.9 else "warning",  # 允许10%的误差
            "details": {
                "original_derma_messages": original_derma_msg_count,
                "original_diagnosis_messages": original_diag_msg_count,
                "original_total": original_total,
                "migrated_messages": messages_total
            }
        }
        
        logger.info(f"  Original derma messages: {original_derma_msg_count}")
        logger.info(f"  Original diagnosis messages: {original_diag_msg_count}")
        logger.info(f"  Messages in messages table: {messages_total}")
        
        # ========== 汇总结果 ==========
        logger.info("=" * 50)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 50)
        
        all_passed = all(
            r["status"] in ["pass", "warning"] 
            for r in [results["derma_sessions"], results["diagnosis_sessions"], results["messages"]]
        )
        
        results["overall"] = "pass" if all_passed else "fail"
        
        for key, value in results.items():
            if key == "overall":
                logger.info(f"\n{'='*20} OVERALL: {value.upper()} {'='*20}")
            else:
                status = value.get("status", "unknown")
                icon = "✅" if status == "pass" else ("⚠️" if status == "warning" else "❌")
                logger.info(f"{icon} {key}: {status}")
        
        return results
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        raise
    finally:
        db.close()


def check_session_data_quality():
    """
    检查会话数据质量
    """
    db = SessionLocal()
    
    try:
        logger.info("=" * 50)
        logger.info("Checking session data quality...")
        
        # 统计各类型会话
        type_counts = db.query(
            SessionModel.agent_type, 
            func.count(SessionModel.id)
        ).group_by(SessionModel.agent_type).all()
        
        logger.info("\nSession types distribution:")
        for agent_type, count in type_counts:
            logger.info(f"  {agent_type}: {count}")
        
        # 检查有数据的会话
        sessions_with_messages = db.query(func.count(SessionModel.id)).join(
            Message, Message.session_id == SessionModel.id
        ).scalar()
        
        logger.info(f"\nSessions with messages: {sessions_with_messages}")
        
        # 检查空状态的会话
        sessions_without_state = db.query(func.count(SessionModel.id)).filter(
            SessionModel.agent_state == None
        ).scalar()
        
        logger.info(f"Sessions without agent_state: {sessions_without_state}")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify session data migration")
    parser.add_argument("--quality", action="store_true", help="Also run data quality check")
    args = parser.parse_args()
    
    results = verify_migration()
    
    if args.quality:
        check_session_data_quality()
    
    # 返回退出码
    sys.exit(0 if results["overall"] == "pass" else 1)

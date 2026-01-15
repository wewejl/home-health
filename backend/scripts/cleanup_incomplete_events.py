#!/usr/bin/env python3
"""
清理数据库中的不完整病历事件和测试数据

清理规则：
1. 删除 sessions 字段为空或消息数为0的病历事件
2. 删除主诉为空且症状为空的病历事件
3. 删除旧的测试会话（derma_sessions, diagnosis_sessions）
4. 可选：删除所有测试数据重新开始

使用方法：
    python scripts/cleanup_incomplete_events.py --dry-run  # 预览将删除的数据
    python scripts/cleanup_incomplete_events.py            # 执行清理
    python scripts/cleanup_incomplete_events.py --full     # 完全清理（包括所有会话和事件）
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
from sqlalchemy import func
from app.database import SessionLocal
from app.models.medical_event import MedicalEvent
from app.models.session import Session
from app.models.derma_session import DermaSession
from app.models.diagnosis_session import DiagnosisSession
from app.models.message import Message


def cleanup_incomplete_events(db, dry_run=True):
    """清理不完整的病历事件"""
    print("\n=== 清理不完整的病历事件 ===\n")
    
    # 1. 查找 sessions 字段为空的事件
    # PostgreSQL需要使用cast来比较JSON
    from sqlalchemy import cast, Text
    empty_sessions = db.query(MedicalEvent).filter(
        (MedicalEvent.sessions == None) | (cast(MedicalEvent.sessions, Text) == '[]')
    ).all()
    
    print(f"找到 {len(empty_sessions)} 个 sessions 字段为空的事件:")
    for event in empty_sessions[:5]:
        print(f"  - 事件 {event.id}: {event.title} (创建于 {event.created_at})")
    if len(empty_sessions) > 5:
        print(f"  ... 还有 {len(empty_sessions) - 5} 个")
    
    # 2. 查找主诉和症状都为空的事件
    incomplete_events = db.query(MedicalEvent).filter(
        (MedicalEvent.chief_complaint == None) | (MedicalEvent.chief_complaint == "")
    ).all()
    
    # 进一步筛选：检查 sessions 中是否有有效数据
    truly_incomplete = []
    for event in incomplete_events:
        if not event.sessions:
            truly_incomplete.append(event)
            continue
        
        # 检查所有会话是否都没有主诉和消息
        has_valid_data = False
        for sess in event.sessions:
            if sess.get("chief_complaint") or sess.get("message_count", 0) > 2:
                has_valid_data = True
                break
        
        if not has_valid_data:
            truly_incomplete.append(event)
    
    print(f"\n找到 {len(truly_incomplete)} 个真正不完整的事件（无主诉且无有效会话数据）:")
    for event in truly_incomplete[:5]:
        print(f"  - 事件 {event.id}: {event.title}")
        if event.sessions:
            for sess in event.sessions[:2]:
                print(f"    会话 {sess.get('session_id', 'unknown')[:8]}: 消息数={sess.get('message_count', 0)}")
    if len(truly_incomplete) > 5:
        print(f"  ... 还有 {len(truly_incomplete) - 5} 个")
    
    # 合并去重
    to_delete = set([e.id for e in empty_sessions] + [e.id for e in truly_incomplete])
    
    if not dry_run:
        deleted_count = 0
        for event_id in to_delete:
            event = db.query(MedicalEvent).filter(MedicalEvent.id == event_id).first()
            if event:
                db.delete(event)
                deleted_count += 1
        
        db.commit()
        print(f"\n✅ 已删除 {deleted_count} 个不完整的病历事件")
    else:
        print(f"\n[预览模式] 将删除 {len(to_delete)} 个不完整的病历事件")
    
    return len(to_delete)


def cleanup_old_sessions(db, dry_run=True):
    """清理旧的专用会话表数据"""
    print("\n=== 清理旧的专用会话表 ===\n")
    
    derma_count = db.query(DermaSession).count()
    diagnosis_count = db.query(DiagnosisSession).count()
    
    print(f"找到 {derma_count} 条 derma_sessions 记录")
    print(f"找到 {diagnosis_count} 条 diagnosis_sessions 记录")
    
    if not dry_run:
        db.query(DermaSession).delete()
        db.query(DiagnosisSession).delete()
        db.commit()
        print(f"\n✅ 已删除所有旧会话表数据")
    else:
        print(f"\n[预览模式] 将删除 {derma_count + diagnosis_count} 条旧会话记录")
    
    return derma_count + diagnosis_count


def cleanup_orphan_messages(db, dry_run=True):
    """清理孤儿消息（会话已删除但消息还在）"""
    print("\n=== 清理孤儿消息 ===\n")
    
    # 查找所有消息的 session_id
    all_message_sessions = db.query(Message.session_id).distinct().all()
    message_session_ids = set([s[0] for s in all_message_sessions])
    
    # 查找所有有效的 session_id
    valid_sessions = db.query(Session.id).all()
    valid_session_ids = set([s[0] for s in valid_sessions])
    
    # 找出孤儿会话ID
    orphan_session_ids = message_session_ids - valid_session_ids
    
    if orphan_session_ids:
        orphan_count = db.query(Message).filter(
            Message.session_id.in_(orphan_session_ids)
        ).count()
        
        print(f"找到 {len(orphan_session_ids)} 个孤儿会话，共 {orphan_count} 条消息")
        
        if not dry_run:
            db.query(Message).filter(
                Message.session_id.in_(orphan_session_ids)
            ).delete(synchronize_session=False)
            db.commit()
            print(f"\n✅ 已删除 {orphan_count} 条孤儿消息")
        else:
            print(f"\n[预览模式] 将删除 {orphan_count} 条孤儿消息")
        
        return orphan_count
    else:
        print("未找到孤儿消息")
        return 0


def full_cleanup(db, dry_run=True):
    """完全清理：删除所有会话、消息和病历事件"""
    from app.models.medical_event import EventAttachment, EventNote, ExportRecord, ExportAccessLog
    
    print("\n=== ⚠️  完全清理模式 ===\n")
    
    session_count = db.query(Session).count()
    message_count = db.query(Message).count()
    event_count = db.query(MedicalEvent).count()
    attachment_count = db.query(EventAttachment).count()
    note_count = db.query(EventNote).count()
    export_count = db.query(ExportRecord).count()
    access_log_count = db.query(ExportAccessLog).count()
    
    print(f"将删除:")
    print(f"  - {session_count} 个会话")
    print(f"  - {message_count} 条消息")
    print(f"  - {event_count} 个病历事件")
    print(f"  - {attachment_count} 个附件")
    print(f"  - {note_count} 条备注")
    print(f"  - {export_count} 个导出记录")
    print(f"  - {access_log_count} 条访问日志")
    
    if not dry_run:
        # 按顺序删除（考虑外键约束，从最深层开始）
        try:
            db.query(ExportAccessLog).delete()
            db.query(ExportRecord).delete()
            db.query(EventNote).delete()
            db.query(EventAttachment).delete()
            db.query(Message).delete()
            db.query(Session).delete()
            db.query(MedicalEvent).delete()
            db.query(DermaSession).delete()
            db.query(DiagnosisSession).delete()
            db.commit()
            print(f"\n✅ 已完全清理数据库")
        except Exception as e:
            db.rollback()
            print(f"\n❌ 清理失败，已回滚: {e}")
            raise
    else:
        print(f"\n[预览模式] 使用 --full 参数且不带 --dry-run 来执行完全清理")
    
    return session_count + message_count + event_count


def show_statistics(db):
    """显示数据库统计信息"""
    print("\n=== 数据库统计 ===\n")
    
    # 统一会话表
    sessions = db.query(Session.agent_type, func.count(Session.id)).group_by(Session.agent_type).all()
    print("统一会话表 (sessions):")
    total_sessions = 0
    for agent_type, count in sessions:
        print(f"  - {agent_type:15}: {count} 条")
        total_sessions += count
    print(f"  总计: {total_sessions} 条\n")
    
    # 消息表
    message_count = db.query(Message).count()
    print(f"消息表 (messages): {message_count} 条\n")
    
    # 病历事件表
    events = db.query(MedicalEvent.agent_type, func.count(MedicalEvent.id)).group_by(MedicalEvent.agent_type).all()
    print("病历事件表 (medical_events):")
    total_events = 0
    for agent_type, count in events:
        print(f"  - {agent_type.value if agent_type else 'None':15}: {count} 条")
        total_events += count
    print(f"  总计: {total_events} 条\n")
    
    # 旧表
    derma_count = db.query(DermaSession).count()
    diagnosis_count = db.query(DiagnosisSession).count()
    print(f"旧会话表:")
    print(f"  - derma_sessions: {derma_count} 条")
    print(f"  - diagnosis_sessions: {diagnosis_count} 条")


def main():
    parser = argparse.ArgumentParser(description='清理数据库中的不完整数据')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际删除数据')
    parser.add_argument('--full', action='store_true', help='完全清理所有数据（危险操作）')
    parser.add_argument('--stats', action='store_true', help='只显示统计信息')
    
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        # 显示统计信息
        show_statistics(db)
        
        if args.stats:
            return
        
        if args.full:
            if args.dry_run:
                full_cleanup(db, dry_run=True)
            else:
                confirm = input("\n⚠️  确认要删除所有数据吗？这个操作不可恢复！输入 'YES' 确认: ")
                if confirm == "YES":
                    full_cleanup(db, dry_run=False)
                else:
                    print("已取消操作")
        else:
            # 常规清理
            total_deleted = 0
            total_deleted += cleanup_incomplete_events(db, dry_run=args.dry_run)
            total_deleted += cleanup_old_sessions(db, dry_run=args.dry_run)
            total_deleted += cleanup_orphan_messages(db, dry_run=args.dry_run)
            
            print(f"\n{'[预览]' if args.dry_run else ''} 总计处理 {total_deleted} 条记录")
            
            if args.dry_run:
                print("\n提示: 使用不带 --dry-run 参数来执行实际清理")
        
        # 清理后显示统计
        if not args.dry_run and not args.stats:
            print("\n清理后的统计:")
            show_statistics(db)
            
    finally:
        db.close()


if __name__ == "__main__":
    main()

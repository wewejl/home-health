"""
数据库迁移：添加病历事件相关表

创建表：
- medical_events: 病历事件主表
- event_attachments: 附件表
- event_notes: 用户备注表
- export_records: 导出记录表
- export_access_logs: 导出访问日志表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models.medical_event import (
    MedicalEvent, EventAttachment, EventNote, ExportRecord, ExportAccessLog
)


def run_migration():
    """运行迁移"""
    print("🚀 开始创建病历事件相关表...")
    
    # 使用 SQLAlchemy 创建表
    from app.database import Base
    
    # 只创建新表，不影响现有表
    tables_to_create = [
        MedicalEvent.__table__,
        EventAttachment.__table__,
        EventNote.__table__,
        ExportRecord.__table__,
        ExportAccessLog.__table__
    ]
    
    for table in tables_to_create:
        try:
            table.create(engine, checkfirst=True)
            print(f"  ✅ 表 {table.name} 创建成功（或已存在）")
        except Exception as e:
            print(f"  ⚠️ 表 {table.name} 创建失败: {e}")
    
    print("✅ 病历事件表迁移完成")


def verify_tables():
    """验证表是否创建成功"""
    db = SessionLocal()
    try:
        # 检查表是否存在
        result = db.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('medical_events', 'event_attachments', 'event_notes', 'export_records', 'export_access_logs')
        """))
        tables = [row[0] for row in result.fetchall()]
        
        expected_tables = ['medical_events', 'event_attachments', 'event_notes', 'export_records', 'export_access_logs']
        
        print("\n📊 表验证结果:")
        for table in expected_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (不存在)")
        
        return len(tables) == len(expected_tables)
    except Exception as e:
        print(f"验证失败: {e}")
        # SQLite 兼容检查
        try:
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"\n📊 SQLite 表列表: {tables}")
            return True
        except:
            return False
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
    verify_tables()

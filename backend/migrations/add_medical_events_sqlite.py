"""
数据库迁移：添加病历事件相关表 (SQLite)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)


def upgrade():
    """创建病历事件相关表"""
    with engine.connect() as conn:
        # 创建 medical_events 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS medical_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                department VARCHAR(50) NOT NULL,
                agent_type VARCHAR(20) DEFAULT 'general',
                status VARCHAR(20) DEFAULT 'active',
                chief_complaint TEXT,
                summary TEXT,
                risk_level VARCHAR(20) DEFAULT 'low',
                ai_analysis TEXT,
                sessions TEXT,
                session_count INTEGER DEFAULT 0,
                attachment_count INTEGER DEFAULT 0,
                export_count INTEGER DEFAULT 0,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_medical_events_user_id ON medical_events(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_medical_events_status ON medical_events(status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_medical_events_department ON medical_events(department)"))
        
        # 创建 event_attachments 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS event_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                type VARCHAR(20) NOT NULL,
                url VARCHAR(500) NOT NULL,
                thumbnail_url VARCHAR(500),
                filename VARCHAR(255),
                file_size INTEGER,
                mime_type VARCHAR(100),
                file_metadata TEXT,
                description TEXT,
                is_important BOOLEAN DEFAULT 0,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES medical_events(id) ON DELETE CASCADE
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_event_attachments_event_id ON event_attachments(event_id)"))
        
        # 创建 event_notes 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS event_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                is_important BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES medical_events(id) ON DELETE CASCADE
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_event_notes_event_id ON event_notes(event_id)"))
        
        # 创建 export_records 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS export_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                user_id INTEGER NOT NULL,
                export_type VARCHAR(20) DEFAULT 'pdf',
                event_ids TEXT,
                export_options TEXT,
                file_url VARCHAR(500),
                share_token VARCHAR(100) UNIQUE,
                share_password VARCHAR(100),
                expires_at TIMESTAMP,
                max_views INTEGER,
                view_count INTEGER DEFAULT 0,
                last_viewed_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES medical_events(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_export_records_user_id ON export_records(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_export_records_share_token ON export_records(share_token)"))
        
        # 创建 export_access_logs 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS export_access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                export_id INTEGER NOT NULL,
                ip_address VARCHAR(50),
                user_agent VARCHAR(500),
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (export_id) REFERENCES export_records(id) ON DELETE CASCADE
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_export_access_logs_export_id ON export_access_logs(export_id)"))
        
        conn.commit()
        print("✅ Migration completed: medical_events tables created")


def downgrade():
    """删除病历事件相关表"""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS export_access_logs"))
        conn.execute(text("DROP TABLE IF EXISTS export_records"))
        conn.execute(text("DROP TABLE IF EXISTS event_notes"))
        conn.execute(text("DROP TABLE IF EXISTS event_attachments"))
        conn.execute(text("DROP TABLE IF EXISTS medical_events"))
        conn.commit()
        print("✅ Rollback completed: medical_events tables dropped")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--downgrade", action="store_true", help="Rollback migration")
    args = parser.parse_args()
    
    if args.downgrade:
        downgrade()
    else:
        upgrade()

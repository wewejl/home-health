"""
添加 records_analyzed 字段到 Doctor 模型

运行方式：
    python migrations/add_records_analyzed_field.py
"""
import sqlite3
import os
from pathlib import Path


def migrate_sqlite(db_path: str = "app.db"):
    """为 SQLite 数据库添加 records_analyzed 字段"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(doctors)")
        columns = [col[1] for col in cursor.fetchall()]

        if "records_analyzed" in columns:
            print("字段 records_analyzed 已存在，跳过迁移")
            return True

        # 添加字段
        cursor.execute("""
            ALTER TABLE doctors
            ADD COLUMN records_analyzed BOOLEAN DEFAULT 0
        """)

        conn.commit()
        print("✅ 成功添加 records_analyzed 字段到 doctors 表")
        return True

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    # 获取数据库路径
    backend_dir = Path(__file__).parent.parent
    db_path = backend_dir / "app.db"

    print(f"开始迁移数据库: {db_path}")
    migrate_sqlite(str(db_path))

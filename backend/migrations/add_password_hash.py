"""
数据库迁移脚本：添加 password_hash 字段到 users 表
运行方式: python -m migrations.add_password_hash
"""
import sqlite3
import os

def migrate():
    """添加 password_hash 列到 users 表"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.db")
    
    if not os.path.exists(db_path):
        print(f"[Migration] 数据库文件不存在: {db_path}")
        print("[Migration] 跳过迁移，新建数据库时会自动包含此字段")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "password_hash" in columns:
            print("[Migration] password_hash 列已存在，跳过迁移")
            return
        
        # 添加列
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
        conn.commit()
        print("[Migration] ✅ 成功添加 password_hash 列到 users 表")
        
    except Exception as e:
        print(f"[Migration] ❌ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()

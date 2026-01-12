"""
数据库迁移脚本 - 用户表新增字段

运行方式:
    cd backend
    source venv/bin/activate
    python migrate_user_table.py

注意: 
    - 此脚本用于 SQLite 数据库
    - 执行前请备份数据库文件 app.db
    - 如果使用 PostgreSQL/MySQL，请使用 Alembic 进行迁移
"""
import sqlite3
import os

DATABASE_PATH = "./app.db"

MIGRATIONS = [
    # 添加 avatar_url 字段
    ("avatar_url", "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)"),
    # 添加 gender 字段
    ("gender", "ALTER TABLE users ADD COLUMN gender VARCHAR(10)"),
    # 添加 birthday 字段
    ("birthday", "ALTER TABLE users ADD COLUMN birthday DATE"),
    # 添加紧急联系人字段
    ("emergency_contact_name", "ALTER TABLE users ADD COLUMN emergency_contact_name VARCHAR(50)"),
    ("emergency_contact_phone", "ALTER TABLE users ADD COLUMN emergency_contact_phone VARCHAR(20)"),
    ("emergency_contact_relation", "ALTER TABLE users ADD COLUMN emergency_contact_relation VARCHAR(20)"),
    # 添加状态字段
    ("is_profile_completed", "ALTER TABLE users ADD COLUMN is_profile_completed BOOLEAN DEFAULT 0"),
    ("is_active", "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"),
    # 添加 updated_at 字段 (SQLite不支持非常量默认值，所以不设默认值)
    ("updated_at", "ALTER TABLE users ADD COLUMN updated_at TIMESTAMP"),
]


def get_existing_columns(cursor):
    """获取表中已存在的列名"""
    cursor.execute("PRAGMA table_info(users)")
    return [row[1] for row in cursor.fetchall()]


def run_migrations():
    """执行数据库迁移"""
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ 数据库文件不存在: {DATABASE_PATH}")
        print("   请先启动后端服务创建数据库，或检查路径是否正确")
        return False
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        existing_columns = get_existing_columns(cursor)
        print(f"📋 现有列: {existing_columns}")
        
        migrated_count = 0
        skipped_count = 0
        
        for column_name, sql in MIGRATIONS:
            if column_name in existing_columns:
                print(f"⏭️  跳过: {column_name} (已存在)")
                skipped_count += 1
            else:
                try:
                    cursor.execute(sql)
                    print(f"✅ 添加: {column_name}")
                    migrated_count += 1
                except sqlite3.OperationalError as e:
                    print(f"❌ 失败: {column_name} - {e}")
        
        conn.commit()
        
        print(f"\n📊 迁移完成: {migrated_count} 个新增, {skipped_count} 个跳过")
        
        # 显示最终表结构
        print("\n📋 最终表结构:")
        cursor.execute("PRAGMA table_info(users)")
        for row in cursor.fetchall():
            print(f"   - {row[1]}: {row[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("🚀 开始用户表迁移...\n")
    success = run_migrations()
    if success:
        print("\n✅ 迁移成功完成!")
    else:
        print("\n❌ 迁移失败，请检查错误信息")

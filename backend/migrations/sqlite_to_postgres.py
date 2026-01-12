"""
SQLite 到 PostgreSQL 数据迁移脚本
运行方式: python -m migrations.sqlite_to_postgres
"""
import os
import sys
import sqlite3
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PostgreSQL 连接配置
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "xinlin_prod",
    "user": "xinlin_prod",
    "password": "wszxy123"
}

# SQLite 数据库路径
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.db")

# 表迁移顺序（考虑外键依赖）
TABLE_ORDER = [
    "departments",
    "users",
    "admin_users",
    "doctors",
    "drug_categories",
    "drugs",
    "drug_category_association",
    "diseases",
    "knowledge_bases",
    "knowledge_documents",
    "sessions",
    "messages",
    "session_feedbacks",
    "diagnosis_sessions",
    "derma_sessions",
    "audit_logs",
]


def get_sqlite_connection():
    """获取 SQLite 连接"""
    if not os.path.exists(SQLITE_DB_PATH):
        raise FileNotFoundError(f"SQLite 数据库不存在: {SQLITE_DB_PATH}")
    return sqlite3.connect(SQLITE_DB_PATH)


def get_pg_connection():
    """获取 PostgreSQL 连接"""
    import psycopg
    conn_str = f"host={PG_CONFIG['host']} port={PG_CONFIG['port']} dbname={PG_CONFIG['database']} user={PG_CONFIG['user']} password={PG_CONFIG['password']}"
    return psycopg.connect(conn_str)


def get_table_columns(sqlite_conn, table_name):
    """获取表的列信息"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [(col[1], col[2]) for col in cursor.fetchall()]


def get_table_data(sqlite_conn, table_name):
    """获取表的所有数据"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return columns, rows


def convert_value(value, col_type):
    """转换值为 PostgreSQL 兼容格式"""
    if value is None:
        return None
    
    col_type_upper = col_type.upper()
    
    # JSON 类型 - 使用 psycopg 的 Json 适配器
    if "JSON" in col_type_upper:
        from psycopg.types.json import Json
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return Json(parsed)
            except:
                return Json(value)
        return Json(value)
    
    # BOOLEAN 类型
    if "BOOLEAN" in col_type_upper or "BOOL" in col_type_upper:
        if isinstance(value, int):
            return bool(value)
        return value
    
    return value


def create_pg_schema(pg_conn):
    """在 PostgreSQL 中创建 schema（使用 SQLAlchemy 模型）"""
    print("[迁移] 创建 PostgreSQL schema...")
    
    # 使用 SQLAlchemy 创建表
    from app.database import Base, engine
    from sqlalchemy import create_engine
    
    # 创建 PostgreSQL engine
    pg_url = f"postgresql+psycopg://{PG_CONFIG['user']}:{PG_CONFIG['password']}@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}"
    pg_engine = create_engine(pg_url)
    
    # 导入所有模型
    from app.models import (
        User, Department, Doctor, Session, Message, 
        KnowledgeBase, KnowledgeDocument, AdminUser, AuditLog,
        SessionFeedback, Disease, Drug, DrugCategory, 
        DiagnosisSession, DermaSession
    )
    
    # 创建所有表
    Base.metadata.create_all(bind=pg_engine)
    print("[迁移] ✅ PostgreSQL schema 创建完成")
    
    return pg_engine


def migrate_table(sqlite_conn, pg_conn, table_name, columns_info):
    """迁移单个表的数据"""
    columns, rows = get_table_data(sqlite_conn, table_name)
    
    if not rows:
        print(f"[迁移] {table_name}: 无数据，跳过")
        return 0
    
    # 构建列类型映射
    col_types = {col[0]: col[1] for col in columns_info}
    
    # 构建插入语句
    placeholders = ", ".join(["%s"] * len(columns))
    columns_str = ", ".join([f'"{col}"' for col in columns])
    insert_sql = f'INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
    
    cursor = pg_conn.cursor()
    success_count = 0
    
    for row in rows:
        # 转换每个值
        converted_row = []
        for i, value in enumerate(row):
            col_name = columns[i]
            col_type = col_types.get(col_name, "TEXT")
            converted_row.append(convert_value(value, col_type))
        
        try:
            cursor.execute(insert_sql, converted_row)
            success_count += 1
        except Exception as e:
            print(f"[迁移] {table_name} 插入失败: {e}")
            print(f"  数据: {converted_row[:3]}...")  # 只打印前3个字段
    
    pg_conn.commit()
    print(f"[迁移] {table_name}: 迁移 {success_count}/{len(rows)} 条记录")
    return success_count


def reset_sequences(pg_conn):
    """重置 PostgreSQL 序列（自增ID）"""
    print("[迁移] 重置序列...")
    cursor = pg_conn.cursor()
    
    # 需要重置序列的表
    tables_with_serial = [
        "users", "departments", "doctors", "messages", 
        "admin_users", "audit_logs", "session_feedbacks",
        "diseases", "drugs", "drug_categories", "knowledge_documents"
    ]
    
    for table in tables_with_serial:
        try:
            cursor.execute(f"""
                SELECT setval(pg_get_serial_sequence('{table}', 'id'), 
                       COALESCE((SELECT MAX(id) FROM {table}), 1), true)
            """)
        except Exception as e:
            print(f"[迁移] 重置 {table} 序列失败: {e}")
    
    pg_conn.commit()
    print("[迁移] ✅ 序列重置完成")


def verify_migration(sqlite_conn, pg_conn):
    """验证迁移数据一致性"""
    print("\n[验证] 开始数据一致性校验...")
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    all_passed = True
    results = []
    
    for table in TABLE_ORDER:
        try:
            # SQLite 计数
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            # PostgreSQL 计数
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cursor.fetchone()[0]
            
            status = "✅" if sqlite_count == pg_count else "❌"
            if sqlite_count != pg_count:
                all_passed = False
            
            results.append((table, sqlite_count, pg_count, status))
            
        except Exception as e:
            results.append((table, "?", "?", f"❌ {e}"))
            all_passed = False
    
    # 打印结果表格
    print("\n" + "=" * 60)
    print(f"{'表名':<30} {'SQLite':<10} {'PostgreSQL':<10} {'状态'}")
    print("=" * 60)
    for table, s_count, p_count, status in results:
        print(f"{table:<30} {str(s_count):<10} {str(p_count):<10} {status}")
    print("=" * 60)
    
    if all_passed:
        print("\n[验证] ✅ 所有表数据一致性校验通过！")
    else:
        print("\n[验证] ❌ 部分表数据不一致，请检查！")
    
    return all_passed


def backup_sqlite():
    """备份 SQLite 数据库"""
    backup_path = SQLITE_DB_PATH + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(SQLITE_DB_PATH, backup_path)
    print(f"[备份] SQLite 数据库已备份到: {backup_path}")
    return backup_path


def main():
    """主迁移流程"""
    print("=" * 60)
    print("  SQLite -> PostgreSQL 数据迁移工具")
    print("  鑫琳医生项目 v1.0")
    print("=" * 60)
    print()
    
    # 1. 备份 SQLite
    print("[阶段 1] 备份源数据库")
    backup_path = backup_sqlite()
    
    # 2. 连接数据库
    print("\n[阶段 2] 连接数据库")
    sqlite_conn = get_sqlite_connection()
    print(f"[连接] SQLite: {SQLITE_DB_PATH}")
    
    pg_conn = get_pg_connection()
    print(f"[连接] PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}")
    
    # 3. 创建 PostgreSQL schema
    print("\n[阶段 3] 创建 PostgreSQL schema")
    create_pg_schema(pg_conn)
    
    # 4. 迁移数据
    print("\n[阶段 4] 迁移数据")
    total_migrated = 0
    for table in TABLE_ORDER:
        columns_info = get_table_columns(sqlite_conn, table)
        count = migrate_table(sqlite_conn, pg_conn, table, columns_info)
        total_migrated += count
    
    print(f"\n[迁移] 总计迁移 {total_migrated} 条记录")
    
    # 5. 重置序列
    print("\n[阶段 5] 重置序列")
    reset_sequences(pg_conn)
    
    # 6. 验证
    print("\n[阶段 6] 验证数据一致性")
    verify_migration(sqlite_conn, pg_conn)
    
    # 关闭连接
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n" + "=" * 60)
    print("  迁移完成！")
    print("=" * 60)
    print(f"\n下一步操作:")
    print(f"1. 更新 .env 文件中的 DATABASE_URL")
    print(f"2. 重启应用服务")
    print(f"3. 运行验证脚本确认功能正常")
    print(f"\n如需回滚，使用备份文件: {backup_path}")


if __name__ == "__main__":
    main()

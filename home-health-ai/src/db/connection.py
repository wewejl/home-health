#!/usr/bin/env python3
"""
PostgreSQL 数据库连接管理
"""

import psycopg
from config.settings import DATABASE_URL

def get_connection():
    """获取数据库连接"""
    return psycopg.connect(DATABASE_URL)

def test_connection():
    """测试数据库连接"""
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 测试查询
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]

        # 查看表
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('agent_states', 'chat_history', 'audit_logs')
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]

        cur.close()
        conn.close()

        print("✅ 数据库连接成功")
        print(f"   PostgreSQL 版本: {version.split(',')[0]}")
        print(f"   已创建的表: {', '.join(tables)}")

        return True

    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    test_connection()

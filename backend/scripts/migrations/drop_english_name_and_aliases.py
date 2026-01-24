"""
数据库迁移：删除 english_name 和 aliases 字段

执行方法：
    python scripts/migrations/drop_english_name_and_aliases.py
"""
import sqlite3
import os
from pathlib import Path

# 数据库路径
script_dir = Path(__file__).parent
DB_PATH = script_dir.parent.parent / "app.db"


def migrate():
    """执行迁移"""
    db_path_str = str(DB_PATH)
    if not os.path.exists(db_path_str):
        print(f"数据库不存在: {db_path_str}")
        return False

    print(f"开始迁移数据库: {db_path_str}")
    print("-" * 50)

    conn = sqlite3.connect(db_path_str)
    cursor = conn.cursor()

    try:
        # 检查列是否存在
        cursor.execute("PRAGMA table_info(diseases)")
        columns = {row[1]: row[0] for row in cursor.fetchall()}

        columns_to_drop = []
        if "english_name" in columns:
            columns_to_drop.append("english_name")
        if "aliases" in columns:
            columns_to_drop.append("aliases")

        if not columns_to_drop:
            print("无需迁移：字段已不存在")
            return True

        print(f"将删除以下列: {', '.join(columns_to_drop)}")

        # SQLite 不支持 ALTER TABLE DROP COLUMN，
        # 需要重建表

        # 1. 获取现有表结构
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='diseases'")
        create_sql = cursor.fetchone()[0]
        print(f"\n原表结构:\n{create_sql}")

        # 2. 创建新表（不含 english_name 和 aliases）
        new_columns = [col for col in columns.keys() if col not in columns_to_drop]

        # 构建列定义
        column_defs = []
        for col in new_columns:
            cursor.execute(f"PRAGMA table_info(diseases)")
            for row in cursor.fetchall():
                if row[1] == col:
                    # row: cid, name, type, notnull, default_value, pk
                    col_def = f'"{row[1]}" {row[2] or "TEXT"}'
                    if row[4]:  # default value
                        col_def += f" DEFAULT {row[4]}"
                    if row[5]:  # primary key
                        col_def += " PRIMARY KEY"
                    elif row[3]:  # not null
                        col_def += " NOT NULL"
                    column_defs.append(col_def)
                    break

        new_create_sql = f"""
CREATE TABLE diseases_new (
    {',\n    '.join(column_defs)}
)
"""
        print(f"\n新表结构:\n{new_create_sql}")

        # 3. 创建新表
        cursor.execute("DROP TABLE IF EXISTS diseases_new")
        cursor.execute(new_create_sql)

        # 4. 复制数据（排除删除的列）
        cols_str = ', '.join([f'"{col}"' for col in new_columns])
        cursor.execute(f"""
            INSERT INTO diseases_new ({cols_str})
            SELECT {cols_str} FROM diseases
        """)

        copied_count = cursor.rowcount
        print(f"复制了 {copied_count} 条记录")

        # 5. 删除旧表，重命名新表
        cursor.execute("DROP TABLE diseases")
        cursor.execute("ALTER TABLE diseases_new RENAME TO diseases")

        # 6. 重建索引
        # wiki_id 索引
        cursor.execute('CREATE INDEX IF NOT EXISTS "ix_diseases_wiki_id" ON diseases (wiki_id)')
        # name 索引
        cursor.execute('CREATE INDEX IF NOT EXISTS "ix_diseases_name" ON diseases (name)')
        # pinyin 索引
        cursor.execute('CREATE INDEX IF NOT EXISTS "ix_diseases_pinyin" ON diseases (pinyin)')
        # pinyin_abbr 索引
        cursor.execute('CREATE INDEX IF NOT EXISTS "ix_diseases_pinyin_abbr" ON diseases (pinyin_abbr)')
        # source 索引
        cursor.execute('CREATE INDEX IF NOT EXISTS "ix_diseases_source" ON diseases (source)')

        conn.commit()

        print("-" * 50)
        print("迁移完成!")

        # 验证
        cursor.execute("PRAGMA table_info(diseases)")
        new_columns = [row[1] for row in cursor.fetchall()]
        print(f"\n当前列: {', '.join(new_columns)}")

        return True

    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()

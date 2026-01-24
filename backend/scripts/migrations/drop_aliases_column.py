"""
数据库迁移：删除 aliases 字段

执行方法：
    python scripts/migrations/drop_aliases_column.py
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
        # 检查 aliases 列是否存在
        cursor.execute("PRAGMA table_info(diseases)")
        columns = [row[1] for row in cursor.fetchall()]

        if "aliases" not in columns:
            print("无需迁移：aliases 字段已不存在")
            return True

        print("将删除 aliases 列")

        # SQLite 不支持 ALTER TABLE DROP COLUMN，需要重建表
        # 1. 获取所有列（除了 aliases）
        columns_to_keep = [col for col in columns if col != "aliases"]

        # 2. 创建新表
        new_columns_def = []
        for col in columns_to_keep:
            cursor.execute(f"PRAGMA table_info(diseases)")
            for row in cursor.fetchall():
                if row[1] == col:
                    col_def = f'"{row[1]}" {row[2] or "TEXT"}'
                    if row[4]:  # default value
                        col_def += f" DEFAULT {row[4]}"
                    if row[5]:  # primary key
                        col_def += " PRIMARY KEY"
                    elif row[3]:  # not null
                        col_def += " NOT NULL"
                    new_columns_def.append(col_def)
                    break

        new_create_sql = f"""
CREATE TABLE diseases_new (
    {',\n    '.join(new_columns_def)},
    FOREIGN KEY(department_id) REFERENCES departments (id)
)
"""

        # 3. 创建新表
        cursor.execute("DROP TABLE IF EXISTS diseases_new")
        cursor.execute(new_create_sql)

        # 4. 复制数据
        cols_str = ', '.join([f'"{col}"' for col in columns_to_keep])
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
        cursor.execute('CREATE INDEX IF NOT EXISTS "ix_diseases_pinyin" ON diseases (pinyin)')
        cursor.execute('CREATE INDEX IF NOT EXISTS "ix_diseases_pinyin_abbr" ON diseases (pinyin_abbr)')

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
        import traceback
        traceback.print_exc()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()

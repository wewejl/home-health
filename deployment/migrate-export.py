#!/usr/bin/env python3
"""
SQLite 到 PostgreSQL 数据迁移导出脚本
将本地 SQLite 数据导出为 PostgreSQL 兼容的 SQL 文件
"""

import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path

# 配置
PROJECT_ROOT = Path(__file__).parent.parent
SQLITE_DB_PATH = PROJECT_ROOT / "backend" / "app.db"
OUTPUT_DIR = PROJECT_ROOT / "deployment" / "migrate-data"
OUTPUT_FILE = OUTPUT_DIR / "dump.sql"

# PostgreSQL 类型映射
TYPE_MAPPING = {
    "INTEGER": "INTEGER",
    "TEXT": "TEXT",
    "REAL": "REAL",
    "BLOB": "BYTEA",
    "BOOLEAN": "BOOLEAN",  # SQLite 存储 INTEGER
    "TIMESTAMP": "TIMESTAMP",
    "JSON": "JSONB",
}

# 创建输出目录
OUTPUT_DIR.mkdir(exist_ok=True)


def sqlite_type_to_pgtype(sqlite_type):
    """转换 SQLite 类型到 PostgreSQL 类型"""
    sqlite_type = sqlite_type.upper()
    if "INTEGER" in sqlite_type or "INT" in sqlite_type:
        return "INTEGER"
    elif "TEXT" in sqlite_type or "VARCHAR" in sqlite_type or "CHAR" in sqlite_type:
        return "TEXT"
    elif "REAL" in sqlite_type or "FLOAT" in sqlite_type or "DOUBLE" in sqlite_type:
        return "REAL"
    elif "BLOB" in sqlite_type:
        return "BYTEA"
    elif "BOOLEAN" in sqlite_type:
        return "BOOLEAN"
    else:
        return "TEXT"


def get_table_schema(cursor, table_name):
    """获取表结构"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    schema_sql = f"-- Table: {table_name}\n"
    schema_sql += f"DROP TABLE IF EXISTS {table_name} CASCADE;\n"
    schema_sql += f"CREATE TABLE {table_name} (\n"

    column_defs = []
    primary_keys = []

    for col in columns:
        cid, name, col_type, not_null, default_val, pk = col
        pg_type = sqlite_type_to_pgtype(col_type)

        col_def = f"    {name} {pg_type}"

        if not_null:
            col_def += " NOT NULL"

        if default_val is not None:
            if default_val == "CURRENT_TIMESTAMP":
                col_def += " DEFAULT CURRENT_TIMESTAMP"
            elif isinstance(default_val, str) and default_val.upper() in ("TRUE", "FALSE"):
                col_def += f" DEFAULT {default_val.upper()}"
            elif isinstance(default_val, str) and default_val.isdigit():
                col_def += f" DEFAULT {default_val}"
            else:
                # 字符串默认值
                col_def += f" DEFAULT '{default_val}'"

        column_defs.append(col_def)
        if pk:
            primary_keys.append(name)

    if column_defs:
        schema_sql += ",\n".join(column_defs)

    if primary_keys:
        schema_sql += f",\n    PRIMARY KEY ({', '.join(primary_keys)})"

    schema_sql += "\n);\n\n"

    return schema_sql


def export_table_data(cursor, table_name, output_file):
    """导出表数据"""
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    columns = [col[1] for col in columns_info]
    column_types = {col[1]: col[2] for col in columns_info}

    if not rows:
        output_file.write(f"-- Table {table_name}: 无数据\n\n")
        return

    output_file.write(f"-- Data for table: {table_name}\n")
    output_file.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES\n")

    value_rows = []
    for row in rows:
        values = []
        for i, value in enumerate(row):
            col_name = columns[i]
            col_type = column_types.get(col_name, "")

            if value is None:
                values.append("NULL")
            elif isinstance(value, bool):
                # Python bool 类型
                values.append("TRUE" if value else "FALSE")
            elif isinstance(value, int) and "BOOLEAN" in col_type.upper():
                # SQLite 用 0/1 存储布尔值，需要转换
                values.append("TRUE" if value else "FALSE")
            elif isinstance(value, (int, float)):
                values.append(str(value))
            elif isinstance(value, (dict, list)):
                # JSON 类型，使用 PostgreSQL jsonb 类型
                json_str = json.dumps(value, ensure_ascii=False)
                # 转义单引号
                json_str = json_str.replace("'", "''")
                values.append(f"'{json_str}'::jsonb")
            else:
                # 字符串类型
                str_val = str(value)
                # 转义单引号
                str_val = str_val.replace("'", "''")
                # 转义反斜杠
                str_val = str_val.replace("\\", "\\\\")
                values.append(f"'{str_val}'")

        value_rows.append(f"({', '.join(values)})")

    output_file.write(",\n".join(value_rows) + ";\n\n")


def export_sequences(cursor, output_file):
    """导出序列（用于自增 ID）"""
    # 获取所有有自增列的表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()

    output_file.write("-- 序列设置（用于自增 ID）\n")
    output_file.write("-- 注意: PostgreSQL 需要手动创建序列或使用 SERIAL/BIGSERIAL\n\n")

    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        for col in columns:
            cid, name, col_type, not_null, default_val, pk = col
            # SQLite 的 INTEGER PRIMARY KEY 自动递增
            if pk and "INTEGER" in col_type.upper():
                output_file.write(f"-- {table_name}.{name} 是自增主键\n")
                output_file.write(f"-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY\n\n")


def main():
    print(f"=== SQLite 到 PostgreSQL 数据迁移导出 ===")
    print(f"SQLite 数据库: {SQLITE_DB_PATH}")
    print(f"输出文件: {OUTPUT_FILE}")

    if not SQLITE_DB_PATH.exists():
        print(f"错误: SQLite 数据库文件不存在: {SQLITE_DB_PATH}")
        return

    # 连接 SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"发现 {len(tables)} 个表: {', '.join(tables)}")

    # 写入 SQL 文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        # 文件头
        f.write(f"-- PostgreSQL 数据库转储文件\n")
        f.write(f"-- 源数据库: SQLite ({SQLITE_DB_PATH})\n")
        f.write(f"-- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"--\n")
        f.write(f"-- 使用方法:\n")
        f.write(f"--   psql -h 123.206.232.231 -U xinlin_prod -d xinlin_prod < {OUTPUT_FILE.name}\n")
        f.write(f"--\n\n")

        # 禁用触发器和约束
        f.write("-- 开始数据迁移\n")
        f.write("BEGIN;\n\n")

        # 导出每个表的结构和数据
        for table in tables:
            print(f"处理表: {table}...")

            # 获取表结构
            schema = get_table_schema(cursor, table)
            f.write(schema)

            # 导出数据
            export_table_data(cursor, table, f)

        # 序列设置
        export_sequences(cursor, f)

        # 结束
        f.write("COMMIT;\n")
        f.write("-- 数据迁移完成\n\n")

    # 清理
    conn.close()

    print(f"\n导出完成!")
    print(f"SQL 文件大小: {OUTPUT_FILE.stat().st_size / 1024:.2f} KB")
    print(f"\n下一步: 执行部署脚本")
    print(f"  bash deployment/deploy-with-data.sh")


if __name__ == "__main__":
    main()

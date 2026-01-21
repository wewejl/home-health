#!/usr/bin/env python3
"""
添加 disease.source 字段并标记数据来源
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine
from sqlalchemy import text


def add_source_column():
    """添加 source 列到 diseases 表"""
    db = SessionLocal()

    try:
        # PostgreSQL 检查列是否存在
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'diseases'
            AND column_name = 'source'
        """))
        exists = result.fetchone() is not None

        if exists:
            print("✓ source 列已存在")
        else:
            # 添加 source 列（PostgreSQL 语法）
            db.execute(text("ALTER TABLE diseases ADD COLUMN source VARCHAR(50)"))
            db.commit()
            print("✓ 已添加 source 列")

        # 创建索引
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_diseases_source
                ON diseases (source)
            """))
            db.commit()
            print("✓ 已创建 source 索引")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"索引创建注意: {e}")

    except Exception as e:
        print(f"添加列失败: {e}")
        db.rollback()
    finally:
        db.close()


def update_source_data():
    """更新现有数据的来源标记"""
    db = SessionLocal()

    try:
        # 标记 ICD-10 来源（概述包含 ICD-10编码 且无症状详情）
        icd10_count = db.execute(text("""
            UPDATE diseases
            SET source = 'ICD-10'
            WHERE overview LIKE '%ICD-10编码%'
            AND (symptoms = '' OR symptoms IS NULL)
        """))
        db.commit()
        print(f"✓ 标记 ICD-10 来源: {icd10_count.rowcount} 条")

        # 标记 medical.json 来源（有症状详情）
        medical_count = db.execute(text("""
            UPDATE diseases
            SET source = 'medical.json'
            WHERE (symptoms != '' AND symptoms IS NOT NULL)
            AND source IS NULL
        """))
        db.commit()
        print(f"✓ 标记 medical.json 来源: {medical_count.rowcount} 条")

        # 统计
        print("\n数据来源统计:")
        result = db.execute(text("""
            SELECT
                COALESCE(source, '未标记') as source,
                COUNT(*) as count
            FROM diseases
            GROUP BY source
        """))
        for row in result.fetchall():
            print(f"  {row[0]}: {row[1]} 条")

    except Exception as e:
        print(f"更新数据失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("="*50)
    print("添加 source 字段并标记数据来源")
    print("="*50)

    add_source_column()
    print()
    update_source_data()

    print("\n✅ 完成!")

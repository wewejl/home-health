"""
添加疾病扩展字段迁移脚本
新增字段: complications, body_parts, related_symptoms, exam_items, related_diseases
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import get_db


def migrate():
    """执行迁移"""
    db = next(get_db())

    try:
        print("开始迁移: 添加疾病扩展字段...")

        # 检查字段是否已存在
        check_sql = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'diseases'
            AND column_name IN ('complications', 'body_parts', 'related_symptoms', 'exam_items', 'related_diseases')
        """
        result = db.execute(text(check_sql)).fetchall()
        existing_columns = [row[0] for row in result]

        # 添加 complications 字段（并发症）
        if 'complications' not in existing_columns:
            print("  添加 complications 字段...")
            db.execute(text("""
                ALTER TABLE diseases
                ADD COLUMN complications TEXT;
            """))
        else:
            print("  complications 字段已存在，跳过")

        # 添加 body_parts 字段（部位）
        if 'body_parts' not in existing_columns:
            print("  添加 body_parts 字段...")
            db.execute(text("""
                ALTER TABLE diseases
                ADD COLUMN body_parts TEXT;
            """))
        else:
            print("  body_parts 字段已存在，跳过")

        # 添加 related_symptoms 字段（相关症状）
        if 'related_symptoms' not in existing_columns:
            print("  添加 related_symptoms 字段...")
            db.execute(text("""
                ALTER TABLE diseases
                ADD COLUMN related_symptoms TEXT;
            """))
        else:
            print("  related_symptoms 字段已存在，跳过")

        # 添加 exam_items 字段（检查项目）
        if 'exam_items' not in existing_columns:
            print("  添加 exam_items 字段...")
            db.execute(text("""
                ALTER TABLE diseases
                ADD COLUMN exam_items TEXT;
            """))
        else:
            print("  exam_items 字段已存在，跳过")

        # 添加 related_diseases 字段（相关疾病）
        if 'related_diseases' not in existing_columns:
            print("  添加 related_diseases 字段...")
            db.execute(text("""
                ALTER TABLE diseases
                ADD COLUMN related_diseases TEXT;
            """))
        else:
            print("  related_diseases 字段已存在，跳过")

        db.commit()
        print("\n迁移完成!")

    except Exception as e:
        db.rollback()
        print(f"\n迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()

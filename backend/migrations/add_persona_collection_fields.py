"""
数据库迁移：添加医生分身相关字段

为 doctors 表添加：
- persona_completed: 对话式采集完成标记
- records_analyzed: 病历分析完成标记
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """运行迁移"""
    print("🚀 开始添加医生分身相关字段...")

    with engine.connect() as conn:
        # 检查字段是否已存在
        check_persona = conn.execute(text(
            "SELECT COUNT(*) as cnt FROM pragma_table_info('doctors') WHERE name='persona_completed'"
        )).fetchone()

        check_records = conn.execute(text(
            "SELECT COUNT(*) as cnt FROM pragma_table_info('doctors') WHERE name='records_analyzed'"
        )).fetchone()

        if check_persona[0] == 0:
            print("  ➕ 添加 persona_completed 字段...")
            conn.execute(text(
                "ALTER TABLE doctors ADD COLUMN persona_completed BOOLEAN DEFAULT 0"
            ))
            conn.commit()
            print("  ✅ persona_completed 字段已添加")
        else:
            print("  ℹ️ persona_completed 字段已存在，跳过")

        if check_records[0] == 0:
            print("  ➕ 添加 records_analyzed 字段...")
            conn.execute(text(
                "ALTER TABLE doctors ADD COLUMN records_analyzed BOOLEAN DEFAULT 0"
            ))
            conn.commit()
            print("  ✅ records_analyzed 字段已添加")
        else:
            print("  ℹ️ records_analyzed 字段已存在，跳过")

    print("✅ 迁移完成！")


def rollback_migration():
    """回滚迁移（SQLite 不支持 DROP COLUMN，需要重建表）"""
    print("⚠️ SQLite 不支持直接删除列，如需回滚请手动重建表")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()

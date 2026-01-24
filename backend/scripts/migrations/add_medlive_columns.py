"""
迁移脚本：为 diseases 表添加 MedLive 支持字段
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine


def migrate():
    """执行迁移"""
    print("开始迁移 diseases 表...")

    with engine.connect() as conn:
        # 添加 wiki_id 列
        try:
            conn.execute(text("ALTER TABLE diseases ADD COLUMN wiki_id VARCHAR(50)"))
            print("✓ 添加 wiki_id 列")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"wiki_id: {e}")

        # 添加 english_name 列
        try:
            conn.execute(text("ALTER TABLE diseases ADD COLUMN english_name VARCHAR(200)"))
            print("✓ 添加 english_name 列")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"english_name: {e}")

        # 添加 url 列
        try:
            conn.execute(text("ALTER TABLE diseases ADD COLUMN url VARCHAR(500)"))
            print("✓ 添加 url 列")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"url: {e}")

        # 添加 sections 列 (JSON)
        try:
            conn.execute(text("ALTER TABLE diseases ADD COLUMN sections JSON"))
            print("✓ 添加 sections 列")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"sections: {e}")

        # 创建唯一索引
        try:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_diseases_wiki_id ON diseases(wiki_id)"))
            print("✓ 创建 wiki_id 唯一索引")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"wiki_id 索引: {e}")

        # 修改 department_id 为可空
        try:
            conn.execute(text("ALTER TABLE diseases ALTER COLUMN department_id DROP NOT NULL"))
            print("✓ 修改 department_id 为可空")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"department_id: {e}")

        # 修改 source 列默认值
        try:
            conn.execute(text("ALTER TABLE diseases ALTER COLUMN source SET DEFAULT 'manual'"))
            print("✓ 设置 source 默认值")
        except Exception as e:
            if "already exists" not in str(e):
                print(f"source 默认值: {e}")

        conn.commit()
        print("迁移完成!")


if __name__ == "__main__":
    migrate()

"""
添加 ReAct Agent 增强字段到 derma_sessions 表

执行方式:
cd backend
source venv/bin/activate
python migrations/add_react_agent_fields.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.database import engine


def upgrade():
    """添加新字段"""
    with engine.connect() as conn:
        # 添加 advice_history 字段
        conn.execute(text("""
            ALTER TABLE derma_sessions 
            ADD COLUMN IF NOT EXISTS advice_history JSON DEFAULT '[]'::json
        """))
        
        # 添加 diagnosis_card 字段
        conn.execute(text("""
            ALTER TABLE derma_sessions 
            ADD COLUMN IF NOT EXISTS diagnosis_card JSON DEFAULT NULL
        """))
        
        # 添加 knowledge_refs 字段
        conn.execute(text("""
            ALTER TABLE derma_sessions 
            ADD COLUMN IF NOT EXISTS knowledge_refs JSON DEFAULT '[]'::json
        """))
        
        # 添加 reasoning_steps 字段
        conn.execute(text("""
            ALTER TABLE derma_sessions 
            ADD COLUMN IF NOT EXISTS reasoning_steps JSON DEFAULT '[]'::json
        """))
        
        conn.commit()
        print("✅ 成功添加 ReAct Agent 增强字段")


def downgrade():
    """回滚迁移"""
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE derma_sessions DROP COLUMN IF EXISTS advice_history"))
        conn.execute(text("ALTER TABLE derma_sessions DROP COLUMN IF EXISTS diagnosis_card"))
        conn.execute(text("ALTER TABLE derma_sessions DROP COLUMN IF EXISTS knowledge_refs"))
        conn.execute(text("ALTER TABLE derma_sessions DROP COLUMN IF EXISTS reasoning_steps"))
        conn.commit()
        print("✅ 成功回滚 ReAct Agent 增强字段")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--downgrade", action="store_true", help="回滚迁移")
    args = parser.parse_args()
    
    if args.downgrade:
        downgrade()
    else:
        upgrade()

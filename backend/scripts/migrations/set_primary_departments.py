#!/usr/bin/env python3
"""
设置主要科室标记
将前 12 个科室（sort_order <= 12）标记为主要科室
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

def main():
    print(f"=== 设置主要科室标记 ===")
    print(f"数据库: {DATABASE_URL}")

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # 检查当前状态
        result = conn.execute(text("SELECT id, name, is_primary FROM departments ORDER BY sort_order"))
        departments = result.fetchall()

        print(f"\n当前科室状态:")
        for dept in departments:
            print(f"  {dept.id}: {dept.name} - is_primary={dept.is_primary}")

        # 更新前 12 个科室
        print(f"\n更新前 12 个科室为 is_primary=True...")
        result = conn.execute(text("""
            UPDATE departments
            SET is_primary = TRUE
            WHERE sort_order <= 12
        """))
        print(f"  更新了 {result.rowcount} 条记录")

        # 验证结果
        result = conn.execute(text("""
            SELECT id, name, is_primary FROM departments
            WHERE is_primary = TRUE
            ORDER BY sort_order
        """))
        primary_departments = result.fetchall()

        print(f"\n主要科室列表:")
        for dept in primary_departments:
            print(f"  {dept.id}: {dept.name}")

        conn.commit()

    print(f"\n完成!")

if __name__ == "__main__":
    main()

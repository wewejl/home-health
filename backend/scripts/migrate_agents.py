#!/usr/bin/env python3
"""
智能体目录结构迁移脚本
将平铺式结构迁移到模块化结构

使用方法：
    cd backend
    python scripts/migrate_agents.py [--dry-run]

说明：
    --dry-run: 只显示将要执行的操作，不实际移动文件
"""
import os
import shutil
import argparse
from pathlib import Path


def migrate_agents(dry_run: bool = False):
    """执行迁移"""
    # 确定 services 目录
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    services_dir = backend_dir / "app" / "services"
    
    if not services_dir.exists():
        print(f"❌ 错误: 找不到 services 目录: {services_dir}")
        return False
    
    print(f"📁 Services 目录: {services_dir}")
    print(f"🔧 模式: {'预览 (dry-run)' if dry_run else '执行迁移'}")
    print("=" * 60)
    
    # 检查是否已经迁移
    if (services_dir / "base").exists() and (services_dir / "dermatology").exists():
        print("✅ 目录结构已是模块化格式，无需迁移")
        return True
    
    # 1. 创建目录结构
    dirs_to_create = [
        "base",
        "general", 
        "dermatology",
        "cardiology",
        "orthopedics"
    ]
    
    print("\n📂 创建目录结构:")
    for dir_name in dirs_to_create:
        dir_path = services_dir / dir_name
        if not dir_path.exists():
            print(f"  创建: {dir_name}/")
            if not dry_run:
                dir_path.mkdir(exist_ok=True)
                (dir_path / "__init__.py").touch()
    
    # 2. 迁移文件映射
    migrations = {
        # General
        "general_agent.py": ("general", "general_agent.py"),
        
        # Dermatology
        "derma_agent.py": ("dermatology", "derma_agent.py"),
        "derma_agent_wrapper.py": ("dermatology", "derma_wrapper.py"),
        "derma_crew_service.py": ("dermatology", "derma_crew_service.py"),
        "crewai_agents.py": ("dermatology", "derma_agents.py"),
        
        # Cardiology
        "cardio_agent.py": ("cardiology", "cardio_agent.py"),
        "cardio_agent_wrapper.py": ("cardiology", "cardio_wrapper.py"),
        "cardio_crew_service.py": ("cardiology", "cardio_crew_service.py"),
        "cardio_agents.py": ("cardiology", "cardio_agents.py"),
    }
    
    print("\n📦 迁移文件:")
    moved_files = []
    for old_name, (subdir, new_name) in migrations.items():
        old_path = services_dir / old_name
        new_path = services_dir / subdir / new_name
        
        if old_path.exists():
            print(f"  {old_name} → {subdir}/{new_name}")
            if not dry_run:
                shutil.move(str(old_path), str(new_path))
            moved_files.append((old_name, f"{subdir}/{new_name}"))
        else:
            print(f"  ⚠️ 跳过 (不存在): {old_name}")
    
    # 3. 提示需要手动更新的 import 路径
    print("\n" + "=" * 60)
    print("📝 迁移完成后需要手动更新 import 路径:")
    print("""
# 旧路径 → 新路径
from .general_agent import GeneralAgent
→ from .general import GeneralAgent

from .derma_agent_wrapper import DermaAgentWrapper
→ from .dermatology import DermaAgentWrapper

from .cardio_agent_wrapper import CardioAgentWrapper
→ from .cardiology import CardioAgentWrapper

# 各模块内部也需要更新相对导入
from .derma_agent import ...
→ from .derma_agent import ... (模块内保持不变)

from ..config import get_settings
→ from ...config import get_settings (多一层)
""")
    
    if dry_run:
        print("\n⚠️ 这是预览模式，未实际执行任何操作")
        print("移除 --dry-run 参数以执行实际迁移")
    else:
        print("\n✅ 迁移完成！")
        print("请检查并更新相关 import 路径")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="智能体目录结构迁移脚本")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示将要执行的操作，不实际移动文件"
    )
    args = parser.parse_args()
    
    migrate_agents(dry_run=args.dry_run)


if __name__ == "__main__":
    main()

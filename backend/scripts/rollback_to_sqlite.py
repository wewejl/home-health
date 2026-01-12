"""
回滚脚本：从 PostgreSQL 回滚到 SQLite
运行方式: python -m scripts.rollback_to_sqlite
"""
import os
import sys
import shutil

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BACKEND_DIR, ".env")
SQLITE_DB = os.path.join(BACKEND_DIR, "app.db")


def find_latest_backup():
    """查找最新的 SQLite 备份文件"""
    backups = []
    for f in os.listdir(BACKEND_DIR):
        if f.startswith("app.db.backup_"):
            backups.append(f)
    
    if not backups:
        return None
    
    backups.sort(reverse=True)
    return os.path.join(BACKEND_DIR, backups[0])


def rollback_env():
    """回滚 .env 配置"""
    print("[回滚] 更新 .env 配置...")
    
    with open(ENV_FILE, "r") as f:
        content = f.read()
    
    # 注释掉 PostgreSQL 配置，启用 SQLite
    lines = content.split("\n")
    new_lines = []
    
    for line in lines:
        if line.startswith("DATABASE_URL=postgresql"):
            new_lines.append("# " + line)
            new_lines.append("DATABASE_URL=sqlite:///./app.db")
        elif line == "# DATABASE_URL=sqlite:///./app.db":
            continue  # 跳过旧的注释行
        else:
            new_lines.append(line)
    
    with open(ENV_FILE, "w") as f:
        f.write("\n".join(new_lines))
    
    print("[回滚] ✅ .env 已更新为 SQLite 配置")


def restore_backup(backup_path):
    """恢复 SQLite 备份"""
    if os.path.exists(SQLITE_DB):
        os.rename(SQLITE_DB, SQLITE_DB + ".pg_era")
        print(f"[回滚] 旧数据库已重命名为 app.db.pg_era")
    
    shutil.copy2(backup_path, SQLITE_DB)
    print(f"[回滚] ✅ 已从备份恢复: {backup_path}")


def main():
    print("=" * 50)
    print("  PostgreSQL -> SQLite 回滚工具")
    print("=" * 50)
    print()
    
    # 查找备份
    backup = find_latest_backup()
    if not backup:
        print("[回滚] ❌ 未找到 SQLite 备份文件")
        print("  请手动恢复 app.db 文件")
        return 1
    
    print(f"[回滚] 找到备份: {backup}")
    
    # 确认
    confirm = input("\n确认回滚到 SQLite? (yes/no): ")
    if confirm.lower() != "yes":
        print("[回滚] 已取消")
        return 0
    
    # 执行回滚
    restore_backup(backup)
    rollback_env()
    
    print("\n" + "=" * 50)
    print("回滚完成！请重启应用服务。")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())

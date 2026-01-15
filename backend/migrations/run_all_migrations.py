"""
主迁移脚本：按顺序执行所有会话数据迁移

执行前请先备份数据库：
    pg_dump -U postgres home_health > backup_before_migration.sql

执行方式：
    cd backend
    python -m migrations.run_all_migrations
    
    # 或者先预览迁移内容
    python -m migrations.run_all_migrations --dry-run
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


def run_all_migrations(dry_run: bool = False):
    """
    执行所有迁移脚本
    
    执行顺序:
    1. migrate_derma_sessions - 迁移皮肤科会话
    2. migrate_diagnosis_sessions - 迁移全科会话
    3. migrate_messages - 迁移消息历史
    4. verify_migration - 验证迁移结果
    """
    from migrations.migrate_derma_sessions import migrate_derma_sessions
    from migrations.migrate_diagnosis_sessions import migrate_diagnosis_sessions
    from migrations.migrate_messages import migrate_all_messages
    from migrations.verify_migration import verify_migration
    
    logger.info("=" * 60)
    logger.info("STARTING SESSION DATA MIGRATION")
    logger.info(f"Dry Run: {dry_run}")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    results = {}
    
    try:
        # Step 1: 迁移 derma_sessions
        logger.info("\n" + "=" * 60)
        logger.info("STEP 1/4: Migrating derma_sessions...")
        logger.info("=" * 60)
        results["derma_sessions"] = migrate_derma_sessions(dry_run=dry_run)
        
        # Step 2: 迁移 diagnosis_sessions
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2/4: Migrating diagnosis_sessions...")
        logger.info("=" * 60)
        results["diagnosis_sessions"] = migrate_diagnosis_sessions(dry_run=dry_run)
        
        # Step 3: 迁移消息
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3/4: Migrating messages...")
        logger.info("=" * 60)
        results["messages"] = migrate_all_messages(dry_run=dry_run)
        
        # Step 4: 验证迁移
        if not dry_run:
            logger.info("\n" + "=" * 60)
            logger.info("STEP 4/4: Verifying migration...")
            logger.info("=" * 60)
            results["verification"] = verify_migration()
        
        # 最终汇总
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION COMPLETE")
        logger.info("=" * 60)
        
        logger.info("\nResults Summary:")
        logger.info(f"  Derma Sessions: {results.get('derma_sessions', {})}")
        logger.info(f"  Diagnosis Sessions: {results.get('diagnosis_sessions', {})}")
        logger.info(f"  Messages: {results.get('messages', {})}")
        
        if not dry_run and results.get("verification"):
            overall = results["verification"].get("overall", "unknown")
            logger.info(f"  Verification: {overall}")
            
            if overall != "pass":
                logger.warning("⚠️ Migration completed with issues. Please review the verification results.")
                return False
        
        logger.info("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        logger.error("Please check the logs and consider rolling back if necessary.")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run all session data migrations")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be migrated")
    args = parser.parse_args()
    
    success = run_all_migrations(dry_run=args.dry_run)
    sys.exit(0 if success else 1)

# 会话架构重构 - 数据迁移指南

## 概述

本次迁移将旧的分离会话表 (`derma_sessions`, `diagnosis_sessions`) 的数据统一迁移到 `sessions` 表，解决病历生成时数据不匹配导致的假数据问题。

## 迁移文件清单

| 文件 | 说明 |
|------|------|
| `migrate_derma_sessions.py` | 迁移皮肤科会话数据 |
| `migrate_diagnosis_sessions.py` | 迁移全科诊室会话数据 |
| `migrate_messages.py` | 迁移消息历史数据 |
| `verify_migration.py` | 验证迁移数据完整性 |
| `run_all_migrations.py` | 主迁移脚本，按顺序执行所有迁移 |
| `rollback_migration.py` | 回滚脚本 |

## 执行步骤

### 1. 备份数据库（必须）

```bash
# PostgreSQL
pg_dump -U postgres home_health > backup_$(date +%Y%m%d_%H%M%S).sql

# SQLite
cp home_health.db home_health_backup_$(date +%Y%m%d_%H%M%S).db
```

### 2. 预览迁移内容（推荐）

```bash
cd backend
python -m migrations.run_all_migrations --dry-run
```

### 3. 执行迁移

```bash
cd backend
python -m migrations.run_all_migrations
```

### 4. 验证迁移结果

```bash
cd backend
python -m migrations.verify_migration --quality
```

### 5. 部署新代码

```bash
git pull origin main
docker-compose restart backend
```

## 单独执行迁移脚本

如需单独执行某个迁移脚本：

```bash
# 只迁移皮肤科会话
python -m migrations.migrate_derma_sessions

# 只迁移全科会话
python -m migrations.migrate_diagnosis_sessions

# 只迁移消息
python -m migrations.migrate_messages

# 只验证
python -m migrations.verify_migration
```

## 回滚方案

### 方案1: 使用回滚脚本

```bash
cd backend
python -m migrations.rollback_migration
```

### 方案2: 恢复数据库备份

```bash
# PostgreSQL
psql -U postgres home_health < backup_YYYYMMDD_HHMMSS.sql

# SQLite
cp home_health_backup_YYYYMMDD_HHMMSS.db home_health.db
```

### 方案3: 代码回滚

```bash
git revert <commit_hash>
docker-compose restart backend
```

## 数据映射说明

### agent_state 字段结构

迁移后，原表的字段将被合并到 `sessions.agent_state` JSON 字段中：

```json
{
  "stage": "completed",
  "progress": 100,
  "chief_complaint": "主诉内容",
  "symptoms": ["症状1", "症状2"],
  "symptom_details": {},
  "risk_level": "low",
  
  // 皮肤科特有
  "skin_analyses": [],
  "possible_conditions": [],
  
  // 全科特有
  "possible_diseases": [],
  "recommendations": {},
  
  // 原始消息备份
  "original_messages": []
}
```

### agent_type 映射

| 旧表 | agent_type |
|------|------------|
| `derma_sessions` | `dermatology` |
| `diagnosis_sessions` | `general` |

## 注意事项

1. **不要在高峰期执行迁移** - 建议在凌晨或用户量较少时执行
2. **确保有足够磁盘空间** - 迁移过程中会产生日志文件
3. **监控数据库性能** - 大量数据迁移可能影响数据库性能
4. **保留旧表至少7天** - 确认无问题后再删除

## 迁移后清理

确认迁移成功且运行稳定后（建议等待7天），可以执行以下清理操作：

```sql
-- 重命名旧表（不立即删除）
ALTER TABLE derma_sessions RENAME TO derma_sessions_deprecated;
ALTER TABLE diagnosis_sessions RENAME TO diagnosis_sessions_deprecated;

-- 7天后确认无问题可删除
-- DROP TABLE derma_sessions_deprecated;
-- DROP TABLE diagnosis_sessions_deprecated;
```

## 联系方式

如遇问题，请联系：
- 技术负责人
- 项目群

## 更新记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-01-15 | v1.0 | 初始版本 |

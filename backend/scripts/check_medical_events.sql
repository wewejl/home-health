-- 检查 medical_events 表的数据完整性
-- 使用方式: psql -d your_database -f check_medical_events.sql

\echo '============================================================'
\echo '检查 medical_events 表数据完整性'
\echo '============================================================'

-- 1. 总记录数
\echo ''
\echo '📊 总记录数:'
SELECT COUNT(*) as total_count FROM medical_events;

-- 2. 检查无效的 agent_type
\echo ''
\echo '⚠️  检查无效的 agent_type (应该是: cardio, derma, ortho, neuro, general, endo, gastro, respiratory):'
SELECT id, agent_type, department, title 
FROM medical_events 
WHERE agent_type NOT IN ('cardio', 'derma', 'ortho', 'neuro', 'general', 'endo', 'gastro', 'respiratory')
LIMIT 10;

-- 3. 检查无效的 status
\echo ''
\echo '⚠️  检查无效的 status (应该是: active, completed, exported, archived):'
SELECT id, status, title 
FROM medical_events 
WHERE status NOT IN ('active', 'completed', 'exported', 'archived')
LIMIT 10;

-- 4. 检查无效的 risk_level
\echo ''
\echo '⚠️  检查无效的 risk_level (应该是: low, medium, high, emergency):'
SELECT id, risk_level, title 
FROM medical_events 
WHERE risk_level NOT IN ('low', 'medium', 'high', 'emergency')
LIMIT 10;

-- 5. 检查空的必填字段
\echo ''
\echo '⚠️  检查空的 title:'
SELECT id, title, department FROM medical_events WHERE title IS NULL OR title = '' LIMIT 10;

\echo ''
\echo '⚠️  检查空的 department:'
SELECT id, title, department FROM medical_events WHERE department IS NULL OR department = '' LIMIT 10;

-- 6. 按科室统计
\echo ''
\echo '📈 按科室分布:'
SELECT agent_type, COUNT(*) as count 
FROM medical_events 
GROUP BY agent_type 
ORDER BY count DESC;

-- 7. 按状态统计
\echo ''
\echo '📈 按状态分布:'
SELECT status, COUNT(*) as count 
FROM medical_events 
GROUP BY status 
ORDER BY count DESC;

-- 8. 按风险等级统计
\echo ''
\echo '📈 按风险等级分布:'
SELECT risk_level, COUNT(*) as count 
FROM medical_events 
GROUP BY risk_level 
ORDER BY count DESC;

-- 9. 修复无效的枚举值 (取消注释以执行修复)
\echo ''
\echo '🔧 修复脚本 (需要手动执行):'
\echo '-- 修复无效的 agent_type'
\echo 'UPDATE medical_events SET agent_type = ''general'' WHERE agent_type NOT IN (''cardio'', ''derma'', ''ortho'', ''neuro'', ''general'', ''endo'', ''gastro'', ''respiratory'');'
\echo ''
\echo '-- 修复无效的 status'
\echo 'UPDATE medical_events SET status = ''active'' WHERE status NOT IN (''active'', ''completed'', ''exported'', ''archived'');'
\echo ''
\echo '-- 修复无效的 risk_level'
\echo 'UPDATE medical_events SET risk_level = ''low'' WHERE risk_level NOT IN (''low'', ''medium'', ''high'', ''emergency'');'
\echo ''
\echo '-- 修复空的 title'
\echo 'UPDATE medical_events SET title = ''病历事件 '' || id WHERE title IS NULL OR title = '''';'
\echo ''
\echo '-- 修复空的 department'
\echo 'UPDATE medical_events SET department = ''全科'' WHERE department IS NULL OR department = '''';'

\echo ''
\echo '============================================================'
\echo '✅ 检查完成'
\echo '============================================================'

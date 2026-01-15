-- 修复 medical_events 表的数据完整性问题
-- 使用方式: psql -d your_database -f fix_medical_events.sql

\echo '============================================================'
\echo '开始修复 medical_events 表数据完整性问题'
\echo '============================================================'

-- 开始事务
BEGIN;

-- 1. 修复无效的 agent_type
\echo ''
\echo '🔧 修复无效的 agent_type...'
UPDATE medical_events 
SET agent_type = 'general' 
WHERE agent_type NOT IN ('cardio', 'derma', 'ortho', 'neuro', 'general', 'endo', 'gastro', 'respiratory');

\echo '   受影响的行数:'
SELECT COUNT(*) FROM medical_events 
WHERE agent_type NOT IN ('cardio', 'derma', 'ortho', 'neuro', 'general', 'endo', 'gastro', 'respiratory');

-- 2. 修复无效的 status
\echo ''
\echo '🔧 修复无效的 status...'
UPDATE medical_events 
SET status = 'active' 
WHERE status NOT IN ('active', 'completed', 'exported', 'archived');

-- 3. 修复无效的 risk_level
\echo ''
\echo '🔧 修复无效的 risk_level...'
UPDATE medical_events 
SET risk_level = 'low' 
WHERE risk_level NOT IN ('low', 'medium', 'high', 'emergency');

-- 4. 修复空的 title
\echo ''
\echo '🔧 修复空的 title...'
UPDATE medical_events 
SET title = '病历事件 ' || id 
WHERE title IS NULL OR title = '';

-- 5. 修复空的 department
\echo ''
\echo '🔧 修复空的 department...'
UPDATE medical_events 
SET department = '全科' 
WHERE department IS NULL OR department = '';

-- 6. 修复 NULL 的 JSON 字段
\echo ''
\echo '🔧 修复 NULL 的 sessions 字段...'
UPDATE medical_events 
SET sessions = '[]'::json 
WHERE sessions IS NULL;

\echo ''
\echo '🔧 修复 NULL 的 ai_analysis 字段...'
UPDATE medical_events 
SET ai_analysis = '{}'::json 
WHERE ai_analysis IS NULL;

-- 7. 修复计数字段
\echo ''
\echo '🔧 修复 session_count...'
UPDATE medical_events 
SET session_count = 0 
WHERE session_count IS NULL;

\echo ''
\echo '🔧 修复 attachment_count...'
UPDATE medical_events 
SET attachment_count = 0 
WHERE attachment_count IS NULL;

\echo ''
\echo '🔧 修复 export_count...'
UPDATE medical_events 
SET export_count = 0 
WHERE export_count IS NULL;

-- 提交事务
COMMIT;

\echo ''
\echo '============================================================'
\echo '✅ 修复完成'
\echo '============================================================'

-- 验证修复结果
\echo ''
\echo '📊 修复后的数据统计:'
\echo ''
\echo '按科室分布:'
SELECT agent_type, COUNT(*) as count FROM medical_events GROUP BY agent_type ORDER BY count DESC;

\echo ''
\echo '按状态分布:'
SELECT status, COUNT(*) as count FROM medical_events GROUP BY status ORDER BY count DESC;

\echo ''
\echo '按风险等级分布:'
SELECT risk_level, COUNT(*) as count FROM medical_events GROUP BY risk_level ORDER BY count DESC;

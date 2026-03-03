-- ============================================
-- HIS 门诊 AI 助手系统数据库结构
-- ============================================
-- 说明：
-- 1. 本系统是为现有 HIS 系统赋能 AI，不需要独立的用户管理
-- 2. 用户身份由 HIS 系统传入（his_user_id）
-- 3. 患者 ID 也由 HIS 系统传入（his_patient_id）
-- 4. AI 系统只负责：对话能力 + 状态记忆 + 审计日志
--
-- 数据库: his_outpatient_ai
-- PostgreSQL 17+
-- ============================================

-- =====================================================
-- 表 1: Agent 状态表（核心 - 用于恢复对话）
-- =====================================================
CREATE TABLE IF NOT EXISTS agent_states (
    session_id TEXT PRIMARY KEY,
    his_user_id TEXT NOT NULL,
    his_patient_id TEXT,
    state_json JSONB NOT NULL,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_agent_states_user_id ON agent_states(his_user_id);
CREATE INDEX IF NOT EXISTS idx_agent_states_patient_id ON agent_states(his_patient_id);
CREATE INDEX IF NOT EXISTS idx_agent_states_updated_at ON agent_states(updated_at DESC);

-- 添加注释
COMMENT ON TABLE agent_states IS 'Agent 状态存储表，用于恢复跨会话对话';
COMMENT ON COLUMN agent_states.session_id IS '会话唯一标识';
COMMENT ON COLUMN agent_states.his_user_id IS 'HIS 系统的用户ID（医生ID）';
COMMENT ON COLUMN agent_states.his_patient_id IS 'HIS 系统的患者ID（可选）';
COMMENT ON COLUMN agent_states.state_json IS 'AutoGen save_state() 返回的完整状态（JSON格式）';
COMMENT ON COLUMN agent_states.message_count IS '当前会话的消息数量';

-- =====================================================
-- 表 2: 对话历史表（审计合规）
-- =====================================================
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    his_user_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(his_user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at DESC);

-- 添加注释
COMMENT ON TABLE chat_history IS '对话历史记录表，用于医疗合规审计';
COMMENT ON COLUMN chat_history.session_id IS '会话ID';
COMMENT ON COLUMN chat_history.his_user_id IS '操作用户ID（医生ID）';
COMMENT ON COLUMN chat_history.role IS '角色：user(用户)/assistant(AI)/system(系统)';
COMMENT ON COLUMN chat_history.content IS '消息内容';
COMMENT ON COLUMN chat_history.metadata IS '额外信息（如工具调用、模型参数等）';

-- =====================================================
-- 表 3: 审计日志表（监管合规）
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    his_user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_session_id ON audit_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(his_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- 添加注释
COMMENT ON TABLE audit_logs IS '审计日志表，记录所有系统操作用于监管合规';
COMMENT ON COLUMN audit_logs.session_id IS '会话ID';
COMMENT ON COLUMN audit_logs.his_user_id IS '操作用户ID';
COMMENT ON COLUMN audit_logs.event_type IS '事件类型：chat/tool_call/tool_result/error/state_save';
COMMENT ON COLUMN audit_logs.event_data IS '事件详细数据（JSON格式）';

-- =====================================================
-- 触发器：自动更新 updated_at
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_agent_states_updated_at
    BEFORE UPDATE ON agent_states
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 验证表创建
-- =====================================================

-- 显示所有创建的表
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
    AND table_name IN ('agent_states', 'chat_history', 'audit_logs')
ORDER BY table_name;

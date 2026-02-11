/**
 * 咨询/会话相关类型定义
 */

/**
 * 消息发送者类型
 */
export type SenderType = 'user' | 'ai';

/**
 * 对话消息
 */
export interface ConsultationMessage {
  id: number;
  session_id: string;
  sender: SenderType;
  content: string;
  message_type: string;
  attachments?: Attachment[];
  created_at: string;
}

/**
 * 附件
 */
export interface Attachment {
  type: string;
  url: string;
  thumbnail_url?: string;
  size?: number;
  name?: string;
}

/**
 * 对话会话
 */
export interface ConsultationSession {
  id: string;
  user_id: number;
  doctor_id?: number;
  agent_type: string;
  last_message?: string;
  status: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

/**
 * 对话详情响应
 */
export interface ConsultationDetailResponse {
  session: ConsultationSession;
  messages: ConsultationMessage[];
}

/**
 * 消息列表响应
 */
export interface MessageListResponse {
  messages: ConsultationMessage[];
  has_more: boolean;
}

/**
 * 创建会话请求
 */
export interface SessionCreateRequest {
  doctor_id?: number;
  agent_type?: string;
}

/**
 * 发送消息请求
 */
export interface MessageCreateRequest {
  content: string;
  action?: string;
  attachments?: Attachment[];
}

/**
 * 增强版消息请求
 */
export interface EnhancedMessageCreateRequest extends MessageCreateRequest {
  action: string;
}

/**
 * 增强版会话请求
 */
export interface EnhancedSessionCreateRequest extends SessionCreateRequest {
  agent_type: string;
}

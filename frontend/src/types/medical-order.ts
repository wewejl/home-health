/**
 * 医嘱相关类型定义
 */

/**
 * 医嘱类型
 */
export type OrderType = 'medication' | 'monitoring' | 'behavior' | 'followup';

/**
 * 调度类型
 */
export type ScheduleType = 'once' | 'daily' | 'weekly' | 'custom';

/**
 * 医嘱状态
 */
export type OrderStatus = 'draft' | 'active' | 'completed' | 'stopped';

/**
 * 任务状态
 */
export type TaskStatus = 'pending' | 'completed' | 'overdue' | 'skipped';

/**
 * 医嘱（主表）
 */
export interface MedicalOrder {
  id: number;
  patient_id: number;
  doctor_id?: number;
  order_type: OrderType;
  title: string;
  description?: string;
  schedule_type: ScheduleType;
  start_date: string;
  end_date?: string;
  frequency?: string;
  reminder_times: string[];
  weekdays: number[];
  ai_generated: boolean;
  ai_session_id?: string;
  status: OrderStatus;
  created_at: string;
  updated_at: string;
}

/**
 * 任务实例
 */
export interface TaskInstance {
  id: number;
  order_id: number;
  patient_id: number;
  scheduled_date: string;
  scheduled_time: string;
  status: TaskStatus;
  completed_at?: string;
  completion_notes?: string;
  // 关联医嘱信息
  order_title?: string;
  order_type?: string;
}

/**
 * 打卡记录
 */
export interface CompletionRecord {
  id: number;
  task_instance_id: number;
  completed_by: number;
  completion_type: string;
  value?: Record<string, unknown>;
  photo_url?: string;
  notes?: string;
  created_at: string;
}

/**
 * 依从性统计
 */
export interface ComplianceStats {
  date?: string;
  total: number;
  completed: number;
  overdue: number;
  pending: number;
  rate: number;
}

/**
 * 周依从性
 */
export interface WeeklyCompliance {
  daily_rates: number[];
  average_rate: number;
  dates: string[];
}

/**
 * 任务列表响应
 */
export interface TaskListResponse {
  date: string;
  pending: TaskInstance[];
  completed: TaskInstance[];
  overdue: TaskInstance[];
  summary: ComplianceStats;
}

/**
 * 家属关系
 */
export interface FamilyBond {
  id: number;
  patient_id: number;
  family_member_id: number;
  relationship_type: string;
  notification_level: string;
  family_member_name?: string;
  family_member_phone?: string;
  patient_name?: string;
}

/**
 * 激活医嘱请求
 */
export interface ActivateOrderRequest {
  confirm: boolean;
}

/**
 * 打卡记录请求
 */
export interface CompletionRecordRequest {
  task_instance_id: number;
  completion_type: string;
  value?: Record<string, unknown>;
  photo_url?: string;
  notes?: string;
}

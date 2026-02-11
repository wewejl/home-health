/**
 * 患者相关类型定义
 */

/**
 * 患者（医生工作台视图）
 */
export interface Patient {
  id: number;
  nickname?: string;
  phone: string;
  gender?: string;
  age?: number;
  last_consultation_at?: string;
  active_orders_count: number;
  completion_rate: number;
}

/**
 * 患者详情（扩展信息）
 */
export interface PatientDetail extends Patient {
  avatar_url?: string;
  is_profile_completed: boolean;
  created_at?: string;
}

/**
 * 可分配患者（用于添加患者对话框）
 */
export interface AssignablePatient {
  id: number;
  nickname: string;
  phone: string;
  gender?: string;
  age?: number;
  is_assigned: boolean;
  assigned_at?: string;
}

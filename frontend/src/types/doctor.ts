/**
 * 医生相关类型定义
 */

/**
 * 管理的 AI 分身信息
 */
export interface ManagedDoctorInfo {
  id: number;
  name: string;
  title?: string;
  department?: string;
}

/**
 * 医生信息
 */
export interface DoctorInfo {
  id: number;
  username: string;
  email?: string;
  role: string;
  department_id?: number;
  department_name?: string;
  managed_doctors: ManagedDoctorInfo[];
}

/**
 * 医生属性
 */
export interface DoctorAttributes {
  title?: string;
  specialty?: string;
  license_no?: string;
  hospital?: string;
}

/**
 * 患者统计数据
 */
export interface PatientStats {
  total: number;
  active: number;
  new_today: number;
  low_compliance: number;
}

/**
 * 患者分配请求
 */
export interface PatientAssignRequest {
  patient_id: number;
  relationship_type?: string;
  notes?: string;
}

/**
 * 患者分配响应
 */
export interface PatientAssignResponse {
  id: number;
  doctor_id: number;
  patient_id: number;
  relationship_type: string;
  is_active: boolean;
  notes?: string;
  assigned_at: string;
  created_at: string;
  updated_at?: string;
}

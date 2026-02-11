/**
 * 科室相关类型定义
 */

/**
 * 科室信息
 */
export interface Department {
  id: number;
  name: string;
  description?: string;
  icon?: string;
  created_at: string;
  updated_at: string;
}

/**
 * 科室列表项
 */
export interface DepartmentListItem {
  id: number;
  name: string;
  description?: string;
  icon?: string;
  doctors_count: number;
}

/**
 * 科室详情
 */
export interface DepartmentDetail extends Department {
  doctors: DepartmentDoctor[];
}

/**
 * 科室医生
 */
export interface DepartmentDoctor {
  id: number;
  name: string;
  title?: string;
  specialty?: string;
}

/**
 * 创建科室请求
 */
export interface DepartmentCreateRequest {
  name: string;
  description?: string;
  icon?: string;
}

/**
 * 更新科室请求
 */
export interface DepartmentUpdateRequest {
  name?: string;
  description?: string;
  icon?: string;
}

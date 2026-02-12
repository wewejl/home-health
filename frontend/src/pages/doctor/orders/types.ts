// 医嘱调度类型定义
export type ScheduleType = 'once' | 'daily' | 'weekly';

// 星期选项
export const WEEKDAY_OPTIONS = [
  { label: '周一', value: 1 },
  { label: '周二', value: 2 },
  { label: '周三', value: 3 },
  { label: '周四', value: 4 },
  { label: '周五', value: 5 },
  { label: '周六', value: 6 },
  { label: '周日', value: 0 },
];

// 调度类型选项
export const SCHEDULE_TYPE_OPTIONS = [
  { label: '一次性', value: 'once' },
  { label: '每日', value: 'daily' },
  { label: '每周', value: 'weekly' },
];

// 医嘱类型选项
export const ORDER_TYPE_OPTIONS = [
  { label: '用药任务', value: 'medication' },
  { label: '监测任务', value: 'monitoring' },
  { label: '行为任务', value: 'behavior' },
  { label: '复诊任务', value: 'followup' },
];

// 医嘱数据接口
export interface MedicalOrder {
  id: number;
  patient_id: number;
  doctor_id: number;
  order_type: string;
  title: string;
  description?: string;
  status: string;
  schedule_type?: string;
  start_date: string;
  end_date?: string;
  reminder_times?: string[];
  frequency?: string;
  created_at: string;
}

// 基础信息表单数据
export interface BasicInfoData {
  order_type?: string;
  title?: string;
  description?: string;
  end_date?: string;  // 编辑模式下的结束日期
}

// 调度配置表单数据
export interface ScheduleData {
  schedule_type?: ScheduleType;
  start_date?: string;
  end_date?: string;
  reminder_times?: string[];
  frequency?: string;
  weekdays?: number[];
}

// 表单错误类型
export interface FormErrors {
  order_type?: string;
  title?: string;
  schedule_type?: string;
  start_date?: string;
  reminder_times?: string;
  weekdays?: string;
  medications?: string;
}

// 药品类型
export interface Drug {
  id: number;
  name: string;
  generic_name?: string;
  specification?: string;
  manufacturer?: string;
  category?: string;
  unit?: string;
  stock_count?: number;
}

// 医嘱项目（药品/检查）
export interface OrderItem {
  item_type: 'drug' | 'examination';
  drug_id?: number;
  name: string;
  dosage?: string;
  frequency?: string;
  duration?: string;
  notes?: string;
  sort_order?: number;
}

// 医嘱模板类型
export interface OrderTemplate {
  id: number;
  name: string;
  description?: string;
  order_type: string;
  template_data: any;
  is_active: boolean;
  created_at: string;
}

// 步骤类型
export type StepType = 'basic' | 'schedule' | 'medications' | 'confirm';

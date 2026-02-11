/**
 * 角色常量定义
 *
 * 与后端 AdminRole 保持一致:
 * - backend/app/models/admin_user.py
 */

export const ROLES = {
  /** 系统管理员 */
  ADMIN: 'admin',
  /** 医生 */
  DOCTOR: 'doctor',
} as const;

/** 角色类型 */
export type Role = (typeof ROLES)[keyof typeof ROLES];

/** 角色显示名称映射 */
export const ROLE_LABELS: Record<Role, string> = {
  [ROLES.ADMIN]: '管理员',
  [ROLES.DOCTOR]: '医生',
};

/** 权限定义（预留扩展） */
export const PERMISSIONS = {
  // 管理员权限
  MANAGE_DEPARTMENTS: 'manage_departments',
  MANAGE_DOCTORS: 'manage_doctors',
  MANAGE_DISEASES: 'manage_diseases',
  MANAGE_DRUGS: 'manage_drugs',
  MANAGE_KNOWLEDGE: 'manage_knowledge',
  VIEW_STATS: 'view_stats',
  VIEW_FEEDBACKS: 'view_feedbacks',

  // 医生权限
  VIEW_PATIENTS: 'view_patients',
  ASSIGN_PATIENTS: 'assign_patients',
  MANAGE_ORDERS: 'manage_orders',
  VIEW_CONSULTATIONS: 'view_consultations',
} as const;

/** 权限类型 */
export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];

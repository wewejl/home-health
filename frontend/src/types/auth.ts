/**
 * 认证和授权相关类型定义
 */

import type { Role } from '@/constants/roles';

/**
 * 当前登录用户
 */
export interface CurrentUser {
  id: number;
  username: string;
  email?: string;
  role: Role;
  is_active: boolean;
}

/**
 * 登录响应
 */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  admin: CurrentUser;
}

/**
 * 登录请求
 */
export interface LoginRequest {
  username: string;
  password: string;
}

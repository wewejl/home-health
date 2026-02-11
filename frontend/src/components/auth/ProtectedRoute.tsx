/**
 * 权限守卫路由组件
 *
 * 用于保护需要特定角色才能访问的路由
 */

import { Navigate, Outlet } from 'react-router-dom';
import type { Role } from '@/constants/roles';

interface ProtectedRouteProps {
  /** 用户当前角色 */
  userRole?: Role | null;
  /** 允许访问的角色列表（空数组表示所有已登录用户） */
  allowedRoles?: Role[];
  /** 是否需要登录（false表示公开页面） */
  requireAuth?: boolean;
  /** 重定向路径（默认未登录跳转到登录页） */
  redirectTo?: string;
}

/**
 * 权限守卫组件
 *
 * 用作 <Route> 的 element，子路由通过 <Outlet /> 渲染
 *
 * @example
 * ```tsx
 * // 仅医生可访问的路由组
 * <Route element={<ProtectedRoute userRole={user?.role} allowedRoles={[ROLES.DOCTOR]} />}>
 *   <Route path="patients" element={<PatientList />} />
 * </Route>
 *
 * // 仅管理员可访问的路由组
 * <Route element={<ProtectedRoute userRole={user?.role} allowedRoles={[ROLES.ADMIN]} />}>
 *   <Route path="departments" element={<Departments />} />
 * </Route>
 * ```
 */
export function ProtectedRoute({
  userRole,
  allowedRoles = [],
  requireAuth = true,
  redirectTo,
}: ProtectedRouteProps) {
  // 未登录且需要登录
  if (requireAuth && !userRole) {
    return <Navigate to={redirectTo || '/login'} replace />;
  }

  // 已登录但角色不在允许列表中
  if (requireAuth && userRole && allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
    // 根据当前角色重定向到对应的首页
    const fallbackPath = userRole === 'doctor' ? '/patients' : '/';
    return <Navigate to={redirectTo || fallbackPath} replace />;
  }

  return <Outlet />;
}

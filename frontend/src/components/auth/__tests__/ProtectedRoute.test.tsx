/**
 * ProtectedRoute 组件测试
 *
 * 测试覆盖：
 * 1. 未认证用户重定向测试
 * 2. 已认证用户访问测试
 * 3. 角色权限验证测试
 * 4. 自定义重定向路径测试
 * 5. 公开路由测试 (requireAuth: false)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter, Routes, Route, MemoryRouter } from 'react-router-dom';
import { ProtectedRoute } from '../ProtectedRoute';

// Create a wrapper component to test ProtectedRoute in isolation
const TestWrapper = ({
  userRole,
  allowedRoles = [],
  requireAuth = true,
  redirectTo,
  children,
}: {
  userRole: string | null | undefined;
  allowedRoles?: string[];
  requireAuth?: boolean;
  redirectTo?: string;
  children: React.ReactNode;
}) => {
  return (
    <MemoryRouter initialEntries={['/protected']}>
      <Routes>
        <Route
          path="/protected"
          element={
            <ProtectedRoute
              userRole={userRole}
              allowedRoles={allowedRoles}
              requireAuth={requireAuth}
              redirectTo={redirectTo}
            />
          }
        >
          <Route index element={children} />
        </Route>
        <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />
        <Route path="/patients" element={<div data-testid="patients-page">Patients Page</div>} />
        <Route path="/custom-login" element={<div data-testid="custom-login">Custom Login</div>} />
        <Route path="/unauthorized" element={<div data-testid="unauthorized">Unauthorized</div>} />
        <Route path="/" element={<div data-testid="home-page">Home Page</div>} />
      </Routes>
    </MemoryRouter>
  );
};

describe('ProtectedRoute Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Unauthenticated User', () => {
    it('should redirect to login when userRole is null and requireAuth is true', () => {
      render(
        <TestWrapper userRole={null} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });

    it('should redirect to login when userRole is undefined and requireAuth is true', () => {
      render(
        <TestWrapper userRole={undefined} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });

    it('should redirect to custom path when redirectTo is provided', () => {
      render(
        <TestWrapper userRole={null} requireAuth={true} redirectTo="/custom-login">
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.getByTestId('custom-login')).toBeInTheDocument();
    });
  });

  describe('Authenticated User', () => {
    it('should render content when user is authenticated with valid role', () => {
      render(
        <TestWrapper userRole="admin" allowedRoles={['admin']} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should render content when user is authenticated with no role restrictions', () => {
      render(
        <TestWrapper userRole="admin" allowedRoles={[]} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should render content when user role is in allowedRoles list', () => {
      render(
        <TestWrapper userRole="doctor" allowedRoles={['admin', 'doctor']} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Role-based Access Control', () => {
    it('should redirect to fallback when user role is not in allowedRoles', () => {
      render(
        <TestWrapper userRole="user" allowedRoles={['admin', 'doctor']} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      // User role should redirect to / (not admin or doctor)
      expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });

    it('should redirect to /patients when user is doctor but not allowed', () => {
      render(
        <TestWrapper userRole="doctor" allowedRoles={['admin']} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.getByTestId('patients-page')).toBeInTheDocument();
    });

    it('should redirect to custom path when provided and role is not allowed', () => {
      render(
        <TestWrapper userRole="user" allowedRoles={['admin']} requireAuth={true} redirectTo="/unauthorized">
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.getByTestId('unauthorized')).toBeInTheDocument();
    });

    it('should allow access when user role matches exactly', () => {
      render(
        <TestWrapper userRole="admin" allowedRoles={['admin']} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should allow access to multiple allowed roles', () => {
      const manyRoles = ['admin', 'doctor', 'nurse'];

      render(
        <TestWrapper userRole="doctor" allowedRoles={manyRoles} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Public Routes (requireAuth: false)', () => {
    it('should render content when requireAuth is false and user is not authenticated', () => {
      render(
        <TestWrapper userRole={null} allowedRoles={[]} requireAuth={false}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should render content when requireAuth is false and user is authenticated', () => {
      render(
        <TestWrapper userRole="admin" allowedRoles={[]} requireAuth={false}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should render content when requireAuth is false regardless of role restrictions', () => {
      render(
        <TestWrapper userRole="user" allowedRoles={['admin']} requireAuth={false}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should render content when requireAuth is false with empty allowedRoles', () => {
      render(
        <TestWrapper userRole={undefined} allowedRoles={[]} requireAuth={false}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty string as userRole', () => {
      render(
        <TestWrapper userRole={''} allowedRoles={[]} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      // Empty string is falsy, so should redirect to login
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });

    it('should handle numeric userRole (truthy value)', () => {
      render(
        <TestWrapper userRole={1 as any} allowedRoles={[]} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      // Numeric 1 is truthy, and allowedRoles is empty, so it should render
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should handle role with special characters', () => {
      render(
        <TestWrapper userRole="super-admin_123" allowedRoles={['super-admin_123']} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should handle large allowedRoles array', () => {
      const manyRoles = ['admin', 'doctor', 'nurse', 'pharmacist', 'receptionist', 'lab-tech', 'radiologist'];

      render(
        <TestWrapper userRole="doctor" allowedRoles={manyRoles} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Default Redirect Behavior', () => {
    it('should use default /login redirect when userRole is null', () => {
      render(
        <TestWrapper userRole={null} allowedRoles={[]} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });

    it('should use default /patients redirect for doctor role when not allowed', () => {
      render(
        <TestWrapper userRole="doctor" allowedRoles={['admin']} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('patients-page')).toBeInTheDocument();
    });

    it('should use default / redirect for other roles when not allowed', () => {
      render(
        <TestWrapper userRole="nurse" allowedRoles={['admin']} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });
  });

  describe('Component Rendering', () => {
    it('should render Outlet when conditions are met', () => {
      render(
        <TestWrapper userRole="admin" allowedRoles={['admin']} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
          <div data-testid="additional-content">Additional Content</div>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
      expect(screen.getByTestId('additional-content')).toBeInTheDocument();
    });

    it('should not render Outlet when conditions are not met', () => {
      render(
        <TestWrapper userRole={null} allowedRoles={[]} requireAuth={true}>
          <div data-testid="protected-content">Protected Content</div>
        </TestWrapper>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });
  });
});

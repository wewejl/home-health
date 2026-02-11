import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useSearchParams } from 'react-router-dom';
import { ThemeProvider } from './components/theme-provider';
import { ToastProvider } from '@/components/ui/toast';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { ROLES } from './constants/roles';
import type { CurrentUser } from './types/auth';
import MainLayout from './layouts/MainLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Doctors from './pages/Doctors';
import Departments from './pages/Departments';
import Diseases from './pages/Diseases';
import Drugs from './pages/Drugs';
import Knowledge from './pages/Knowledge';
import Feedbacks from './pages/Feedbacks';
import Stats from './pages/Stats';
import MedicalOrders from './pages/MedicalOrders';
import PatientCompliance from './pages/PatientCompliance';
import Rounding from './pages/Rounding';
import RoundingDetail from './pages/RoundingDetail';
import DoctorPersonaChat from './pages/admin/DoctorPersonaChat';
import DoctorRecordAnalysis from './pages/admin/DoctorRecordAnalysis';
// 医生工作台页面
import PatientList from './pages/doctor/PatientList';
import PatientDetail from './pages/doctor/PatientDetail';

// 读取测试模式配置（可通过环境变量 VITE_ADMIN_TEST_MODE 关闭）
const ADMIN_TEST_MODE = import.meta.env.VITE_ADMIN_TEST_MODE === 'true';

// 内部组件：用于获取 URL 参数
function AppContent() {
  const [isAuthenticated, setIsAuthenticated] = useState(ADMIN_TEST_MODE);  // 根据环境变量决定默认状态
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    // 测试模式：使用虚拟用户
    if (ADMIN_TEST_MODE) {
      // 优先级：1. URL参数 > 2. localStorage > 3. 默认值
      const urlRole = searchParams.get('role');
      const localRole = localStorage.getItem('test_role');

      // 确定使用的角色
      let role: typeof ROLES[keyof typeof ROLES] = ROLES.DOCTOR;  // 默认角色
      if (urlRole === ROLES.ADMIN || urlRole === ROLES.DOCTOR) {
        role = urlRole;
        localStorage.setItem('test_role', role);
      } else if (localRole === ROLES.ADMIN || localRole === ROLES.DOCTOR) {
        role = localRole;
      }

      const testUser: CurrentUser = {
        id: 1,
        username: role === ROLES.DOCTOR ? "test_doctor" : "test_admin",
        role: role,
        is_active: true
      };

      setUser(testUser);
      setIsAuthenticated(true);
      setLoading(false);
      return;
    }

    // 生产模式：从 localStorage 恢复用户信息
    const token = localStorage.getItem('admin_token');
    const userStr = localStorage.getItem('admin_user');

    if (token && userStr) {
      try {
        const savedUser = JSON.parse(userStr);
        setUser(savedUser);
        setIsAuthenticated(true);
      } catch (e) {
        console.error('Failed to parse user from localStorage:', e);
        setIsAuthenticated(false);
      }
    } else {
      setIsAuthenticated(false);
    }
    setLoading(false);
  }, [searchParams]);

  const handleLogin = (token: string, adminUser: CurrentUser) => {
    localStorage.setItem('admin_token', token);
    localStorage.setItem('admin_user', JSON.stringify(adminUser));
    setUser(adminUser);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    setUser(null);
    setIsAuthenticated(false);
  };

  if (loading) {
    return null;
  }

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // 可以在这里将错误上报到日志服务
        console.error('Application error:', error, errorInfo);
      }}
    >
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <ToastProvider>
          <Routes>
          <Route
              path="/login"
              element={
                isAuthenticated ? (
                  <Navigate to="/" replace />
                ) : (
                  <Login onLogin={handleLogin} />
                )
              }
            />
            <Route
              path="/"
              element={
                isAuthenticated ? (
                  <MainLayout user={user} onLogout={handleLogout} />
                ) : (
                  <Navigate to="/login" replace />
                )
              }
            >
              {/* 医生路由 */}
              <Route element={<ProtectedRoute userRole={user?.role} allowedRoles={[ROLES.DOCTOR]} />}>
                <Route index element={<Navigate to="/patients" replace />} />
                <Route path="patients" element={<PatientList />} />
                <Route path="patients/:patientId" element={<PatientDetail />} />
              </Route>

              {/* 管理员路由 */}
              <Route element={<ProtectedRoute userRole={user?.role} allowedRoles={[ROLES.ADMIN]} />}>
                <Route index element={<Dashboard />} />
                <Route path="departments" element={<Departments />} />
                <Route path="doctors" element={<Doctors />} />
                <Route path="doctors/:id/persona" element={<DoctorPersonaChat />} />
                <Route path="doctors/:id/analyze" element={<DoctorRecordAnalysis />} />
                <Route path="diseases" element={<Diseases />} />
                <Route path="drugs" element={<Drugs />} />
                <Route path="knowledge" element={<Knowledge />} />
                <Route path="feedbacks" element={<Feedbacks />} />
                <Route path="stats" element={<Stats />} />
                <Route path="medical-orders" element={<MedicalOrders />} />
                <Route path="patient-compliance" element={<PatientCompliance />} />
                <Route path="rounding" element={<Rounding />} />
                <Route path="rounding/:patientId" element={<RoundingDetail />} />
              </Route>
            </Route>
          </Routes>
        </ToastProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

// 主 App 组件，只负责提供 BrowserRouter
function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;

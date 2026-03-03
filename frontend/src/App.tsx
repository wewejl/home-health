import { useEffect, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useSearchParams } from 'react-router-dom';
import { ThemeProvider } from './components/theme-provider';
import { ToastProvider } from '@/components/ui/toast';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { ROLES } from './constants/roles';
import { useAuthStore } from './store/authStore';
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
import PatientList from './pages/doctor/PatientList';
import PatientDetail from './pages/doctor/PatientDetail';

// 代码分割 - 使用 React.lazy() 按需加载大型页面
const Rounding = lazy(() => import('./pages/Rounding'));
const RoundingDetail = lazy(() => import('./pages/RoundingDetail'));
const DoctorPersonaChat = lazy(() => import('./pages/admin/DoctorPersonaChat'));
const DoctorRecordAnalysis = lazy(() => import('./pages/admin/DoctorRecordAnalysis'));

// 加载中组件
const PageLoading = () => (
  <div className="flex items-center justify-center min-h-[400px]">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
  </div>
);

// 内部组件：用于获取 URL 参数并初始化认证
function AppContent() {
  const { isAuthenticated, user, isLoading, setAuth, logout, initialize } = useAuthStore();
  const [searchParams] = useSearchParams();

  // 读取测试模式配置（可通过环境变量 VITE_ADMIN_TEST_MODE 关闭）
  const ADMIN_TEST_MODE = import.meta.env.VITE_ADMIN_TEST_MODE === 'true';

  useEffect(() => {
    // 获取 URL 中的角色参数
    const urlRole = searchParams.get('role');

    // 初始化认证状态
    initialize(ADMIN_TEST_MODE, urlRole || undefined);
  }, [searchParams, initialize, ADMIN_TEST_MODE]);

  const handleLogin = (token: string, adminUser: CurrentUser) => {
    setAuth(token, adminUser);
  };

  const handleLogout = () => {
    logout();
  };

  // 初始化中显示加载状态
  if (isLoading) {
    return <PageLoading />;
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
          <Suspense fallback={<PageLoading />}>
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
          </Suspense>
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

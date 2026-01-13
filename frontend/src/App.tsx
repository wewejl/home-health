import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
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
import DermaChat from './pages/DermaChat';

interface AdminUser {
  id: number;
  username: string;
  email?: string;
  role: string;
  is_active: boolean;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<AdminUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    const userStr = localStorage.getItem('admin_user');
    if (token && userStr) {
      try {
        setUser(JSON.parse(userStr));
        setIsAuthenticated(true);
      } catch {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_user');
      }
    }
    setLoading(false);
  }, []);

  const handleLogin = (token: string, adminUser: AdminUser) => {
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
    <ConfigProvider locale={zhCN}>
      <AntApp>
        <BrowserRouter>
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
              <Route index element={<Dashboard />} />
              <Route path="departments" element={<Departments />} />
              <Route path="doctors" element={<Doctors />} />
              <Route path="diseases" element={<Diseases />} />
              <Route path="drugs" element={<Drugs />} />
              <Route path="knowledge" element={<Knowledge />} />
              <Route path="feedbacks" element={<Feedbacks />} />
              <Route path="stats" element={<Stats />} />
              <Route path="derma-chat" element={<DermaChat />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
}

export default App;

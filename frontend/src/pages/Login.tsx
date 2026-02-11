import React, { useState } from 'react';
import { User, Lock, Eye, EyeOff } from 'lucide-react';
import { authApi } from '../api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import type { CurrentUser } from '@/types/auth';

interface LoginProps {
  onLogin: (token: string, user: CurrentUser) => void;
}

interface FormErrors {
  username?: string;
  password?: string;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!username.trim()) {
      newErrors.username = '请输入用户名';
    }
    if (!password) {
      newErrors.password = '请输入密码';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 清除之前的消息
    setErrorMessage('');
    setSuccessMessage('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const response = await authApi.login(username, password);
      const { access_token, admin } = response.data;
      onLogin(access_token, admin);
      setSuccessMessage('登录成功');
    } catch (error: any) {
      setErrorMessage(error.response?.data?.detail || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-sky-500 via-blue-500 to-indigo-600 dark:from-sky-900 dark:via-blue-900 dark:to-indigo-950 p-4">
      <Card className="w-full max-w-md shadow-xl animate-fade-in">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
            <User className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="text-2xl font-bold">灵犀健康</CardTitle>
          <CardDescription className="text-base">智能健康管理平台</CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* 公司信息 */}
          <div className="text-center space-y-1 text-xs text-foreground-secondary py-2 border-y border-border/50">
            <div className="font-medium">岳阳琳烨网络科技有限公司</div>
            <div className="text-[10px] mt-1">
              <span>邮箱: 1024344053@qq.com</span>
              <span className="mx-2">|</span>
              <span>电话: 18107300167</span>
            </div>
            <div className="text-[10px] mt-1 max-w-[280px] mx-auto leading-tight">
              湖南省岳阳市岳阳楼区三眼桥街道李家冲社区居民委员大楼605室
            </div>
          </div>

          {/* 消息提示 */}
          {successMessage && (
            <div className="p-3 rounded-lg bg-success-light/80 text-success text-sm border border-success/20">
              {successMessage}
            </div>
          )}
          {errorMessage && (
            <div className="p-3 rounded-lg bg-danger-light/80 text-danger text-sm border border-danger/20">
              {errorMessage}
            </div>
          )}

          {/* 登录表单 */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm font-medium">
                用户名
              </Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-secondary" />
                <Input
                  id="username"
                  type="text"
                  placeholder="请输入用户名"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className={`pl-10 h-10 ${errors.username ? 'border-danger focus-visible:ring-danger' : ''}`}
                  disabled={loading}
                />
              </div>
              {errors.username && (
                <p className="text-xs text-danger">{errors.username}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">
                密码
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-secondary" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="请输入密码"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`pl-10 pr-10 h-10 ${errors.password ? 'border-danger focus-visible:ring-danger' : ''}`}
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={togglePasswordVisibility}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground-secondary hover:text-foreground transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="text-xs text-danger">{errors.password}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full h-10 mt-2"
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                  登录中...
                </span>
              ) : (
                '登录'
              )}
            </Button>
          </form>
        </CardContent>

        <CardFooter className="flex justify-center">
          <p className="text-xs text-foreground-secondary">
            默认账号: <span className="font-medium text-foreground">admin</span> / <span className="font-medium text-foreground">admin123</span>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
};

export default Login;

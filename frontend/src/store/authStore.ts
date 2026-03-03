import { create } from 'zustand';
import type { CurrentUser } from '@/types/auth';
import { ROLES } from '@/constants/roles';

/**
 * 认证状态管理 Store
 *
 * 使用方式：
 * ```tsx
 * import { useAuthStore } from '@/store/authStore';
 *
 * // 获取状态
 * const { isAuthenticated, user } = useAuthStore();
 *
 * // 登录
 * const { setAuth } = useAuthStore();
 * setAuth(token, user);
 *
 * // 登出
 * const { logout } = useAuthStore();
 * logout();
 * ```
 */

interface AdminUser {
  id: number;
  username: string;
  email?: string;
  role: string;
  is_active: boolean;
}

interface AuthState {
  /** JWT Token */
  token: string | null;
  /** 当前用户信息 */
  user: AdminUser | null;
  /** 是否已认证 */
  isAuthenticated: boolean;
  /** 是否正在初始化 */
  isLoading: boolean;

  /** 设置认证信息（登录成功后调用） */
  setAuth: (token: string, user: AdminUser) => void;

  /** 清除认证信息（登出） */
  logout: () => void;

  /** 从 localStorage 恢复认证状态 */
  loadFromStorage: () => void;

  /** 初始化认证状态（测试模式或从存储恢复） */
  initialize: (testMode?: boolean, testRole?: string) => void;
}

const STORAGE_TOKEN_KEY = 'admin_token';
const STORAGE_USER_KEY = 'admin_user';
const STORAGE_TEST_ROLE_KEY = 'test_role';

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setAuth: (token: string, user: AdminUser) => {
    localStorage.setItem(STORAGE_TOKEN_KEY, token);
    localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(user));
    set({ token, user, isAuthenticated: true, isLoading: false });
  },

  logout: () => {
    localStorage.removeItem(STORAGE_TOKEN_KEY);
    localStorage.removeItem(STORAGE_USER_KEY);
    set({ token: null, user: null, isAuthenticated: false, isLoading: false });
  },

  loadFromStorage: () => {
    const token = localStorage.getItem(STORAGE_TOKEN_KEY);
    const userStr = localStorage.getItem(STORAGE_USER_KEY);

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        set({ token, user, isAuthenticated: true, isLoading: false });
      } catch {
        // 解析失败，清除无效数据
        localStorage.removeItem(STORAGE_TOKEN_KEY);
        localStorage.removeItem(STORAGE_USER_KEY);
        set({ token: null, user: null, isAuthenticated: false, isLoading: false });
      }
    } else {
      set({ isLoading: false });
    }
  },

  initialize: (testMode = false, testRole?: string) => {
    if (testMode) {
      // 测试模式：使用虚拟用户
      let role: typeof ROLES[keyof typeof ROLES] = ROLES.DOCTOR;

      // 优先级：1. 参数 > 2. localStorage > 3. 默认值
      if (testRole === ROLES.ADMIN || testRole === ROLES.DOCTOR) {
        role = testRole;
        localStorage.setItem(STORAGE_TEST_ROLE_KEY, role);
      } else {
        const localRole = localStorage.getItem(STORAGE_TEST_ROLE_KEY);
        if (localRole === ROLES.ADMIN || localRole === ROLES.DOCTOR) {
          role = localRole;
        }
      }

      const testUser: AdminUser = {
        id: 1,
        username: role === ROLES.DOCTOR ? 'test_doctor' : 'test_admin',
        role: role,
        is_active: true,
      };

      set({ token: 'test_token', user: testUser, isAuthenticated: true, isLoading: false });
    } else {
      // 生产模式：从 localStorage 恢复
      const token = localStorage.getItem(STORAGE_TOKEN_KEY);
      const userStr = localStorage.getItem(STORAGE_USER_KEY);

      if (token && userStr) {
        try {
          const user = JSON.parse(userStr);
          set({ token, user, isAuthenticated: true, isLoading: false });
        } catch {
          set({ token: null, user: null, isAuthenticated: false, isLoading: false });
        }
      } else {
        set({ token: null, user: null, isAuthenticated: false, isLoading: false });
      }
    }
  },
}));

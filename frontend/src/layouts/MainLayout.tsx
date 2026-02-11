import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Database,
  MessageSquare,
  BarChart3,
  LogOut,
  Stethoscope,
  FileSearch,
  Monitor,
  Heart,
  Video,
  ChevronDown,
} from 'lucide-react';

import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from '@/components/ui/navigation-menu';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar } from '@/components/ui/avatar';
import { ThemeToggle } from '@/components/theme-toggle';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { cn } from '@/lib/utils';
import { ROLES, ROLE_LABELS } from '@/constants/roles';
import type { CurrentUser } from '@/types/auth';

interface MainLayoutProps {
  user: CurrentUser | null;
  onLogout: () => void;
}

interface MenuGroup {
  label: string;
  items: {
    key: string;
    icon: React.ReactNode;
    label: string;
    description?: string;
  }[];
}

const MainLayout: React.FC<MainLayoutProps> = ({ user, onLogout }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // 管理员菜单分组
  const adminMenuGroups: MenuGroup[] = [
    {
      label: '核心管理',
      items: [
        {
          key: '/',
          icon: <LayoutDashboard className="h-4 w-4" />,
          label: '仪表盘',
          description: '系统运营数据和关键指标',
        },
        {
          key: '/departments',
          icon: <Stethoscope className="h-4 w-4" />,
          label: '科室管理',
          description: '管理医院科室信息',
        },
        {
          key: '/doctors',
          icon: <Users className="h-4 w-4" />,
          label: '医生管理',
          description: '管理医生账号和AI分身',
        },
      ],
    },
    {
      label: '知识管理',
      items: [
        {
          key: '/diseases',
          icon: <FileSearch className="h-4 w-4" />,
          label: '疾病百科',
          description: '疾病知识库管理',
        },
        {
          key: '/drugs',
          icon: <Stethoscope className="h-4 w-4" />,
          label: '药品百科',
          description: '药品信息管理',
        },
        {
          key: '/knowledge',
          icon: <Database className="h-4 w-4" />,
          label: '知识库管理',
          description: 'AI知识库配置',
        },
      ],
    },
    {
      label: '监督分析',
      items: [
        {
          key: '/medical-orders',
          icon: <Heart className="h-4 w-4" />,
          label: '医嘱执行监督',
          description: '患者医嘱执行情况',
        },
        {
          key: '/patient-compliance',
          icon: <Monitor className="h-4 w-4" />,
          label: '患者依从性',
          description: '患者依从性分析',
        },
        {
          key: '/rounding',
          icon: <Video className="h-4 w-4" />,
          label: '远程查房',
          description: '远程视频查房',
        },
        {
          key: '/stats',
          icon: <BarChart3 className="h-4 w-4" />,
          label: '统计分析',
          description: '数据统计分析',
        },
        {
          key: '/feedbacks',
          icon: <MessageSquare className="h-4 w-4" />,
          label: '反馈管理',
          description: '用户反馈处理',
        },
      ],
    },
  ];

  // 医生菜单
  const doctorMenuGroups: MenuGroup[] = [
    {
      label: '医生工作台',
      items: [
        {
          key: '/patients',
          icon: <Users className="h-4 w-4" />,
          label: '我的患者',
          description: '管理我的患者列表',
        },
      ],
    },
  ];

  // 根据角色选择菜单
  const menuGroups = user?.role === ROLES.DOCTOR ? doctorMenuGroups : adminMenuGroups;

  const handleNavigate = (key: string) => {
    navigate(key);
  };

  const handleLogout = () => {
    onLogout();
  };

  const isActiveRoute = (key: string) => {
    return location.pathname === key;
  };

  // 渲染顶部导航菜单
  const renderTopNavigation = () => (
    <NavigationMenu className="hidden lg:flex">
      <NavigationMenuList>
        {menuGroups.map((group) => (
          <NavigationMenuItem key={group.label}>
            <NavigationMenuTrigger className="bg-background">
              {group.label}
            </NavigationMenuTrigger>
            <NavigationMenuContent>
              <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2 lg:w-[600px]">
                {group.items.map((item) => (
                  <li key={item.key}>
                    <NavigationMenuLink
                      onClick={() => handleNavigate(item.key)}
                      className={cn(
                        "block select-none space-y-1 rounded-md p-3 leading-none no-underline outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground cursor-pointer",
                        isActiveRoute(item.key) && "bg-accent text-accent-foreground"
                      )}
                    >
                      <div className="flex items-center gap-2 text-sm font-medium">
                        {item.icon}
                        {item.label}
                      </div>
                      <p className="line-clamp-2 text-sm leading-snug text-muted-foreground">
                        {item.description}
                      </p>
                    </NavigationMenuLink>
                  </li>
                ))}
              </ul>
            </NavigationMenuContent>
          </NavigationMenuItem>
        ))}
      </NavigationMenuList>
    </NavigationMenu>
  );

  // 渲染移动端菜单
  const renderMobileMenu = () => (
    <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
      <SheetTrigger className="lg:hidden fixed top-4 left-4 z-50 rounded-md p-2 hover:bg-accent">
        <svg
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </SheetTrigger>
      <SheetContent side="left" className="w-80">
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center border-b">
            <h2 className="text-lg text-primary">灵犀健康</h2>
          </div>

          {/* 菜单列表 */}
          <div className="flex-1 overflow-y-auto py-4">
            {menuGroups.map((group) => (
              <div key={group.label} className="mb-6">
                <h3 className="mb-2 px-4 text-xs font-semibold text-foreground-secondary">
                  {group.label}
                </h3>
                <ul className="space-y-1">
                  {group.items.map((item) => (
                    <li key={item.key}>
                      <button
                        onClick={() => {
                          handleNavigate(item.key);
                          setMobileMenuOpen(false);
                        }}
                        className={cn(
                          "flex w-full items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors",
                          isActiveRoute(item.key)
                            ? "bg-primary text-primary-foreground"
                            : "text-foreground hover:bg-accent"
                        )}
                      >
                        {item.icon}
                        <span>{item.label}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );

  // 平板端简化导航
  const renderTabletNavigation = () => (
    <div className="hidden md:flex lg:hidden items-center gap-1 overflow-x-auto">
      {menuGroups.map((group) => (
        <DropdownMenu key={group.label}>
          <DropdownMenuTrigger className="flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-md hover:bg-accent data-[state=open]:bg-accent">
            {group.label}
            <ChevronDown className="h-3 w-3" />
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56">
            {group.items.map((item) => (
              <DropdownMenuItem
                key={item.key}
                onClick={() => handleNavigate(item.key)}
                className={cn(
                  "flex items-center gap-2 cursor-pointer",
                  isActiveRoute(item.key) && "bg-accent"
                )}
              >
                {item.icon}
                <span>{item.label}</span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      ))}
    </div>
  );

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-white px-4 md:px-6 dark:bg-gray-900">
        {/* 左侧：Logo + 导航 */}
        <div className="flex items-center gap-6">
          {/* 移动端菜单占位 */}
          <div className="lg:hidden w-10" />

          {/* Logo */}
          <div
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => handleNavigate('/')}
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Heart className="h-4 w-4" />
            </div>
            <span className="text-lg font-semibold text-primary">灵犀健康</span>
          </div>

          {/* 顶部导航菜单 */}
          {renderTopNavigation()}
          {renderTabletNavigation()}
        </div>

        {/* 右侧：主题切换 + 用户菜单 */}
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-accent data-[state=open]:bg-accent">
              <Avatar />
              <span className="hidden md:inline">
                {user?.username}
                <span className="ml-1 text-muted-foreground">
                  ({user?.role ? ROLE_LABELS[user.role] : ''})
                </span>
              </span>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-48 right-0">
              <DropdownMenuLabel>
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium">{user?.username}</p>
                  <p className="text-xs text-muted-foreground">
                    {user?.role ? ROLE_LABELS[user.role] : ''}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleLogout}
                className="text-danger cursor-pointer"
              >
                <LogOut className="mr-2 h-4 w-4" />
                退出登录
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* 移动端侧边栏 */}
      {renderMobileMenu()}

      {/* 主内容区域 */}
      <main className="flex-1 p-4 md:p-6 lg:p-8">
        <div className="mx-auto max-w-7xl">
          <Outlet />
        </div>
      </main>

      {/* 页脚 */}
      <footer className="border-t bg-white py-6 dark:bg-gray-900">
        <div className="mx-auto max-w-7xl px-4 text-center text-xs text-muted-foreground md:px-6">
          <div className="mb-2">
            <strong>灵犀健康</strong> © {new Date().getFullYear()} 岳阳琳烨网络科技有限公司
          </div>
          <div className="flex items-center justify-center gap-4">
            <span>邮箱: 1024344053@qq.com</span>
            <span>|</span>
            <span>电话: 18107300167</span>
          </div>
          <div className="mt-2">
            湖南省岳阳市岳阳楼区三眼桥街道李家冲社区居民委员大楼605室
          </div>
        </div>
      </footer>
    </div>
  );
};

export default MainLayout;

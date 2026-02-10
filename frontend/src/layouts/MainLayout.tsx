import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Database,
  MessageSquare,
  BarChart3,
  LogOut,
  Menu,
  X,
  Stethoscope,
  FileSearch,
  Bot,
  Monitor,
  Heart,
  Video,
  UsersRound,
} from 'lucide-react';

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
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface MainLayoutProps {
  user: { username: string; role: string } | null;
  onLogout: () => void;
}

interface MenuItem {
  key: string;
  icon: React.ReactNode;
  label: string;
}

const MainLayout: React.FC<MainLayoutProps> = ({ user, onLogout }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // 医生专用菜单
  const doctorMenuItems: MenuItem[] = [
    {
      key: '/patients',
      icon: <UsersRound className="h-5 w-5" />,
      label: '我的患者',
    },
  ];

  // 管理员菜单
  const adminMenuItems: MenuItem[] = [
    {
      key: '/',
      icon: <LayoutDashboard className="h-5 w-5" />,
      label: '仪表盘',
    },
    {
      key: '/derma-chat',
      icon: <Bot className="h-5 w-5" />,
      label: '皮肤科AI对话',
    },
    {
      key: '/departments',
      icon: <Stethoscope className="h-5 w-5" />,
      label: '科室管理',
    },
    {
      key: '/doctors',
      icon: <Users className="h-5 w-5" />,
      label: '医生管理',
    },
    {
      key: '/diseases',
      icon: <FileSearch className="h-5 w-5" />,
      label: '疾病百科',
    },
    {
      key: '/drugs',
      icon: <Stethoscope className="h-5 w-5" />,
      label: '药品百科',
    },
    {
      key: '/knowledge',
      icon: <Database className="h-5 w-5" />,
      label: '知识库管理',
    },
    {
      key: '/feedbacks',
      icon: <MessageSquare className="h-5 w-5" />,
      label: '反馈管理',
    },
    {
      key: '/stats',
      icon: <BarChart3 className="h-5 w-5" />,
      label: '统计分析',
    },
    {
      key: '/medical-orders',
      icon: <Heart className="h-5 w-5" />,
      label: '医嘱执行监督',
    },
    {
      key: '/patient-compliance',
      icon: <Monitor className="h-5 w-5" />,
      label: '患者依从性',
    },
    {
      key: '/rounding',
      icon: <Video className="h-5 w-5" />,
      label: '远程查房',
    },
  ];

  // 根据角色选择菜单
  const menuItems = user?.role === 'doctor' ? doctorMenuItems : adminMenuItems;

  const handleMenuClick = (key: string) => {
    navigate(key);
    // 移动端点击后关闭菜单
    if (window.innerWidth < 768) {
      setMobileMenuOpen(false);
    }
  };

  const handleLogout = () => {
    onLogout();
  };

  const isActiveRoute = (key: string) => {
    return location.pathname === key;
  };

  // Render menu items as buttons
  const renderMenuItems = () => (
    <ul className="space-y-1 p-2">
      {menuItems.map((item) => (
        <li key={item.key}>
          <button
            onClick={() => handleMenuClick(item.key)}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              isActiveRoute(item.key)
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            )}
            title={collapsed ? item.label : undefined}
          >
            {item.icon}
            {!collapsed && <span>{item.label}</span>}
          </button>
        </li>
      ))}
    </ul>
  );

  return (
    <div className="flex min-h-screen bg-background">
      {/* 移动端侧边栏 - 使用 Sheet 组件 */}
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
        <SheetTrigger
          className="md:hidden fixed top-4 left-4 z-50 rounded-md p-2 hover:bg-accent"
        >
          <Menu className="h-5 w-5" />
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <div className="flex h-screen flex-col">
            {/* Logo 区域 */}
            <div className="flex h-16 items-center justify-center border-b">
              <h2 className="text-lg text-primary">灵犀健康</h2>
            </div>
            {/* 菜单区域 - 使用 ScrollArea */}
            <ScrollArea className="flex-1">
              {renderMenuItems()}
            </ScrollArea>
          </div>
        </SheetContent>
      </Sheet>

      {/* 桌面端侧边栏 */}
      <aside
        className={cn(
          "hidden md:flex md:flex-col md:border-r md:bg-card md:transition-all",
          collapsed ? "md:w-16" : "md:w-64"
        )}
      >
        {/* Logo 区域 */}
        <div className="flex h-16 items-center justify-center border-b">
          <h2 className={cn("text-primary transition-all", collapsed ? "text-base" : "text-lg")}>
            {collapsed ? "灵犀" : "灵犀健康"}
          </h2>
        </div>

        {/* 菜单区域 - 使用 ScrollArea */}
        <ScrollArea className="flex-1">
          {renderMenuItems()}
        </ScrollArea>

        {/* 折叠按钮 */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="m-2 flex items-center justify-center rounded-lg p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        >
          {collapsed ? <Menu className="h-5 w-5" /> : <X className="h-5 w-5" />}
        </button>
      </aside>

      {/* 主内容区域 */}
      <div className="flex flex-1 flex-col min-w-0 md:ml-0">
        {/* 顶部导航栏 */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-card px-4 md:px-6 md:pl-6">
          {/* 占位元素，保持布局平衡 */}
          <div className="md:hidden w-10" />

          {/* 用户信息 */}
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <DropdownMenu>
              <DropdownMenuTrigger className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition-colors hover:bg-accent data-[state=open]:bg-accent">
                <Avatar />
                <span className="hidden md:inline">
                  {user?.username} ({user?.role === 'doctor' ? '医生' : '管理员'})
                </span>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-48 right-0">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium">{user?.username}</p>
                    <p className="text-xs text-muted-foreground">
                      {user?.role === 'doctor' ? '医生' : '管理员'}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-danger cursor-pointer">
                  <LogOut className="mr-2 h-4 w-4" />
                  退出登录
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* 内容区域 */}
        <main className="p-4 md:p-6 lg:p-8">
          <div className="rounded-xl bg-card p-4 md:p-6 shadow-sm">
            <Outlet />
          </div>
        </main>

        {/* 页脚 */}
        <footer className="border-t bg-card py-4">
          <div className="px-4 text-center text-xs text-muted-foreground md:px-6">
            <div className="mb-1">
              <strong>灵犀健康</strong> © {new Date().getFullYear()} 岳阳琳烨网络科技有限公司
            </div>
            <div>邮箱: 1024344053@qq.com | 电话: 18107300167</div>
            <div className="mt-1">湖南省岳阳市岳阳楼区三眼桥街道李家冲社区居民委员大楼605室</div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default MainLayout;

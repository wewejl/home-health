import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout,
  Menu,
  Avatar,
  Dropdown,
  Button,
  theme,
} from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  UserOutlined,
  DatabaseOutlined,
  CommentOutlined,
  BarChartOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MedicineBoxOutlined,
  FileSearchOutlined,
  RobotOutlined,
  MonitorOutlined,
  HeartOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons';

const { Header, Sider, Content, Footer } = Layout;

interface MainLayoutProps {
  user: { username: string; role: string } | null;
  onLogout: () => void;
}

const MainLayout: React.FC<MainLayoutProps> = ({ user, onLogout }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = theme.useToken();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/derma-chat',
      icon: <RobotOutlined />,
      label: '皮肤科AI对话',
    },
    {
      key: '/departments',
      icon: <MedicineBoxOutlined />,
      label: '科室管理',
    },
    {
      key: '/doctors',
      icon: <TeamOutlined />,
      label: '医生管理',
    },
    {
      key: '/diseases',
      icon: <FileSearchOutlined />,
      label: '疾病百科',
    },
    {
      key: '/drugs',
      icon: <MedicineBoxOutlined />,
      label: '药品百科',
    },
    {
      key: '/knowledge',
      icon: <DatabaseOutlined />,
      label: '知识库管理',
    },
    {
      key: '/feedbacks',
      icon: <CommentOutlined />,
      label: '反馈管理',
    },
    {
      key: '/stats',
      icon: <BarChartOutlined />,
      label: '统计分析',
    },
    {
      key: '/medical-orders',
      icon: <HeartOutlined />,
      label: '医嘱执行监督',
    },
    {
      key: '/patient-compliance',
      icon: <MonitorOutlined />,
      label: '患者依从性',
    },
    {
      key: '/rounding',
      icon: <VideoCameraOutlined />,
      label: '远程查房',
    },
  ];

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ];

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      onLogout();
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{ background: token.colorBgContainer }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
          }}
        >
          <h2 style={{ color: token.colorPrimary, margin: 0, fontSize: collapsed ? 16 : 18 }}>
            {collapsed ? '灵犀' : '灵犀健康'}
          </h2>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: token.colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <Dropdown
            menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
            placement="bottomRight"
          >
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user?.username}</span>
            </div>
          </Dropdown>
        </Header>
        <Content
          style={{
            margin: 24,
            padding: 24,
            background: token.colorBgContainer,
            borderRadius: token.borderRadiusLG,
            minHeight: 280,
            overflow: 'auto',
          }}
        >
          <Outlet />
        </Content>
        <Footer
          style={{
            textAlign: 'center',
            background: token.colorBgContainer,
            borderTop: `1px solid ${token.colorBorderSecondary}`,
            padding: '16px 24px',
          }}
        >
          <div style={{ fontSize: 12, color: token.colorTextSecondary }}>
            <div style={{ marginBottom: 4 }}>
              <strong>灵犀健康</strong> © {new Date().getFullYear()} 岳阳琳烨网络科技有限公司
            </div>
            <div>邮箱: 1024344053@qq.com | 电话: 18107300167</div>
            <div>湖南省岳阳市岳阳楼区三眼桥街道李家冲社区居民委员大楼605室</div>
          </div>
        </Footer>
      </Layout>
    </Layout>
  );
};

export default MainLayout;

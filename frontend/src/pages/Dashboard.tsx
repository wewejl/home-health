import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Spin, Typography } from 'antd';
import {
  TeamOutlined,
  MessageOutlined,
  FileTextOutlined,
  CommentOutlined,
  RobotOutlined,
  MedicineBoxOutlined,
} from '@ant-design/icons';
import { statsApi } from '../api';

const { Title } = Typography;

interface OverviewStats {
  total_departments: number;
  total_doctors: number;
  active_ai_doctors: number;
  total_sessions: number;
  total_messages: number;
  today_sessions: number;
  today_messages: number;
  pending_documents: number;
  pending_feedbacks: number;
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<OverviewStats | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await statsApi.getOverview();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Title level={4}>仪表盘</Title>
      
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="科室总数"
              value={stats?.total_departments || 0}
              prefix={<MedicineBoxOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="AI医生总数"
              value={stats?.active_ai_doctors || 0}
              suffix={`/ ${stats?.total_doctors || 0}`}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总会话数"
              value={stats?.total_sessions || 0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总消息数"
              value={stats?.total_messages || 0}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日会话"
              value={stats?.today_sessions || 0}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日消息"
              value={stats?.today_messages || 0}
              prefix={<MessageOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="待审核文档"
              value={stats?.pending_documents || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: stats?.pending_documents ? '#faad14' : undefined }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="待处理反馈"
              value={stats?.pending_feedbacks || 0}
              prefix={<CommentOutlined />}
              valueStyle={{ color: stats?.pending_feedbacks ? '#f5222d' : undefined }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;

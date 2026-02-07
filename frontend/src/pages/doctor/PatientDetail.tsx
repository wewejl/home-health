import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Tabs, Card, Row, Col, Statistic, Tag, Typography, Button, Space, Descriptions } from 'antd';
import {
  UserOutlined,
  ArrowLeftOutlined,
  MessageOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import ConsultationsTab from './ConsultationsTab';
import OrdersTab from './OrdersTab';
import TasksTab from './TasksTab';

const { Title, Text } = Typography;

interface Patient {
  id: number;
  nickname?: string;
  phone: string;
  gender?: string;
  age?: number;
  avatar_url?: string;
  is_profile_completed?: boolean;
  active_orders_count: number;
  completion_rate: number;
  created_at?: string;
}

const PatientDetail = () => {
  const navigate = useNavigate();
  const { patientId } = useParams<{ patientId: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (patientId) {
      fetchPatientDetail();
    }
  }, [patientId]);

  const fetchPatientDetail = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/doctor/patients/${patientId}`);
      const data = await response.json();
      setPatient(data);
    } catch (error) {
      console.error('Failed to fetch patient:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !patient) {
    return <div>加载中...</div>;
  }

  const percent = Math.round(patient.completion_rate * 100);

  const tabItems = [
    {
      key: 'consultations',
      label: 'AI对话记录',
      icon: <MessageOutlined />,
      children: <ConsultationsTab patientId={Number(patientId)} />,
    },
    {
      key: 'orders',
      label: '医嘱管理',
      icon: <FileTextOutlined />,
      children: <OrdersTab patientId={Number(patientId)} refresh={fetchPatientDetail} />,
    },
    {
      key: 'tasks',
      label: '任务完成情况',
      icon: <CheckCircleOutlined />,
      children: <TasksTab patientId={Number(patientId)} />,
    },
  ];

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/patients')}
        style={{ marginBottom: 16 }}
      >
        返回患者列表
      </Button>

      <Card>
        <Row gutter={24}>
          <Col span={6}>
            <div style={{ textAlign: 'center' }}>
              <div
                style={{
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  background: '#f0f0f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 16px',
                }}
              >
                <UserOutlined style={{ fontSize: 32, color: '#999' }} />
              </div>
              <Title level={5} style={{ margin: 0 }}>
                {patient.nickname || '未设置姓名'}
              </Title>
              <Text type="secondary">{patient.phone}</Text>
            </div>
          </Col>

          <Col span={18}>
            <Descriptions column={3} bordered size="small">
              <Descriptions.Item label="性别">
                {patient.gender ? (
                  <Tag color={patient.gender === '男' ? 'blue' : 'pink'}>{patient.gender}</Tag>
                ) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="年龄">{patient.age || '-'}</Descriptions.Item>
              <Descriptions.Item label="资料完善度">
                <Tag color={patient.is_profile_completed ? 'success' : 'warning'}>
                  {patient.is_profile_completed ? '已完善' : '未完善'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="进行中医嘱">
                <Tag color={patient.active_orders_count > 0 ? 'blue' : 'default'}>
                  {patient.active_orders_count} 条
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="最近7天完成率">
                <Tag
                  color={percent >= 80 ? 'success' : percent >= 50 ? 'processing' : 'error'}
                >
                  {percent}%
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="注册时间">
                {patient.created_at ? new Date(patient.created_at).toLocaleDateString() : '-'}
              </Descriptions.Item>
            </Descriptions>
          </Col>
        </Row>

        <Row gutter={16} style={{ marginTop: 24 }}>
          <Col span={8}>
            <Card size="small">
              <Statistic
                title="进行中医嘱"
                value={patient.active_orders_count}
                suffix="条"
                valueStyle={{ color: patient.active_orders_count > 0 ? '#1890ff' : '#999' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small">
              <Statistic
                title="最近7天完成率"
                value={percent}
                suffix="%"
                valueStyle={{
                  color: percent >= 80 ? '#52c41a' : percent >= 50 ? '#faad14' : '#ff4d4f'
                }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small">
              <Statistic
                title="患者状态"
                value={patient.is_profile_completed ? '已完善' : '未完善'}
                valueStyle={{
                  color: patient.is_profile_completed ? '#52c41a' : '#faad14',
                  fontSize: 18
                }}
              />
            </Card>
          </Col>
        </Row>
      </Card>

      <Card style={{ marginTop: 16 }} bodyStyle={{ padding: 0 }}>
        <Tabs items={tabItems} />
      </Card>
    </div>
  );
};

export default PatientDetail;

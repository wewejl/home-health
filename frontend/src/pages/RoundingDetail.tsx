import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Row,
  Col,
  Card,
  Button,
  Space,
  Typography,
  Tag,
  Avatar,
  List,
  Statistic,
  Alert,
  message,
  Spin,
} from 'antd';
import {
  ArrowLeftOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  UserOutlined,
  RobotOutlined,
  MessageOutlined,
  MedicineBoxOutlined,
  FileTextOutlined,
  LineChartOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { Line } from '@ant-design/charts';
import axios from 'axios';
import './RoundingDetail.css';

const { Text, Paragraph } = Typography;

// ============================================
// TYPES
// ============================================

interface Message {
  id: number;
  isAi: boolean;
  content: string;
  time: string;
  created_at: string;
}

interface Task {
  id: number;
  title: string;
  scheduled_time: string;
  status: 'pending' | 'completed' | 'overdue';
  completed_at?: string;
  value?: { value: number; unit: string };
  notes?: string;
  order_type: string;
}

interface PatientDetailData {
  id: number;
  name: string;
  nickname?: string;
  avatar?: string;
  condition?: string;
  last_seen: string;
  last_consultation: string;
  alerts: Array<{ type: string; severity: string; message: string; value?: any }>;
  total_tasks: number;
  completed_tasks: number;
  completion_rate: number;
  recent_messages: Message[];
  today_tasks: Task[];
  compliance_rate: number;
  daily_compliance: Array<{ date: string; rate: number }>;
}

// API 基础路径
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ============================================
// MAIN COMPONENT
// ============================================

const RoundingDetail: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [patientData, setPatientData] = useState<PatientDetailData | null>(null);

  // 获取 token
  const getToken = () => {
    return localStorage.getItem('token') || sessionStorage.getItem('token') || '';
  };

  // 加载患者详情数据
  useEffect(() => {
    const fetchPatientDetail = async () => {
      if (!patientId) {
        message.error('患者ID无效');
        navigate('/rounding');
        return;
      }

      try {
        setLoading(true);
        const token = getToken();
        const response = await axios.get<PatientDetailData>(
          `${API_BASE}/rounding/patients/${patientId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        setPatientData(response.data);
      } catch (error) {
        console.error('Failed to fetch patient detail:', error);
        message.error('加载患者详情失败');
      } finally {
        setLoading(false);
      }
    };

    fetchPatientDetail();
  }, [patientId, navigate]);

  if (loading) {
    return (
      <div className="rounding-detail-page">
        <div className="loading-container">
          <Spin size="large" tip="加载患者数据..." />
        </div>
      </div>
    );
  }

  if (!patientData) {
    return (
      <div className="rounding-detail-page">
        <div className="loading-container">
          <p>患者数据不存在</p>
          <Button type="primary" onClick={() => navigate('/rounding')}>
            返回列表
          </Button>
        </div>
      </div>
    );
  }

  // 图表数据
  const chartData = patientData.daily_compliance.map((d) => ({
    date: d.date,
    rate: d.rate,
  }));

  const chartConfig = {
    data: chartData,
    xField: 'date',
    yField: 'rate',
    yAxis: {
      max: 100,
      min: 0,
      label: {
        formatter: (v: string) => `${v}%`,
        style: { fill: '#64748b' },
      },
    },
    xAxis: {
      label: {
        style: { fill: '#64748b' },
      },
    },
    smooth: true,
    line: {
      color: '#3b82f6',
    },
    point: {
      size: 6,
      shape: 'circle',
      style: { fill: '#3b82f6', stroke: '#1e293b', lineWidth: 2 },
    },
    tooltip: {
      formatter: (datum: any) => ({
        name: '完成率',
        value: `${datum.rate}%`,
      }),
    },
  };

  const getTaskStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'overdue': return '已超时';
      default: return '待完成';
    }
  };

  const getTaskStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981';
      case 'overdue': return '#ef4444';
      default: return '#94a3b8';
    }
  };

  return (
    <div className="rounding-detail-page">
      {/* 顶部导航 */}
      <div className="detail-header">
        <Button
          className="back-button"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/rounding')}
        >
          返回患者列表
        </Button>
      </div>

      {/* 患者信息 + 预警横幅 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={8}>
          <Card className="info-card">
            <div className="patient-detail-header">
              <Avatar className="patient-detail-avatar" size={72} icon={<UserOutlined />} />
              <div className="patient-detail-info">
                <h2 className="patient-detail-name">{patientData.name}</h2>
                <Text className="patient-detail-condition">{patientData.condition || '居家患者'}</Text>
                <div className="patient-detail-meta">
                  <Text style={{ color: '#64748b', fontSize: 13 }}>
                    <ClockCircleOutlined style={{ marginRight: 4 }} />
                    上次问诊: {patientData.last_consultation}
                  </Text>
                  <Text style={{ color: '#64748b', fontSize: 13, marginLeft: 16 }}>
                    上次活跃: {patientData.last_seen}
                  </Text>
                </div>
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card className="alert-card" bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }} size={12}>
              {patientData.alerts.length > 0 ? (
                patientData.alerts.map((alert, index) => (
                  <Alert
                    key={index}
                    className={alert.severity === 'high' ? 'alert-danger' : 'alert-warning'}
                    message={alert.severity === 'high' ? '⚠️ 危险预警' : '⚠️ 注意事项'}
                    description={alert.message}
                    showIcon
                    closable
                  />
                ))
              ) : (
                <Alert
                  message="暂无预警"
                  description="患者当前状态正常，无异常预警"
                  type="success"
                  showIcon
                />
              )}
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 今日统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card className="stat-card">
            <Statistic
              title="今日任务"
              value={patientData.total_tasks}
              suffix={`/ ${patientData.completed_tasks}`}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="stat-card">
            <Statistic
              title="完成率"
              value={patientData.completion_rate}
              suffix="%"
              valueStyle={{
                color: patientData.completion_rate >= 80 ? '#10b981' :
                       patientData.completion_rate >= 50 ? '#f59e0b' : '#ef4444'
              }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="stat-card">
            <Statistic
              title="近7天平均"
              value={patientData.compliance_rate}
              suffix="%"
              prefix={<LineChartOutlined />}
              valueStyle={{ color: '#3b82f6' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="stat-card">
            <Statistic
              title="未完成"
              value={patientData.total_tasks - patientData.completed_tasks}
              valueStyle={{
                color: patientData.total_tasks - patientData.completed_tasks > 0 ? '#f59e0b' : '#10b981'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 中间区域：对话 + 医嘱 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* 左侧：最近对话 */}
        <Col xs={24} lg={12}>
          <Card
            className="content-card"
            title={
              <Space>
                <MessageOutlined />
                <span>最近对话</span>
              </Space>
            }
            extra={<Button type="link" onClick={() => message.info('跳转到对话页面')}>查看全部</Button>}
          >
            <List
              className="message-list"
              dataSource={patientData.recent_messages}
              renderItem={(msg) => (
                <div className={`message-item ${msg.isAi ? 'message-ai' : 'message-user'}`}>
                  <Avatar className={`message-avatar ${msg.isAi ? 'avatar-ai' : 'avatar-user'}`}>
                    {msg.isAi ? <RobotOutlined /> : <UserOutlined />}
                  </Avatar>
                  <div className="message-content-wrapper">
                    <div className={`message-content ${msg.isAi ? 'content-ai' : 'content-user'}`}>
                      <Paragraph>{msg.content}</Paragraph>
                      <Text className="message-time">{msg.time}</Text>
                    </div>
                  </div>
                </div>
              )}
            />
          </Card>
        </Col>

        {/* 右侧：医嘱列表 */}
        <Col xs={24} lg={12}>
          <Card
            className="content-card"
            title={
              <Space>
                <MedicineBoxOutlined />
                <span>今日医嘱</span>
              </Space>
            }
            extra={<Button type="primary" icon={<PlusOutlined />} size="small">添加医嘱</Button>}
          >
            <div className="task-list">
              {patientData.today_tasks.map(task => (
                <div
                  key={task.id}
                  className={`task-item task-item-${task.status}`}
                >
                  <div className="task-info">
                    <Text className="task-title">
                      {task.status === 'completed' && <CheckCircleOutlined style={{ marginRight: 6, color: '#10b981' }} />}
                      {task.status === 'overdue' && <WarningOutlined style={{ marginRight: 6, color: '#ef4444' }} />}
                      {task.title}
                    </Text>
                    <Text className="task-time">
                      计划时间: {task.scheduled_time}
                      {task.completed_at && ` · 完成于 ${task.completed_at}`}
                    </Text>
                    {task.value && (
                      <div className="task-value">
                        <span>{task.value.value} {task.value.unit}</span>
                      </div>
                    )}
                    {task.notes && (
                      <Text style={{ fontSize: 12, color: '#64748b' }}>{task.notes}</Text>
                    )}
                  </div>
                  <Tag
                    className="task-status"
                    style={{
                      backgroundColor: task.status === 'completed' ? 'rgba(16, 185, 129, 0.2)' :
                                       task.status === 'overdue' ? 'rgba(239, 68, 68, 0.2)' :
                                       'rgba(100, 116, 139, 0.2)',
                      color: getTaskStatusColor(task.status),
                      border: 'none',
                      padding: '4px 10px',
                      fontSize: '12px',
                    }}
                  >
                    {getTaskStatusText(task.status)}
                  </Tag>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {/* 底部：依从性趋势 */}
      <Card
        className="chart-card"
        title={
          <Space>
            <LineChartOutlined />
            <span>依从性趋势（近7天）</span>
          </Space>
        }
      >
        <div className="chart-container">
          <Line {...chartConfig} height={200} />
        </div>
      </Card>
    </div>
  );
};

export default RoundingDetail;

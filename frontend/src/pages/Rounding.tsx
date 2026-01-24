import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Input,
  Select,
  Avatar,
  Typography,
  Badge,
  Empty,
  Spin,
  message,
} from 'antd';
import {
  SearchOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  FireOutlined,
  UserOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import axios from 'axios';
import './Rounding.css';

const { Text } = Typography;
const { Option } = Select;

// ============================================
// TYPES
// ============================================

interface Patient {
  id: number;
  name: string;
  nickname?: string;
  avatar?: string;
  last_seen: string;
  last_consultation: string;
  completionRate: number;
  totalTasks: number;
  completedTasks: number;
  status: 'danger' | 'warning' | 'success';
  alerts?: string[];
  riskLevel?: 'high' | 'medium' | 'low';
}

interface PatientListResponse {
  patients: Patient[];
  stats: {
    total: number;
    abnormal: number;
    high_risk: number;
  };
}

// API 基础路径
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ============================================
// MAIN COMPONENT
// ============================================

const Rounding: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [filteredPatients, setFilteredPatients] = useState<Patient[]>([]);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'abnormal' | 'high-risk'>('all');
  const [stats, setStats] = useState({ total: 0, abnormal: 0, high_risk: 0 });

  // 获取 token
  const getToken = () => {
    return localStorage.getItem('token') || sessionStorage.getItem('token') || '';
  };

  // 加载数据
  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const token = getToken();
        const response = await axios.get<PatientListResponse>(
          `${API_BASE}/rounding/patients`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        setPatients(response.data.patients);
        setFilteredPatients(response.data.patients);
        setStats(response.data.stats);
      } catch (error) {
        console.error('Failed to fetch patients:', error);
        message.error('加载患者数据失败');
        // 使用空数据而不是 mock
        setPatients([]);
        setFilteredPatients([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPatients();
  }, []);

  // 搜索过滤
  useEffect(() => {
    let filtered = [...patients];

    if (searchText) {
      filtered = filtered.filter(p =>
        p.name.toLowerCase().includes(searchText.toLowerCase())
      );
    }

    if (statusFilter === 'abnormal') {
      filtered = filtered.filter(p => p.status === 'danger' || p.status === 'warning');
    } else if (statusFilter === 'high-risk') {
      filtered = filtered.filter(p => p.riskLevel === 'high');
    }

    filtered.sort((a, b) => {
      const statusOrder = { danger: 0, warning: 1, success: 2 };
      return statusOrder[a.status] - statusOrder[b.status];
    });

    setFilteredPatients(filtered);
  }, [searchText, statusFilter, patients]);

  // 点击卡片
  const handleCardClick = (patientId: number) => {
    navigate(`/rounding/${patientId}`);
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'success': return '✓ 执行良好';
      case 'warning': return '⚠ 需要关注';
      default: return '⚠ 异常';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return '#10b981';
      case 'warning': return '#f59e0b';
      default: return '#ef4444';
    }
  };

  if (loading) {
    return (
      <div className="rounding-page">
        <div className="loading-container">
          <Spin size="large" tip="加载患者数据..." />
        </div>
      </div>
    );
  }

  return (
    <div className="rounding-page">
      {/* 顶部标题栏 */}
      <div className="rounding-header">
        <div>
          <h1 className="rounding-title">远程查房</h1>
          <p className="rounding-subtitle">
            实时监控患者医嘱执行情况 · 最后更新: {dayjs().format('HH:mm:ss')}
          </p>
        </div>
      </div>

      {/* 统计概览 */}
      <div className="stats-bar">
        <div className="stat-item">
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.2)' }}>
            <UserOutlined />
          </div>
          <div className="stat-content">
            <span className="stat-label">管理患者</span>
            <span className="stat-value">{stats.total}</span>
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-icon" style={{ background: 'rgba(239, 68, 68, 0.2)' }}>
            <WarningOutlined />
          </div>
          <div className="stat-content">
            <span className="stat-label">异常患者</span>
            <span className="stat-value" style={{ color: stats.abnormal > 0 ? '#ef4444' : '#10b981' }}>
              {stats.abnormal}
            </span>
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.2)' }}>
            <FireOutlined />
          </div>
          <div className="stat-content">
            <span className="stat-label">高风险</span>
            <span className="stat-value" style={{ color: stats.high_risk > 0 ? '#f59e0b' : '#f1f5f9' }}>
              {stats.high_risk}
            </span>
          </div>
        </div>
      </div>

      {/* 筛选栏 */}
      <div className="filter-bar">
        <Input
          className="search-input"
          placeholder="搜索患者姓名..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={e => setSearchText(e.target.value)}
          style={{ width: 240 }}
        />
        <Select
          className="filter-select"
          value={statusFilter}
          onChange={setStatusFilter}
          style={{ width: 140 }}
        >
          <Option value="all">全部患者</Option>
          <Option value="abnormal">只看异常</Option>
          <Option value="high-risk">只看高风险</Option>
        </Select>
      </div>

      {/* 患者卡片网格 */}
      {filteredPatients.length === 0 ? (
        <Empty
          description="没有找到匹配的患者"
          style={{ marginTop: 60 }}
        />
      ) : (
        <div className="patient-grid">
          {filteredPatients.map((patient, index) => (
            <Card
              key={patient.id}
              className={`patient-card patient-card-${patient.status}`}
              onClick={() => handleCardClick(patient.id)}
              hoverable
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {/* 顶部状态条 */}
              <div className={`patient-card-status-bar patient-card-status-bar-${patient.status}`} />

              <div className="patient-header">
                <Avatar className="patient-avatar" size={52} icon={<UserOutlined />} />
                <div className="patient-info">
                  <Text className="patient-name">{patient.name}</Text>
                  <Text className="last-seen">
                    <ClockCircleOutlined style={{ marginRight: 4 }} />
                    上次活跃: {patient.last_seen}
                  </Text>
                </div>
                {patient.riskLevel === 'high' && (
                  <Badge status="error" text="高风险" />
                )}
              </div>

              <div className="patient-status-section">
                <div className="progress-label">
                  <Text style={{ color: getStatusColor(patient.status), fontWeight: 500, fontSize: 13 }}>
                    {getStatusText(patient.status)}
                  </Text>
                  <Text className="completion-percent">
                    {patient.completedTasks}/{patient.totalTasks}
                  </Text>
                </div>

                <div className="progress-wrapper">
                  <div className="progress-bar-container">
                    <div
                      className={`progress-bar-fill progress-bar-fill-${patient.status}`}
                      style={{ width: `${patient.completionRate}%` }}
                    />
                  </div>
                </div>

                <div className="progress-footer">
                  <Text className="completion-rate">{patient.completionRate}%</Text>
                  <Text style={{ color: '#64748b', fontSize: 12 }}>今日完成率</Text>
                </div>

                {patient.alerts && patient.alerts.length > 0 && (
                  <div className={`alert-badge alert-badge-${patient.status}`}>
                    <WarningOutlined />
                    <Text style={{ fontSize: 12 }}>{patient.alerts[0]}</Text>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default Rounding;

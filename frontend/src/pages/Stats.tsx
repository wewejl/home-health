import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Table, Typography, Spin, Select } from 'antd';
import { statsApi } from '../api';

const { Title } = Typography;

interface DailyStats {
  date: string;
  sessions: number;
  messages: number;
}

interface AuditLog {
  id: number;
  admin_user_id: number;
  action: string;
  resource_type: string;
  resource_id: string;
  created_at: string;
}

const Stats: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [trends, setTrends] = useState<DailyStats[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [days, setDays] = useState(7);

  useEffect(() => {
    fetchData();
  }, [days]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [trendsRes, logsRes] = await Promise.all([
        statsApi.getTrends(days),
        statsApi.getLogs({ limit: 20 }),
      ]);
      setTrends(trendsRes.data.daily_stats || []);
      setLogs(logsRes.data || []);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const trendColumns = [
    { title: '日期', dataIndex: 'date' },
    { title: '会话数', dataIndex: 'sessions' },
    { title: '消息数', dataIndex: 'messages' },
  ];

  const logColumns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '管理员ID', dataIndex: 'admin_user_id', width: 80 },
    { title: '操作', dataIndex: 'action', width: 80 },
    { title: '资源类型', dataIndex: 'resource_type', width: 100 },
    { title: '资源ID', dataIndex: 'resource_id', width: 100, ellipsis: true },
    {
      title: '时间',
      dataIndex: 'created_at',
      render: (v: string) => v ? new Date(v).toLocaleString() : '-',
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Title level={4}>统计分析</Title>

      <Row gutter={16}>
        <Col span={12}>
          <Card
            title="趋势数据"
            extra={
              <Select
                value={days}
                onChange={setDays}
                style={{ width: 120 }}
                options={[
                  { value: 7, label: '最近7天' },
                  { value: 14, label: '最近14天' },
                  { value: 30, label: '最近30天' },
                ]}
              />
            }
          >
            <Table
              columns={trendColumns}
              dataSource={trends}
              rowKey="date"
              size="small"
              pagination={false}
              scroll={{ y: 400 }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="审计日志">
            <Table
              columns={logColumns}
              dataSource={logs}
              rowKey="id"
              size="small"
              pagination={false}
              scroll={{ y: 400 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Stats;

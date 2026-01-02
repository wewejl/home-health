import React, { useEffect, useState } from 'react';
import { Table, Tag, Button, Modal, Form, Input, Select, message, Typography, Card, Row, Col, Statistic } from 'antd';
import { CheckOutlined, CloseOutlined, LikeOutlined, DislikeOutlined } from '@ant-design/icons';
import { feedbacksApi } from '../api';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Feedback {
  id: number;
  session_id: string;
  message_id?: number;
  user_id: number;
  rating?: number;
  feedback_type?: string;
  feedback_text?: string;
  status: string;
  resolution_notes?: string;
  created_at: string;
}

interface FeedbackStats {
  total: number;
  by_status: { pending: number; reviewed: number; resolved: number };
  by_type: { helpful: number; unhelpful: number; unsafe: number; inaccurate: number };
}

const Feedbacks: React.FC = () => {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedFeedback, setSelectedFeedback] = useState<Feedback | null>(null);
  const [form] = Form.useForm();
  const [statusFilter, setStatusFilter] = useState<string>('');

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [feedbacksRes, statsRes] = await Promise.all([
        feedbacksApi.list({ status: statusFilter || undefined }),
        feedbacksApi.getStats(),
      ]);
      setFeedbacks(feedbacksRes.data);
      setStats(statsRes.data);
    } catch (error) {
      message.error('加载反馈列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleHandle = (feedback: Feedback) => {
    setSelectedFeedback(feedback);
    form.setFieldsValue({ status: 'resolved', resolution_notes: '' });
    setModalVisible(true);
  };

  const handleSubmit = async () => {
    if (!selectedFeedback) return;
    try {
      const values = await form.validateFields();
      await feedbacksApi.handle(selectedFeedback.id, values);
      message.success('处理成功');
      setModalVisible(false);
      fetchData();
    } catch (error) {
      message.error('处理失败');
    }
  };

  const getTypeTag = (type: string | undefined) => {
    switch (type) {
      case 'helpful':
        return <Tag color="green" icon={<LikeOutlined />}>有帮助</Tag>;
      case 'unhelpful':
        return <Tag color="orange" icon={<DislikeOutlined />}>无帮助</Tag>;
      case 'unsafe':
        return <Tag color="red">不安全</Tag>;
      case 'inaccurate':
        return <Tag color="volcano">不准确</Tag>;
      default:
        return <Tag>-</Tag>;
    }
  };

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'pending':
        return <Tag color="orange">待处理</Tag>;
      case 'reviewed':
        return <Tag color="blue">已审核</Tag>;
      case 'resolved':
        return <Tag color="green">已解决</Tag>;
      default:
        return <Tag>{status}</Tag>;
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '会话ID', dataIndex: 'session_id', width: 150, ellipsis: true },
    {
      title: '评分',
      dataIndex: 'rating',
      width: 80,
      render: (v: number | undefined) => v ? `${v}/5` : '-',
    },
    {
      title: '类型',
      dataIndex: 'feedback_type',
      width: 100,
      render: getTypeTag,
    },
    {
      title: '反馈内容',
      dataIndex: 'feedback_text',
      ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: getStatusTag,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (v: string) => new Date(v).toLocaleString(),
    },
    {
      title: '操作',
      width: 100,
      render: (_: any, record: Feedback) => (
        record.status === 'pending' ? (
          <Button size="small" type="primary" onClick={() => handleHandle(record)}>
            处理
          </Button>
        ) : (
          <Text type="secondary">已处理</Text>
        )
      ),
    },
  ];

  return (
    <div>
      <Title level={4}>反馈管理</Title>

      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={4}>
            <Card size="small">
              <Statistic title="总反馈" value={stats.total} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic title="待处理" value={stats.by_status.pending} valueStyle={{ color: '#faad14' }} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic title="有帮助" value={stats.by_type.helpful} valueStyle={{ color: '#52c41a' }} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic title="无帮助" value={stats.by_type.unhelpful} valueStyle={{ color: '#fa8c16' }} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic title="不安全" value={stats.by_type.unsafe} valueStyle={{ color: '#f5222d' }} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic title="不准确" value={stats.by_type.inaccurate} valueStyle={{ color: '#eb2f96' }} />
            </Card>
          </Col>
        </Row>
      )}

      <div style={{ marginBottom: 16 }}>
        <Select
          style={{ width: 150 }}
          placeholder="筛选状态"
          allowClear
          value={statusFilter || undefined}
          onChange={(v) => setStatusFilter(v || '')}
          options={[
            { value: 'pending', label: '待处理' },
            { value: 'reviewed', label: '已审核' },
            { value: 'resolved', label: '已解决' },
          ]}
        />
      </div>

      <Table columns={columns} dataSource={feedbacks} rowKey="id" loading={loading} />

      <Modal
        title="处理反馈"
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
      >
        {selectedFeedback && (
          <div style={{ marginBottom: 16 }}>
            <p><strong>反馈类型:</strong> {getTypeTag(selectedFeedback.feedback_type)}</p>
            <p><strong>反馈内容:</strong> {selectedFeedback.feedback_text || '无'}</p>
          </div>
        )}
        <Form form={form} layout="vertical">
          <Form.Item name="status" label="状态" rules={[{ required: true }]}>
            <Select
              options={[
                { value: 'reviewed', label: '已审核' },
                { value: 'resolved', label: '已解决' },
              ]}
            />
          </Form.Item>
          <Form.Item name="resolution_notes" label="处理备注">
            <TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Feedbacks;

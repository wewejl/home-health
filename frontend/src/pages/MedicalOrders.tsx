import React, { useEffect, useState } from 'react';
import {
  Row,
  Col,
  Card,
  Table,
  Button,
  Tag,
  Space,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Typography,
  Tooltip,
  message,
  Tabs,
  Statistic,
  Progress,
  Descriptions,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  CheckCircleOutlined,
  StopOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  MedicineBoxOutlined,
  FileTextOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { medicalOrdersApi } from '../api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

// 类型定义
interface MedicalOrder {
  id: number;
  patient_id: number;
  order_type: string;
  title: string;
  description?: string;
  schedule_type: string;
  start_date: string;
  end_date?: string;
  frequency?: string;
  reminder_times: string[];
  ai_generated: boolean;
  status: string;
  created_at: string;
  updated_at: string;
}

interface TaskInstance {
  id: number;
  order_id: number;
  patient_id: number;
  scheduled_date: string;
  scheduled_time: string;
  status: string;
  completed_at?: string;
  completion_notes?: string;
  order_title?: string;
  order_type?: string;
}

interface ComplianceSummary {
  date: string;
  total: number;
  completed: number;
  overdue: number;
  pending: number;
  rate: number;
}

interface TaskListResponse {
  date: string;
  pending: TaskInstance[];
  completed: TaskInstance[];
  overdue: TaskInstance[];
  summary: ComplianceSummary;
}

// 医嘱类型映射
const ORDER_TYPE_MAP: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  medication: { label: '用药', color: 'blue', icon: <MedicineBoxOutlined /> },
  monitoring: { label: '监测', color: 'green', icon: <FileTextOutlined /> },
  behavior: { label: '行为', color: 'orange', icon: <ClockCircleOutlined /> },
  followup: { label: '复诊', color: 'purple', icon: <CheckCircleOutlined /> },
};

// 调度类型映射
const SCHEDULE_TYPE_MAP: Record<string, string> = {
  once: '一次性',
  daily: '每日',
  weekly: '每周',
  custom: '自定义',
};

// 状态映射
const STATUS_MAP: Record<string, { label: string; color: string }> = {
  draft: { label: '草稿', color: 'default' },
  active: { label: '进行中', color: 'blue' },
  completed: { label: '已完成', color: 'green' },
  stopped: { label: '已停用', color: 'red' },
};

// 任务状态映射
const TASK_STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending: { label: '待完成', color: 'default' },
  completed: { label: '已完成', color: 'success' },
  overdue: { label: '已超时', color: 'error' },
  skipped: { label: '已跳过', color: 'warning' },
};

const MedicalOrders: React.FC = () => {
  // 列表数据
  const [orders, setOrders] = useState<MedicalOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [activeTab, setActiveTab] = useState('orders');

  // 今日任务数据
  const [todayTasks, setTodayTasks] = useState<TaskListResponse | null>(null);
  const [tasksLoading, setTasksLoading] = useState(true);

  // 弹窗状态
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [currentOrder, setCurrentOrder] = useState<MedicalOrder | null>(null);

  const [form] = Form.useForm();

  // 获取医嘱列表
  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await medicalOrdersApi.list(statusFilter);
      setOrders(response.data);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
      message.error('获取医嘱列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取今日任务
  const fetchTodayTasks = async () => {
    try {
      setTasksLoading(true);
      const today = dayjs().format('YYYY-MM-DD');
      const response = await medicalOrdersApi.getDailyTasks(today);
      setTodayTasks(response.data);
    } catch (error) {
      console.error('Failed to fetch today tasks:', error);
    } finally {
      setTasksLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    fetchTodayTasks();
  }, [statusFilter]);

  // 创建医嘱
  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      const data = {
        ...values,
        start_date: values.start_date.format('YYYY-MM-DD'),
        end_date: values.end_date?.format('YYYY-MM-DD'),
        reminder_times: values.reminder_times?.map((t: dayjs.Dayjs) => t.format('HH:mm')) || [],
      };
      await medicalOrdersApi.create(data);
      message.success('医嘱创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      fetchOrders();
    } catch (error) {
      console.error('Create failed:', error);
      message.error('创建失败');
    }
  };

  // 更新医嘱
  const handleUpdate = async () => {
    if (!currentOrder) return;
    try {
      const values = await form.validateFields();
      const data = {
        ...values,
        end_date: values.end_date?.format('YYYY-MM-DD'),
        reminder_times: values.reminder_times?.map((t: dayjs.Dayjs) => t.format('HH:mm')) || [],
      };
      await medicalOrdersApi.update(currentOrder.id, data);
      message.success('医嘱更新成功');
      setEditModalVisible(false);
      setCurrentOrder(null);
      form.resetFields();
      fetchOrders();
    } catch (error) {
      console.error('Update failed:', error);
      message.error('更新失败');
    }
  };

  // 激活医嘱
  const handleActivate = async (id: number) => {
    try {
      await medicalOrdersApi.activate(id, true);
      message.success('医嘱已激活');
      fetchOrders();
    } catch (error) {
      console.error('Activate failed:', error);
      message.error('激活失败');
    }
  };

  // 打开编辑弹窗
  const openEditModal = (order: MedicalOrder) => {
    setCurrentOrder(order);
    form.setFieldsValue({
      ...order,
      start_date: dayjs(order.start_date),
      end_date: order.end_date ? dayjs(order.end_date) : undefined,
      reminder_times: order.reminder_times?.map((t) => dayjs(t, 'HH:mm')) || [],
    });
    setEditModalVisible(true);
  };

  // 打开详情弹窗
  const openDetailModal = (order: MedicalOrder) => {
    setCurrentOrder(order);
    setDetailModalVisible(true);
  };

  // 医嘱列表表格列
  const orderColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '类型',
      dataIndex: 'order_type',
      key: 'order_type',
      width: 80,
      render: (type: string) => {
        const config = ORDER_TYPE_MAP[type] || ORDER_TYPE_MAP.medication;
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.label}
          </Tag>
        );
      },
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '调度',
      dataIndex: 'schedule_type',
      key: 'schedule_type',
      width: 80,
      render: (type: string) => SCHEDULE_TYPE_MAP[type] || type,
    },
    {
      title: '提醒时间',
      dataIndex: 'reminder_times',
      key: 'reminder_times',
      width: 120,
      render: (times: string[]) => times?.join(', ') || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string, record: MedicalOrder) => {
        const config = STATUS_MAP[status] || STATUS_MAP.draft;
        return (
          <Space direction="vertical" size={0}>
            <Tag color={config.color}>{config.label}</Tag>
            {record.ai_generated && (
              <Tag color="cyan" icon={<RobotOutlined />}>AI生成</Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: '开始日期',
      dataIndex: 'start_date',
      key: 'start_date',
      width: 110,
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_: any, record: MedicalOrder) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => openDetailModal(record)}
            />
          </Tooltip>
          {record.status === 'draft' && (
            <>
              <Tooltip title="编辑">
                <Button
                  type="link"
                  size="small"
                  icon={<EditOutlined />}
                  onClick={() => openEditModal(record)}
                />
              </Tooltip>
              <Tooltip title="激活医嘱">
                <Button
                  type="link"
                  size="small"
                  icon={<CheckCircleOutlined />}
                  onClick={() => handleActivate(record.id)}
                />
              </Tooltip>
            </>
          )}
          {record.status === 'active' && (
            <Tooltip title="停用">
              <Button
                type="link"
                size="small"
                danger
                icon={<StopOutlined />}
                onClick={() => message.info('停用功能开发中')}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  // 任务表格列
  const taskColumns = [
    {
      title: '任务',
      dataIndex: 'order_title',
      key: 'order_title',
      ellipsis: true,
      render: (title: string, record: TaskInstance) => (
        <Space direction="vertical" size={0}>
          <Text strong>{title || '未命名任务'}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.order_type && ORDER_TYPE_MAP[record.order_type]?.label}
          </Text>
        </Space>
      ),
    },
    {
      title: '计划时间',
      key: 'time',
      width: 100,
      render: (_: any, record: TaskInstance) => (
        <Text>{record.scheduled_time}</Text>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string) => {
        const config = TASK_STATUS_MAP[status] || TASK_STATUS_MAP.pending;
        return <Tag color={config.color}>{config.label}</Tag>;
      },
    },
    {
      title: '完成时间',
      dataIndex: 'completed_at',
      key: 'completed_at',
      width: 160,
      render: (time: string) => time ? dayjs(time).format('MM-DD HH:mm') : '-',
    },
  ];

  // 今日任务概览卡片
  const renderTodayOverview = () => {
    if (!todayTasks) return null;
    const { summary } = todayTasks;
    const percent = Math.round(summary.rate * 100);

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日任务"
              value={summary.total}
              suffix={`/ ${summary.completed + summary.overdue}`}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="完成率"
              value={percent}
              suffix="%"
              valueStyle={{ color: percent >= 80 ? '#52c41a' : percent >= 50 ? '#faad14' : '#f5222d' }}
            />
            <Progress percent={percent} size="small" showInfo={false} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="待完成"
              value={summary.pending}
              valueStyle={{ color: summary.pending > 0 ? '#1890ff' : undefined }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已超时"
              value={summary.overdue}
              valueStyle={{ color: summary.overdue > 0 ? '#f5222d' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={4} style={{ margin: 0 }}>
            医嘱执行监督
          </Title>
        </Col>
        <Col>
          <Space>
            <Select
              placeholder="筛选状态"
              allowClear
              style={{ width: 120 }}
              onChange={setStatusFilter}
            >
              <Option value="">全部</Option>
              <Option value="draft">草稿</Option>
              <Option value="active">进行中</Option>
              <Option value="completed">已完成</Option>
              <Option value="stopped">已停用</Option>
            </Select>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
            >
              新建医嘱
            </Button>
          </Space>
        </Col>
      </Row>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'orders',
            label: `医嘱列表 (${orders.length})`,
            children: (
              <Card>
                <Table
                  columns={orderColumns}
                  dataSource={orders}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 10 }}
                  scroll={{ x: 800 }}
                />
              </Card>
            ),
          },
          {
            key: 'tasks',
            label: '今日任务',
            children: (
              <>
                {renderTodayOverview()}
                <Card
                  title={
                    <Space>
                      <ClockCircleOutlined />
                      <span>{dayjs().format('YYYY年MM月DD日')} 任务清单</span>
                    </Space>
                  }
                  loading={tasksLoading}
                >
                  <Row gutter={[16, 16]}>
                    {/* 待完成任务 */}
                    <Col xs={24} lg={8}>
                      <Card
                        type="inner"
                        title={<Tag color="default">待完成 ({todayTasks?.pending.length || 0})</Tag>}
                        size="small"
                      >
                        <Table
                          columns={taskColumns}
                          dataSource={todayTasks?.pending || []}
                          rowKey="id"
                          size="small"
                          pagination={false}
                          showHeader={false}
                        />
                      </Card>
                    </Col>
                    {/* 已完成任务 */}
                    <Col xs={24} lg={8}>
                      <Card
                        type="inner"
                        title={<Tag color="success">已完成 ({todayTasks?.completed.length || 0})</Tag>}
                        size="small"
                      >
                        <Table
                          columns={taskColumns}
                          dataSource={todayTasks?.completed || []}
                          rowKey="id"
                          size="small"
                          pagination={false}
                          showHeader={false}
                        />
                      </Card>
                    </Col>
                    {/* 已超时任务 */}
                    <Col xs={24} lg={8}>
                      <Card
                        type="inner"
                        title={<Tag color="error">已超时 ({todayTasks?.overdue.length || 0})</Tag>}
                        size="small"
                      >
                        <Table
                          columns={taskColumns}
                          dataSource={todayTasks?.overdue || []}
                          rowKey="id"
                          size="small"
                          pagination={false}
                          showHeader={false}
                        />
                      </Card>
                    </Col>
                  </Row>
                </Card>
              </>
            ),
          },
        ]}
      />

      {/* 创建医嘱弹窗 */}
      <Modal
        title={
          <Space>
            <PlusOutlined />
            新建医嘱
          </Space>
        }
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        width={600}
        okText="创建"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="医嘱类型"
                name="order_type"
                rules={[{ required: true, message: '请选择医嘱类型' }]}
              >
                <Select placeholder="选择类型">
                  <Option value="medication">用药</Option>
                  <Option value="monitoring">监测</Option>
                  <Option value="behavior">行为</Option>
                  <Option value="followup">复诊</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="调度类型"
                name="schedule_type"
                rules={[{ required: true, message: '请选择调度类型' }]}
              >
                <Select placeholder="选择调度">
                  <Option value="once">一次性</Option>
                  <Option value="daily">每日</Option>
                  <Option value="weekly">每周</Option>
                  <Option value="custom">自定义</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            label="医嘱标题"
            name="title"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="例如：早餐前注射胰岛素" />
          </Form.Item>
          <Form.Item label="详细说明" name="description">
            <TextArea rows={3} placeholder="医嘱的详细说明..." />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="开始日期"
                name="start_date"
                rules={[{ required: true, message: '请选择开始日期' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="结束日期" name="end_date">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="频次" name="frequency">
            <Input placeholder="例如：每日3次" />
          </Form.Item>
          <Form.Item label="提醒时间" name="reminder_times">
            <Select
              mode="tags"
              placeholder="输入提醒时间，如 08:00"
              style={{ width: '100%' }}
            >
              <Option value="08:00">08:00</Option>
              <Option value="12:00">12:00</Option>
              <Option value="18:00">18:00</Option>
              <Option value="21:00">21:00</Option>
            </Select>
          </Form.Item>
          <Form.Item label="AI 生成标记" name="ai_generated" valuePropName="checked">
            <Select placeholder="选择来源" defaultValue={false}>
              <Option value={false}>手动创建</Option>
              <Option value={true}>AI 生成</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑医嘱弹窗 */}
      <Modal
        title={
          <Space>
            <EditOutlined />
            编辑医嘱
          </Space>
        }
        open={editModalVisible}
        onOk={handleUpdate}
        onCancel={() => {
          setEditModalVisible(false);
          setCurrentOrder(null);
          form.resetFields();
        }}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="医嘱标题"
            name="title"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item label="详细说明" name="description">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="结束日期" name="end_date">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="频次" name="frequency">
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="提醒时间" name="reminder_times">
            <Select
              mode="tags"
              placeholder="输入提醒时间，如 08:00"
              style={{ width: '100%' }}
            >
              <Option value="08:00">08:00</Option>
              <Option value="12:00">12:00</Option>
              <Option value="18:00">18:00</Option>
              <Option value="21:00">21:00</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 医嘱详情弹窗 */}
      <Modal
        title={
          <Space>
            <EyeOutlined />
            医嘱详情
          </Space>
        }
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false);
          setCurrentOrder(null);
        }}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          currentOrder?.status === 'draft' && (
            <Button
              key="activate"
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={() => {
                if (currentOrder) {
                  handleActivate(currentOrder.id);
                  setDetailModalVisible(false);
                }
              }}
            >
              激活医嘱
            </Button>
          ),
        ]}
        width={700}
      >
        {currentOrder && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="医嘱ID" span={2}>
              {currentOrder.id}
            </Descriptions.Item>
            <Descriptions.Item label="类型">
              <Tag color={ORDER_TYPE_MAP[currentOrder.order_type]?.color}>
                {ORDER_TYPE_MAP[currentOrder.order_type]?.label}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={STATUS_MAP[currentOrder.status]?.color}>
                {STATUS_MAP[currentOrder.status]?.label}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="标题" span={2}>
              {currentOrder.title}
            </Descriptions.Item>
            <Descriptions.Item label="调度类型">
              {SCHEDULE_TYPE_MAP[currentOrder.schedule_type]}
            </Descriptions.Item>
            <Descriptions.Item label="频次">
              {currentOrder.frequency || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="开始日期">
              {currentOrder.start_date}
            </Descriptions.Item>
            <Descriptions.Item label="结束日期">
              {currentOrder.end_date || '未设置'}
            </Descriptions.Item>
            <Descriptions.Item label="提醒时间" span={2}>
              {currentOrder.reminder_times?.join(', ') || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="详细说明" span={2}>
              {currentOrder.description || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="AI 生成" span={2}>
              {currentOrder.ai_generated ? (
                <Tag color="cyan" icon={<RobotOutlined />}>
                  AI 生成
                </Tag>
              ) : (
                <Tag>手动创建</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {dayjs(currentOrder.created_at).format('YYYY-MM-DD HH:mm')}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {dayjs(currentOrder.updated_at).format('YYYY-MM-DD HH:mm')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default MedicalOrders;

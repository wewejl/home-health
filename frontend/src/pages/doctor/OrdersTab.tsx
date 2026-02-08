import React, { useState, useEffect } from 'react';
import { Table, Tag, Button, Space, Modal, Form, Input, Select, DatePicker, message, Typography } from 'antd';
import { PlusOutlined, EditOutlined, StopOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface MedicalOrder {
  id: number;
  patient_id: number;
  doctor_id: number;
  order_type: string;
  title: string;
  description?: string;
  status: string;
  start_date: string;
  end_date?: string;
  created_at: string;
}

interface OrdersTabProps {
  patientId: number;
  refresh: () => void;
}

const OrdersTab: React.FC<OrdersTabProps> = ({ patientId, refresh }) => {
  const [orders, setOrders] = useState<MedicalOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingOrder, setEditingOrder] = useState<MedicalOrder | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchOrders();
  }, [patientId]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/doctor/patients/${patientId}/orders`);
      const data = await response.json();
      setOrders(data);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingOrder(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (order: MedicalOrder) => {
    setEditingOrder(order);
    form.setFieldsValue({
      title: order.title,
      description: order.description,
      order_type: order.order_type,
      start_date: dayjs(order.start_date),
      end_date: order.end_date ? dayjs(order.end_date) : undefined,
    });
    setModalVisible(true);
  };

  const handleStop = async (orderId: number) => {
    Modal.confirm({
      title: '确认停用',
      content: '确定要停用这条医嘱吗？停用后将不再生成任务。',
      onOk: async () => {
        try {
          await fetch(`/api/doctor/orders/${orderId}`, {
            method: 'DELETE',
          });
          message.success('医嘱已停用');
          fetchOrders();
          refresh();
        } catch (error) {
          message.error('停用失败');
        }
      },
    });
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        ...values,
        patient_id: patientId,
        start_date: values.start_date.format('YYYY-MM-DD'),
        end_date: values.end_date?.format('YYYY-MM-DD'),
      };

      if (editingOrder) {
        // 更新医嘱
        await fetch(`/api/doctor/orders/${editingOrder.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: payload.title,
            description: payload.description,
            end_date: payload.end_date,
          }),
        });
        message.success('医嘱已更新');
      } else {
        // 创建新医嘱
        await fetch('/api/doctor/orders', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        message.success('医嘱已创建');
      }

      setModalVisible(false);
      fetchOrders();
      refresh();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const getOrderTypeLabel = (type: string) => {
    const typeMap: Record<string, { label: string; color: string }> = {
      'medication': { label: '用药任务', color: 'blue' },
      'monitoring': { label: '监测任务', color: 'green' },
      'behavior': { label: '行为任务', color: 'orange' },
      'followup': { label: '复诊任务', color: 'purple' },
    };
    const info = typeMap[type] || { label: type, color: 'default' };
    return <Tag color={info.color}>{info.label}</Tag>;
  };

  const getStatusLabel = (status: string) => {
    const statusMap: Record<string, { label: string; color: string }> = {
      'draft': { label: '草稿', color: 'default' },
      'active': { label: '进行中', color: 'blue' },
      'completed': { label: '已完成', color: 'green' },
      'stopped': { label: '已停用', color: 'red' },
    };
    const info = statusMap[status] || { label: status, color: 'default' };
    return <Tag color={info.color}>{info.label}</Tag>;
  };

  const columns: ColumnsType<MedicalOrder> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
    },
    {
      title: '医嘱类型',
      dataIndex: 'order_type',
      width: 120,
      render: getOrderTypeLabel,
    },
    {
      title: '医嘱标题',
      dataIndex: 'title',
      ellipsis: true,
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
      render: (desc: string) => desc || '-',
    },
    {
      title: '开始日期',
      dataIndex: 'start_date',
      width: 120,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '结束日期',
      dataIndex: 'end_date',
      width: 120,
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD') : '长期',
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: getStatusLabel,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: MedicalOrder) => (
        <Space>
          {record.status !== 'stopped' && (
            <>
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              >
                编辑
              </Button>
              <Button
                type="link"
                size="small"
                danger
                icon={<StopOutlined />}
                onClick={() => handleStop(record.id)}
              >
                停用
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 16 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Title level={5} style={{ margin: 0 }}>医嘱列表</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          创建医嘱
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={orders}
        rowKey="id"
        loading={loading}
        pagination={false}
        size="small"
      />

      <Modal
        title={editingOrder ? '编辑医嘱' : '创建医嘱'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="医嘱类型"
            name="order_type"
            rules={[{ required: true, message: '请选择医嘱类型' }]}
          >
            <Select placeholder="请选择医嘱类型">
              <Option value="medication">用药任务</Option>
              <Option value="monitoring">监测任务</Option>
              <Option value="behavior">行为任务</Option>
              <Option value="followup">复诊任务</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="医嘱标题"
            name="title"
            rules={[{ required: true, message: '请输入医嘱标题' }]}
          >
            <Input placeholder="例如：每日服用降压药" />
          </Form.Item>

          <Form.Item label="详细描述" name="description">
            <TextArea
              rows={4}
              placeholder="请输入医嘱的详细描述，包括用药方法、注意事项等"
            />
          </Form.Item>

          <Form.Item
            label="开始日期"
            name="start_date"
            rules={[{ required: true, message: '请选择开始日期' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item label="结束日期" name="end_date">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default OrdersTab;

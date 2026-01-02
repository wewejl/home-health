import React, { useEffect, useState } from 'react';
import {
  Table, Button, Space, Modal, Form, Input, InputNumber,
  message, Popconfirm, Typography, Tag
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { departmentsApi } from '../api';

const { Title } = Typography;

interface Department {
  id: number;
  name: string;
  description: string;
  icon: string;
  sort_order: number;
  is_active: boolean;
  doctor_count: number;
}

const Departments: React.FC = () => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingDept, setEditingDept] = useState<Department | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchDepartments();
  }, []);

  const fetchDepartments = async () => {
    setLoading(true);
    try {
      const response = await departmentsApi.list();
      setDepartments(response.data);
    } catch (error) {
      message.error('加载科室列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingDept(null);
    form.resetFields();
    form.setFieldsValue({ sort_order: 0, is_active: true });
    setModalVisible(true);
  };

  const handleEdit = (record: Department) => {
    setEditingDept(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingDept) {
        await departmentsApi.update(editingDept.id, values);
        message.success('更新成功');
      } else {
        await departmentsApi.create(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchDepartments();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await departmentsApi.delete(id);
      message.success('删除成功');
      fetchDepartments();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '名称', dataIndex: 'name', width: 120 },
    { title: '描述', dataIndex: 'description', ellipsis: true },
    { title: '图标', dataIndex: 'icon', width: 150 },
    { title: '排序', dataIndex: 'sort_order', width: 80 },
    {
      title: '医生数',
      dataIndex: 'doctor_count',
      width: 80,
      render: (v: number) => <Tag color={v > 0 ? 'blue' : 'default'}>{v}</Tag>,
    },
    {
      title: '操作',
      width: 120,
      render: (_: any, record: Department) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm
            title="确定删除?"
            description={record.doctor_count > 0 ? '该科室下有医生，无法删除' : undefined}
            onConfirm={() => handleDelete(record.id)}
            disabled={record.doctor_count > 0}
          >
            <Button size="small" danger icon={<DeleteOutlined />} disabled={record.doctor_count > 0} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4}>科室管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新增科室
        </Button>
      </div>

      <Table columns={columns} dataSource={departments} rowKey="id" loading={loading} />

      <Modal
        title={editingDept ? '编辑科室' : '新增科室'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入科室名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="icon" label="图标">
            <Input placeholder="SF Symbols 图标名称" />
          </Form.Item>
          <Form.Item name="sort_order" label="排序">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Departments;

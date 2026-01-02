import React, { useEffect, useState } from 'react';
import {
  Table, Button, Space, Modal, Form, Input, InputNumber, Select,
  message, Popconfirm, Typography, Tag, Switch, Tabs
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, FireOutlined } from '@ant-design/icons';
import { diseasesApi, departmentsApi } from '../api';

const { Title } = Typography;
const { TextArea } = Input;
const { TabPane } = Tabs;

interface Disease {
  id: number;
  name: string;
  pinyin: string;
  pinyin_abbr: string;
  aliases: string;
  department_id: number;
  department_name: string;
  recommended_department: string;
  overview: string;
  symptoms: string;
  causes: string;
  diagnosis: string;
  treatment: string;
  prevention: string;
  care: string;
  author_name: string;
  author_title: string;
  author_avatar: string;
  reviewer_info: string;
  is_hot: boolean;
  sort_order: number;
  is_active: boolean;
  view_count: number;
  created_at: string;
  updated_at: string;
}

interface Department {
  id: number;
  name: string;
}

const Diseases: React.FC = () => {
  const [diseases, setDiseases] = useState<Disease[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingDisease, setEditingDisease] = useState<Disease | null>(null);
  const [filters, setFilters] = useState<{ department_id?: number; is_active?: boolean; search?: string }>({});
  const [form] = Form.useForm();

  useEffect(() => {
    fetchDepartments();
    fetchDiseases();
  }, []);

  useEffect(() => {
    fetchDiseases();
  }, [filters]);

  const fetchDepartments = async () => {
    try {
      const response = await departmentsApi.list();
      setDepartments(response.data);
    } catch (error) {
      message.error('加载科室列表失败');
    }
  };

  const fetchDiseases = async () => {
    setLoading(true);
    try {
      const response = await diseasesApi.list(filters);
      setDiseases(response.data);
    } catch (error) {
      message.error('加载疾病列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingDisease(null);
    form.resetFields();
    form.setFieldsValue({
      sort_order: 0,
      is_active: true,
      is_hot: false,
      reviewer_info: '三甲医生专业编审 · 鑫琳医生官方出品'
    });
    setModalVisible(true);
  };

  const handleEdit = async (record: Disease) => {
    try {
      const response = await diseasesApi.get(record.id);
      setEditingDisease(response.data);
      form.setFieldsValue(response.data);
      setModalVisible(true);
    } catch (error) {
      message.error('加载疾病详情失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingDisease) {
        await diseasesApi.update(editingDisease.id, values);
        message.success('更新成功');
      } else {
        await diseasesApi.create(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchDiseases();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await diseasesApi.delete(id);
      message.success('删除成功');
      fetchDiseases();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const handleToggleHot = async (id: number, isHot: boolean) => {
    try {
      await diseasesApi.toggleHot(id, isHot);
      message.success(isHot ? '已设为热门' : '已取消热门');
      fetchDiseases();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleToggleActive = async (id: number, isActive: boolean) => {
    try {
      await diseasesApi.toggleActive(id, isActive);
      message.success(isActive ? '已启用' : '已禁用');
      fetchDiseases();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    {
      title: '名称',
      dataIndex: 'name',
      width: 150,
      render: (text: string, record: Disease) => (
        <Space>
          {text}
          {record.is_hot && <FireOutlined style={{ color: '#ff4d4f' }} />}
        </Space>
      ),
    },
    { title: '科室', dataIndex: 'department_name', width: 100 },
    { title: '拼音', dataIndex: 'pinyin', width: 120, ellipsis: true },
    { title: '别名', dataIndex: 'aliases', width: 150, ellipsis: true },
    {
      title: '浏览量',
      dataIndex: 'view_count',
      width: 80,
      render: (v: number) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: '热门',
      dataIndex: 'is_hot',
      width: 70,
      render: (isHot: boolean, record: Disease) => (
        <Switch
          size="small"
          checked={isHot}
          onChange={(checked) => handleToggleHot(record.id, checked)}
        />
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 70,
      render: (isActive: boolean, record: Disease) => (
        <Switch
          size="small"
          checked={isActive}
          onChange={(checked) => handleToggleActive(record.id, checked)}
        />
      ),
    },
    {
      title: '操作',
      width: 100,
      render: (_: any, record: Disease) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4}>疾病百科管理</Title>
        <Space>
          <Select
            placeholder="选择科室"
            allowClear
            style={{ width: 150 }}
            onChange={(v) => setFilters({ ...filters, department_id: v })}
          >
            {departments.map((d) => (
              <Select.Option key={d.id} value={d.id}>{d.name}</Select.Option>
            ))}
          </Select>
          <Select
            placeholder="状态"
            allowClear
            style={{ width: 100 }}
            onChange={(v) => setFilters({ ...filters, is_active: v })}
          >
            <Select.Option value={true}>已启用</Select.Option>
            <Select.Option value={false}>已禁用</Select.Option>
          </Select>
          <Input.Search
            placeholder="搜索疾病名称"
            allowClear
            style={{ width: 200 }}
            onSearch={(v) => setFilters({ ...filters, search: v || undefined })}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新增疾病
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={diseases}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1000 }}
        pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }}
      />

      <Modal
        title={editingDisease ? '编辑疾病' : '新增疾病'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={900}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Tabs defaultActiveKey="basic">
            <TabPane tab="基本信息" key="basic">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <Form.Item name="name" label="疾病名称" rules={[{ required: true, message: '请输入疾病名称' }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="department_id" label="所属科室" rules={[{ required: true, message: '请选择科室' }]}>
                  <Select>
                    {departments.map((d) => (
                      <Select.Option key={d.id} value={d.id}>{d.name}</Select.Option>
                    ))}
                  </Select>
                </Form.Item>
                <Form.Item name="pinyin" label="拼音">
                  <Input placeholder="留空自动生成" />
                </Form.Item>
                <Form.Item name="pinyin_abbr" label="拼音首字母">
                  <Input placeholder="留空自动生成" />
                </Form.Item>
                <Form.Item name="aliases" label="别名/同义词" style={{ gridColumn: 'span 2' }}>
                  <Input placeholder="多个别名用逗号分隔" />
                </Form.Item>
                <Form.Item name="recommended_department" label="推荐就诊科室">
                  <Input placeholder="如：内科、儿科等" />
                </Form.Item>
                <Form.Item name="sort_order" label="排序">
                  <InputNumber min={0} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item name="is_hot" label="热门" valuePropName="checked">
                  <Switch />
                </Form.Item>
                <Form.Item name="is_active" label="启用" valuePropName="checked">
                  <Switch />
                </Form.Item>
              </div>
            </TabPane>

            <TabPane tab="疾病内容" key="content">
              <Form.Item name="overview" label="简介/概述">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
              <Form.Item name="symptoms" label="症状">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
              <Form.Item name="causes" label="病因">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
              <Form.Item name="diagnosis" label="诊断">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
              <Form.Item name="treatment" label="治疗">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
              <Form.Item name="prevention" label="预防">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
              <Form.Item name="care" label="日常护理/注意事项">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
            </TabPane>

            <TabPane tab="作者信息" key="author">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <Form.Item name="author_name" label="作者姓名">
                  <Input />
                </Form.Item>
                <Form.Item name="author_title" label="作者职称">
                  <Input placeholder="如：主治医师、副主任医师等" />
                </Form.Item>
                <Form.Item name="author_avatar" label="作者头像URL" style={{ gridColumn: 'span 2' }}>
                  <Input placeholder="头像图片链接" />
                </Form.Item>
                <Form.Item name="reviewer_info" label="审核信息" style={{ gridColumn: 'span 2' }}>
                  <Input placeholder="如：三甲医生专业编审 · 鑫琳医生官方出品" />
                </Form.Item>
              </div>
            </TabPane>
          </Tabs>
        </Form>
      </Modal>
    </div>
  );
};

export default Diseases;

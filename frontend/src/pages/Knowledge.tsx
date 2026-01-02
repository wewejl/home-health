import React, { useEffect, useState } from 'react';
import {
  Table, Button, Space, Tag, Modal, Form, Input, Select,
  message, Popconfirm, Typography, Card, Tabs, Badge
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, FileTextOutlined, SyncOutlined } from '@ant-design/icons';
import { knowledgeBasesApi, documentsApi, departmentsApi, doctorsApi } from '../api';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  doctor_id?: number;
  department_id?: number;
  total_documents: number;
  total_chunks: number;
  is_active: boolean;
}

interface Document {
  id: number;
  title: string;
  content: string;
  doc_type: string;
  status: string;
  tags: string[];
  created_at: string;
}

const Knowledge: React.FC = () => {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [doctors, setDoctors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedKb, setSelectedKb] = useState<KnowledgeBase | null>(null);
  const [kbModalVisible, setKbModalVisible] = useState(false);
  const [docModalVisible, setDocModalVisible] = useState(false);
  const [editingKb, setEditingKb] = useState<KnowledgeBase | null>(null);
  const [editingDoc, setEditingDoc] = useState<Document | null>(null);
  const [kbForm] = Form.useForm();
  const [docForm] = Form.useForm();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [kbRes, deptRes, docRes] = await Promise.all([
        knowledgeBasesApi.list(),
        departmentsApi.list(),
        doctorsApi.list(),
      ]);
      setKnowledgeBases(kbRes.data);
      setDepartments(deptRes.data);
      setDoctors(docRes.data);
    } catch (error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async (kbId: string) => {
    try {
      const res = await knowledgeBasesApi.listDocuments(kbId);
      setDocuments(res.data);
    } catch (error) {
      message.error('加载文档失败');
    }
  };

  const handleSelectKb = (kb: KnowledgeBase) => {
    setSelectedKb(kb);
    fetchDocuments(kb.id);
  };

  const handleCreateKb = () => {
    setEditingKb(null);
    kbForm.resetFields();
    setKbModalVisible(true);
  };

  const handleEditKb = (kb: KnowledgeBase) => {
    setEditingKb(kb);
    kbForm.setFieldsValue(kb);
    setKbModalVisible(true);
  };

  const handleSubmitKb = async () => {
    try {
      const values = await kbForm.validateFields();
      if (editingKb) {
        await knowledgeBasesApi.update(editingKb.id, values);
        message.success('更新成功');
      } else {
        await knowledgeBasesApi.create(values);
        message.success('创建成功');
      }
      setKbModalVisible(false);
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const handleDeleteKb = async (id: string) => {
    try {
      await knowledgeBasesApi.delete(id);
      message.success('删除成功');
      if (selectedKb?.id === id) {
        setSelectedKb(null);
        setDocuments([]);
      }
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const handleReindex = async (id: string) => {
    try {
      await knowledgeBasesApi.reindex(id);
      message.success('重新索引完成');
      fetchData();
    } catch (error) {
      message.error('重新索引失败');
    }
  };

  const handleCreateDoc = () => {
    if (!selectedKb) return;
    setEditingDoc(null);
    docForm.resetFields();
    setDocModalVisible(true);
  };

  const handleSubmitDoc = async () => {
    if (!selectedKb) return;
    try {
      const values = await docForm.validateFields();
      if (editingDoc) {
        await documentsApi.update(editingDoc.id, values);
        message.success('更新成功');
      } else {
        await knowledgeBasesApi.createDocument(selectedKb.id, values);
        message.success('创建成功');
      }
      setDocModalVisible(false);
      fetchDocuments(selectedKb.id);
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const handleApproveDoc = async (docId: number, approved: boolean) => {
    try {
      await documentsApi.approve(docId, { approved });
      message.success(approved ? '审核通过' : '审核拒绝');
      if (selectedKb) fetchDocuments(selectedKb.id);
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleDeleteDoc = async (docId: number) => {
    try {
      await documentsApi.delete(docId);
      message.success('删除成功');
      if (selectedKb) fetchDocuments(selectedKb.id);
      fetchData();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const kbColumns = [
    { title: 'ID', dataIndex: 'id', width: 150, ellipsis: true },
    { title: '名称', dataIndex: 'name' },
    {
      title: '文档数',
      dataIndex: 'total_documents',
      width: 80,
      render: (v: number) => <Badge count={v} showZero color={v > 0 ? 'blue' : 'default'} />,
    },
    {
      title: '操作',
      width: 180,
      render: (_: any, record: KnowledgeBase) => (
        <Space>
          <Button size="small" onClick={() => handleSelectKb(record)}>查看</Button>
          <Button size="small" icon={<SyncOutlined />} onClick={() => handleReindex(record.id)} />
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEditKb(record)} />
          <Popconfirm title="确定删除?" onConfirm={() => handleDeleteKb(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const docColumns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '标题', dataIndex: 'title', ellipsis: true },
    {
      title: '类型',
      dataIndex: 'doc_type',
      width: 80,
      render: (v: string) => <Tag>{v || '-'}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: (v: string) => (
        <Tag color={v === 'approved' ? 'green' : v === 'rejected' ? 'red' : 'orange'}>
          {v === 'approved' ? '已通过' : v === 'rejected' ? '已拒绝' : '待审核'}
        </Tag>
      ),
    },
    {
      title: '操作',
      width: 200,
      render: (_: any, record: Document) => (
        <Space>
          {record.status === 'pending' && (
            <>
              <Button size="small" type="primary" onClick={() => handleApproveDoc(record.id, true)}>
                通过
              </Button>
              <Button size="small" danger onClick={() => handleApproveDoc(record.id, false)}>
                拒绝
              </Button>
            </>
          )}
          <Popconfirm title="确定删除?" onConfirm={() => handleDeleteDoc(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={4}>知识库管理</Title>
      
      <div style={{ display: 'flex', gap: 16 }}>
        <Card
          title="知识库列表"
          style={{ width: 500 }}
          extra={<Button type="primary" size="small" icon={<PlusOutlined />} onClick={handleCreateKb}>新增</Button>}
        >
          <Table
            columns={kbColumns}
            dataSource={knowledgeBases}
            rowKey="id"
            loading={loading}
            size="small"
            pagination={false}
          />
        </Card>

        <Card
          title={selectedKb ? `文档列表 - ${selectedKb.name}` : '请选择知识库'}
          style={{ flex: 1 }}
          extra={
            selectedKb && (
              <Button type="primary" size="small" icon={<PlusOutlined />} onClick={handleCreateDoc}>
                添加文档
              </Button>
            )
          }
        >
          {selectedKb ? (
            <Table columns={docColumns} dataSource={documents} rowKey="id" size="small" />
          ) : (
            <Text type="secondary">请从左侧选择一个知识库查看文档</Text>
          )}
        </Card>
      </div>

      <Modal
        title={editingKb ? '编辑知识库' : '新增知识库'}
        open={kbModalVisible}
        onOk={handleSubmitKb}
        onCancel={() => setKbModalVisible(false)}
      >
        <Form form={kbForm} layout="vertical">
          <Form.Item name="id" label="知识库ID" rules={[{ required: !editingKb }]} hidden={!!editingKb}>
            <Input placeholder="唯一标识，如 kb-dermatology-liuwu" />
          </Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item name="doctor_id" label="关联医生">
            <Select allowClear options={doctors.map((d) => ({ value: d.id, label: d.name }))} />
          </Form.Item>
          <Form.Item name="department_id" label="关联科室">
            <Select allowClear options={departments.map((d) => ({ value: d.id, label: d.name }))} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={editingDoc ? '编辑文档' : '添加文档'}
        open={docModalVisible}
        onOk={handleSubmitDoc}
        onCancel={() => setDocModalVisible(false)}
        width={600}
      >
        <Form form={docForm} layout="vertical">
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true }]}>
            <TextArea rows={8} />
          </Form.Item>
          <Form.Item name="doc_type" label="类型">
            <Select
              allowClear
              options={[
                { value: 'case', label: '病例' },
                { value: 'faq', label: 'FAQ' },
                { value: 'guideline', label: '指南' },
                { value: 'sop', label: 'SOP' },
              ]}
            />
          </Form.Item>
          <Form.Item name="source" label="来源">
            <Input placeholder="如：刘武医生提供" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Knowledge;

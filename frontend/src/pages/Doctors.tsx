import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table, Button, Space, Tag, Modal, Form, Input, Select, Switch,
  message, Popconfirm, Typography, Card, Drawer, InputNumber, Tabs
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined, MessageOutlined, FileTextOutlined } from '@ant-design/icons';
import { doctorsApi, departmentsApi, knowledgeBasesApi } from '../api';

const { Title } = Typography;
const { TextArea } = Input;

interface Doctor {
  id: number;
  name: string;
  title: string;
  department_id: number;
  hospital: string;
  specialty: string;
  is_ai: boolean;
  is_active: boolean;
  ai_persona_prompt?: string;
  ai_model: string;
  ai_temperature: number;
  ai_max_tokens: number;
  knowledge_base_id?: string;
}

const Doctors: React.FC = () => {
  const navigate = useNavigate();
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [testDrawerVisible, setTestDrawerVisible] = useState(false);
  const [editingDoctor, setEditingDoctor] = useState<Doctor | null>(null);
  const [testDoctor, setTestDoctor] = useState<Doctor | null>(null);
  const [testMessage, setTestMessage] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [testLoading, setTestLoading] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [doctorsRes, deptsRes, kbsRes] = await Promise.all([
        doctorsApi.list(),
        departmentsApi.list(),
        knowledgeBasesApi.list(),
      ]);
      setDoctors(doctorsRes.data);
      setDepartments(deptsRes.data);
      setKnowledgeBases(kbsRes.data);
    } catch (error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingDoctor(null);
    form.resetFields();
    form.setFieldsValue({
      is_ai: true,
      is_active: true,
      ai_model: 'qwen-plus',
      ai_temperature: 0.7,
      ai_max_tokens: 500,
      rating: 5.0,
    });
    setModalVisible(true);
  };

  const handleEdit = (record: Doctor) => {
    setEditingDoctor(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingDoctor) {
        await doctorsApi.update(editingDoctor.id, values);
        message.success('更新成功');
      } else {
        await doctorsApi.create(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await doctorsApi.delete(id);
      message.success('删除成功');
      fetchData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const handleToggleActive = async (id: number, isActive: boolean) => {
    try {
      await doctorsApi.activate(id, isActive);
      message.success(isActive ? '已启用' : '已停用');
      fetchData();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleTest = (doctor: Doctor) => {
    setTestDoctor(doctor);
    setTestMessage('');
    setTestResult(null);
    setTestDrawerVisible(true);
  };

  const handleTestSubmit = async () => {
    if (!testDoctor || !testMessage.trim()) return;
    setTestLoading(true);
    try {
      const res = await doctorsApi.test(testDoctor.id, testMessage);
      setTestResult(res.data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '测试失败');
    } finally {
      setTestLoading(false);
    }
  };

  // 跳转到对话式配置页面
  const handlePersonaChat = (doctorId: number) => {
    navigate(`/admin/doctors/${doctorId}/persona`);
  };

  // 跳转到病历分析页面
  const handleRecordAnalysis = (doctorId: number) => {
    navigate(`/admin/doctors/${doctorId}/analyze`);
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '姓名', dataIndex: 'name', width: 100 },
    { title: '职称', dataIndex: 'title', width: 120 },
    {
      title: '科室',
      dataIndex: 'department_id',
      width: 120,
      render: (id: number) => departments.find((d) => d.id === id)?.name || '-',
    },
    { title: '医院', dataIndex: 'hospital', ellipsis: true },
    {
      title: 'AI模型',
      dataIndex: 'ai_model',
      width: 120,
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 80,
      render: (v: boolean, record: Doctor) => (
        <Switch checked={v} onChange={(checked) => handleToggleActive(record.id, checked)} />
      ),
    },
    {
      title: '操作',
      width: 360,
      render: (_: any, record: Doctor) => (
        <Space wrap>
          {record.is_ai && (
            <>
              <Button
                size="small"
                icon={<MessageOutlined />}
                onClick={() => handlePersonaChat(record.id)}
                type="primary"
                ghost
              >
                配置分身
              </Button>
              <Button
                size="small"
                icon={<FileTextOutlined />}
                onClick={() => handleRecordAnalysis(record.id)}
              >
                病历分析
              </Button>
            </>
          )}
          <Button size="small" icon={<PlayCircleOutlined />} onClick={() => handleTest(record)}>
            测试
          </Button>
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
        <Title level={4}>医生管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新增医生
        </Button>
      </div>

      <Table columns={columns} dataSource={doctors} rowKey="id" loading={loading} scroll={{ x: 1100 }} />

      <Modal
        title={editingDoctor ? '编辑医生' : '新增医生'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={700}
      >
        <Form form={form} layout="vertical">
          <Tabs
            items={[
              {
                key: 'basic',
                label: '基础信息',
                children: (
                  <>
                    <Form.Item name="name" label="姓名" rules={[{ required: true }]}>
                      <Input />
                    </Form.Item>
                    <Form.Item name="title" label="职称">
                      <Input />
                    </Form.Item>
                    <Form.Item name="department_id" label="科室" rules={[{ required: true }]}>
                      <Select options={departments.map((d) => ({ value: d.id, label: d.name }))} />
                    </Form.Item>
                    <Form.Item name="hospital" label="医院">
                      <Input />
                    </Form.Item>
                    <Form.Item name="specialty" label="专长">
                      <TextArea rows={2} />
                    </Form.Item>
                    <Form.Item name="rating" label="评分">
                      <InputNumber min={0} max={5} step={0.1} />
                    </Form.Item>
                  </>
                ),
              },
              {
                key: 'ai',
                label: 'AI配置',
                children: (
                  <>
                    <Form.Item name="is_ai" label="AI医生" valuePropName="checked">
                      <Switch />
                    </Form.Item>
                    <Form.Item name="ai_model" label="AI模型">
                      <Select
                        options={[
                          { value: 'qwen-turbo', label: 'Qwen Turbo' },
                          { value: 'qwen-plus', label: 'Qwen Plus' },
                          { value: 'qwen-max', label: 'Qwen Max' },
                        ]}
                      />
                    </Form.Item>
                    <Form.Item name="ai_temperature" label="温度">
                      <InputNumber min={0} max={2} step={0.1} />
                    </Form.Item>
                    <Form.Item name="ai_max_tokens" label="最大Token">
                      <InputNumber min={100} max={2000} />
                    </Form.Item>
                    <Form.Item name="knowledge_base_id" label="知识库">
                      <Select
                        allowClear
                        options={knowledgeBases.map((kb) => ({ value: kb.id, label: kb.name }))}
                      />
                    </Form.Item>
                    <Form.Item name="ai_persona_prompt" label="人设Prompt">
                      <TextArea rows={6} placeholder="自定义AI人格化提示词，或使用「配置分身」功能通过对话生成..." />
                    </Form.Item>
                  </>
                ),
              },
            ]}
          />
        </Form>
      </Modal>

      <Drawer
        title={`测试AI回复 - ${testDoctor?.name}`}
        open={testDrawerVisible}
        onClose={() => setTestDrawerVisible(false)}
        width={500}
      >
        <div style={{ marginBottom: 16 }}>
          <TextArea
            rows={3}
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            placeholder="输入测试问题..."
          />
          <Button
            type="primary"
            onClick={handleTestSubmit}
            loading={testLoading}
            style={{ marginTop: 8 }}
            block
          >
            发送测试
          </Button>
        </div>
        {testResult && (
          <Card title="AI回复" size="small">
            <p><strong>问题:</strong> {testResult.question}</p>
            <p><strong>回答:</strong> {testResult.answer}</p>
            {testResult.rag_context && (
              <p><strong>RAG上下文:</strong> {testResult.rag_context}</p>
            )}
            <p><strong>模型:</strong> {testResult.model} | <strong>温度:</strong> {testResult.temperature}</p>
          </Card>
        )}
      </Drawer>
    </div>
  );
};

export default Doctors;

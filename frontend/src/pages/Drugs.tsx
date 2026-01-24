import React, { useEffect, useState } from 'react';
import {
  Table, Button, Space, Modal, Form, Input, InputNumber, Select,
  message, Popconfirm, Typography, Tag, Switch, Tabs
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, FireOutlined } from '@ant-design/icons';
import { drugsApi, drugCategoriesApi } from '../api';

const { Title } = Typography;
const { TextArea } = Input;
const { TabPane } = Tabs;

interface DrugCategory {
  id: number;
  name: string;
  icon: string;
  display_type: string;
  sort_order: number;
  is_active: boolean;
  drug_count: number;
}

interface Drug {
  id: number;
  name: string;
  pinyin: string;
  pinyin_abbr: string;
  aliases: string;
  common_brands: string;
  pregnancy_level: string;
  pregnancy_desc: string;
  lactation_level: string;
  lactation_desc: string;
  children_usable: boolean;
  children_desc: string;
  indications: string;
  contraindications: string;
  dosage: string;
  side_effects: string;
  precautions: string;
  interactions: string;
  storage: string;
  author_name: string;
  author_title: string;
  author_avatar: string;
  reviewer_info: string;
  is_hot: boolean;
  sort_order: number;
  is_active: boolean;
  view_count: number;
  category_ids: number[];
  category_names: string[];
}

const Drugs: React.FC = () => {
  const [drugs, setDrugs] = useState<Drug[]>([]);
  const [categories, setCategories] = useState<DrugCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [categoryModalVisible, setCategoryModalVisible] = useState(false);
  const [editingDrug, setEditingDrug] = useState<Drug | null>(null);
  const [editingCategory, setEditingCategory] = useState<DrugCategory | null>(null);
  const [filters, setFilters] = useState<{ category_id?: number; is_active?: boolean; q?: string }>({});
  const [form] = Form.useForm();
  const [categoryForm] = Form.useForm();

  useEffect(() => {
    fetchCategories();
    fetchDrugs();
  }, []);

  useEffect(() => {
    fetchDrugs();
  }, [filters]);

  const fetchCategories = async () => {
    try {
      const response = await drugCategoriesApi.list(true);
      setCategories(response.data);
    } catch (error) {
      message.error('加载分类列表失败');
    }
  };

  const fetchDrugs = async () => {
    setLoading(true);
    try {
      const response = await drugsApi.list(filters);
      setDrugs(response.data.items || response.data);
    } catch (error) {
      message.error('加载药品列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingDrug(null);
    form.resetFields();
    form.setFieldsValue({
      sort_order: 0,
      is_active: true,
      is_hot: false,
      children_usable: true,
      reviewer_info: '三甲医生专业编审 · 灵犀医生官方出品',
      category_ids: []
    });
    setModalVisible(true);
  };

  const handleEdit = async (record: Drug) => {
    try {
      const response = await drugsApi.get(record.id);
      setEditingDrug(response.data);
      form.setFieldsValue(response.data);
      setModalVisible(true);
    } catch (error) {
      message.error('加载药品详情失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingDrug) {
        await drugsApi.update(editingDrug.id, values);
        message.success('更新成功');
      } else {
        await drugsApi.create(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchDrugs();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await drugsApi.delete(id);
      message.success('删除成功');
      fetchDrugs();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const handleToggleHot = async (id: number) => {
    try {
      await drugsApi.toggleHot(id);
      message.success('操作成功');
      fetchDrugs();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleToggleActive = async (id: number) => {
    try {
      await drugsApi.toggleActive(id);
      message.success('操作成功');
      fetchDrugs();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 分类管理
  const handleCreateCategory = () => {
    setEditingCategory(null);
    categoryForm.resetFields();
    categoryForm.setFieldsValue({
      sort_order: 0,
      is_active: true,
      display_type: 'grid'
    });
    setCategoryModalVisible(true);
  };

  const handleEditCategory = (record: DrugCategory) => {
    setEditingCategory(record);
    categoryForm.setFieldsValue(record);
    setCategoryModalVisible(true);
  };

  const handleSubmitCategory = async () => {
    try {
      const values = await categoryForm.validateFields();
      if (editingCategory) {
        await drugCategoriesApi.update(editingCategory.id, values);
        message.success('更新成功');
      } else {
        await drugCategoriesApi.create(values);
        message.success('创建成功');
      }
      setCategoryModalVisible(false);
      fetchCategories();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const handleDeleteCategory = async (id: number) => {
    try {
      await drugCategoriesApi.delete(id);
      message.success('删除成功');
      fetchCategories();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const drugColumns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    {
      title: '名称',
      dataIndex: 'name',
      width: 150,
      render: (text: string, record: Drug) => (
        <Space>
          {text}
          {record.is_hot && <FireOutlined style={{ color: '#ff4d4f' }} />}
        </Space>
      ),
    },
    { title: '商品名', dataIndex: 'common_brands', width: 150, ellipsis: true },
    {
      title: '分类',
      dataIndex: 'category_names',
      width: 120,
      render: (names: string[]) => names?.map((n, i) => <Tag key={i}>{n}</Tag>),
    },
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
      render: (isHot: boolean, record: Drug) => (
        <Switch
          size="small"
          checked={isHot}
          onChange={() => handleToggleHot(record.id)}
        />
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 70,
      render: (isActive: boolean, record: Drug) => (
        <Switch
          size="small"
          checked={isActive}
          onChange={() => handleToggleActive(record.id)}
        />
      ),
    },
    {
      title: '操作',
      width: 100,
      render: (_: any, record: Drug) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const categoryColumns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '名称', dataIndex: 'name', width: 150 },
    { title: '图标', dataIndex: 'icon', width: 100 },
    { title: '显示类型', dataIndex: 'display_type', width: 100 },
    { title: '药品数', dataIndex: 'drug_count', width: 80 },
    { title: '排序', dataIndex: 'sort_order', width: 60 },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 70,
      render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? '启用' : '禁用'}</Tag>,
    },
    {
      title: '操作',
      width: 100,
      render: (_: any, record: DrugCategory) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEditCategory(record)} />
          <Popconfirm title="确定删除?" onConfirm={() => handleDeleteCategory(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Tabs defaultActiveKey="drugs">
        <TabPane tab="药品管理" key="drugs">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
            <Title level={4}>药品百科管理</Title>
            <Space>
              <Select
                placeholder="选择分类"
                allowClear
                style={{ width: 150 }}
                onChange={(v) => setFilters({ ...filters, category_id: v })}
              >
                {categories.map((c) => (
                  <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>
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
                placeholder="搜索药品名称"
                allowClear
                style={{ width: 200 }}
                onSearch={(v) => setFilters({ ...filters, q: v || undefined })}
              />
              <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                新增药品
              </Button>
            </Space>
          </div>

          <Table
            columns={drugColumns}
            dataSource={drugs}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1000 }}
            pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }}
          />
        </TabPane>

        <TabPane tab="分类管理" key="categories">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
            <Title level={4}>药品分类管理</Title>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateCategory}>
              新增分类
            </Button>
          </div>

          <Table
            columns={categoryColumns}
            dataSource={categories}
            rowKey="id"
            pagination={false}
          />
        </TabPane>
      </Tabs>

      {/* 药品编辑弹窗 */}
      <Modal
        title={editingDrug ? '编辑药品' : '新增药品'}
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
                <Form.Item name="name" label="药品名称" rules={[{ required: true, message: '请输入药品名称' }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="common_brands" label="常见商品名">
                  <Input placeholder="如：赛乐欣、希舒美" />
                </Form.Item>
                <Form.Item name="pinyin" label="拼音">
                  <Input placeholder="留空自动生成" />
                </Form.Item>
                <Form.Item name="pinyin_abbr" label="拼音首字母">
                  <Input placeholder="留空自动生成" />
                </Form.Item>
                <Form.Item name="aliases" label="别名" style={{ gridColumn: 'span 2' }}>
                  <Input placeholder="多个别名用逗号分隔" />
                </Form.Item>
                <Form.Item name="category_ids" label="所属分类">
                  <Select mode="multiple" placeholder="选择分类">
                    {categories.map((c) => (
                      <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>
                    ))}
                  </Select>
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

            <TabPane tab="安全等级" key="safety">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <Form.Item name="pregnancy_level" label="孕期安全等级">
                  <Select placeholder="选择等级" allowClear>
                    <Select.Option value="A">A - 安全</Select.Option>
                    <Select.Option value="B">B - 较安全</Select.Option>
                    <Select.Option value="C">C - 慎用</Select.Option>
                    <Select.Option value="D">D - 有风险</Select.Option>
                    <Select.Option value="X">X - 禁用</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item name="pregnancy_desc" label="孕期说明">
                  <Input placeholder="如：妊娠分级 B" />
                </Form.Item>
                <Form.Item name="lactation_level" label="哺乳期等级">
                  <Select placeholder="选择等级" allowClear>
                    <Select.Option value="L1">L1 - 最安全</Select.Option>
                    <Select.Option value="L2">L2 - 较安全</Select.Option>
                    <Select.Option value="L3">L3 - 中等安全</Select.Option>
                    <Select.Option value="L4">L4 - 可能有害</Select.Option>
                    <Select.Option value="L5">L5 - 禁用</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item name="lactation_desc" label="哺乳说明">
                  <Input placeholder="如：哺乳分级 L2" />
                </Form.Item>
                <Form.Item name="children_usable" label="儿童可用" valuePropName="checked">
                  <Switch />
                </Form.Item>
                <Form.Item name="children_desc" label="儿童用药说明">
                  <Input placeholder="儿童用药参考说明" />
                </Form.Item>
              </div>
            </TabPane>

            <TabPane tab="药品内容" key="content">
              <Form.Item name="indications" label="功效作用/适应症">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
              <Form.Item name="contraindications" label="用药禁忌">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
              <Form.Item name="dosage" label="用法用量">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
              <Form.Item name="side_effects" label="不良反应">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
              <Form.Item name="precautions" label="注意事项">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
              <Form.Item name="interactions" label="药物相互作用">
                <TextArea rows={4} placeholder="支持 Markdown 格式" />
              </Form.Item>
              <Form.Item name="storage" label="贮藏方法">
                <TextArea rows={2} placeholder="支持 Markdown 格式" />
              </Form.Item>
            </TabPane>

            <TabPane tab="作者信息" key="author">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <Form.Item name="author_name" label="作者姓名">
                  <Input />
                </Form.Item>
                <Form.Item name="author_title" label="作者职称">
                  <Input placeholder="如：主治医师" />
                </Form.Item>
                <Form.Item name="author_avatar" label="作者头像URL" style={{ gridColumn: 'span 2' }}>
                  <Input placeholder="头像图片链接" />
                </Form.Item>
                <Form.Item name="reviewer_info" label="审核信息" style={{ gridColumn: 'span 2' }}>
                  <Input placeholder="如：三甲医生专业编审 · 灵犀医生官方出品" />
                </Form.Item>
              </div>
            </TabPane>
          </Tabs>
        </Form>
      </Modal>

      {/* 分类编辑弹窗 */}
      <Modal
        title={editingCategory ? '编辑分类' : '新增分类'}
        open={categoryModalVisible}
        onOk={handleSubmitCategory}
        onCancel={() => setCategoryModalVisible(false)}
        width={500}
        destroyOnClose
      >
        <Form form={categoryForm} layout="vertical">
          <Form.Item name="name" label="分类名称" rules={[{ required: true, message: '请输入分类名称' }]}>
            <Input placeholder="如：热门药品、孕期/哺乳期用药" />
          </Form.Item>
          <Form.Item name="icon" label="图标">
            <Input placeholder="图标名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item name="display_type" label="显示类型">
            <Select>
              <Select.Option value="grid">网格</Select.Option>
              <Select.Option value="list">列表</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="sort_order" label="排序">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="is_active" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Drugs;

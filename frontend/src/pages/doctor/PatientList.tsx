import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Table, Input, Card, Tag, Space, Progress, Typography } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

interface Patient {
  id: number;
  nickname?: string;
  phone: string;
  gender?: string;
  age?: number;
  last_consultation_at?: string;
  active_orders_count: number;
  completion_rate: number;
}

const PatientList = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    fetchPatients();
  }, [searchText]);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const url = searchText
        ? `/api/doctor/patients?search=${encodeURIComponent(searchText)}`
        : '/api/doctor/patients';

      const response = await fetch(url);
      const data = await response.json();
      setPatients(data);
    } catch (error) {
      console.error('Failed to fetch patients:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns: ColumnsType<Patient> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
    },
    {
      title: '姓名',
      dataIndex: 'nickname',
      render: (name: string, record: Patient) => (
        <Space>
          <span>{name || '未设置'}</span>
          {record.gender && (
            <Tag color={record.gender === '男' ? 'blue' : 'pink'}>
              {record.gender}
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: '年龄',
      dataIndex: 'age',
      width: 80,
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      width: 130,
    },
    {
      title: '进行中医嘱',
      dataIndex: 'active_orders_count',
      width: 100,
      render: (count: number) => (
        <Tag color={count > 0 ? 'blue' : 'default'}>{count}</Tag>
      ),
    },
    {
      title: '完成率',
      dataIndex: 'completion_rate',
      width: 150,
      render: (rate: number) => {
        const percent = Math.round(rate * 100);
        const color = percent >= 80 ? 'success' : percent >= 50 ? 'normal' : 'exception';
        return <Progress percent={percent} status={color} size="small" />;
      },
    },
    {
      title: '最后咨询',
      dataIndex: 'last_consultation_at',
      width: 120,
      render: (date: string) => (date ? new Date(date).toLocaleDateString() : '-'),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: Patient) => (
        <a onClick={() => navigate(`/patients/${record.id}`)}>查看</a>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>我的患者</Typography.Title>
        <Input
          placeholder="搜索患者姓名或手机号"
          prefix={<SearchOutlined />}
          style={{ width: 250 }}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          allowClear
        />
      </div>

      <Table
        columns={columns}
        dataSource={patients}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </div>
  );
};

export default PatientList;

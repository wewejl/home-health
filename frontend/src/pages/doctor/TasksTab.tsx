import React, { useState, useEffect } from 'react';
import { DatePicker, Card, Row, Col, Statistic, List, Tag, Empty, Typography } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, WarningOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

interface TaskInstance {
  id: number;
  order_id: number;
  patient_id: number;
  scheduled_date: string;
  scheduled_time: string;
  status: string;
  completed_at?: string;
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

interface TasksTabProps {
  patientId: number;
}

const TasksTab: React.FC<TasksTabProps> = ({ patientId }) => {
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [taskList, setTaskList] = useState<{
    pending: TaskInstance[];
    completed: TaskInstance[];
    overdue: TaskInstance[];
    summary: ComplianceSummary;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedDate) {
      fetchTasks(selectedDate.format('YYYY-MM-DD'));
    }
  }, [patientId, selectedDate]);

  const fetchTasks = async (date: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/doctor/patients/${patientId}/tasks?task_date=${date}`);
      const data = await response.json();
      setTaskList(data);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const onDateChange = (date: any) => {
    if (date) {
      setSelectedDate(date);
    }
  };

  const getOrderTypeLabel = (type?: string) => {
    if (!type) return '-';
    const typeMap: Record<string, { label: string; color: string }> = {
      'medication': { label: '用药', color: 'blue' },
      'monitoring': { label: '监测', color: 'green' },
      'behavior': { label: '行为', color: 'orange' },
      'followup': { label: '复诊', color: 'purple' },
    };
    const info = typeMap[type] || { label: type, color: 'default' };
    return <Tag color={info.color}>{info.label}</Tag>;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />;
      case 'pending':
        return <ClockCircleOutlined style={{ color: '#faad14', fontSize: 20 }} />;
      case 'overdue':
        return <WarningOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />;
      default:
        return <ClockCircleOutlined style={{ fontSize: 20 }} />;
    }
  };

  const getStatusLabel = (status: string) => {
    const statusMap: Record<string, { label: string; color: string }> = {
      'pending': { label: '待完成', color: 'default' },
      'completed': { label: '已完成', color: 'success' },
      'overdue': { label: '已超时', color: 'error' },
      'skipped': { label: '已跳过', color: 'default' },
    };
    const info = statusMap[status] || { label: status, color: 'default' };
    return <Tag color={info.color}>{info.label}</Tag>;
  };

  const renderTaskList = (tasks: TaskInstance[], title: string, emptyText: string) => (
    <Card
      title={title}
      size="small"
      style={{ height: 'calc(100vh - 400px)', overflow: 'auto' }}
    >
      {tasks.length === 0 ? (
        <Empty description={emptyText} image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <List
          dataSource={tasks}
          renderItem={(task) => (
            <List.Item key={task.id}>
              <List.Item.Meta
                avatar={getStatusIcon(task.status)}
                title={
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text strong>{task.order_title || '未命名医嘱'}</Text>
                    {getStatusLabel(task.status)}
                  </div>
                }
                description={
                  <div>
                    <Space>
                      {getOrderTypeLabel(task.order_type)}
                      <Text type="secondary">
                        计划时间: {task.scheduled_time}
                      </Text>
                      {task.completed_at && (
                        <Text type="secondary">
                          完成时间: {dayjs(task.completed_at).format('HH:mm')}
                        </Text>
                      )}
                    </Space>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Card>
  );

  return (
    <div style={{ padding: 16 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={5} style={{ margin: 0 }}>任务执行情况</Title>
        <DatePicker
          value={selectedDate}
          onChange={onDateChange}
          format="YYYY-MM-DD"
          allowClear={false}
        />
      </div>

      {taskList && (
        <>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="总任务数"
                  value={taskList.summary.total}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="已完成"
                  value={taskList.summary.completed}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="待完成"
                  value={taskList.summary.pending}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="完成率"
                  value={Math.round(taskList.summary.rate * 100)}
                  suffix="%"
                  valueStyle={{
                    color: taskList.summary.rate >= 0.8 ? '#52c41a' : taskList.summary.rate >= 0.5 ? '#faad14' : '#ff4d4f'
                  }}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              {renderTaskList(taskList.completed, '已完成', '该日无已完成任务')}
            </Col>
            <Col span={8}>
              {renderTaskList(taskList.pending, '待完成', '该日无待完成任务')}
            </Col>
            <Col span={8}>
              {renderTaskList(taskList.overdue, '已超时', '该日无超时任务')}
            </Col>
          </Row>
        </>
      )}

      {!taskList && !loading && (
        <Empty description="请选择日期查看任务" />
      )}
    </div>
  );
};

import { Space } from 'antd';

export default TasksTab;

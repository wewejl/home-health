import React, { useEffect, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Select,
  DatePicker,
  Statistic,
  Table,
  Typography,
  Tag,
  Alert,
  Space,
  Progress,
  List,
} from 'antd';
import {
  RiseOutlined,
  FallOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CalendarOutlined,
} from '@ant-design/icons';
import { Line, Column, Pie } from '@ant-design/charts';
import { medicalOrdersApi } from '../api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

// 依从性数据类型
interface DailyCompliance {
  date: string;
  total: number;
  completed: number;
  overdue: number;
  pending: number;
  rate: number;
}

interface WeeklyCompliance {
  daily_rates: number[];
  average_rate: number;
  dates: string[];
}

interface AbnormalRecord {
  id: number;
  task_title: string;
  value_data: Record<string, any>;
  completed_at: string;
  alert_type?: string;
}

const PatientCompliance: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<number>(1);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(7, 'day'),
    dayjs(),
  ]);

  // 依从性数据
  const [weeklyData, setWeeklyData] = useState<WeeklyCompliance | null>(null);
  const [dailyData, setDailyData] = useState<DailyCompliance[]>([]);
  const [abnormalRecords, setAbnormalRecords] = useState<AbnormalRecord[]>([]);

  // 患者列表（模拟数据，实际应从用户API获取）
  const patients = [
    { id: 1, name: '测试患者' },
    { id: 2, name: '张三' },
    { id: 3, name: '李四' },
  ];

  // 获取周依从性数据
  const fetchWeeklyCompliance = async () => {
    try {
      const response = await medicalOrdersApi.getWeeklyCompliance();
      setWeeklyData(response.data);

      // 转换为每日数据格式
      const daily: DailyCompliance[] = response.data.dates.map((date: string, index: number) => ({
        date,
        total: 10, // 模拟数据
        completed: Math.round(10 * response.data.daily_rates[index]),
        overdue: Math.round(Math.random() * 2),
        pending: Math.round(10 * (1 - response.data.daily_rates[index])),
        rate: response.data.daily_rates[index],
      }));
      setDailyData(daily);
    } catch (error) {
      console.error('Failed to fetch weekly compliance:', error);
    }
  };

  // 获取异常记录
  const fetchAbnormalRecords = async () => {
    try {
      const response = await medicalOrdersApi.getAbnormalRecords(30);
      setAbnormalRecords(response.data);
    } catch (error) {
      console.error('Failed to fetch abnormal records:', error);
    }
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchWeeklyCompliance(), fetchAbnormalRecords()]).finally(() => {
      setLoading(false);
    });
  }, [selectedPatient]);

  // 计算统计数据
  const averageRate = weeklyData?.average_rate || 0;
  const totalTasks = dailyData.reduce((sum, day) => sum + day.total, 0);
  const completedTasks = dailyData.reduce((sum, day) => sum + day.completed, 0);
  const overdueTasks = dailyData.reduce((sum, day) => sum + day.overdue, 0);

  // 趋势图表数据
  const trendLineData = dailyData.map((day) => ({
    date: dayjs(day.date).format('MM/DD'),
    value: Math.round(day.rate * 100),
  }));

  const barChartData = dailyData.map((day) => ({
    date: dayjs(day.date).format('MM/DD'),
    总任务数: day.total,
    已完成: day.completed,
  }));

  // 饼图数据
  const pieData = [
    { type: '已完成', value: completedTasks },
    { type: '已超时', value: overdueTasks },
    { type: '待完成', value: totalTasks - completedTasks - overdueTasks },
  ];

  // 异常记录表格列
  const abnormalColumns = [
    {
      title: '任务',
      dataIndex: 'task_title',
      key: 'task_title',
    },
    {
      title: '异常值',
      dataIndex: 'value_data',
      key: 'value_data',
      render: (value: Record<string, any>) => {
        if (!value) return '-';
        return JSON.stringify(value);
      },
    },
    {
      title: '记录时间',
      dataIndex: 'completed_at',
      key: 'completed_at',
      render: (time: string) => dayjs(time).format('MM-DD HH:mm'),
    },
    {
      title: '类型',
      dataIndex: 'alert_type',
      key: 'alert_type',
      render: (type: string) => {
        const typeMap: Record<string, { text: string; color: string }> = {
          glucose_low: { text: '低血糖', color: 'red' },
          glucose_high: { text: '高血糖', color: 'orange' },
          bp_high: { text: '高血压', color: 'red' },
          temp_high: { text: '发烧', color: 'orange' },
        };
        const config = typeMap[type] || { text: type, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
  ];

  // 折线图配置
  const lineConfig = {
    data: trendLineData,
    xField: 'date',
    yField: 'value',
    yAxis: { max: 100, min: 0 },
    smooth: true,
    point: { size: 4 },
    color: '#1890ff',
    tooltip: {
      formatter: (datum: any) => ({
        name: '完成率',
        value: `${datum.value}%`,
      }),
    },
  };

  // 柱状图配置
  const barConfig = {
    data: barChartData,
    xField: 'date',
    yField: ['总任务数', '已完成'],
    seriesField: 'type',
    color: ['#1890ff', '#52c41a'],
    columnWidthRatio: 0.6,
    legend: {
      position: 'top' as const,
    },
  };

  // 饼图配置
  const pieConfig = {
    data: pieData,
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    innerRadius: 0.6,
    color: ['#52c41a', '#f5222d', '#faad14'],
    label: {
      type: 'inner' as const,
      offset: '-50%',
      content: '{value}',
      style: { textAlign: 'center' as const, fontSize: 14 },
    },
    legend: {
      position: 'bottom' as const,
    },
  };

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={4} style={{ margin: 0 }}>
            患者依从性分析
          </Title>
        </Col>
        <Col>
          <Space>
            <Select
              style={{ width: 120 }}
              value={selectedPatient}
              onChange={setSelectedPatient}
            >
              {patients.map((p) => (
                <Select.Option key={p.id} value={p.id}>
                  {p.name}
                </Select.Option>
              ))}
            </Select>
            <RangePicker
              value={dateRange}
              onChange={(dates) => dates && setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
            />
          </Space>
        </Col>
      </Row>

      {/* 统计概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="平均依从率"
              value={Math.round(averageRate * 100)}
              suffix="%"
              prefix={
                averageRate >= 0.8 ? (
                  <RiseOutlined style={{ color: '#52c41a' }} />
                ) : (
                  <FallOutlined style={{ color: '#f5222d' }} />
                )
              }
              valueStyle={{
                color: averageRate >= 0.8 ? '#52c41a' : averageRate >= 0.6 ? '#faad14' : '#f5222d',
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="总任务数"
              value={totalTasks}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="已完成"
              value={completedTasks}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="已超时"
              value={overdueTasks}
              prefix={<WarningOutlined />}
              valueStyle={{ color: overdueTasks > 0 ? '#f5222d' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 趋势图表 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={16}>
          <Card title="近7天依从性趋势" loading={loading}>
            <Line {...lineConfig} height={250} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="任务完成分布" loading={loading}>
            <Pie {...pieConfig} height={200} />
          </Card>
        </Col>
      </Row>

      {/* 每日详细数据 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="每日任务详情" loading={loading}>
            <Column {...barConfig} height={200} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="近7天完成率" loading={loading}>
            <List
              dataSource={dailyData}
              renderItem={(day) => {
                const percent = Math.round(day.rate * 100);
                return (
                  <List.Item>
                    <List.Item.Meta
                      title={
                        <Space>
                          <Text>{dayjs(day.date).format('MM月DD日')}</Text>
                          <Text type="secondary">({day.completed}/{day.total})</Text>
                        </Space>
                      }
                      description={
                        <Progress
                          percent={percent}
                          status={percent >= 80 ? 'success' : percent >= 60 ? 'normal' : 'exception'}
                          size="small"
                        />
                      }
                    />
                  </List.Item>
                );
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 异常记录 */}
      <Card
        title={
          <Space>
            <WarningOutlined style={{ color: '#f5222d' }} />
            <span>异常监测记录</span>
            <Tag color="#f5222d">{abnormalRecords.length}</Tag>
          </Space>
        }
        loading={loading}
      >
        {abnormalRecords.length === 0 ? (
          <Alert
            message="暂无异常记录"
            description="患者近30天内没有监测到异常数值"
            type="success"
            showIcon
          />
        ) : (
          <Table
            columns={abnormalColumns}
            dataSource={abnormalRecords}
            rowKey="id"
            pagination={{ pageSize: 5 }}
            size="small"
          />
        )}
      </Card>

      {/* 健康建议 */}
      <Card
        title="健康建议"
        style={{ marginTop: 16 }}
        loading={loading}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          {averageRate >= 0.8 ? (
            <Alert
              message="依从性优秀"
              description="患者近7天医嘱执行率保持在80%以上，请继续保持！"
              type="success"
              showIcon
            />
          ) : averageRate >= 0.6 ? (
            <Alert
              message="依从性一般"
              description="患者近7天医嘱执行率为60%-80%，建议关注提醒，帮助患者按时完成医嘱。"
              type="warning"
              showIcon
            />
          ) : (
            <Alert
              message="依从性偏低"
              description="患者近7天医嘱执行率低于60%，需要重点关注，建议联系患者了解原因并提供帮助。"
              type="error"
              showIcon
            />
          )}

          {overdueTasks > 0 && (
            <Alert
              message={`发现 ${overdueTasks} 个超时任务`}
              description="有部分任务未按时完成，建议患者设置提醒，或联系家属协助监督。"
              type="warning"
              showIcon
            />
          )}

          {abnormalRecords.length > 0 && (
            <Alert
              message={`发现 ${abnormalRecords.length} 条异常记录`}
              description="监测到异常数值，建议及时就医或调整治疗方案。"
              type="error"
              showIcon
            />
          )}
        </Space>
      </Card>
    </div>
  );
};

export default PatientCompliance;

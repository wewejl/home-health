import { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, User, MessageSquare, FileText, CheckCircle2 } from 'lucide-react';
import { doctorApi } from '@/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { PatientDetailCardSkeleton } from '@/components/medical/loading-skeleton';
import ConsultationsTab from './ConsultationsTab';
import OrdersTab from './OrdersTab';
import TasksTab from './TasksTab';

interface Patient {
  id: number;
  nickname?: string;
  phone: string;
  gender?: string;
  age?: number;
  avatar_url?: string;
  is_profile_completed?: boolean;
  active_orders_count: number;
  completion_rate: number;
  created_at?: string;
}

const PatientDetail = () => {
  const navigate = useNavigate();
  const { patientId } = useParams<{ patientId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);

  // 从 URL 参数获取当前激活的 Tab，默认为 consultations
  const activeTab = searchParams.get('tab') || 'consultations';

  const handleTabChange = (value: string) => {
    setSearchParams({ tab: value });
  };

  useEffect(() => {
    if (patientId) {
      fetchPatientDetail();
    }
  }, [patientId]);

  const fetchPatientDetail = async () => {
    setLoading(true);
    try {
      const response = await doctorApi.getPatient(Number(patientId));
      setPatient(response.data);
    } catch (error) {
      console.error('Failed to fetch patient:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !patient) {
    return (
      <div className="page-container min-h-screen">
        {/* 返回按钮骨架 */}
        <div className="h-10 w-24 bg-muted animate-pulse rounded mb-4" />

        {/* 患者详情卡片骨架 */}
        <PatientDetailCardSkeleton />

        {/* Tabs 骨架 */}
        <Card>
          <div className="flex gap-4 p-2 border-b">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-10 w-24 bg-muted animate-pulse rounded" />
            ))}
          </div>
          <div className="p-4 flex items-center justify-center h-64">
            <div className="text-muted-foreground">加载中...</div>
          </div>
        </Card>
      </div>
    );
  }

  const percent = Math.round(patient.completion_rate * 100);

  const getCompletionColor = (value: number) => {
    if (value >= 80) return 'text-success';
    if (value >= 50) return 'text-warning';
    return 'text-danger';
  };

  return (
    <div className="page-container min-h-screen">
      {/* 返回按钮 */}
      <Button
        variant="ghost"
        className="mb-4"
        onClick={() => navigate('/patients')}
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        返回患者列表
      </Button>

      {/* 患者基本信息卡片 */}
      <Card className="mb-4">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-6">
            {/* 头像区域 */}
            <div className="flex-shrink-0 flex flex-col items-center">
              <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center mb-3">
                <User className="h-10 w-10 text-muted-foreground" />
              </div>
              <h3 className="font-semibold text-lg">
                {patient.nickname || '未设置姓名'}
              </h3>
              <p className="text-sm text-muted-foreground">{patient.phone}</p>
            </div>

            <Separator orientation="vertical" className="hidden md:block" />

            {/* 详细信息 */}
            <div className="flex-1">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {/* 性别 */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="text-sm text-muted-foreground">性别</span>
                  {patient.gender ? (
                    <Badge variant={patient.gender === '男' ? 'default' : 'secondary'}>
                      {patient.gender}
                    </Badge>
                  ) : (
                    <span className="text-sm">-</span>
                  )}
                </div>

                {/* 年龄 */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="text-sm text-muted-foreground">年龄</span>
                  <span className="font-medium">{patient.age || '-'}</span>
                </div>

                {/* 资料完善度 */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="text-sm text-muted-foreground">资料完善度</span>
                  <Badge
                    variant={patient.is_profile_completed ? 'default' : 'secondary'}
                    className={patient.is_profile_completed ? 'bg-medical-success' : ''}
                  >
                    {patient.is_profile_completed ? '已完善' : '未完善'}
                  </Badge>
                </div>

                {/* 进行中医嘱 */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="text-sm text-muted-foreground">进行中医嘱</span>
                  <Badge variant={patient.active_orders_count > 0 ? 'default' : 'secondary'}>
                    {patient.active_orders_count} 条
                  </Badge>
                </div>

                {/* 最近7天完成率 */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="text-sm text-muted-foreground">最近7天完成率</span>
                  <span className={`font-semibold ${getCompletionColor(percent)}`}>
                    {percent}%
                  </span>
                </div>

                {/* 注册时间 */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="text-sm text-muted-foreground">注册时间</span>
                  <span className="text-sm">
                    {patient.created_at ? new Date(patient.created_at).toLocaleDateString() : '-'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <Card className="stat-card">
          <CardContent className="p-5">
            <p className="text-xs text-muted-foreground uppercase tracking-wide mb-2">进行中医嘱</p>
            <p className={`text-3xl font-bold tracking-tight ${patient.active_orders_count > 0 ? '' : 'text-muted-foreground'}`}>
              {patient.active_orders_count}
              <span className="text-lg font-normal text-muted-foreground ml-1">条</span>
            </p>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="p-5">
            <p className="text-xs text-muted-foreground uppercase tracking-wide mb-2">最近7天完成率</p>
            <p className={`text-3xl font-bold tracking-tight ${getCompletionColor(percent)}`}>
              {percent}
              <span className="text-lg font-normal text-muted-foreground ml-1">%</span>
            </p>
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardContent className="p-5">
            <p className="text-xs text-muted-foreground uppercase tracking-wide mb-2">患者状态</p>
            <p className={`text-xl font-bold tracking-tight ${patient.is_profile_completed ? 'text-success' : 'text-warning'}`}>
              {patient.is_profile_completed ? '已完善' : '未完善'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 选项卡 */}
      <Card>
        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
          <TabsList className="w-full justify-start rounded-none border-b">
            <TabsTrigger value="consultations" className="gap-2">
              <MessageSquare className="h-4 w-4" />
              AI对话记录
            </TabsTrigger>
            <TabsTrigger value="orders" className="gap-2">
              <FileText className="h-4 w-4" />
              医嘱管理
            </TabsTrigger>
            <TabsTrigger value="tasks" className="gap-2">
              <CheckCircle2 className="h-4 w-4" />
              任务完成情况
            </TabsTrigger>
          </TabsList>
          <TabsContent value="consultations" className="mt-0">
            <ConsultationsTab patientId={Number(patientId)} />
          </TabsContent>
          <TabsContent value="orders" className="mt-0">
            <OrdersTab patientId={Number(patientId)} refresh={fetchPatientDetail} />
          </TabsContent>
          <TabsContent value="tasks" className="mt-0">
            <TasksTab patientId={Number(patientId)} />
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
};

export default PatientDetail;

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, AlertTriangle, Clock, Flame, User, Loader2 } from 'lucide-react';
import dayjs from 'dayjs';
import axios from 'axios';

// shadcn/ui components
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

// ============================================
// TYPES
// ============================================

interface Patient {
  id: number;
  name: string;
  nickname?: string;
  avatar?: string;
  last_seen: string;
  last_consultation: string;
  completionRate: number;
  totalTasks: number;
  completedTasks: number;
  status: 'danger' | 'warning' | 'success';
  alerts?: string[];
  riskLevel?: 'high' | 'medium' | 'low';
}

interface PatientListResponse {
  patients: Patient[];
  stats: {
    total: number;
    abnormal: number;
    high_risk: number;
  };
}

// API 基础路径
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ============================================
// MAIN COMPONENT
// ============================================

const Rounding: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [filteredPatients, setFilteredPatients] = useState<Patient[]>([]);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'abnormal' | 'high-risk'>('all');
  const [stats, setStats] = useState({ total: 0, abnormal: 0, high_risk: 0 });

  // 加载数据
  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const response = await axios.get<PatientListResponse>(
          `${API_BASE}/rounding/patients`
        );
        setPatients(response.data.patients);
        setFilteredPatients(response.data.patients);
        setStats(response.data.stats);
      } catch (error) {
        console.error('Failed to fetch patients:', error);
        // 使用空数据
        setPatients([]);
        setFilteredPatients([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPatients();
  }, []);

  // 搜索过滤
  useEffect(() => {
    let filtered = [...patients];

    if (searchText) {
      filtered = filtered.filter(p =>
        p.name.toLowerCase().includes(searchText.toLowerCase())
      );
    }

    if (statusFilter === 'abnormal') {
      filtered = filtered.filter(p => p.status === 'danger' || p.status === 'warning');
    } else if (statusFilter === 'high-risk') {
      filtered = filtered.filter(p => p.riskLevel === 'high');
    }

    filtered.sort((a, b) => {
      const statusOrder = { danger: 0, warning: 1, success: 2 };
      return statusOrder[a.status] - statusOrder[b.status];
    });

    setFilteredPatients(filtered);
  }, [searchText, statusFilter, patients]);

  // 点击卡片
  const handleCardClick = (patientId: number) => {
    navigate(`/rounding/${patientId}`);
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'success': return '执行良好';
      case 'warning': return '需要关注';
      default: return '异常';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-foreground-secondary">加载患者数据...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        {/* 顶部标题栏 */}
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-foreground mb-1">远程查房</h1>
          <p className="text-sm text-foreground-secondary">
            实时监控患者医嘱执行情况 · 最后更新: {dayjs().format('HH:mm:ss')}
          </p>
        </div>

        {/* 统计概览 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card className="p-4">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <User className="h-5 w-5 text-primary" />
              </div>
              <div>
                <div className="text-sm text-foreground-secondary">管理患者</div>
                <div className="text-2xl font-semibold text-foreground">{stats.total}</div>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-danger/10 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-danger" />
              </div>
              <div>
                <div className="text-sm text-foreground-secondary">异常患者</div>
                <div className={`text-2xl font-semibold ${stats.abnormal > 0 ? 'text-danger' : 'text-success'}`}>
                  {stats.abnormal}
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-warning/10 flex items-center justify-center">
                <Flame className="h-5 w-5 text-warning" />
              </div>
              <div>
                <div className="text-sm text-foreground-secondary">高风险</div>
                <div className={`text-2xl font-semibold ${stats.high_risk > 0 ? 'text-warning' : 'text-muted-foreground'}`}>
                  {stats.high_risk}
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* 筛选栏 */}
        <div className="flex flex-wrap items-center gap-3 mb-6">
          <div className="relative flex-1 max-w-[240px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-secondary" />
            <Input
              placeholder="搜索患者姓名..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部患者</SelectItem>
              <SelectItem value="abnormal">只看异常</SelectItem>
              <SelectItem value="high-risk">只看高风险</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 患者卡片网格 */}
        {filteredPatients.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-foreground-secondary">
            <AlertTriangle className="h-12 w-12 mb-4 opacity-50" />
            <p className="text-sm">没有找到匹配的患者</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredPatients.map((patient) => (
              <Card
                key={patient.id}
                className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:-translate-y-1 overflow-hidden"
                onClick={() => handleCardClick(patient.id)}
              >
                {/* 顶部状态条 */}
                <div className={`h-1.5 w-full ${
                  patient.status === 'success' ? 'bg-success' :
                  patient.status === 'warning' ? 'bg-warning' : 'bg-danger'
                }`} />

                <div className="p-4">
                  <div className="flex items-start gap-3 mb-4">
                    <Avatar className="h-12 w-12" fallback={patient.name.charAt(0)} />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-foreground truncate">{patient.name}</h3>
                      <p className="text-xs text-foreground-secondary flex items-center gap-1 mt-1">
                        <Clock className="h-3 w-3" />
                        上次活跃: {patient.last_seen}
                      </p>
                    </div>
                    {patient.riskLevel === 'high' && (
                      <Badge variant="danger" className="shrink-0">高风险</Badge>
                    )}
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className={`font-medium ${
                        patient.status === 'success' ? 'text-success' :
                        patient.status === 'warning' ? 'text-warning' : 'text-danger'
                      }`}>
                        {getStatusText(patient.status)}
                      </span>
                      <span className="text-foreground-secondary">
                        {patient.completedTasks}/{patient.totalTasks}
                      </span>
                    </div>

                    <Progress value={patient.completionRate} className="h-2" />

                    <div className="flex items-center justify-between">
                      <span className="text-lg font-semibold text-foreground">
                        {patient.completionRate}%
                      </span>
                      <span className="text-xs text-foreground-secondary">今日完成率</span>
                    </div>

                    {patient.alerts && patient.alerts.length > 0 && (
                      <div className={`flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs ${
                        patient.status === 'success' ? 'bg-success-light/80 text-success' :
                        patient.status === 'warning' ? 'bg-warning-light/80 text-warning' :
                        'bg-danger-light/80 text-danger'
                      }`}>
                        <AlertTriangle className="h-3.5 w-3.5" />
                        <span className="truncate">{patient.alerts[0]}</span>
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Rounding;

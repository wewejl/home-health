import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Fragment } from 'react';
import { Search, User, Users, UserCheck, PlusCircle, AlertTriangle } from 'lucide-react';
import { doctorApi } from '@/api';
import { Button } from '@/components/ui/button';
import { useDebounce } from '@/hooks/useDebounce';
import { PatientCardSkeleton } from '@/components/medical/loading-skeleton';
import { LargePatientCard, type Patient } from '@/components/patient';
import { AssignPatientDialog } from './AssignPatientDialog';

interface ManagedDoctor {
  id: number;
  name: string;
  title?: string;
  department?: string;
}

interface DoctorInfo {
  id: number;
  username: string;
  email?: string;
  role: string;
  department_id?: number;
  department_name?: string;
  managed_doctors: ManagedDoctor[];
}

interface PatientStats {
  total: number;
  active: number;
  new_today: number;
  low_compliance: number;
}

const PatientList = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [searchText, setSearchText] = useState('');
  const debouncedSearch = useDebounce(searchText, 300);
  const [doctorInfo, setDoctorInfo] = useState<DoctorInfo | null>(null);
  const [stats, setStats] = useState<PatientStats>({
    total: 0,
    active: 0,
    new_today: 0,
    low_compliance: 0,
  });
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);

  useEffect(() => {
    fetchDoctorInfo();
    fetchPatientStats();
    fetchPatients();
  }, [debouncedSearch]);

  const fetchDoctorInfo = async () => {
    try {
      const response = await doctorApi.getMe();
      setDoctorInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch doctor info:', error);
    }
  };

  const fetchPatientStats = async () => {
    try {
      const response = await doctorApi.getPatientStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch patient stats:', error);
    }
  };

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const response = await doctorApi.getPatients(debouncedSearch);
      const patientData = response.data;
      setPatients(patientData);
    } catch (error) {
      console.error('Failed to fetch patients:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDoctorInitial = (username: string): string => {
    return username?.[0] || '医';
  };

  const getAiDoctorInitial = (name: string): string => {
    return name?.[0] || '?';
  };

  const getAiDoctorGradient = (index: number): string => {
    const gradients = [
      'from-sky-400 to-sky-600',
      'from-emerald-400 to-emerald-600',
      'from-violet-400 to-violet-600',
    ];
    return gradients[index % gradients.length];
  };

  const handleQuickConsult = (patient: Patient) => {
    // 导航到患者详情页的咨询 Tab
    navigate(`/patients/${patient.id}?tab=consultations`);
  };

  return (
    <Fragment>
      <div className="page-container min-h-screen">
      {/* 页面标题 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">我的患者</h1>
          <p className="text-foreground-secondary mt-1">
            共 <span className="text-primary font-semibold">{patients.length}</span> 位患者
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-5 h-5 text-foreground-tertiary absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="搜索患者姓名或手机号"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="pl-10 pr-4 py-3 w-80 bg-surface border border-border rounded-xl text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          <Button
            className="px-6 py-3 bg-primary hover:bg-primary-hover rounded-xl"
            onClick={() => setAssignDialogOpen(true)}
          >
            <PlusCircle className="w-4 h-4 mr-2" />
            添加患者
          </Button>
        </div>
      </div>

      {/* 医生信息横条 */}
      {doctorInfo && (
        <div className="bg-surface rounded-xl border border-border p-5 shadow-sm mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-sky-500 to-sky-600 flex items-center justify-center text-white text-xl font-bold shadow-md">
                {getDoctorInitial(doctorInfo.username)}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">
                  Dr. {doctorInfo.username}
                </h2>
                <p className="text-foreground-secondary text-sm">
                  {doctorInfo.department_name || '内科'} · 主任医师
                </p>
              </div>
            </div>
            <div className="h-8 w-px bg-border"></div>
            <div className="flex items-center gap-2">
              <span className="text-foreground-secondary text-sm">管理的AI分身：</span>
              <div className="flex -space-x-2">
                {doctorInfo.managed_doctors.map((doctor, idx) => (
                  <div
                    key={doctor.id}
                    className={`w-10 h-10 rounded-full bg-gradient-to-br ${getAiDoctorGradient(idx)} border-2 border-surface flex items-center justify-center text-white text-sm font-bold shadow-sm`}
                  >
                    {getAiDoctorInitial(doctor.name)}
                  </div>
                ))}
                {doctorInfo.managed_doctors.length === 0 && (
                  <span className="text-foreground-tertiary text-sm">暂未分配</span>
                )}
              </div>
            </div>
            <button className="px-4 py-2 text-primary text-sm font-medium hover:bg-primary/10 rounded-lg transition-colors">
              管理分身 →
            </button>
          </div>
        </div>
      )}

      {/* 统计条 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="stat-card rounded-xl border border-border p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-foreground-secondary text-sm">总患者</p>
              <p className="text-3xl font-bold text-foreground mt-1">{stats.total}</p>
            </div>
            <div className="w-12 h-12 bg-info-light rounded-xl flex items-center justify-center">
              <Users className="w-6 h-6 text-info" />
            </div>
          </div>
        </div>
        <div className="stat-card rounded-xl border border-border p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-foreground-secondary text-sm">活跃患者</p>
              <p className="text-3xl font-bold text-success mt-1">{stats.active}</p>
            </div>
            <div className="w-12 h-12 bg-success-light rounded-xl flex items-center justify-center">
              <UserCheck className="w-6 h-6 text-success" />
            </div>
          </div>
        </div>
        <div className="stat-card rounded-xl border border-border p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-foreground-secondary text-sm">今日新增</p>
              <p className="text-3xl font-bold text-primary mt-1">+{stats.new_today}</p>
            </div>
            <div className="w-12 h-12 bg-info-light rounded-xl flex items-center justify-center">
              <PlusCircle className="w-6 h-6 text-info" />
            </div>
          </div>
        </div>
        <div className="stat-card rounded-xl border border-border p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-foreground-secondary text-sm">低依从</p>
              <p className="text-3xl font-bold text-warning mt-1">{stats.low_compliance}</p>
            </div>
            <div className="w-12 h-12 bg-warning-light rounded-xl flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-warning" />
            </div>
          </div>
        </div>
      </div>

      {/* 患者卡片网格 - 大卡片设计 */}
      {loading ? (
        <PatientCardSkeleton />
      ) : patients.length === 0 ? (
        <div className="bg-surface rounded-xl border border-border p-12 text-center">
          <User className="w-16 h-16 text-foreground-tertiary mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-foreground mb-2">暂无患者数据</h3>
          <p className="text-sm text-foreground-secondary">
            {searchText ? '尝试使用其他关键词搜索' : '当有患者分配给您时，将在此显示'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {patients.map((patient) => (
            <LargePatientCard
              key={patient.id}
              patient={patient}
              onClick={() => navigate(`/patients/${patient.id}`)}
              onQuickConsult={handleQuickConsult}
            />
          ))}
        </div>
      )}
      </div>

      {/* 添加患者对话框 */}
      <AssignPatientDialog
        open={assignDialogOpen}
        onClose={() => setAssignDialogOpen(false)}
        onSuccess={() => {
          fetchPatients();
          fetchPatientStats();
        }}
      />
    </Fragment>
  );
};

export default PatientList;

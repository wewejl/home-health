import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

export interface Patient {
  id: number;
  nickname?: string;
  phone: string;
  gender?: string;
  age?: number;
  last_consultation_at?: string;
  active_orders_count: number;
  completion_rate: number;
}

interface PatientCardProps {
  patient: Patient;
  onClick: () => void;
}

// 获取性别徽章样式
const getGenderBadgeVariant = (gender?: string): 'default' | 'secondary' | 'outline' => {
  if (gender === '男') return 'default';
  if (gender === '女') return 'secondary';
  return 'outline';
};

// 获取头像颜色渐变类名（基于姓氏）
const getAvatarGradient = (name?: string): string => {
  const initial = name?.[0] || '?';
  const gradients = [
    'from-blue-500 to-cyan-500',
    'from-purple-500 to-pink-500',
    'from-green-500 to-emerald-500',
    'from-orange-500 to-amber-500',
    'from-rose-500 to-red-500',
    'from-indigo-500 to-violet-500',
  ];
  // 根据姓氏首字符的编码选择渐变色
  const index = initial.charCodeAt(0) % gradients.length;
  return gradients[index];
};

// 隐藏手机号中间4位
const maskPhone = (phone: string): string => {
  if (!phone || phone.length < 7) return phone;
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2');
};

// 格式化最后咨询时间
const formatLastConsultation = (dateStr?: string): string => {
  if (!dateStr) return '从未咨询';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return '今天';
  if (diffDays === 1) return '昨天';
  if (diffDays < 7) return `${diffDays}天前`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}周前`;
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
};

// 获取完成率颜色
const getCompletionRateColor = (rate: number): string => {
  if (rate >= 0.8) return 'text-success';
  if (rate >= 0.5) return 'text-warning';
  return 'text-danger';
};

export const PatientCard: React.FC<PatientCardProps> = ({ patient, onClick }) => {
  const initial = patient.nickname?.[0] || '?';
  const avatarGradient = getAvatarGradient(patient.nickname);
  const genderVariant = getGenderBadgeVariant(patient.gender);
  const completionRateColor = getCompletionRateColor(patient.completion_rate);
  const completionPercent = Math.round(patient.completion_rate * 100);
  const lastConsultationText = formatLastConsultation(patient.last_consultation_at);

  return (
    <Card
      className="patient-card group cursor-pointer overflow-hidden"
      onClick={onClick}
    >
      {/* 卡片内容 */}
      <div className="p-5">
        {/* 头部：头像和基本信息 */}
        <div className="flex items-start gap-2 mb-4">
          {/* 头像 */}
          <div className={`w-14 h-14 rounded-full bg-gradient-to-br ${avatarGradient} flex items-center justify-center shadow-md flex-shrink-0`}>
            <span className="text-xl font-bold text-white">
              {initial}
            </span>
          </div>

          {/* 姓名和性别 */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-semibold text-foreground truncate">
                {patient.nickname || '未设置姓名'}
              </h3>
              {patient.gender && (
                <Badge variant={genderVariant} className="text-xs">
                  {patient.gender}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2 text-sm text-foreground-secondary">
              {patient.age ? (
                <span>{patient.age}岁</span>
              ) : (
                <span className="text-foreground-tertiary italic text-xs">未填写年龄</span>
              )}
              <span>{maskPhone(patient.phone)}</span>
            </div>
          </div>
        </div>

        {/* 医嘱数量和完成率 */}
        <div className="space-y-3">
          {/* 医嘱数量 */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-foreground-secondary">进行中医嘱</span>
            <Badge
              variant={patient.active_orders_count > 0 ? 'default' : 'secondary'}
              className="font-medium"
            >
              {patient.active_orders_count}
            </Badge>
          </div>

          {/* 完成率进度条 */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-foreground-secondary">完成率</span>
              <span className={`text-sm font-semibold ${completionRateColor}`}>
                {completionPercent}%
              </span>
            </div>
            <div className="relative h-2 bg-surface-alt rounded-full overflow-hidden">
              <Progress
                value={completionPercent}
                className="h-2 absolute top-0 left-0 w-full"
              />
            </div>
          </div>
        </div>

        {/* 最后咨询时间 */}
        <div className="mt-4 pt-3 border-t border-border/50">
          <div className="flex items-center justify-between text-xs text-foreground-secondary">
            <span>最后咨询</span>
            <span className={patient.last_consultation_at ? 'font-medium text-foreground' : ''}>
              {lastConsultationText}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default PatientCard;

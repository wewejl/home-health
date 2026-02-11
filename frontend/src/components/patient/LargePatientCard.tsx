import React from 'react';
import { Calendar, Clock } from 'lucide-react';
import { type Patient } from '@/types/patient';

export interface LargePatientCardProps {
  patient: Patient;
  onClick: () => void;
  onQuickConsult?: (patient: Patient) => void;
}

// 获取头像颜色渐变类名（基于姓氏）
const getAvatarGradient = (name?: string): string => {
  const initial = name?.[0] || '?';
  const gradients = [
    'from-sky-500 to-sky-600',
    'from-purple-500 to-purple-600',
    'from-emerald-500 to-emerald-600',
    'from-violet-500 to-violet-600',
    'from-rose-500 to-rose-600',
    'from-amber-500 to-amber-600',
  ];
  const index = initial.charCodeAt(0) % gradients.length;
  return gradients[index];
};

// 获取性别徽章样式
const getGenderBadgeStyle = (gender?: string): string => {
  if (gender === '男') return 'bg-sky-100 text-sky-700';
  if (gender === '女') return 'bg-pink-100 text-pink-700';
  return 'bg-surface text-foreground-secondary';
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
  return `${Math.floor(diffDays / 7)}周前`;
};

// 格式化创建时间
const formatCreatedAt = (dateStr?: string): string => {
  if (!dateStr) return '未知';
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
};

// 获取完成率颜色
const getCompletionRateColor = (rate: number): string => {
  if (rate >= 0.8) return 'text-success';
  if (rate >= 0.5) return 'text-warning';
  return 'text-danger';
};

/**
 * LargePatientCard - 大型患者卡片组件
 *
 * 显示患者详细信息，包括头像、基本信息、医嘱完成率等
 */
export const LargePatientCard: React.FC<LargePatientCardProps> = ({
  patient,
  onClick,
  onQuickConsult,
}) => {
  const initial = patient.nickname?.[0] || '患';
  const avatarGradient = getAvatarGradient(patient.nickname);
  const genderBadgeStyle = getGenderBadgeStyle(patient.gender);
  const completionRateColor = getCompletionRateColor(patient.completion_rate);
  const completionPercent = Math.round(patient.completion_rate * 100);
  const lastConsultationText = formatLastConsultation(patient.last_consultation_at);
  const createdAtText = formatCreatedAt(patient.last_consultation_at);

  const handleQuickConsult = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onQuickConsult) {
      onQuickConsult(patient);
    }
  };

  return (
    <div
      className="card-hover bg-background rounded-2xl border border-border p-6 cursor-pointer dark:bg-gray-800 dark:border-gray-700"
      onClick={onClick}
    >
      {/* 顶部：头像 + 基本信息 */}
      <div className="flex gap-5 mb-5">
        <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${avatarGradient} flex items-center justify-center text-white text-2xl font-bold shadow-lg`}>
          {initial}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-xl font-bold text-foreground dark:text-gray-100">
              {patient.nickname || '未设置姓名'}
            </h3>
            {patient.gender && (
              <span className={`px-2 py-1 rounded-lg text-sm font-medium ${genderBadgeStyle}`}>
                {patient.gender}
              </span>
            )}
          </div>
          <div className="flex items-center gap-4 text-foreground-secondary dark:text-foreground-secondary text-sm">
            <span>{patient.age ? `${patient.age}岁` : '年龄未知'}</span>
            <span className="text-foreground-secondary/50">|</span>
            <span>{maskPhone(patient.phone)}</span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="text-right">
            <p className="text-2xl font-bold text-primary">{patient.active_orders_count}</p>
            <p className="text-xs text-foreground-secondary">进行中医嘱</p>
          </div>
        </div>
      </div>

      {/* 分隔线 */}
      <div className="h-px bg-surface dark:bg-gray-700 mb-4"></div>

      {/* 中部：详情信息 */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-foreground-secondary" />
          <div>
            <p className="text-xs text-foreground-secondary">最后咨询</p>
            <p className="text-sm font-medium text-foreground dark:text-gray-100">{lastConsultationText}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-foreground-secondary" />
          <div>
            <p className="text-xs text-foreground-secondary">创建时间</p>
            <p className="text-sm font-medium text-foreground dark:text-gray-100">{createdAtText}</p>
          </div>
        </div>
      </div>

      {/* 底部：完成率 */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-foreground">医嘱完成率</span>
          <span className={`text-2xl font-bold ${completionRateColor}`}>{completionPercent}%</span>
        </div>
        <div className="h-3 bg-surface dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="progress-bar h-full rounded-full transition-all duration-500"
            style={{ width: `${completionPercent}%` }}
          ></div>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-3 pt-4 border-t border-gray-100 dark:border-gray-700">
        <button
          className="flex-1 py-2.5 bg-primary text-white rounded-xl font-medium hover:bg-primary-hover transition-colors"
          onClick={(e) => {
            e.stopPropagation();
            onClick();
          }}
        >
          查看详情
        </button>
        <button
          className="flex-1 py-2.5 border border-border text-foreground rounded-xl font-medium hover:bg-surface transition-colors dark:border-gray-600 dark:text-foreground-secondary/50 dark:hover:bg-gray-700"
          onClick={handleQuickConsult}
        >
          快速咨询
        </button>
      </div>
    </div>
  );
};

export default LargePatientCard;

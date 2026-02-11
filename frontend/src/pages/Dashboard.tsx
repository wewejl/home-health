import React, { useEffect, useState } from 'react';
import {
  Users,
  MessageSquare,
  FileText,
  MessageCircle,
  Bot,
  BriefcaseMedical,
} from 'lucide-react';
import { statsApi } from '../api';
import { StatCardGrid } from '@/components/medical/stat-card';
import { PageHeader } from '@/components/medical/page-header';
import { LoadingSkeleton } from '@/components/medical/loading-skeleton';

interface OverviewStats {
  total_departments: number;
  total_doctors: number;
  active_ai_doctors: number;
  total_sessions: number;
  total_messages: number;
  today_sessions: number;
  today_messages: number;
  pending_documents: number;
  pending_feedbacks: number;
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<OverviewStats | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await statsApi.getOverview();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-32 bg-surface-alt rounded animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <LoadingSkeleton key={i} variant="card" />
          ))}
        </div>
      </div>
    );
  }

  // 第一行统计卡片
  const primaryStats = [
    {
      title: '科室总数',
      value: stats?.total_departments || 0,
      icon: <BriefcaseMedical className="h-5 w-5" />,
      variant: 'primary' as const,
    },
    {
      title: 'AI医生总数',
      value: `${stats?.active_ai_doctors || 0} / ${stats?.total_doctors || 0}`,
      icon: <Bot className="h-5 w-5" />,
      variant: 'success' as const,
    },
    {
      title: '总会话数',
      value: stats?.total_sessions || 0,
      icon: <Users className="h-5 w-5" />,
      variant: 'info' as const,
    },
    {
      title: '总消息数',
      value: stats?.total_messages || 0,
      icon: <MessageSquare className="h-5 w-5" />,
      variant: 'warning' as const,
    },
  ];

  // 第二行统计卡片 - 动态颜色根据数值决定
  const pendingDocsVariant: 'primary' | 'warning' = stats?.pending_documents ? 'warning' : 'primary';
  const pendingFeedbacksVariant: 'primary' | 'danger' = stats?.pending_feedbacks ? 'danger' : 'primary';

  const secondaryStats = [
    {
      title: '今日会话',
      value: stats?.today_sessions || 0,
      icon: <Users className="h-5 w-5" />,
      variant: 'primary' as const,
    },
    {
      title: '今日消息',
      value: stats?.today_messages || 0,
      icon: <MessageSquare className="h-5 w-5" />,
      variant: 'primary' as const,
    },
    {
      title: '待审核文档',
      value: stats?.pending_documents || 0,
      icon: <FileText className="h-5 w-5" />,
      variant: pendingDocsVariant,
    },
    {
      title: '待处理反馈',
      value: stats?.pending_feedbacks || 0,
      icon: <MessageCircle className="h-5 w-5" />,
      variant: pendingFeedbacksVariant,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="仪表盘"
        description="查看系统运营数据和关键指标"
      />

      {/* 主要统计卡片 */}
      <StatCardGrid items={primaryStats} cols={4} />

      {/* 次要统计卡片 */}
      <StatCardGrid items={secondaryStats} cols={4} />
    </div>
  );
};

export default Dashboard;

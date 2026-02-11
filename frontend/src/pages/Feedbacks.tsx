import React, { useEffect, useState } from 'react';
import { ThumbsUp, ThumbsDown, AlertTriangle, XOctagon, Loader2 } from 'lucide-react';
import { feedbacksApi } from '../api';
import { useToast } from '@/components/ui/toast';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

interface Feedback {
  id: number;
  session_id: string;
  message_id?: number;
  user_id: number;
  rating?: number;
  feedback_type?: string;
  feedback_text?: string;
  status: string;
  resolution_notes?: string;
  created_at: string;
}

interface FeedbackStats {
  total: number;
  by_status: { pending: number; reviewed: number; resolved: number };
  by_type: { helpful: number; unhelpful: number; unsafe: number; inaccurate: number };
}

const Feedbacks: React.FC = () => {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedFeedback, setSelectedFeedback] = useState<Feedback | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [formStatus, setFormStatus] = useState<string>('resolved');
  const [resolutionNotes, setResolutionNotes] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);

  const { success, error: showError } = useToast();

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [feedbacksRes, statsRes] = await Promise.all([
        feedbacksApi.list({ status: statusFilter || undefined }),
        feedbacksApi.getStats(),
      ]);
      setFeedbacks(feedbacksRes.data);
      setStats(statsRes.data);
    } catch (err) {
      showError('加载反馈列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleHandle = (feedback: Feedback) => {
    setSelectedFeedback(feedback);
    setFormStatus('resolved');
    setResolutionNotes('');
    setModalVisible(true);
  };

  const handleSubmit = async () => {
    if (!selectedFeedback) return;

    setSubmitting(true);
    try {
      await feedbacksApi.handle(selectedFeedback.id, {
        status: formStatus,
        resolution_notes: resolutionNotes || undefined,
      });
      success('处理成功');
      setModalVisible(false);
      fetchData();
    } catch (err) {
      showError('处理失败');
    } finally {
      setSubmitting(false);
    }
  };

  const getTypeBadge = (type: string | undefined) => {
    switch (type) {
      case 'helpful':
        return (
          <Badge variant="success" className="gap-1">
            <ThumbsUp className="h-3 w-3" />
            有帮助
          </Badge>
        );
      case 'unhelpful':
        return (
          <Badge variant="warning" className="gap-1">
            <ThumbsDown className="h-3 w-3" />
            无帮助
          </Badge>
        );
      case 'unsafe':
        return (
          <Badge variant="danger" className="gap-1">
            <AlertTriangle className="h-3 w-3" />
            不安全
          </Badge>
        );
      case 'inaccurate':
        return (
          <Badge variant="danger" className="gap-1">
            <XOctagon className="h-3 w-3" />
            不准确
          </Badge>
        );
      default:
        return <Badge variant="secondary">-</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="warning">待处理</Badge>;
      case 'reviewed':
        return <Badge variant="info">已审核</Badge>;
      case 'resolved':
        return <Badge variant="success">已解决</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold tracking-tight">反馈管理</h2>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card className="p-4">
            <div className="text-sm text-foreground-secondary">总反馈</div>
            <div className="text-2xl font-semibold mt-1">{stats.total}</div>
          </Card>
          <Card className="p-4">
            <div className="text-sm text-foreground-secondary">待处理</div>
            <div className="text-2xl font-semibold mt-1 text-warning">{stats.by_status.pending}</div>
          </Card>
          <Card className="p-4">
            <div className="text-sm text-foreground-secondary">有帮助</div>
            <div className="text-2xl font-semibold mt-1 text-success">{stats.by_type.helpful}</div>
          </Card>
          <Card className="p-4">
            <div className="text-sm text-foreground-secondary">无帮助</div>
            <div className="text-2xl font-semibold mt-1 text-warning">{stats.by_type.unhelpful}</div>
          </Card>
          <Card className="p-4">
            <div className="text-sm text-foreground-secondary">不安全</div>
            <div className="text-2xl font-semibold mt-1 text-danger">{stats.by_type.unsafe}</div>
          </Card>
          <Card className="p-4">
            <div className="text-sm text-foreground-secondary">不准确</div>
            <div className="text-2xl font-semibold mt-1 text-danger">{stats.by_type.inaccurate}</div>
          </Card>
        </div>
      )}

      {/* 筛选器 */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Label htmlFor="status-filter">状态筛选:</Label>
          <Select value={statusFilter || 'all'} onValueChange={(v) => setStatusFilter(v === 'all' ? '' : v)}>
            <SelectTrigger id="status-filter" className="w-[150px]">
              <SelectValue placeholder="全部状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="pending">待处理</SelectItem>
              <SelectItem value="reviewed">已审核</SelectItem>
              <SelectItem value="resolved">已解决</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* 表格 */}
      <div className="rounded-lg border border-border bg-surface">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-16">ID</TableHead>
              <TableHead className="w-40">会话ID</TableHead>
              <TableHead className="w-20">评分</TableHead>
              <TableHead className="w-24">类型</TableHead>
              <TableHead>反馈内容</TableHead>
              <TableHead className="w-24">状态</TableHead>
              <TableHead className="w-36">创建时间</TableHead>
              <TableHead className="w-24 text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-foreground-secondary">加载中...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : feedbacks.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center text-foreground-secondary">
                  暂无数据
                </TableCell>
              </TableRow>
            ) : (
              feedbacks.map((feedback) => (
                <TableRow key={feedback.id}>
                  <TableCell className="text-sm">{feedback.id}</TableCell>
                  <TableCell className="text-sm text-foreground-secondary truncate" title={feedback.session_id}>
                    {feedback.session_id.slice(0, 12)}...
                  </TableCell>
                  <TableCell className="text-sm">
                    {feedback.rating ? `${feedback.rating}/5` : '-'}
                  </TableCell>
                  <TableCell>{getTypeBadge(feedback.feedback_type)}</TableCell>
                  <TableCell className="text-sm text-foreground-secondary truncate max-w-xs">
                    {feedback.feedback_text || '-'}
                  </TableCell>
                  <TableCell>{getStatusBadge(feedback.status)}</TableCell>
                  <TableCell className="text-sm text-foreground-secondary">
                    {new Date(feedback.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">
                    {feedback.status === 'pending' ? (
                      <Button
                        size="sm"
                        onClick={() => handleHandle(feedback)}
                        className="h-8"
                      >
                        处理
                      </Button>
                    ) : (
                      <span className="text-sm text-foreground-secondary">已处理</span>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* 处理对话框 */}
      <Dialog open={modalVisible} onOpenChange={setModalVisible}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>处理反馈</DialogTitle>
          </DialogHeader>
          {selectedFeedback && (
            <div className="space-y-4 py-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-foreground-secondary">反馈类型:</span>
                  {getTypeBadge(selectedFeedback.feedback_type)}
                </div>
                <div>
                  <span className="text-sm text-foreground-secondary">反馈内容:</span>
                  <p className="text-sm mt-1">
                    {selectedFeedback.feedback_text || '无'}
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="status">
                  状态 <span className="text-danger">*</span>
                </Label>
                <Select value={formStatus} onValueChange={setFormStatus}>
                  <SelectTrigger id="status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="reviewed">已审核</SelectItem>
                    <SelectItem value="resolved">已解决</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">处理备注</Label>
                <Textarea
                  id="notes"
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="请输入处理备注..."
                  rows={3}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setModalVisible(false)}
              disabled={submitting}
            >
              取消
            </Button>
            <Button onClick={handleSubmit} disabled={submitting} className="gap-2">
              {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
              提交
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Feedbacks;

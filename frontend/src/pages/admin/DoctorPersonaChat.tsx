import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Send, RotateCcw, Check } from 'lucide-react';
import { personaChatApi } from '@/api';
import { useToast } from '@/components/ui/toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogAction, AlertDialogCancel } from '@/components/ui/alert-dialog';
import { cn } from '@/lib/utils';

// 采集阶段定义
const STAGES = [
  { key: 'greeting', label: '问候' },
  { key: 'specialty', label: '专科特点' },
  { key: 'style', label: '沟通风格' },
  { key: 'approach', label: '问诊思路' },
  { key: 'prescription', label: '处方习惯' },
  { key: 'advice', label: '生活建议' },
  { key: 'summary', label: '总结确认' },
];

interface ChatMessage {
  id: string;
  role: 'ai' | 'user';
  content: string;
  timestamp: Date;
}

interface DoctorInfo {
  doctor_id: number;
  name: string;
  persona_completed: boolean;
  has_persona_prompt: boolean;
  ai_model: string;
  ai_temperature: number;
}

const DoctorPersonaChat: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const doctorId = parseInt(id || '0');
  const { success, error } = useToast();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [currentStage, setCurrentStage] = useState<string>('');
  const [collectionState, setCollectionState] = useState<string>('');
  const [isComplete, setIsComplete] = useState(false);
  const [generatedPrompt, setGeneratedPrompt] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [doctorInfo, setDoctorInfo] = useState<DoctorInfo | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // 对话框状态
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [backDialogOpen, setBackDialogOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 防止用户刷新页面丢失进度
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges && !isComplete) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [hasUnsavedChanges, isComplete]);

  // 初始化
  useEffect(() => {
    const initChat = async () => {
      try {
        // 获取医生状态
        const statusRes = await personaChatApi.getStatus(doctorId);
        setDoctorInfo(statusRes.data);

        // 开始对话采集
        const startRes = await personaChatApi.start(doctorId);
        addAIMessage(startRes.data.message);
        setCollectionState(startRes.data.state);
        setCurrentStage(startRes.data.stage);
        setIsComplete(startRes.data.is_complete);
      } catch (err: any) {
        error(err.response?.data?.detail || '初始化失败');
      }
    };

    initChat();
  }, [doctorId, error]);

  // 添加 AI 消息
  const addAIMessage = (content: string) => {
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'ai',
      content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
  };

  // 添加用户消息
  const addUserMessage = (content: string) => {
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
    setHasUnsavedChanges(true);
  };

  // 发送消息
  const handleSend = async () => {
    if (!inputValue.trim() || loading || isComplete) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    addUserMessage(userMessage);
    setLoading(true);

    try {
      const res = await personaChatApi.sendMessage(doctorId, userMessage, collectionState);

      addAIMessage(res.data.message);
      setCollectionState(res.data.state);
      setCurrentStage(res.data.stage);
      setIsComplete(res.data.is_complete);

      if (res.data.is_complete) {
        setGeneratedPrompt(res.data.generated_prompt || '');
        setHasUnsavedChanges(false);
      }

      // 聚焦回输入框
      if (!res.data.is_complete) {
        setTimeout(() => inputRef.current?.focus(), 100);
      }
    } catch (err: any) {
      error(err.response?.data?.detail || '发送失败');
      // 恢复输入
      setInputValue(userMessage);
    } finally {
      setLoading(false);
    }
  };

  // 确认配置
  const handleConfirm = () => {
    success('医生分身配置已保存');
    navigate('/admin/doctors');
  };

  // 重新配置
  const handleReset = async () => {
    try {
      await personaChatApi.reset(doctorId);
      // 重置状态
      setMessages([]);
      setCollectionState('');
      setCurrentStage('');
      setIsComplete(false);
      setGeneratedPrompt('');
      setHasUnsavedChanges(false);

      // 重新开始
      const startRes = await personaChatApi.start(doctorId);
      addAIMessage(startRes.data.message);
      setCollectionState(startRes.data.state);
      setCurrentStage(startRes.data.stage);
      setResetDialogOpen(false);
    } catch (err: any) {
      error(err.response?.data?.detail || '重置失败');
    }
  };

  // 返回
  const handleBack = () => {
    if (hasUnsavedChanges && !isComplete) {
      setBackDialogOpen(true);
    } else {
      navigate('/admin/doctors');
    }
  };

  // 计算进度
  const getStageIndex = (stage: string) => {
    return STAGES.findIndex(s => s.key === stage);
  };

  const currentStageIndex = getStageIndex(currentStage);

  // 键盘事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="min-h-screen bg-background p-4 md:p-6">
      <div className="max-w-4xl mx-auto space-y-4">
        {/* 顶部导航 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={handleBack}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h2 className="text-xl font-semibold">
              {doctorInfo?.name} - 医生分身配置
            </h2>
          </div>
          <div className="flex items-center gap-2">
            {!isComplete && (
              <Badge variant="info">进度: {currentStageIndex + 1}/{STAGES.length}</Badge>
            )}
            {isComplete && (
              <Badge variant="success" className="gap-1">
                <Check className="h-3 w-3" />
                配置完成
              </Badge>
            )}
            {!isComplete && (
              <Button variant="outline" size="sm" onClick={() => setResetDialogOpen(true)} className="gap-1">
                <RotateCcw className="h-4 w-4" />
                重新开始
              </Button>
            )}
          </div>
        </div>

        {/* 阶段进度条 */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              {STAGES.map((stage, index) => (
                <React.Fragment key={stage.key}>
                  <div className="flex flex-col items-center">
                    <div
                      className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors",
                        index === currentStageIndex && "bg-primary text-primary-foreground ring-4 ring-primary/20",
                        index < currentStageIndex && "bg-success text-success-foreground",
                        index > currentStageIndex && "bg-secondary text-foreground-secondary"
                      )}
                      title={stage.label}
                    >
                      {index < currentStageIndex ? <Check className="h-4 w-4" /> : index + 1}
                    </div>
                    <span className={cn(
                      "text-xs mt-1",
                      index === currentStageIndex ? "text-primary font-medium" : "text-foreground-secondary"
                    )}>
                      {stage.label}
                    </span>
                  </div>
                  {index < STAGES.length - 1 && (
                    <div className={cn(
                      "flex-1 h-0.5 mx-2 transition-colors",
                      index < currentStageIndex ? "bg-success" : "bg-secondary"
                    )} />
                  )}
                </React.Fragment>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 聊天区域 */}
        <Card className="min-h-[400px]">
          <CardContent className="p-4">
            <div className="space-y-4 max-h-[500px] overflow-y-auto">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    "flex gap-3",
                    msg.role === 'user' ? "justify-end" : "justify-start"
                  )}
                >
                  {msg.role === 'ai' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-lg">
                      🤖
                    </div>
                  )}
                  <div className={cn(
                    "max-w-[70%] rounded-lg px-4 py-2",
                    msg.role === 'ai'
                      ? "bg-secondary text-foreground"
                      : "bg-primary text-primary-foreground"
                  )}>
                    <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                    <div className={cn(
                      "text-xs mt-1",
                      msg.role === 'ai' ? "text-foreground-secondary" : "text-primary-foreground/70"
                    )}>
                      {msg.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* 完成后显示生成的 Prompt */}
            {isComplete && generatedPrompt && (
              <div className="mt-6 space-y-4 p-4 rounded-lg bg-success-light/10 border border-success/20">
                <h3 className="font-semibold text-success">配置摘要</h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm font-medium mb-2">生成的 AI 人设 Prompt：</p>
                    <p className="text-sm text-foreground-secondary whitespace-pre-wrap bg-background/50 p-3 rounded-md">
                      {generatedPrompt}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleConfirm} className="gap-1">
                      <Check className="h-4 w-4" />
                      确认保存
                    </Button>
                    <Button variant="outline" onClick={() => setResetDialogOpen(true)}>
                      重新配置
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 输入区域 */}
        {!isComplete && (
          <Card>
            <CardContent className="p-4">
              <div className="flex gap-2">
                <Textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入您的回答...（Enter 发送，Shift + Enter 换行）"
                  rows={1}
                  disabled={loading}
                  className={cn(
                    "flex-1 resize-none",
                    "min-h-[38px] max-h-[120px] h-auto"
                  )}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = 'auto';
                    target.style.height = Math.min(target.scrollHeight, 120) + 'px';
                  }}
                />
                <Button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || loading}
                  className="gap-1"
                >
                  {loading ? (
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                  发送
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 重置确认对话框 */}
      <AlertDialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>重新配置</AlertDialogTitle>
            <AlertDialogDescription>
              确定要清空当前配置重新开始吗？
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleReset}>确定</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* 返回确认对话框 */}
      <AlertDialog open={backDialogOpen} onOpenChange={setBackDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>离开页面</AlertDialogTitle>
            <AlertDialogDescription>
              配置进度将丢失，确定离开吗？
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={() => navigate('/admin/doctors')}>
              确定
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default DoctorPersonaChat;

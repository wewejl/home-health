import { useState, useEffect } from 'react';
import { MessageSquare, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { doctorApi } from '@/api';
import dayjs from 'dayjs';

interface ConsultationMessage {
  id: number;
  sender: string;
  content: string;
  created_at?: string;
}

interface ConsultationSession {
  id: string;
  user_id: number;
  doctor_id?: number;
  agent_type: string;
  last_message?: string;
  created_at?: string;
  updated_at?: string;
  message_count: number;
}

interface ConsultationsTabProps {
  patientId: number;
}

const ConsultationsTab: React.FC<ConsultationsTabProps> = ({ patientId }) => {
  const [sessions, setSessions] = useState<ConsultationSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<ConsultationSession | null>(null);
  const [messages, setMessages] = useState<ConsultationMessage[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);

  useEffect(() => {
    fetchSessions();
  }, [patientId]);

  const fetchSessions = async () => {
    setSessionsLoading(true);
    try {
      const { data } = await doctorApi.getPatientConsultations(patientId, 20);
      setSessions(data);
    } catch (error) {
      console.error('Failed to fetch consultations:', error);
    } finally {
      setSessionsLoading(false);
    }
  };

  const fetchMessages = async (sessionId: string) => {
    setMessagesLoading(true);
    try {
      const { data } = await doctorApi.getConsultation(sessionId);
      setSelectedSession(data.session);
      setMessages(data.messages);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    } finally {
      setMessagesLoading(false);
    }
  };

  const getAgentTypeLabel = (agentType: string) => {
    const typeMap: Record<string, string> = {
      'general': '通用问诊',
      'derma': '皮肤科',
      'cardio': '心血管科',
      'endo': '内分泌科',
      'neuro': '神经科',
      'respiratory': '呼吸科',
      'digest': '消化科',
      'nephro': '肾病科',
    };
    return typeMap[agentType] || agentType;
  };

  return (
    <div className="p-4">
      <div className="flex flex-col md:flex-row gap-4 h-[600px]">
        {/* 会话列表 */}
        <Card className="w-full md:w-80 flex-shrink-0 overflow-hidden flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">对话记录</CardTitle>
          </CardHeader>
          <CardContent className="p-0 overflow-auto flex-1">
            {sessionsLoading ? (
              <div className="p-4 space-y-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="flex items-start gap-3 p-4 border rounded-lg">
                    <div className="h-5 w-5 bg-muted animate-pulse rounded mt-0.5" />
                    <div className="flex-1 min-w-0 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="h-4 w-20 bg-muted animate-pulse rounded" />
                        <div className="h-5 w-10 bg-muted animate-pulse rounded" />
                      </div>
                      <div className="h-4 w-full bg-muted animate-pulse rounded" />
                      <div className="flex items-center gap-1">
                        <div className="h-3 w-3 bg-muted animate-pulse rounded" />
                        <div className="h-3 w-24 bg-muted animate-pulse rounded" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center p-8 text-muted-foreground">
                <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>暂无对话记录</p>
              </div>
            ) : (
              <div className="divide-y">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    onClick={() => fetchMessages(session.id)}
                    className={`p-4 cursor-pointer transition-colors hover:bg-muted/50 ${
                      selectedSession?.id === session.id ? 'bg-muted' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <MessageSquare className="h-5 w-5 text-primary mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-sm">{getAgentTypeLabel(session.agent_type)}</span>
                          <Badge variant="secondary" className="text-xs">
                            {session.message_count} 条
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground truncate mb-1">
                          {session.last_message || '无消息'}
                        </p>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {dayjs(session.updated_at).format('YYYY-MM-DD HH:mm')}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 消息详情 */}
        <Card className="flex-1 min-w-0 overflow-hidden flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">
              {selectedSession ? '对话详情' : '请选择一个对话'}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 overflow-auto flex-1">
            {messagesLoading ? (
              <div className="space-y-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="p-3 rounded-lg border-l-4 bg-muted/30">
                    <div className="h-5 w-16 bg-muted animate-pulse rounded mb-2" />
                    <div className="space-y-2">
                      <div className="h-4 w-full bg-muted animate-pulse rounded" />
                      <div className="h-4 w-4/5 bg-muted animate-pulse rounded" />
                    </div>
                    <div className="h-3 w-32 bg-muted animate-pulse rounded mt-2" />
                  </div>
                ))}
              </div>
            ) : !selectedSession ? (
              <div className="text-center text-muted-foreground h-full flex items-center justify-center">
                <p>请从左侧选择一个对话查看详情</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* 会话信息 */}
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-sm font-medium">
                    {getAgentTypeLabel(selectedSession.agent_type)} - {selectedSession.message_count} 条消息
                  </p>
                </div>

                <Separator />

                {/* 消息列表 */}
                <div className="space-y-3">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`p-3 rounded-lg border-l-4 ${
                        message.sender === 'user'
                          ? 'border-success bg-success-light/30'
                          : 'border-info bg-info-light/30'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Badge
                          variant={message.sender === 'user' ? 'default' : 'secondary'}
                          className={message.sender === 'user' ? 'bg-success' : ''}
                        >
                          {message.sender === 'user' ? '患者' : 'AI助手'}
                        </Badge>
                      </div>
                      <p className="text-sm whitespace-pre-wrap mb-2">{message.content}</p>
                      <p className="text-xs text-muted-foreground">
                        {dayjs(message.created_at).format('YYYY-MM-DD HH:mm:ss')}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ConsultationsTab;

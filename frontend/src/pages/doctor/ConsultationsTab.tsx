import React, { useState, useEffect } from 'react';
import { List, Tag, Typography, Empty, Card, Collapse } from 'antd';
import { MessageOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

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
      const response = await fetch(`/api/doctor/patients/${patientId}/consultations?limit=20`);
      const data = await response.json();
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
      const response = await fetch(`/api/doctor/consultations/${sessionId}`);
      const data = await response.json();
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
    <div style={{ padding: 16 }}>
      <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 300px)' }}>
        {/* 会话列表 */}
        <Card
          title="对话记录"
          style={{ width: 350, overflow: 'auto' }}
          bodyStyle={{ padding: 0 }}
        >
          {sessionsLoading ? (
            <div style={{ padding: 16, textAlign: 'center' }}>加载中...</div>
          ) : sessions.length === 0 ? (
            <Empty description="暂无对话记录" style={{ padding: 32 }} />
          ) : (
            <List
              dataSource={sessions}
              renderItem={(session) => (
                <List.Item
                  key={session.id}
                  onClick={() => fetchMessages(session.id)}
                  style={{
                    padding: '12px 16px',
                    cursor: 'pointer',
                    background: selectedSession?.id === session.id ? '#e6f7ff' : undefined
                  }}
                >
                  <List.Item.Meta
                    avatar={<MessageOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                    title={
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Text strong>{getAgentTypeLabel(session.agent_type)}</Text>
                        <Tag color="blue">{session.message_count} 条消息</Tag>
                      </div>
                    }
                    description={
                      <div>
                        <Text ellipsis style={{ display: 'block' }}>
                          {session.last_message || '无消息'}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          <ClockCircleOutlined /> {dayjs(session.updated_at).format('YYYY-MM-DD HH:mm')}
                        </Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </Card>

        {/* 消息详情 */}
        <Card
          title={selectedSession ? '对话详情' : '请选择一个对话'}
          style={{ flex: 1, overflow: 'auto' }}
          bodyStyle={{ padding: 16 }}
        >
          {messagesLoading ? (
            <div style={{ textAlign: 'center' }}>加载中...</div>
          ) : !selectedSession ? (
            <Empty description="请从左侧选择一个对话查看详情" />
          ) : (
            <Collapse defaultActiveKey={['1']}>
              <Panel header={`${selectedSession.agent_type} - ${selectedSession.message_count} 条消息`} key="1">
                <List
                  dataSource={messages}
                  renderItem={(message) => (
                    <List.Item
                      key={message.id}
                      style={{
                        borderLeft: message.sender === 'user' ? '3px solid #52c41a' : '3px solid #1890ff',
                        paddingLeft: 12,
                        marginBottom: 8,
                        background: message.sender === 'user' ? '#f6ffed' : '#e6f7ff'
                      }}
                    >
                      <List.Item.Meta
                        title={
                          <Tag color={message.sender === 'user' ? 'green' : 'blue'}>
                            {message.sender === 'user' ? '患者' : 'AI助手'}
                          </Tag>
                        }
                        description={
                          <div>
                            <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                              {message.content}
                            </Paragraph>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {dayjs(message.created_at).format('YYYY-MM-DD HH:mm:ss')}
                            </Text>
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              </Panel>
            </Collapse>
          )}
        </Card>
      </div>
    </div>
  );
};

export default ConsultationsTab;

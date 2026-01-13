import React, { useState, useEffect, useRef } from 'react';
import { Card, Input, Button, Space, Tag, Spin, message, Typography, Avatar, Empty } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, ReloadOutlined } from '@ant-design/icons';
import { dermaAgentApi } from '../api';

// 添加光标闪烁动画
const cursorBlinkStyle = `
  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }
`;

// 注入样式
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.innerHTML = cursorBlinkStyle;
  document.head.appendChild(styleElement);
}

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  quick_options?: Array<{
    text: string;
    value: string;
    category: string;
  }>;
  isStreaming?: boolean;
}

interface ThinkingStep {
  type: string;
  content: string;
  timestamp: number;
}

const DermaChat: React.FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [quickOptions, setQuickOptions] = useState<Array<{text: string; value: string; category: string}>>([]);
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 初始化会话
  useEffect(() => {
    initSession();
  }, []);

  const initSession = async () => {
    try {
      setInitializing(true);
      const response = await dermaAgentApi.createSession();
      const data = response.data;
      setSessionId(data.session_id);
      
      // 添加初始助手消息
      if (data.message) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.message,
          timestamp: new Date().toISOString(),
          quick_options: data.quick_options || []
        };
        setMessages([assistantMessage]);
        
        // 设置快捷选项
        if (data.quick_options && data.quick_options.length > 0) {
          setQuickOptions(data.quick_options);
        }
      }
    } catch (error) {
      console.error('Failed to create session:', error);
      message.error('创建会话失败，请刷新页面重试');
    } finally {
      setInitializing(false);
    }
  };

  // 发送消息（SSE 流式）
  const handleSend = async (text?: string) => {
    const messageText = text || inputValue.trim();
    if (!messageText || !sessionId) return;

    // 添加用户消息到界面
    const userMessage: Message = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
    };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInputValue('');
    setQuickOptions([]);
    setLoading(true);
    setStreamingMessage('');
    setThinkingSteps([]);

    // 添加一个占位的助手消息用于流式更新
    const placeholderMessage: Message = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true
    };
    setMessages(prev => [...prev, placeholderMessage]);

    try {
      // 构建历史消息格式
      const history = updatedMessages.map(msg => ({
        role: msg.role,
        message: msg.content,
        timestamp: msg.timestamp
      }));
      
      // 使用 SSE 流式请求
      dermaAgentApi.sendMessageStream(sessionId, messageText, history, {
        onMeta: (data) => {
          console.log('Meta:', data);
        },
        onStep: (step) => {
          // 添加思考步骤
          console.log('[DermaChat] Received step:', step);
          setThinkingSteps(prev => {
            const newSteps = [...prev, {
              type: step.type,
              content: step.content,
              timestamp: Date.now()
            }];
            console.log('[DermaChat] Updated thinking steps:', newSteps);
            return newSteps;
          });
        },
        onChunk: (text) => {
          // 累积流式文本
          setStreamingMessage(prev => {
            const newContent = prev + text;
            // 同时更新消息列表中的流式消息
            setMessages(msgs => {
              const newMessages = [...msgs];
              if (newMessages.length > 0 && newMessages[newMessages.length - 1].isStreaming) {
                newMessages[newMessages.length - 1] = {
                  ...newMessages[newMessages.length - 1],
                  content: newContent
                };
              }
              return newMessages;
            });
            return newContent;
          });
        },
        onComplete: (data) => {
          // 更新最后一条消息为完整内容
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = {
              role: 'assistant',
              content: data.message || streamingMessage,
              timestamp: new Date().toISOString(),
              quick_options: data.quick_options || [],
              isStreaming: false
            };
            return newMessages;
          });
          
          // 更新快捷选项
          if (data.quick_options && data.quick_options.length > 0) {
            setQuickOptions(data.quick_options);
          } else {
            setQuickOptions([]);
          }
          
          setLoading(false);
          setStreamingMessage('');
          setThinkingSteps([]);
        },
        onError: (error) => {
          console.error('Stream error:', error);
          message.error('发送消息失败：' + error);
          // 移除占位消息
          setMessages(prev => prev.slice(0, -1));
          setLoading(false);
          setStreamingMessage('');
          setThinkingSteps([]);
        }
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      message.error('发送消息失败，请重试');
      // 移除占位消息
      setMessages(prev => prev.slice(0, -1));
      setLoading(false);
      setStreamingMessage('');
      setThinkingSteps([]);
    }
  };

  // 处理快捷选项点击
  const handleQuickOption = (value: string) => {
    handleSend(value);
  };

  // 重新开始
  const handleRestart = () => {
    setMessages([]);
    setQuickOptions([]);
    setSessionId(null);
    initSession();
  };

  // 处理回车发送
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (initializing) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" tip="正在初始化智能体..." />
      </div>
    );
  }

  return (
    <div style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* 头部 */}
      <Card 
        style={{ marginBottom: 16, borderRadius: 8 }}
        bodyStyle={{ padding: '16px 24px' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Avatar icon={<RobotOutlined />} size={40} style={{ backgroundColor: '#1890ff' }} />
            <div>
              <Title level={4} style={{ margin: 0 }}>皮肤科AI助手</Title>
              <Text type="secondary" style={{ fontSize: 12 }}>
                像朋友一样聊天，了解皮肤问题并给出专业建议
              </Text>
            </div>
          </Space>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={handleRestart}
            disabled={loading}
          >
            重新开始
          </Button>
        </div>
      </Card>

      {/* 消息区域 */}
      <Card 
        style={{ 
          flex: 1, 
          marginBottom: 16, 
          overflow: 'hidden',
          borderRadius: 8,
        }}
        bodyStyle={{ 
          height: '100%', 
          padding: 0,
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <div 
          style={{ 
            flex: 1, 
            overflowY: 'auto', 
            padding: 24,
            backgroundColor: '#f5f5f5'
          }}
        >
          {messages.length === 0 ? (
            <Empty 
              description="开始对话吧！描述一下你的皮肤问题"
              style={{ marginTop: 100 }}
            />
          ) : (
            <>
              {messages.map((msg, index) => (
                <div
                  key={index}
                  style={{
                    display: 'flex',
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    marginBottom: 16,
                  }}
                >
                  {msg.role === 'assistant' && (
                    <Avatar 
                      icon={<RobotOutlined />} 
                      style={{ backgroundColor: '#1890ff', marginRight: 12 }} 
                    />
                  )}
                  <div
                    style={{
                      maxWidth: '70%',
                      padding: '12px 16px',
                      borderRadius: 12,
                      backgroundColor: msg.role === 'user' ? '#1890ff' : '#fff',
                      color: msg.role === 'user' ? '#fff' : '#000',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {msg.content}
                    {/* 流式消息显示光标 */}
                    {msg.isStreaming && (
                      <span style={{ animation: 'blink 1s infinite', marginLeft: 2 }}>▊</span>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <Avatar 
                      icon={<UserOutlined />} 
                      style={{ backgroundColor: '#87d068', marginLeft: 12 }} 
                    />
                  )}
                </div>
              ))}
              {loading && (
                <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 16 }}>
                  <Avatar 
                    icon={<RobotOutlined />} 
                    style={{ backgroundColor: '#1890ff', marginRight: 12 }} 
                  />
                  <div style={{ maxWidth: '70%' }}>
                    {/* 思考步骤展示 */}
                    {thinkingSteps.length > 0 && (
                      <div
                        style={{
                          padding: '8px 12px',
                          borderRadius: 8,
                          backgroundColor: '#f0f5ff',
                          marginBottom: 8,
                          fontSize: 12,
                          color: '#1890ff',
                        }}
                      >
                        {thinkingSteps.map((step, idx) => {
                          let icon = '⚙️';
                          let text = step.content;
                          
                          if (step.type === 'thinking') {
                            icon = '🤔';
                            text = '正在分析您的症状...';
                          } else if (step.type === 'tool') {
                            icon = '🔧';
                            text = step.content || '正在查询知识库...';
                          } else if (step.type === 'reasoning') {
                            icon = '💡';
                            text = step.content || '正在推理分析...';
                          } else if (step.type === 'step') {
                            icon = '⚙️';
                            text = step.content || '处理中...';
                          }
                          
                          return (
                            <div key={idx} style={{ marginBottom: 4, display: 'flex', alignItems: 'center' }}>
                              <span style={{ marginRight: 4 }}>{icon}</span>
                              <span>{text}</span>
                            </div>
                          );
                        })}
                      </div>
                    )}
                    {/* 无内容时显示加载 */}
                    {!streamingMessage && (
                      <div
                        style={{
                          padding: '12px 16px',
                          borderRadius: 12,
                          backgroundColor: '#fff',
                          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                        }}
                      >
                        <Spin size="small" />
                        <Text style={{ marginLeft: 8 }}>正在思考...</Text>
                      </div>
                    )}
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* 快捷选项 */}
        {quickOptions.length > 0 && !loading && (
          <div style={{ 
            padding: '12px 24px', 
            borderTop: '1px solid #f0f0f0',
            backgroundColor: '#fff'
          }}>
            <Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
              快捷回复：
            </Text>
            <Space wrap>
              {quickOptions.map((option, index) => (
                <Tag
                  key={index}
                  color="blue"
                  style={{ 
                    cursor: 'pointer', 
                    padding: '4px 12px',
                    fontSize: 13,
                    border: '1px solid #1890ff'
                  }}
                  onClick={() => handleQuickOption(option.value)}
                >
                  {option.text}
                </Tag>
              ))}
            </Space>
          </div>
        )}
      </Card>

      {/* 输入区域 */}
      <Card 
        style={{ borderRadius: 8 }}
        bodyStyle={{ padding: 16 }}
      >
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="描述你的皮肤问题，比如：手上起了红疹，很痒..."
            autoSize={{ minRows: 2, maxRows: 4 }}
            disabled={loading}
            style={{ borderRadius: '8px 0 0 8px' }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={() => handleSend()}
            loading={loading}
            disabled={!inputValue.trim() || loading}
            style={{ 
              height: 'auto',
              borderRadius: '0 8px 8px 0',
              minHeight: 64
            }}
          >
            发送
          </Button>
        </Space.Compact>
        <Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
          💡 提示：按 Enter 发送，Shift + Enter 换行
        </Text>
      </Card>
    </div>
  );
};

export default DermaChat;

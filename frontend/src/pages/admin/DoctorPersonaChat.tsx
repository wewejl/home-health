import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Input, message, Card, Space, Modal, Tag, Typography } from 'antd';
import { ArrowLeftOutlined, SendOutlined, ReloadOutlined, CheckOutlined } from '@ant-design/icons';
import { personaChatApi } from '../../api';
import './DoctorPersonaChat.css';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

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

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [currentStage, setCurrentStage] = useState<string>('');
  const [collectionState, setCollectionState] = useState<string>('');
  const [isComplete, setIsComplete] = useState(false);
  const [generatedPrompt, setGeneratedPrompt] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [doctorInfo, setDoctorInfo] = useState<DoctorInfo | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

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
      } catch (error: any) {
        message.error(error.response?.data?.detail || '初始化失败');
      }
    };

    initChat();
  }, [doctorId]);

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
    } catch (error: any) {
      message.error(error.response?.data?.detail || '发送失败');
      // 恢复输入
      setInputValue(userMessage);
    } finally {
      setLoading(false);
    }
  };

  // 确认配置
  const handleConfirm = () => {
    message.success('医生分身配置已保存');
    navigate('/admin/doctors');
  };

  // 重新配置
  const handleReset = async () => {
    Modal.confirm({
      title: '重新配置',
      content: '确定要清空当前配置重新开始吗？',
      onOk: async () => {
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
        } catch (error: any) {
          message.error(error.response?.data?.detail || '重置失败');
        }
      },
    });
  };

  // 返回确认
  const handleBack = () => {
    if (hasUnsavedChanges && !isComplete) {
      Modal.confirm({
        title: '离开页面',
        content: '配置进度将丢失，确定离开吗？',
        onOk: () => navigate('/admin/doctors'),
      });
    } else {
      navigate('/admin/doctors');
    }
  };

  // 计算进度
  const getStageIndex = (stage: string) => {
    return STAGES.findIndex(s => s.key === stage);
  };

  const currentStageIndex = getStageIndex(currentStage);

  // 检测修改指令
  const detectModifyCommand = (input: string): string | null => {
    const lowerInput = input.toLowerCase().trim();

    for (const stage of STAGES) {
      if (lowerInput.includes(`修改${stage.label}`) || lowerInput.includes(`重新${stage.label}`)) {
        return stage.key;
      }
    }

    return null;
  };

  // 键盘事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="persona-chat-container">
      {/* 顶部导航 */}
      <div className="persona-header">
        <div className="persona-header-left">
          <Button icon={<ArrowLeftOutlined />} onClick={handleBack}>
            返回
          </Button>
          <Title level={4} style={{ margin: '0 16px' }}>
            {doctorInfo?.name} - 医生分身配置
          </Title>
        </div>
        <Space>
          {!isComplete && (
            <Tag color="blue">进度: {currentStageIndex + 1}/{STAGES.length}</Tag>
          )}
          {isComplete && (
            <Tag color="success" icon={<CheckOutlined />}>配置完成</Tag>
          )}
          {!isComplete && (
            <Button icon={<ReloadOutlined />} onClick={handleReset} size="small">
              重新开始
            </Button>
          )}
        </Space>
      </div>

      {/* 阶段进度条 */}
      <div className="stage-progress">
        {STAGES.map((stage, index) => (
          <React.Fragment key={stage.key}>
            <div
              className={`stage-dot ${index === currentStageIndex ? 'active' : ''} ${index < currentStageIndex ? 'completed' : ''}`}
              title={stage.label}
            >
              {index < currentStageIndex ? <CheckOutlined /> : index + 1}
            </div>
            {index < STAGES.length - 1 && (
              <div className={`stage-line ${index < currentStageIndex ? 'completed' : ''}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* 聊天区域 */}
      <div className="chat-container">
        <div className="messages-list">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-item ${msg.role}`}>
              <div className={`message-bubble ${msg.role}`}>
                {msg.role === 'ai' && <div className="ai-avatar">🤖</div>}
                <div className="message-content">
                  <div className="message-text">{msg.content}</div>
                  <div className="message-time">
                    {msg.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* 完成后显示生成的 Prompt */}
        {isComplete && generatedPrompt && (
          <Card className="summary-card" title="配置摘要" bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>生成的 AI 人设 Prompt：</Text>
                <Paragraph className="generated-prompt">
                  {generatedPrompt}
                </Paragraph>
              </div>
              <Space>
                <Button type="primary" icon={<CheckOutlined />} onClick={handleConfirm}>
                  确认保存
                </Button>
                <Button onClick={handleReset}>
                  重新配置
                </Button>
              </Space>
            </Space>
          </Card>
        )}
      </div>

      {/* 输入区域 */}
      {!isComplete && (
        <div className="input-area">
          <TextArea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入您的回答...（Enter 发送，Shift + Enter 换行）"
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={loading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={loading}
            disabled={!inputValue.trim()}
          >
            发送
          </Button>
        </div>
      )}
    </div>
  );
};

export default DoctorPersonaChat;

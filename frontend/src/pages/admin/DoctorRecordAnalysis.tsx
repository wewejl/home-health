import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Button, Card, Upload, message, Typography, Space, Steps,
  Row, Col, Tag, Spin, Alert
} from 'antd';
import {
  ArrowLeftOutlined, UploadOutlined, CheckOutlined, LoadingOutlined,
  FileTextOutlined, ExperimentOutlined, FormOutlined
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';
import { doctorsApi } from '../../api';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;

// 步骤定义
const STEPS = [
  { title: '上传病历', icon: <UploadOutlined /> },
  { title: '分析中', icon: <ExperimentOutlined /> },
  { title: '确认结果', icon: <FormOutlined /> },
];

interface FeatureCard {
  title: string;
  content: string;
  icon: React.ReactNode;
}

const FeatureCard: React.FC<FeatureCard> = ({ title, content, icon }) => (
  <Card className="feature-card" size="small">
    <Space direction="vertical" style={{ width: '100%' }}>
      <Space>
        {icon}
        <Text strong>{title}</Text>
      </Space>
      <Paragraph style={{ margin: 0, color: '#666' }}>{content}</Paragraph>
    </Space>
  </Card>
);

const DoctorRecordAnalysis: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const doctorId = parseInt(id || '0');

  const [currentStep, setCurrentStep] = useState(0);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // 上传配置
  const uploadProps: UploadProps = {
    name: 'files',
    multiple: true,
    fileList,
    accept: '.pdf,.jpg,.jpeg,.png,.webp,.txt',
    beforeUpload: (file) => {
      // 验证文件大小
      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('文件大小不能超过 10MB');
        return Upload.LIST_IGNORE;
      }

      // 验证文件数量
      if (fileList.length >= 5) {
        message.error('最多支持上传 5 个文件');
        return Upload.LIST_IGNORE;
      }

      return false; // 阻止自动上传
    },
    onChange: ({ fileList: newFileList }) => {
      setFileList(newFileList);
    },
    onRemove: (file) => {
      setFileList(fileList.filter((item) => item.uid !== file.uid));
    },
  };

  // 开始分析
  const handleAnalyze = async () => {
    if (fileList.length === 0) {
      message.warning('请先上传病历文件');
      return;
    }

    setAnalyzing(true);
    setError(null);
    setCurrentStep(1);

    try {
      // 准备表单数据
      const formData = new FormData();
      fileList.forEach((file) => {
        if (file.originFileObj) {
          formData.append('files', file.originFileObj);
        }
      });

      // 调用分析 API
      const response = await doctorsApi.analyzeRecords(doctorId, formData);
      const result = response.data;

      setAnalysisResult(result);
      setCurrentStep(2);
      message.success('病历分析完成');
    } catch (err: any) {
      setError(err.response?.data?.detail || '分析失败，请重试');
      setCurrentStep(0);
    } finally {
      setAnalyzing(false);
    }
  };

  // 确认保存
  const handleConfirm = async () => {
    try {
      // 调用保存 API
      await doctorsApi.saveAnalysisResult(doctorId, analysisResult.generated_prompt);

      message.success('病历分析结果已保存到医生配置');
      navigate('/admin/doctors');
    } catch (err: any) {
      message.error(err.response?.data?.detail || '保存失败');
    }
  };

  // 重新上传
  const handleReset = () => {
    setFileList([]);
    setCurrentStep(0);
    setAnalysisResult(null);
    setError(null);
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* 顶部导航 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/admin/doctors')}>
          返回医生列表
        </Button>
        <Title level={4} style={{ margin: 0 }}>
          病历分析 - 医生 #{doctorId}
        </Title>
        <div style={{ width: '120px' }} />
      </div>

      {/* 步骤指示器 */}
      <Card style={{ marginBottom: '24px' }}>
        <Steps current={currentStep} items={STEPS} />
      </Card>

      {/* 步骤 1: 上传病历 */}
      {currentStep === 0 && (
        <Card title="上传病历文件" bordered={false}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              message="支持格式：PDF、JPG、PNG、TXT"
              description="最多上传 5 个文件，每个文件不超过 10MB。系统将从病历中提取医生的诊疗特征。"
              type="info"
              showIcon
            />

            <Dragger {...uploadProps} style={{ padding: '40px' }}>
              <p className="ant-upload-drag-icon">
                <FileTextOutlined style={{ fontSize: '48px', color: '#5C44FF' }} />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">支持 PDF、图片、文本格式的病历文件</p>
            </Dragger>

            {fileList.length > 0 && (
              <div style={{ marginTop: '16px' }}>
                <Text strong>已选择 {fileList.length} 个文件：</Text>
                {fileList.map((file) => (
                  <Tag key={file.uid} style={{ margin: '4px' }}>
                    {file.name} ({((file.size || 0) / 1024).toFixed(0)} KB)
                  </Tag>
                ))}
              </div>
            )}

            <Button
              type="primary"
              size="large"
              icon={<ExperimentOutlined />}
              onClick={handleAnalyze}
              disabled={fileList.length === 0}
              block
            >
              开始分析
            </Button>
          </Space>
        </Card>
      )}

      {/* 步骤 1: 分析中 */}
      {currentStep === 1 && analyzing && (
        <Card style={{ textAlign: 'center', padding: '60px' }} bordered={false}>
          <Spin size="large" indicator={<LoadingOutlined style={{ fontSize: '48px' }} spin />} />
          <Title level={4} style={{ marginTop: '24px' }}>
            正在分析病历...
          </Title>
          <Paragraph type="secondary">
            这可能需要几秒钟，请稍候
          </Paragraph>
        </Card>
      )}

      {/* 步骤 2: 确认结果 */}
      {currentStep === 2 && analysisResult && (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 成功提示 */}
          <Alert
            message="病历分析完成"
            description={`成功解析 ${analysisResult.parsed_files.length} 个文件，提取了以下诊疗特征`}
            type="success"
            showIcon
          />

          {/* 提取的特征 */}
          <Card title="提取的诊疗特征" bordered={false}>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={12}>
                <FeatureCard
                  title="诊断思路"
                  content={analysisResult.features.diagnostic_style}
                  icon={<ExperimentOutlined />}
                />
              </Col>
              <Col xs={24} sm={12} md={12}>
                <FeatureCard
                  title="处方习惯"
                  content={analysisResult.features.prescription_habits}
                  icon={<FileTextOutlined />}
                />
              </Col>
              <Col xs={24} sm={12} md={12}>
                <FeatureCard
                  title="随访习惯"
                  content={analysisResult.features.follow_up_pattern}
                  icon={<FormOutlined />}
                />
              </Col>
              <Col xs={24} sm={12} md={12}>
                <FeatureCard
                  title="沟通风格"
                  content={analysisResult.features.communication_style}
                  icon={<ExperimentOutlined />}
                />
              </Col>
            </Row>
          </Card>

          {/* 生成的 Prompt */}
          <Card title="生成的 AI 人设 Prompt" bordered={false}>
            <div
              style={{
                background: '#f9f9f9',
                padding: '16px',
                borderRadius: '8px',
                borderLeft: '4px solid #5C44FF',
                whiteSpace: 'pre-wrap',
                maxHeight: '300px',
                overflowY: 'auto'
              }}
            >
              {analysisResult.generated_prompt}
            </div>
          </Card>

          {/* 操作按钮 */}
          <Card bordered={false}>
            <Space size="middle">
              <Button
                type="primary"
                size="large"
                icon={<CheckOutlined />}
                onClick={handleConfirm}
              >
                确认并保存
              </Button>
              <Button
                size="large"
                onClick={handleReset}
              >
                重新上传
              </Button>
              <Button
                size="large"
                onClick={() => navigate('/admin/doctors')}
              >
                取消
              </Button>
            </Space>
          </Card>
        </Space>
      )}

      {/* 错误提示 */}
      {error && (
        <Alert
          message="分析失败"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={handleReset}>
              重试
            </Button>
          }
        />
      )}
    </div>
  );
};

export default DoctorRecordAnalysis;

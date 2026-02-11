import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Upload, Check, FileText, FlaskConical,
  ClipboardList, Stethoscope
} from 'lucide-react';
import { doctorsApi } from '@/api';
import { useToast } from '@/components/ui/toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { FeatureCard } from '@/components/medical/FeatureCard';
import { cn } from '@/lib/utils';

// 步骤定义
const STEPS = [
  { title: '上传病历', icon: Upload },
  { title: '分析中', icon: FlaskConical },
  { title: '确认结果', icon: ClipboardList },
];

interface FileItem {
  uid: string;
  name: string;
  size: number;
  file?: File;
}

const DoctorRecordAnalysis: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const doctorId = parseInt(id || '0');
  const { success, error, warning } = useToast();

  const [currentStep, setCurrentStep] = useState(0);
  const [fileList, setFileList] = useState<FileItem[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // 文件选择处理
  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;

    const newFiles: FileItem[] = [];
    const maxFiles = 5;
    const maxSize = 10 * 1024 * 1024; // 10MB

    for (let i = 0; i < files.length && fileList.length + newFiles.length < maxFiles; i++) {
      const file = files[i];

      // 验证文件类型
      const validTypes = ['.pdf', '.jpg', '.jpeg', '.png', '.webp', '.txt'];
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!validTypes.includes(ext)) {
        warning(`不支持的文件类型: ${file.name}`);
        continue;
      }

      // 验证文件大小
      if (file.size > maxSize) {
        warning(`文件大小超过 10MB: ${file.name}`);
        continue;
      }

      newFiles.push({
        uid: Date.now().toString() + i,
        name: file.name,
        size: file.size,
        file,
      });
    }

    setFileList(prev => [...prev, ...newFiles]);
  };

  // 拖拽处理
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  // 移除文件
  const handleRemove = (uid: string) => {
    setFileList(prev => prev.filter(item => item.uid !== uid));
  };

  // 开始分析
  const handleAnalyze = async () => {
    if (fileList.length === 0) {
      warning('请先上传病历文件');
      return;
    }

    setAnalyzing(true);
    setErrorMessage(null);
    setCurrentStep(1);

    try {
      // 准备表单数据
      const formData = new FormData();
      fileList.forEach((item) => {
        if (item.file) {
          formData.append('files', item.file);
        }
      });

      // 调用分析 API
      const response = await doctorsApi.analyzeRecords(doctorId, formData);
      const result = response.data;

      setAnalysisResult(result);
      setCurrentStep(2);
      success('病历分析完成');
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || '分析失败，请重试');
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

      success('病历分析结果已保存到医生配置');
      navigate('/admin/doctors');
    } catch (err: any) {
      error(err.response?.data?.detail || '保存失败');
    }
  };

  // 重新上传
  const handleReset = () => {
    setFileList([]);
    setCurrentStep(0);
    setAnalysisResult(null);
    setErrorMessage(null);
  };

  // 计算进度百分比
  const getProgress = () => {
    switch (currentStep) {
      case 0: return 0;
      case 1: return 50;
      case 2: return 100;
      default: return 0;
    }
  };

  return (
    <div className="min-h-screen bg-background p-4 md:p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* 顶部导航 */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => navigate('/admin/doctors')} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            返回医生列表
          </Button>
          <h1 className="text-xl font-semibold">
            病历分析 - 医生 #{doctorId}
          </h1>
          <div className="w-24" />
        </div>

        {/* 步骤指示器 */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              {STEPS.map((step, index) => {
                const Icon = step.icon;
                const isActive = index === currentStep;
                const isCompleted = index < currentStep;

                return (
                  <React.Fragment key={step.title}>
                    <div className="flex flex-col items-center">
                      <div
                        className={cn(
                          "w-10 h-10 rounded-full flex items-center justify-center transition-all",
                          isActive && "bg-primary text-primary-foreground ring-4 ring-primary/20",
                          isCompleted && "bg-success text-success-foreground",
                          !isActive && !isCompleted && "bg-secondary text-foreground-secondary"
                        )}
                      >
                        {isCompleted ? (
                          <Check className="h-5 w-5" />
                        ) : (
                          <Icon className="h-5 w-5" />
                        )}
                      </div>
                      <span className={cn(
                        "text-xs mt-2 text-center",
                        isActive ? "text-primary font-medium" : "text-foreground-secondary"
                      )}>
                        {step.title}
                      </span>
                    </div>
                    {index < STEPS.length - 1 && (
                      <div className="flex-1 h-1 mx-4 max-w-[100px]">
                        <Progress value={isCompleted ? 100 : 0} className="h-full" />
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
            <div className="mt-4">
              <Progress value={getProgress()} className="h-2" />
            </div>
          </CardContent>
        </Card>

        {/* 步骤 0: 上传病历 */}
        {currentStep === 0 && (
          <Card>
            <CardHeader>
              <CardTitle>上传病历文件</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* 提示信息 */}
              <div className="flex items-start gap-3 p-4 rounded-lg bg-info-light/20 border border-info/30">
                <div className="text-info mt-0.5">
                  <FileText className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-info">支持格式：PDF、JPG、PNG、TXT</p>
                  <p className="text-sm text-foreground-secondary mt-1">
                    最多上传 5 个文件，每个文件不超过 10MB。系统将从病历中提取医生的诊疗特征。
                  </p>
                </div>
              </div>

              {/* 拖拽上传区域 */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={cn(
                  "border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
                  isDragging
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50 hover:bg-secondary/50"
                )}
              >
                <div className="flex flex-col items-center gap-4">
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                    <FileText className="h-8 w-8 text-primary" />
                  </div>
                  <div>
                    <p className="text-lg font-medium">点击或拖拽文件到此区域上传</p>
                    <p className="text-sm text-foreground-secondary mt-1">
                      支持 PDF、图片、文本格式的病历文件
                    </p>
                  </div>
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.jpg,.jpeg,.png,.webp,.txt"
                    onChange={(e) => handleFileSelect(e.target.files)}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload">
                    <Button variant="outline" className="cursor-pointer" asChild>
                      <span>选择文件</span>
                    </Button>
                  </label>
                </div>
              </div>

              {/* 已选文件列表 */}
              {fileList.length > 0 && (
                <div className="space-y-3">
                  <p className="text-sm font-medium">已选择 {fileList.length} 个文件：</p>
                  <div className="flex flex-wrap gap-2">
                    {fileList.map((file) => (
                      <Badge
                        key={file.uid}
                        variant="secondary"
                        className="gap-1 pr-2 pl-3 py-1.5"
                      >
                        <span>{file.name}</span>
                        <span className="text-foreground-secondary">
                          ({(file.size / 1024).toFixed(0)} KB)
                        </span>
                        <button
                          onClick={() => handleRemove(file.uid)}
                          className="ml-1 hover:text-danger transition-colors"
                        >
                          <Check className="h-3 w-3 rotate-45" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* 开始分析按钮 */}
              <Button
                size="lg"
                onClick={handleAnalyze}
                disabled={fileList.length === 0}
                className="w-full gap-2"
              >
                <FlaskConical className="h-5 w-5" />
                开始分析
              </Button>
            </CardContent>
          </Card>
        )}

        {/* 步骤 1: 分析中 */}
        {currentStep === 1 && analyzing && (
          <Card>
            <CardContent className="py-16">
              <div className="flex flex-col items-center text-center space-y-6">
                <div className="relative">
                  <div className="w-16 h-16 border-4 border-primary/20 rounded-full" />
                  <div className="absolute inset-0 w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                  <Stethoscope className="absolute inset-0 m-auto h-6 w-6 text-primary" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">正在分析病历...</h3>
                  <p className="text-foreground-secondary">
                    这可能需要几秒钟，请稍候
                  </p>
                </div>
                <Progress value={50} className="w-64" />
              </div>
            </CardContent>
          </Card>
        )}

        {/* 步骤 2: 确认结果 */}
        {currentStep === 2 && analysisResult && (
          <div className="space-y-6">
            {/* 成功提示 */}
            <Card className="border-success/50 bg-success-light/10">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-success mt-0.5" />
                  <div>
                    <p className="font-medium text-success">病历分析完成</p>
                    <p className="text-sm text-foreground-secondary mt-1">
                      成功解析 {analysisResult.parsed_files?.length || 0} 个文件，提取了以下诊疗特征
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 提取的特征 */}
            <Card>
              <CardHeader>
                <CardTitle>提取的诊疗特征</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FeatureCard
                    title="诊断思路"
                    content={analysisResult.features?.diagnostic_style || '暂无'}
                    icon={<FlaskConical className="h-5 w-5" />}
                  />
                  <FeatureCard
                    title="处方习惯"
                    content={analysisResult.features?.prescription_habits || '暂无'}
                    icon={<ClipboardList className="h-5 w-5" />}
                  />
                  <FeatureCard
                    title="随访习惯"
                    content={analysisResult.features?.follow_up_pattern || '暂无'}
                    icon={<Stethoscope className="h-5 w-5" />}
                  />
                  <FeatureCard
                    title="沟通风格"
                    content={analysisResult.features?.communication_style || '暂无'}
                    icon={<FileText className="h-5 w-5" />}
                  />
                </div>
              </CardContent>
            </Card>

            {/* 生成的 Prompt */}
            <Card>
              <CardHeader>
                <CardTitle>生成的 AI 人设 Prompt</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="p-4 rounded-lg bg-secondary border-l-4 border-primary">
                  <pre className="text-sm whitespace-pre-wrap font-sans text-foreground-secondary">
                    {analysisResult.generated_prompt}
                  </pre>
                </div>
              </CardContent>
            </Card>

            {/* 操作按钮 */}
            <Card>
              <CardContent className="p-6">
                <div className="flex flex-wrap gap-3">
                  <Button size="lg" onClick={handleConfirm} className="gap-2">
                    <Check className="h-4 w-4" />
                    确认并保存
                  </Button>
                  <Button size="lg" variant="outline" onClick={handleReset}>
                    重新上传
                  </Button>
                  <Button
                    size="lg"
                    variant="ghost"
                    onClick={() => navigate('/admin/doctors')}
                  >
                    取消
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* 错误提示 */}
        {errorMessage && (
          <Card className="border-danger/50 bg-danger-light/10">
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <FlaskConical className="h-5 w-5 text-danger mt-0.5" />
                  <div>
                    <p className="font-medium text-danger">分析失败</p>
                    <p className="text-sm text-foreground-secondary mt-1">{errorMessage}</p>
                  </div>
                </div>
                <Button size="sm" variant="outline" onClick={handleReset}>
                  重试
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default DoctorRecordAnalysis;

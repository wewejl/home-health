import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus, Edit, Trash2, Play, MessageSquare, FileText,
  Loader2, Stethoscope, Brain, Zap
} from 'lucide-react';
import { doctorsApi, departmentsApi, knowledgeBasesApi } from '../api';

// shadcn/ui components
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableHeader, TableBody,
  TableHead, TableRow, TableCell
} from '@/components/ui/table';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogFooter
} from '@/components/ui/dialog';
import {
  Sheet, SheetContent, SheetHeader, SheetTitle
} from '@/components/ui/sheet';
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader,
  AlertDialogTitle, AlertDialogDescription, AlertDialogFooter,
  AlertDialogAction, AlertDialogCancel
} from '@/components/ui/alert-dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem
} from '@/components/ui/select';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { InputNumber } from '@/components/ui/input-number';
import { useToast } from '@/components/ui/toast';

interface Doctor {
  id: number;
  name: string;
  title: string;
  department_id: number;
  hospital: string;
  specialty: string;
  is_ai: boolean;
  is_active: boolean;
  ai_persona_prompt?: string;
  ai_model: string;
  ai_temperature: number;
  ai_max_tokens: number;
  knowledge_base_id?: string;
}

interface FormData {
  name?: string;
  title?: string;
  department_id?: number;
  hospital?: string;
  specialty?: string;
  rating?: number;
  is_ai?: boolean;
  is_active?: boolean;
  ai_model?: string;
  ai_temperature?: number;
  ai_max_tokens?: number;
  knowledge_base_id?: string;
  ai_persona_prompt?: string;
}

const Doctors: React.FC = () => {
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingDoctor, setEditingDoctor] = useState<Doctor | null>(null);

  // Drawer state
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [testDoctor, setTestDoctor] = useState<Doctor | null>(null);
  const [testMessage, setTestMessage] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [testLoading, setTestLoading] = useState(false);

  // Delete confirmation
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [doctorToDelete, setDoctorToDelete] = useState<number | null>(null);

  // Form state
  const [formData, setFormData] = useState<FormData>({
    is_ai: true,
    is_active: true,
    ai_model: 'qwen-plus',
    ai_temperature: 0.7,
    ai_max_tokens: 500,
    rating: 5.0,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [doctorsRes, deptsRes, kbsRes] = await Promise.all([
        doctorsApi.list(),
        departmentsApi.list(),
        knowledgeBasesApi.list(),
      ]);
      setDoctors(doctorsRes.data);
      setDepartments(deptsRes.data);
      setKnowledgeBases(kbsRes.data);
    } catch (err) {
      error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingDoctor(null);
    setFormData({
      is_ai: true,
      is_active: true,
      ai_model: 'qwen-plus',
      ai_temperature: 0.7,
      ai_max_tokens: 500,
      rating: 5.0,
    });
    setModalOpen(true);
  };

  const handleEdit = (record: Doctor) => {
    setEditingDoctor(record);
    setFormData(record);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    // Basic validation
    if (!formData.name?.trim()) {
      error('请输入姓名');
      return;
    }
    if (!formData.department_id) {
      error('请选择科室');
      return;
    }

    try {
      if (editingDoctor) {
        await doctorsApi.update(editingDoctor.id, formData);
        success('更新成功');
      } else {
        await doctorsApi.create(formData);
        success('创建成功');
      }
      setModalOpen(false);
      fetchData();
    } catch (err: any) {
      error(err.response?.data?.detail || '操作失败');
    }
  };

  const handleDeleteConfirm = async () => {
    if (!doctorToDelete) return;
    try {
      await doctorsApi.delete(doctorToDelete);
      success('删除成功');
      setDeleteConfirmOpen(false);
      fetchData();
    } catch (err: any) {
      error(err.response?.data?.detail || '删除失败');
    }
  };

  const handleToggleActive = async (id: number, isActive: boolean) => {
    try {
      await doctorsApi.activate(id, isActive);
      success(isActive ? '已启用' : '已停用');
      fetchData();
    } catch (err) {
      error('操作失败');
    }
  };

  const handleTest = (doctor: Doctor) => {
    setTestDoctor(doctor);
    setTestMessage('');
    setTestResult(null);
    setDrawerOpen(true);
  };

  const handleTestSubmit = async () => {
    if (!testDoctor || !testMessage.trim()) return;
    setTestLoading(true);
    try {
      const res = await doctorsApi.test(testDoctor.id, testMessage);
      setTestResult(res.data);
    } catch (err: any) {
      error(err.response?.data?.detail || '测试失败');
    } finally {
      setTestLoading(false);
    }
  };

  const handlePersonaChat = (doctorId: number) => {
    navigate(`/admin/doctors/${doctorId}/persona`);
  };

  const handleRecordAnalysis = (doctorId: number) => {
    navigate(`/admin/doctors/${doctorId}/analyze`);
  };

  const updateFormData = (key: keyof FormData, value: any) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">医生管理</h1>
          <p className="text-sm text-foreground-secondary">
            管理系统中的医生信息，包括AI医生配置
          </p>
        </div>
        <Button onClick={handleCreate} className="gap-2">
          <Plus className="h-4 w-4" />
          新增医生
        </Button>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">ID</TableHead>
                  <TableHead className="w-32">姓名</TableHead>
                  <TableHead className="w-32">职称</TableHead>
                  <TableHead className="w-32">科室</TableHead>
                  <TableHead>医院</TableHead>
                  <TableHead className="w-32">AI模型</TableHead>
                  <TableHead className="w-24">状态</TableHead>
                  <TableHead className="w-64">操作</TableHead>
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
                ) : doctors.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="h-24 text-center">
                      <div className="flex flex-col items-center justify-center gap-2 text-foreground-secondary">
                        <Stethoscope className="h-8 w-8 opacity-50" />
                        <span className="text-sm">暂无医生数据</span>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  doctors.map((doctor) => (
                    <TableRow key={doctor.id}>
                      <TableCell className="text-sm text-foreground-secondary">
                        {doctor.id}
                      </TableCell>
                      <TableCell className="font-medium">{doctor.name}</TableCell>
                      <TableCell>{doctor.title || '-'}</TableCell>
                      <TableCell>
                        {departments.find((d) => d.id === doctor.department_id)?.name || '-'}
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate">
                        {doctor.hospital || '-'}
                      </TableCell>
                      <TableCell>
                        <Badge variant="info">{doctor.ai_model}</Badge>
                      </TableCell>
                      <TableCell>
                        <Switch
                          checked={doctor.is_active}
                          onCheckedChange={(checked) => handleToggleActive(doctor.id, checked)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 flex-wrap">
                          {doctor.is_ai && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handlePersonaChat(doctor.id)}
                                className="h-7 gap-1"
                              >
                                <MessageSquare className="h-3 w-3" />
                                配置分身
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleRecordAnalysis(doctor.id)}
                                className="h-7 gap-1"
                              >
                                <FileText className="h-3 w-3" />
                                病历分析
                              </Button>
                            </>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleTest(doctor)}
                            className="h-7 gap-1"
                          >
                            <Play className="h-3 w-3" />
                            测试
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEdit(doctor)}
                            className="h-7 w-7 p-0"
                          >
                            <Edit className="h-3 w-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setDoctorToDelete(doctor.id);
                              setDeleteConfirmOpen(true);
                            }}
                            className="h-7 w-7 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Edit/Create Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Stethoscope className="h-5 w-5 text-primary" />
              {editingDoctor ? '编辑医生' : '新增医生'}
            </DialogTitle>
          </DialogHeader>

          <Tabs defaultValue="basic" className="w-full">
            <TabsList className="w-full">
              <TabsTrigger value="basic" className="flex-1">基础信息</TabsTrigger>
              <TabsTrigger value="ai" className="flex-1">AI配置</TabsTrigger>
            </TabsList>

            <TabsContent value="basic" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">
                    姓名 <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="name"
                    value={formData.name || ''}
                    onChange={(e) => updateFormData('name', e.target.value)}
                    placeholder="请输入姓名"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="title">职称</Label>
                  <Input
                    id="title"
                    value={formData.title || ''}
                    onChange={(e) => updateFormData('title', e.target.value)}
                    placeholder="如：主任医师"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="department_id">
                    科室 <span className="text-destructive">*</span>
                  </Label>
                  <Select
                    value={formData.department_id?.toString()}
                    onValueChange={(val) => updateFormData('department_id', parseInt(val))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="请选择科室" />
                    </SelectTrigger>
                    <SelectContent>
                      {departments.map((d) => (
                        <SelectItem key={d.id} value={d.id.toString()}>
                          {d.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="rating">评分</Label>
                  <InputNumber
                    id="rating"
                    value={formData.rating}
                    onChange={(val) => updateFormData('rating', val ?? 5.0)}
                    min={0}
                    max={5}
                    step={0.1}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="hospital">医院</Label>
                <Input
                  id="hospital"
                  value={formData.hospital || ''}
                  onChange={(e) => updateFormData('hospital', e.target.value)}
                  placeholder="请输入医院名称"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="specialty">专长</Label>
                <Textarea
                  id="specialty"
                  value={formData.specialty || ''}
                  onChange={(e) => updateFormData('specialty', e.target.value)}
                  placeholder="请输入医生专长描述"
                  rows={3}
                />
              </div>
            </TabsContent>

            <TabsContent value="ai" className="space-y-4 mt-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-secondary rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <Brain className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <Label className="font-medium">启用AI医生</Label>
                      <p className="text-xs text-foreground-secondary">
                        开启后该医生将使用AI进行智能回复
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={formData.is_ai ?? false}
                    onCheckedChange={(val) => updateFormData('is_ai', val)}
                  />
                </div>

                {(formData.is_ai) && (
                  <div className="space-y-4 p-4 border border-border rounded-lg bg-secondary/30">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="ai_model">AI模型</Label>
                        <Select
                          value={formData.ai_model}
                          onValueChange={(val) => updateFormData('ai_model', val)}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="qwen-turbo">Qwen Turbo</SelectItem>
                            <SelectItem value="qwen-plus">Qwen Plus</SelectItem>
                            <SelectItem value="qwen-max">Qwen Max</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="temperature">温度参数</Label>
                        <InputNumber
                          value={formData.ai_temperature}
                          onChange={(val) => updateFormData('ai_temperature', val ?? 0.7)}
                          min={0}
                          max={2}
                          step={0.1}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="max_tokens">最大Token数</Label>
                        <InputNumber
                          value={formData.ai_max_tokens}
                          onChange={(val) => updateFormData('ai_max_tokens', val ?? 500)}
                          min={100}
                          max={2000}
                          step={100}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="knowledge_base">知识库</Label>
                        <Select
                          value={formData.knowledge_base_id}
                          onValueChange={(val) => updateFormData('knowledge_base_id', val)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="选择知识库" />
                          </SelectTrigger>
                          <SelectContent>
                            {knowledgeBases.map((kb) => (
                              <SelectItem key={kb.id} value={kb.id}>
                                {kb.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="ai_persona_prompt">人设Prompt</Label>
                      <Textarea
                        id="ai_persona_prompt"
                        value={formData.ai_persona_prompt || ''}
                        onChange={(e) => updateFormData('ai_persona_prompt', e.target.value)}
                        placeholder="自定义AI人格化提示词，或使用「配置分身」功能通过对话生成..."
                        rows={6}
                      />
                    </div>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>

          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setModalOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSubmit}>
              {editingDoctor ? '保存' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Test Drawer */}
      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent side="right" className="w-[500px]">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-warning" />
              测试AI回复 - {testDoctor?.name}
            </SheetTitle>
          </SheetHeader>

          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="test-message">测试问题</Label>
              <Textarea
                id="test-message"
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                placeholder="输入测试问题..."
                rows={4}
              />
            </div>

            <Button
              onClick={handleTestSubmit}
              disabled={testLoading || !testMessage.trim()}
              className="w-full gap-2"
            >
              {testLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  发送中...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  发送测试
                </>
              )}
            </Button>

            {testResult && (
              <Card className="mt-4">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">AI回复结果</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div>
                    <span className="font-medium text-foreground-secondary">问题：</span>
                    <p className="mt-1">{testResult.question}</p>
                  </div>
                  <div>
                    <span className="font-medium text-foreground-secondary">回答：</span>
                    <p className="mt-1">{testResult.answer}</p>
                  </div>
                  {testResult.rag_context && (
                    <div>
                      <span className="font-medium text-foreground-secondary">RAG上下文：</span>
                      <p className="mt-1 text-xs text-foreground-secondary">{testResult.rag_context}</p>
                    </div>
                  )}
                  <div className="flex gap-4 pt-2 border-t border-border">
                    <span className="text-xs text-foreground-secondary">
                      模型：{testResult.model}
                    </span>
                    <span className="text-xs text-foreground-secondary">
                      温度：{testResult.temperature}
                    </span>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </SheetContent>
      </Sheet>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除医生 "{doctors.find(d => d.id === doctorToDelete)?.name}" 吗？
              此操作无法撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteConfirm} className="bg-destructive hover:bg-destructive/90">
              删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Doctors;

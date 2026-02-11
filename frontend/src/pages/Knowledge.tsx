import React, { useEffect, useState, useCallback } from 'react';
import { knowledgeBasesApi, documentsApi, departmentsApi, doctorsApi } from '../api';
import { useToast } from '@/components/ui/toast';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/medical/page-header';
import { LoadingSkeleton } from '@/components/medical/loading-skeleton';
import {
  Plus,
  Edit,
  Trash2,
  Filter,
  Loader2,
  RefreshCw,
  FileText,
  Upload,
  Check,
  X,
} from 'lucide-react';

// Types
interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  doctor_id?: number;
  department_id?: number;
  total_documents: number;
  total_chunks: number;
  is_active: boolean;
}

interface Document {
  id: number;
  title: string;
  content: string;
  doc_type: string;
  status: string;
  tags: string[];
  created_at: string;
}

const Knowledge: React.FC = () => {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [doctors, setDoctors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedKb, setSelectedKb] = useState<KnowledgeBase | null>(null);

  // KB Modal states
  const [kbModalOpen, setKbModalOpen] = useState(false);
  const [kbSubmitting, setKbSubmitting] = useState(false);
  const [editingKb, setEditingKb] = useState<KnowledgeBase | null>(null);
  const [kbFormData, setKbFormData] = useState<{
    id?: string;
    name?: string;
    description?: string;
    doctor_id?: number;
    department_id?: number;
  }>({});

  // Doc Modal states
  const [docModalOpen, setDocModalOpen] = useState(false);
  const [docSubmitting, setDocSubmitting] = useState(false);
  const [editingDoc, setEditingDoc] = useState<Document | null>(null);
  const [docFormData, setDocFormData] = useState<{
    title?: string;
    content?: string;
    doc_type?: string;
    source?: string;
  }>({});
  const [docInputTab, setDocInputTab] = useState<'text' | 'file'>('text');

  const { success, error } = useToast();

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [kbRes, deptRes, docRes] = await Promise.all([
        knowledgeBasesApi.list(),
        departmentsApi.list(),
        doctorsApi.list(),
      ]);
      setKnowledgeBases(kbRes.data);
      setDepartments(deptRes.data);
      setDoctors(docRes.data);
    } catch (err) {
      error('加载数据失败');
    } finally {
      setLoading(false);
    }
  }, [error]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const fetchDocuments = async (kbId: string) => {
    try {
      const res = await knowledgeBasesApi.listDocuments(kbId);
      setDocuments(res.data);
    } catch (err) {
      error('加载文档失败');
    }
  };

  const handleSelectKb = (kb: KnowledgeBase) => {
    setSelectedKb(kb);
    fetchDocuments(kb.id);
  };

  // KB handlers
  const handleCreateKb = () => {
    setEditingKb(null);
    setKbFormData({});
    setKbModalOpen(true);
  };

  const handleEditKb = (kb: KnowledgeBase) => {
    setEditingKb(kb);
    setKbFormData(kb);
    setKbModalOpen(true);
  };

  const handleSubmitKb = async () => {
    if (!kbFormData.name) {
      error('请输入知识库名称');
      return;
    }
    if (!editingKb && !kbFormData.id) {
      error('请输入知识库ID');
      return;
    }

    setKbSubmitting(true);
    try {
      if (editingKb) {
        await knowledgeBasesApi.update(editingKb.id, kbFormData);
        success('更新成功');
      } else {
        await knowledgeBasesApi.create(kbFormData);
        success('创建成功');
      }
      setKbModalOpen(false);
      fetchData();
    } catch (err: any) {
      error(err.response?.data?.detail || '操作失败');
    } finally {
      setKbSubmitting(false);
    }
  };

  const handleDeleteKb = async (id: string) => {
    try {
      await knowledgeBasesApi.delete(id);
      success('删除成功');
      if (selectedKb?.id === id) {
        setSelectedKb(null);
        setDocuments([]);
      }
      fetchData();
    } catch (err: any) {
      error(err.response?.data?.detail || '删除失败');
    }
  };

  const handleReindex = async (id: string) => {
    try {
      await knowledgeBasesApi.reindex(id);
      success('重新索引完成');
      fetchData();
    } catch (err) {
      error('重新索引失败');
    }
  };

  // Doc handlers
  const handleCreateDoc = () => {
    if (!selectedKb) return;
    setEditingDoc(null);
    setDocFormData({});
    setDocInputTab('text');
    setDocModalOpen(true);
  };

  const handleSubmitDoc = async () => {
    if (!selectedKb) return;
    if (!docFormData.title || !docFormData.content) {
      error('请填写标题和内容');
      return;
    }

    setDocSubmitting(true);
    try {
      if (editingDoc) {
        await documentsApi.update(editingDoc.id, docFormData);
        success('更新成功');
      } else {
        await knowledgeBasesApi.createDocument(selectedKb.id, docFormData);
        success('创建成功');
      }
      setDocModalOpen(false);
      if (selectedKb) fetchDocuments(selectedKb.id);
      fetchData();
    } catch (err: any) {
      error(err.response?.data?.detail || '操作失败');
    } finally {
      setDocSubmitting(false);
    }
  };

  const handleUploadFile = async (file: File) => {
    if (!selectedKb) {
      error('请先选择知识库');
      return;
    }

    setUploading(true);
    try {
      await knowledgeBasesApi.uploadDocument(selectedKb.id, file, {
        title: docFormData.title,
        doc_type: docFormData.doc_type || 'faq',
        source: docFormData.source,
      });
      success('上传成功');
      setDocModalOpen(false);
      setDocFormData({});
      if (selectedKb) fetchDocuments(selectedKb.id);
      fetchData();
    } catch (err: any) {
      error(err.response?.data?.detail || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleApproveDoc = async (docId: number, approved: boolean) => {
    try {
      await documentsApi.approve(docId, { approved });
      success(approved ? '审核通过' : '审核拒绝');
      if (selectedKb) fetchDocuments(selectedKb.id);
    } catch (err) {
      error('操作失败');
    }
  };

  const handleDeleteDoc = async (docId: number) => {
    try {
      await documentsApi.delete(docId);
      success('删除成功');
      if (selectedKb) fetchDocuments(selectedKb.id);
      fetchData();
    } catch (err) {
      error('删除失败');
    }
  };

  const updateKbFormData = (field: string, value: any) => {
    setKbFormData((prev) => ({ ...prev, [field]: value }));
  };

  const updateDocFormData = (field: string, value: any) => {
    setDocFormData((prev) => ({ ...prev, [field]: value }));
  };

  const getDocStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return <Badge className="bg-success text-success-foreground">已通过</Badge>;
      case 'rejected':
        return <Badge variant="destructive">已拒绝</Badge>;
      default:
        return <Badge variant="outline">待审核</Badge>;
    }
  };

  if (loading) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="知识库管理"
        description="管理 AI 知识库和文档，支持病例、FAQ、指南、SOP 等类型"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Knowledge Bases Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>知识库列表</CardTitle>
                <CardDescription>选择知识库查看其文档</CardDescription>
              </div>
              <Button size="sm" onClick={handleCreateKb}>
                <Plus className="h-4 w-4 mr-2" />
                新增
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[120px]">ID</TableHead>
                    <TableHead>名称</TableHead>
                    <TableHead className="w-[60px]">文档</TableHead>
                    <TableHead className="w-[120px]">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {knowledgeBases.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="h-32 text-center text-foreground-secondary">
                        <div className="flex flex-col items-center justify-center gap-2">
                          <FileText className="h-8 w-8 text-foreground-tertiary" />
                          <span className="text-sm">暂无知识库</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    knowledgeBases.map((kb) => (
                      <TableRow
                        key={kb.id}
                        className={selectedKb?.id === kb.id ? 'bg-secondary/50' : 'cursor-pointer'}
                        onClick={() => handleSelectKb(kb)}
                      >
                        <TableCell className="text-foreground-secondary text-xs">
                          {kb.id.slice(0, 8)}...
                        </TableCell>
                        <TableCell>{kb.name}</TableCell>
                        <TableCell>
                          <Badge variant="secondary">{kb.total_documents}</Badge>
                        </TableCell>
                        <TableCell onClick={(e) => e.stopPropagation()}>
                          <div className="flex items-center gap-1">
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-7 w-7"
                              onClick={() => handleReindex(kb.id)}
                              title="重新索引"
                            >
                              <RefreshCw className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-7 w-7"
                              onClick={() => handleEditKb(kb)}
                              title="编辑"
                            >
                              <Edit className="h-3.5 w-3.5" />
                            </Button>
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  className="h-7 w-7 text-destructive"
                                  title="删除"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>确认删除</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    确定要删除知识库 "{kb.name}" 吗？此操作无法撤销。
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>取消</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => handleDeleteKb(kb.id)}
                                    className="bg-destructive text-destructive-foreground hover:bg-destructive-hover"
                                  >
                                    删除
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
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

        {/* Documents Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>
                  {selectedKb ? `文档列表 - ${selectedKb.name}` : '文档列表'}
                </CardTitle>
                <CardDescription>
                  {selectedKb ? '管理知识库中的文档' : '请从左侧选择知识库'}
                </CardDescription>
              </div>
              {selectedKb && (
                <Button size="sm" onClick={handleCreateDoc}>
                  <Plus className="h-4 w-4 mr-2" />
                  添加
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!selectedKb ? (
              <div className="h-64 flex items-center justify-center text-foreground-secondary">
                <div className="text-center">
                  <FileText className="h-12 w-12 mx-auto mb-3 text-foreground-tertiary" />
                  <p>请从左侧选择一个知识库查看文档</p>
                </div>
              </div>
            ) : (
              <div className="rounded-lg border overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[60px]">ID</TableHead>
                      <TableHead>标题</TableHead>
                      <TableHead className="w-[70px]">类型</TableHead>
                      <TableHead className="w-[80px]">状态</TableHead>
                      <TableHead className="w-[120px]">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {documents.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="h-32 text-center text-foreground-secondary">
                          <div className="flex flex-col items-center justify-center gap-2">
                            <Filter className="h-8 w-8 text-foreground-tertiary" />
                            <span className="text-sm">暂无文档</span>
                          </div>
                        </TableCell>
                      </TableRow>
                    ) : (
                      documents.map((doc) => (
                        <TableRow key={doc.id}>
                          <TableCell className="text-foreground-secondary">{doc.id}</TableCell>
                          <TableCell className="truncate max-w-[150px]" title={doc.title}>
                            {doc.title}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{doc.doc_type || '-'}</Badge>
                          </TableCell>
                          <TableCell>{getDocStatusBadge(doc.status)}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              {doc.status === 'pending' && (
                                <>
                                  <Button
                                    size="icon"
                                    variant="ghost"
                                    className="h-7 w-7"
                                    onClick={() => handleApproveDoc(doc.id, true)}
                                    title="通过"
                                  >
                                    <Check className="h-3.5 w-3.5 text-success" />
                                  </Button>
                                  <Button
                                    size="icon"
                                    variant="ghost"
                                    className="h-7 w-7"
                                    onClick={() => handleApproveDoc(doc.id, false)}
                                    title="拒绝"
                                  >
                                    <X className="h-3.5 w-3.5 text-destructive" />
                                  </Button>
                                </>
                              )}
                              <AlertDialog>
                                <AlertDialogTrigger asChild>
                                  <Button
                                    size="icon"
                                    variant="ghost"
                                    className="h-7 w-7 text-destructive"
                                    title="删除"
                                  >
                                    <Trash2 className="h-3.5 w-3.5" />
                                  </Button>
                                </AlertDialogTrigger>
                                <AlertDialogContent>
                                  <AlertDialogHeader>
                                    <AlertDialogTitle>确认删除</AlertDialogTitle>
                                    <AlertDialogDescription>
                                      确定要删除文档 "{doc.title}" 吗？此操作无法撤销。
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>
                                  <AlertDialogFooter>
                                    <AlertDialogCancel>取消</AlertDialogCancel>
                                    <AlertDialogAction
                                      onClick={() => handleDeleteDoc(doc.id)}
                                      className="bg-destructive text-destructive-foreground hover:bg-destructive-hover"
                                    >
                                      删除
                                    </AlertDialogAction>
                                  </AlertDialogFooter>
                                </AlertDialogContent>
                              </AlertDialog>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* KB Edit/Create Dialog */}
      <Dialog open={kbModalOpen} onOpenChange={setKbModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingKb ? '编辑知识库' : '新增知识库'}</DialogTitle>
            <DialogDescription>
              {editingKb ? '修改知识库配置' : '创建新的 AI 知识库'}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            {!editingKb && (
              <div className="space-y-2">
                <Label htmlFor="kb_id">
                  知识库ID <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="kb_id"
                  value={kbFormData.id || ''}
                  onChange={(e) => updateKbFormData('id', e.target.value)}
                  placeholder="唯一标识，如 kb-dermatology-liuwu"
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="kb_name">
                名称 <span className="text-destructive">*</span>
              </Label>
              <Input
                id="kb_name"
                value={kbFormData.name || ''}
                onChange={(e) => updateKbFormData('name', e.target.value)}
                placeholder="知识库名称"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="kb_description">描述</Label>
              <Input
                id="kb_description"
                value={kbFormData.description || ''}
                onChange={(e) => updateKbFormData('description', e.target.value)}
                placeholder="知识库描述"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="kb_doctor">关联医生</Label>
              <Select
                value={kbFormData.doctor_id?.toString() || ''}
                onValueChange={(v) => updateKbFormData('doctor_id', v ? Number(v) : undefined)}
              >
                <SelectTrigger id="kb_doctor">
                  <SelectValue placeholder="选择医生" />
                </SelectTrigger>
                <SelectContent>
                  {doctors.map((d) => (
                    <SelectItem key={d.id} value={d.id.toString()}>
                      {d.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="kb_department">关联科室</Label>
              <Select
                value={kbFormData.department_id?.toString() || ''}
                onValueChange={(v) =>
                  updateKbFormData('department_id', v ? Number(v) : undefined)
                }
              >
                <SelectTrigger id="kb_department">
                  <SelectValue placeholder="选择科室" />
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
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setKbModalOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSubmitKb} disabled={kbSubmitting}>
              {kbSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {editingKb ? '更新' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Doc Edit/Create Dialog */}
      <Dialog open={docModalOpen} onOpenChange={setDocModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingDoc ? '编辑文档' : '添加文档'}</DialogTitle>
            <DialogDescription>
              {editingDoc ? '修改文档内容' : '添加新文档到知识库'}
            </DialogDescription>
          </DialogHeader>

          {editingDoc ? (
            // Edit existing document
            <div className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="edit_title">标题</Label>
                <Input
                  id="edit_title"
                  value={docFormData.title || ''}
                  onChange={(e) => updateDocFormData('title', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit_content">内容</Label>
                <Input
                  id="edit_content"
                  value={docFormData.content || ''}
                  onChange={(e) => updateDocFormData('content', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit_doc_type">类型</Label>
                <Select
                  value={docFormData.doc_type || ''}
                  onValueChange={(v) => updateDocFormData('doc_type', v)}
                >
                  <SelectTrigger id="edit_doc_type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="case">病例</SelectItem>
                    <SelectItem value="faq">FAQ</SelectItem>
                    <SelectItem value="guideline">指南</SelectItem>
                    <SelectItem value="sop">SOP</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit_source">来源</Label>
                <Input
                  id="edit_source"
                  value={docFormData.source || ''}
                  onChange={(e) => updateDocFormData('source', e.target.value)}
                  placeholder="如：刘武医生提供"
                />
              </div>
            </div>
          ) : (
            // Create new document with tabs
            <Tabs value={docInputTab} onValueChange={(v) => setDocInputTab(v as 'text' | 'file')}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="text">文本输入</TabsTrigger>
                <TabsTrigger value="file">文件上传</TabsTrigger>
              </TabsList>

              <TabsContent value="text" className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="doc_title">
                    标题 <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="doc_title"
                    value={docFormData.title || ''}
                    onChange={(e) => updateDocFormData('title', e.target.value)}
                    placeholder="文档标题"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="doc_content">
                    内容 <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="doc_content"
                    value={docFormData.content || ''}
                    onChange={(e) => updateDocFormData('content', e.target.value)}
                    placeholder="文档内容"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="doc_doc_type">类型</Label>
                  <Select
                    value={docFormData.doc_type || 'faq'}
                    onValueChange={(v) => updateDocFormData('doc_type', v)}
                  >
                    <SelectTrigger id="doc_doc_type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="case">病例</SelectItem>
                      <SelectItem value="faq">FAQ</SelectItem>
                      <SelectItem value="guideline">指南</SelectItem>
                      <SelectItem value="sop">SOP</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="doc_source">来源</Label>
                  <Input
                    id="doc_source"
                    value={docFormData.source || ''}
                    onChange={(e) => updateDocFormData('source', e.target.value)}
                    placeholder="如：刘武医生提供"
                  />
                </div>
              </TabsContent>

              <TabsContent value="file" className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="file_input">
                    上传文件 (PDF/TXT) <span className="text-destructive">*</span>
                  </Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="file_input"
                      type="file"
                      accept=".pdf,.txt"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          if (!docFormData.title) {
                            updateDocFormData('title', file.name.replace(/\.[^/.]+$/, ''));
                          }
                        }
                      }}
                    />
                    <Upload className="h-5 w-5 text-foreground-secondary" />
                  </div>
                  <p className="text-xs text-foreground-secondary">
                    支持 PDF、TXT 格式，单个文件最大 10MB
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="file_title">标题（可选）</Label>
                  <Input
                    id="file_title"
                    value={docFormData.title || ''}
                    onChange={(e) => updateDocFormData('title', e.target.value)}
                    placeholder="留空则使用文件名"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="file_doc_type">类型</Label>
                  <Select
                    value={docFormData.doc_type || 'faq'}
                    onValueChange={(v) => updateDocFormData('doc_type', v)}
                  >
                    <SelectTrigger id="file_doc_type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="case">病例</SelectItem>
                      <SelectItem value="faq">FAQ</SelectItem>
                      <SelectItem value="guideline">指南</SelectItem>
                      <SelectItem value="sop">SOP</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="file_source">来源</Label>
                  <Input
                    id="file_source"
                    value={docFormData.source || ''}
                    onChange={(e) => updateDocFormData('source', e.target.value)}
                    placeholder="文档来源"
                  />
                </div>
              </TabsContent>
            </Tabs>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setDocModalOpen(false)}>
              取消
            </Button>
            {editingDoc ? (
              <Button onClick={handleSubmitDoc} disabled={docSubmitting}>
                {docSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                保存
              </Button>
            ) : docInputTab === 'text' ? (
              <Button onClick={handleSubmitDoc} disabled={docSubmitting}>
                {docSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                创建
              </Button>
            ) : (
              <Button
                onClick={() => {
                  const fileInput = document.getElementById('file_input') as HTMLInputElement;
                  const file = fileInput?.files?.[0];
                  if (file) {
                    handleUploadFile(file);
                  } else {
                    error('请选择文件');
                  }
                }}
                disabled={uploading}
              >
                {uploading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                上传
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Knowledge;

import React, { useEffect, useState } from 'react';
import { diseasesApi, departmentsApi } from '../api';
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
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { PageHeader } from '@/components/medical/page-header';
import { LoadingSkeleton } from '@/components/medical/loading-skeleton';
import {
  Plus,
  Edit,
  Trash2,
  Flame,
  Search,
  Filter,
  Loader2,
} from 'lucide-react';

// Types
interface Disease {
  id: number;
  name: string;
  pinyin: string;
  pinyin_abbr: string;
  aliases: string;
  department_id: number;
  department_name: string;
  recommended_department: string;
  overview: string;
  symptoms: string;
  causes: string;
  diagnosis: string;
  treatment: string;
  prevention: string;
  care: string;
  author_name: string;
  author_title: string;
  author_avatar: string;
  reviewer_info: string;
  is_hot: boolean;
  sort_order: number;
  is_active: boolean;
  view_count: number;
  created_at: string;
  updated_at: string;
}

interface Department {
  id: number;
  name: string;
}

interface FormData {
  name?: string;
  department_id?: number;
  pinyin?: string;
  pinyin_abbr?: string;
  aliases?: string;
  recommended_department?: string;
  overview?: string;
  symptoms?: string;
  causes?: string;
  diagnosis?: string;
  treatment?: string;
  prevention?: string;
  care?: string;
  author_name?: string;
  author_title?: string;
  author_avatar?: string;
  reviewer_info?: string;
  sort_order?: number;
  is_hot?: boolean;
  is_active?: boolean;
}

const Diseases: React.FC = () => {
  const [diseases, setDiseases] = useState<Disease[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [editingDisease, setEditingDisease] = useState<Disease | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [filters, setFilters] = useState<{
    department_id?: number;
    is_active?: boolean;
    search?: string;
  }>({});
  const [formData, setFormData] = useState<FormData>({});
  const { success, error } = useToast();

  // Fetch departments (only once on mount)
  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const response = await departmentsApi.list();
        setDepartments(response.data);
      } catch (err) {
        error('加载科室列表失败');
      }
    };
    fetchDepartments();
  }, [error]);

  // Fetch diseases when filters change or refreshKey increments
  useEffect(() => {
    const fetchDiseases = async () => {
      setLoading(true);
      try {
        const response = await diseasesApi.list(filters);
        setDiseases(response.data);
      } catch (err) {
        error('加载疾病列表失败');
      } finally {
        setLoading(false);
      }
    };
    fetchDiseases();
  }, [filters, refreshKey, error]);

  // Handlers
  const handleCreate = () => {
    setEditingDisease(null);
    setFormData({
      sort_order: 0,
      is_active: true,
      is_hot: false,
      reviewer_info: '三甲医生专业编审 · 灵犀健康官方出品',
    });
    setModalOpen(true);
  };

  const handleEdit = async (record: Disease) => {
    try {
      const response = await diseasesApi.get(record.id);
      setEditingDisease(response.data);
      setFormData(response.data);
      setModalOpen(true);
    } catch (err) {
      error('加载疾病详情失败');
    }
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.department_id) {
      error('请填写必填字段');
      return;
    }

    setSubmitting(true);
    try {
      if (editingDisease) {
        await diseasesApi.update(editingDisease.id, formData);
        success('更新成功');
      } else {
        await diseasesApi.create(formData);
        success('创建成功');
      }
      setModalOpen(false);
      setRefreshKey(prev => prev + 1);
    } catch (err: any) {
      error(err.response?.data?.detail || '操作失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await diseasesApi.delete(id);
      success('删除成功');
      setRefreshKey(prev => prev + 1);
    } catch (err: any) {
      error(err.response?.data?.detail || '删除失败');
    }
  };

  const handleToggleHot = async (id: number, isHot: boolean) => {
    try {
      await diseasesApi.toggleHot(id, isHot);
      success(isHot ? '已设为热门' : '已取消热门');
      setRefreshKey(prev => prev + 1);
    } catch (err) {
      error('操作失败');
    }
  };

  const handleToggleActive = async (id: number, isActive: boolean) => {
    try {
      await diseasesApi.toggleActive(id, isActive);
      success(isActive ? '已启用' : '已禁用');
      setRefreshKey(prev => prev + 1);
    } catch (err) {
      error('操作失败');
    }
  };

  const updateFormData = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="疾病百科管理"
        description="管理系统中的疾病信息，包括症状、病因、诊断、治疗等"
      />

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-wrap gap-3 items-center">
          <Select
            value={filters.department_id?.toString() || ''}
            onValueChange={(v) =>
              setFilters({ ...filters, department_id: v ? Number(v) : undefined })
            }
          >
            <SelectTrigger className="w-[150px]">
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

          <Select
            value={filters.is_active?.toString() || ''}
            onValueChange={(v) =>
              setFilters({ ...filters, is_active: v === 'true' ? true : v === 'false' ? false : undefined })
            }
          >
            <SelectTrigger className="w-[100px]">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="true">已启用</SelectItem>
              <SelectItem value="false">已禁用</SelectItem>
            </SelectContent>
          </Select>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-tertiary" />
            <Input
              placeholder="搜索疾病名称"
              value={filters.search || ''}
              onChange={(e) =>
                setFilters({ ...filters, search: e.target.value || undefined })
              }
              className="pl-9 w-[200px]"
            />
          </div>
        </div>

        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          新增疾病
        </Button>
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-surface overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[60px]">ID</TableHead>
                <TableHead className="w-[150px]">名称</TableHead>
                <TableHead className="w-[100px]">科室</TableHead>
                <TableHead className="w-[120px]">拼音</TableHead>
                <TableHead className="w-[150px]">别名</TableHead>
                <TableHead className="w-[80px]">浏览量</TableHead>
                <TableHead className="w-[70px]">热门</TableHead>
                <TableHead className="w-[70px]">状态</TableHead>
                <TableHead className="w-[100px]">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {diseases.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="h-32 text-center text-foreground-secondary">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <Filter className="h-8 w-8 text-foreground-tertiary" />
                      <span className="text-sm">暂无数据</span>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                diseases.map((disease) => (
                  <TableRow key={disease.id}>
                    <TableCell className="text-foreground-secondary">{disease.id}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {disease.name}
                        {disease.is_hot && <Flame className="h-4 w-4 text-orange-500" />}
                      </div>
                    </TableCell>
                    <TableCell>{disease.department_name}</TableCell>
                    <TableCell className="truncate max-w-[120px]" title={disease.pinyin}>
                      {disease.pinyin}
                    </TableCell>
                    <TableCell className="truncate max-w-[150px]" title={disease.aliases}>
                      {disease.aliases}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{disease.view_count}</Badge>
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={disease.is_hot}
                        onCheckedChange={(checked) => handleToggleHot(disease.id, checked)}
                      />
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={disease.is_active}
                        onCheckedChange={(checked) => handleToggleActive(disease.id, checked)}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8"
                          onClick={() => handleEdit(disease)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button size="icon" variant="ghost" className="h-8 w-8 text-destructive">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>确认删除</AlertDialogTitle>
                              <AlertDialogDescription>
                                确定要删除疾病 "{disease.name}" 吗？此操作无法撤销。
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>取消</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDelete(disease.id)}
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
      </div>

      {/* Edit/Create Dialog */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingDisease ? '编辑疾病' : '新增疾病'}</DialogTitle>
            <DialogDescription>
              {editingDisease ? '修改疾病信息' : '创建新的疾病条目'}
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="basic" className="mt-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="basic">基本信息</TabsTrigger>
              <TabsTrigger value="content">疾病内容</TabsTrigger>
              <TabsTrigger value="author">作者信息</TabsTrigger>
            </TabsList>

            <TabsContent value="basic" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">
                    疾病名称 <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="name"
                    value={formData.name || ''}
                    onChange={(e) => updateFormData('name', e.target.value)}
                    placeholder="请输入疾病名称"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="department_id">
                    所属科室 <span className="text-destructive">*</span>
                  </Label>
                  <Select
                    value={formData.department_id?.toString()}
                    onValueChange={(v) => updateFormData('department_id', Number(v))}
                  >
                    <SelectTrigger id="department_id">
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

                <div className="space-y-2">
                  <Label htmlFor="pinyin">拼音</Label>
                  <Input
                    id="pinyin"
                    value={formData.pinyin || ''}
                    onChange={(e) => updateFormData('pinyin', e.target.value)}
                    placeholder="留空自动生成"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pinyin_abbr">拼音首字母</Label>
                  <Input
                    id="pinyin_abbr"
                    value={formData.pinyin_abbr || ''}
                    onChange={(e) => updateFormData('pinyin_abbr', e.target.value)}
                    placeholder="留空自动生成"
                  />
                </div>

                <div className="space-y-2 col-span-2">
                  <Label htmlFor="aliases">别名/同义词</Label>
                  <Input
                    id="aliases"
                    value={formData.aliases || ''}
                    onChange={(e) => updateFormData('aliases', e.target.value)}
                    placeholder="多个别名用逗号分隔"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="recommended_department">推荐就诊科室</Label>
                  <Input
                    id="recommended_department"
                    value={formData.recommended_department || ''}
                    onChange={(e) => updateFormData('recommended_department', e.target.value)}
                    placeholder="如：内科、儿科等"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="sort_order">排序</Label>
                  <Input
                    id="sort_order"
                    type="number"
                    min={0}
                    value={formData.sort_order ?? 0}
                    onChange={(e) => updateFormData('sort_order', Number(e.target.value))}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="is_hot">热门</Label>
                    <Switch
                      id="is_hot"
                      checked={formData.is_hot ?? false}
                      onCheckedChange={(checked) => updateFormData('is_hot', checked)}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="is_active">启用</Label>
                    <Switch
                      id="is_active"
                      checked={formData.is_active ?? true}
                      onCheckedChange={(checked) => updateFormData('is_active', checked)}
                    />
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="content" className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="overview">简介/概述</Label>
                <Input
                  id="overview"
                  value={formData.overview || ''}
                  onChange={(e) => updateFormData('overview', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="symptoms">症状</Label>
                <Input
                  id="symptoms"
                  value={formData.symptoms || ''}
                  onChange={(e) => updateFormData('symptoms', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="causes">病因</Label>
                <Input
                  id="causes"
                  value={formData.causes || ''}
                  onChange={(e) => updateFormData('causes', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="diagnosis">诊断</Label>
                <Input
                  id="diagnosis"
                  value={formData.diagnosis || ''}
                  onChange={(e) => updateFormData('diagnosis', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="treatment">治疗</Label>
                <Input
                  id="treatment"
                  value={formData.treatment || ''}
                  onChange={(e) => updateFormData('treatment', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="prevention">预防</Label>
                <Input
                  id="prevention"
                  value={formData.prevention || ''}
                  onChange={(e) => updateFormData('prevention', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="care">日常护理/注意事项</Label>
                <Input
                  id="care"
                  value={formData.care || ''}
                  onChange={(e) => updateFormData('care', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>
            </TabsContent>

            <TabsContent value="author" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="author_name">作者姓名</Label>
                  <Input
                    id="author_name"
                    value={formData.author_name || ''}
                    onChange={(e) => updateFormData('author_name', e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="author_title">作者职称</Label>
                  <Input
                    id="author_title"
                    value={formData.author_title || ''}
                    onChange={(e) => updateFormData('author_title', e.target.value)}
                    placeholder="如：主治医师、副主任医师等"
                  />
                </div>

                <div className="space-y-2 col-span-2">
                  <Label htmlFor="author_avatar">作者头像URL</Label>
                  <Input
                    id="author_avatar"
                    value={formData.author_avatar || ''}
                    onChange={(e) => updateFormData('author_avatar', e.target.value)}
                    placeholder="头像图片链接"
                  />
                </div>

                <div className="space-y-2 col-span-2">
                  <Label htmlFor="reviewer_info">审核信息</Label>
                  <Input
                    id="reviewer_info"
                    value={formData.reviewer_info || ''}
                    onChange={(e) => updateFormData('reviewer_info', e.target.value)}
                    placeholder="如：三甲医生专业编审 · 灵犀健康官方出品"
                  />
                </div>
              </div>
            </TabsContent>
          </Tabs>

          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setModalOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSubmit} disabled={submitting}>
              {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {editingDisease ? '更新' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Diseases;

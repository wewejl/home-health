import React, { useEffect, useState, useCallback } from 'react';
import { drugsApi, drugCategoriesApi } from '../api';
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
  Package,
} from 'lucide-react';

// Types
interface DrugCategory {
  id: number;
  name: string;
  icon: string;
  display_type: string;
  sort_order: number;
  is_active: boolean;
  drug_count: number;
}

interface Drug {
  id: number;
  name: string;
  pinyin: string;
  pinyin_abbr: string;
  aliases: string;
  common_brands: string;
  pregnancy_level: string;
  pregnancy_desc: string;
  lactation_level: string;
  lactation_desc: string;
  children_usable: boolean;
  children_desc: string;
  indications: string;
  contraindications: string;
  dosage: string;
  side_effects: string;
  precautions: string;
  interactions: string;
  storage: string;
  author_name: string;
  author_title: string;
  author_avatar: string;
  reviewer_info: string;
  is_hot: boolean;
  sort_order: number;
  is_active: boolean;
  view_count: number;
  category_ids: number[];
  category_names: string[];
}

interface DrugFormData {
  name?: string;
  common_brands?: string;
  pinyin?: string;
  pinyin_abbr?: string;
  aliases?: string;
  category_ids?: number[];
  sort_order?: number;
  is_hot?: boolean;
  is_active?: boolean;
  pregnancy_level?: string;
  pregnancy_desc?: string;
  lactation_level?: string;
  lactation_desc?: string;
  children_usable?: boolean;
  children_desc?: string;
  indications?: string;
  contraindications?: string;
  dosage?: string;
  side_effects?: string;
  precautions?: string;
  interactions?: string;
  storage?: string;
  author_name?: string;
  author_title?: string;
  author_avatar?: string;
  reviewer_info?: string;
}

interface CategoryFormData {
  name?: string;
  icon?: string;
  description?: string;
  display_type?: string;
  sort_order?: number;
  is_active?: boolean;
}

const Drugs: React.FC = () => {
  const [drugs, setDrugs] = useState<Drug[]>([]);
  const [categories, setCategories] = useState<DrugCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('drugs');

  // Drug modal states
  const [drugModalOpen, setDrugModalOpen] = useState(false);
  const [drugSubmitting, setDrugSubmitting] = useState(false);
  const [editingDrug, setEditingDrug] = useState<Drug | null>(null);
  const [drugFormData, setDrugFormData] = useState<DrugFormData>({});

  // Category modal states
  const [categoryModalOpen, setCategoryModalOpen] = useState(false);
  const [categorySubmitting, setCategorySubmitting] = useState(false);
  const [editingCategory, setEditingCategory] = useState<DrugCategory | null>(null);
  const [categoryFormData, setCategoryFormData] = useState<CategoryFormData>({});

  const [filters, setFilters] = useState<{
    category_id?: number;
    is_active?: boolean;
    q?: string;
  }>({});
  const { success, error } = useToast();

  // Fetch data
  const fetchCategories = useCallback(async () => {
    try {
      const response = await drugCategoriesApi.list(true);
      setCategories(response.data);
    } catch (err) {
      error('加载分类列表失败');
    }
  }, [error]);

  const fetchDrugs = useCallback(async () => {
    setLoading(true);
    try {
      const response = await drugsApi.list(filters);
      setDrugs(response.data.items || response.data);
    } catch (err) {
      error('加载药品列表失败');
    } finally {
      setLoading(false);
    }
  }, [filters, error]);

  useEffect(() => {
    fetchCategories();
    fetchDrugs();
  }, [fetchCategories, fetchDrugs]);

  // Drug handlers
  const handleCreateDrug = () => {
    setEditingDrug(null);
    setDrugFormData({
      sort_order: 0,
      is_active: true,
      is_hot: false,
      children_usable: true,
      reviewer_info: '三甲医生专业编审 · 灵犀健康官方出品',
      category_ids: [],
    });
    setDrugModalOpen(true);
  };

  const handleEditDrug = async (record: Drug) => {
    try {
      const response = await drugsApi.get(record.id);
      setEditingDrug(response.data);
      setDrugFormData(response.data);
      setDrugModalOpen(true);
    } catch (err) {
      error('加载药品详情失败');
    }
  };

  const handleSubmitDrug = async () => {
    if (!drugFormData.name) {
      error('请填写药品名称');
      return;
    }

    setDrugSubmitting(true);
    try {
      if (editingDrug) {
        await drugsApi.update(editingDrug.id, drugFormData);
        success('更新成功');
      } else {
        await drugsApi.create(drugFormData);
        success('创建成功');
      }
      setDrugModalOpen(false);
      fetchDrugs();
    } catch (err: any) {
      error(err.response?.data?.detail || '操作失败');
    } finally {
      setDrugSubmitting(false);
    }
  };

  const handleDeleteDrug = async (id: number) => {
    try {
      await drugsApi.delete(id);
      success('删除成功');
      fetchDrugs();
    } catch (err: any) {
      error(err.response?.data?.detail || '删除失败');
    }
  };

  const handleToggleHot = async (id: number) => {
    try {
      await drugsApi.toggleHot(id);
      success('操作成功');
      fetchDrugs();
    } catch (err) {
      error('操作失败');
    }
  };

  const handleToggleActive = async (id: number) => {
    try {
      await drugsApi.toggleActive(id);
      success('操作成功');
      fetchDrugs();
    } catch (err) {
      error('操作失败');
    }
  };

  // Category handlers
  const handleCreateCategory = () => {
    setEditingCategory(null);
    setCategoryFormData({
      sort_order: 0,
      is_active: true,
      display_type: 'grid',
    });
    setCategoryModalOpen(true);
  };

  const handleEditCategory = (record: DrugCategory) => {
    setEditingCategory(record);
    setCategoryFormData(record);
    setCategoryModalOpen(true);
  };

  const handleSubmitCategory = async () => {
    if (!categoryFormData.name) {
      error('请填写分类名称');
      return;
    }

    setCategorySubmitting(true);
    try {
      if (editingCategory) {
        await drugCategoriesApi.update(editingCategory.id, categoryFormData);
        success('更新成功');
      } else {
        await drugCategoriesApi.create(categoryFormData);
        success('创建成功');
      }
      setCategoryModalOpen(false);
      fetchCategories();
    } catch (err: any) {
      error(err.response?.data?.detail || '操作失败');
    } finally {
      setCategorySubmitting(false);
    }
  };

  const handleDeleteCategory = async (id: number) => {
    try {
      await drugCategoriesApi.delete(id);
      success('删除成功');
      fetchCategories();
    } catch (err: any) {
      error(err.response?.data?.detail || '删除失败');
    }
  };

  const updateDrugFormData = (field: string, value: any) => {
    setDrugFormData((prev) => ({ ...prev, [field]: value }));
  };

  const updateCategoryFormData = (field: string, value: any) => {
    setCategoryFormData((prev) => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="药品百科管理"
        description="管理系统中的药品信息，包括用法用量、不良反应、注意事项等"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="drugs" className="flex items-center gap-2">
            <Package className="h-4 w-4" />
            药品管理
          </TabsTrigger>
          <TabsTrigger value="categories">分类管理</TabsTrigger>
        </TabsList>

        <TabsContent value="drugs" className="space-y-4 mt-6">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex flex-wrap gap-3 items-center">
              <Select
                value={filters.category_id?.toString() || ''}
                onValueChange={(v) =>
                  setFilters({ ...filters, category_id: v ? Number(v) : undefined })
                }
              >
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="选择分类" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((c) => (
                    <SelectItem key={c.id} value={c.id.toString()}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={filters.is_active?.toString() || ''}
                onValueChange={(v) =>
                  setFilters({
                    ...filters,
                    is_active: v === 'true' ? true : v === 'false' ? false : undefined,
                  })
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
                  placeholder="搜索药品名称"
                  value={filters.q || ''}
                  onChange={(e) => setFilters({ ...filters, q: e.target.value || undefined })}
                  className="pl-9 w-[200px]"
                />
              </div>
            </div>

            <Button onClick={handleCreateDrug}>
              <Plus className="h-4 w-4 mr-2" />
              新增药品
            </Button>
          </div>

          {/* Drug Table */}
          <div className="rounded-lg border bg-surface overflow-hidden">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[60px]">ID</TableHead>
                    <TableHead className="w-[150px]">名称</TableHead>
                    <TableHead className="w-[150px]">商品名</TableHead>
                    <TableHead className="w-[120px]">分类</TableHead>
                    <TableHead className="w-[80px]">浏览量</TableHead>
                    <TableHead className="w-[70px]">热门</TableHead>
                    <TableHead className="w-[70px]">状态</TableHead>
                    <TableHead className="w-[100px]">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {drugs.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="h-32 text-center text-foreground-secondary">
                        <div className="flex flex-col items-center justify-center gap-2">
                          <Package className="h-8 w-8 text-foreground-tertiary" />
                          <span className="text-sm">暂无数据</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    drugs.map((drug) => (
                      <TableRow key={drug.id}>
                        <TableCell className="text-foreground-secondary">{drug.id}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {drug.name}
                            {drug.is_hot && <Flame className="h-4 w-4 text-orange-500" />}
                          </div>
                        </TableCell>
                        <TableCell className="truncate max-w-[150px]" title={drug.common_brands}>
                          {drug.common_brands}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {drug.category_names?.map((n, i) => (
                              <Badge key={i} variant="outline" className="text-xs">
                                {n}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{drug.view_count}</Badge>
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={drug.is_hot}
                            onCheckedChange={() => handleToggleHot(drug.id)}
                          />
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={drug.is_active}
                            onCheckedChange={() => handleToggleActive(drug.id)}
                          />
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-8 w-8"
                              onClick={() => handleEditDrug(drug)}
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
                                    确定要删除药品 "{drug.name}" 吗？此操作无法撤销。
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>取消</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => handleDeleteDrug(drug.id)}
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
        </TabsContent>

        <TabsContent value="categories" className="space-y-4 mt-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">药品分类管理</h3>
            <Button onClick={handleCreateCategory}>
              <Plus className="h-4 w-4 mr-2" />
              新增分类
            </Button>
          </div>

          {/* Category Table */}
          <div className="rounded-lg border bg-surface overflow-hidden">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[60px]">ID</TableHead>
                    <TableHead>名称</TableHead>
                    <TableHead className="w-[100px]">图标</TableHead>
                    <TableHead className="w-[100px]">显示类型</TableHead>
                    <TableHead className="w-[80px]">药品数</TableHead>
                    <TableHead className="w-[60px]">排序</TableHead>
                    <TableHead className="w-[70px]">状态</TableHead>
                    <TableHead className="w-[100px]">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {categories.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="h-32 text-center text-foreground-secondary">
                        <div className="flex flex-col items-center justify-center gap-2">
                          <Filter className="h-8 w-8 text-foreground-tertiary" />
                          <span className="text-sm">暂无数据</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    categories.map((category) => (
                      <TableRow key={category.id}>
                        <TableCell className="text-foreground-secondary">{category.id}</TableCell>
                        <TableCell>{category.name}</TableCell>
                        <TableCell>{category.icon}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{category.display_type}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{category.drug_count}</Badge>
                        </TableCell>
                        <TableCell>{category.sort_order}</TableCell>
                        <TableCell>
                          <Badge
                            variant={category.is_active ? 'default' : 'secondary'}
                            className={category.is_active ? 'bg-success text-success-foreground' : ''}
                          >
                            {category.is_active ? '启用' : '禁用'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-8 w-8"
                              onClick={() => handleEditCategory(category)}
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
                                    确定要删除分类 "{category.name}" 吗？此操作无法撤销。
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>取消</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => handleDeleteCategory(category.id)}
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
        </TabsContent>
      </Tabs>

      {/* Drug Edit/Create Dialog */}
      <Dialog open={drugModalOpen} onOpenChange={setDrugModalOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingDrug ? '编辑药品' : '新增药品'}</DialogTitle>
            <DialogDescription>
              {editingDrug ? '修改药品信息' : '创建新的药品条目'}
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="basic" className="mt-4">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="basic">基本信息</TabsTrigger>
              <TabsTrigger value="safety">安全等级</TabsTrigger>
              <TabsTrigger value="content">药品内容</TabsTrigger>
              <TabsTrigger value="author">作者信息</TabsTrigger>
            </TabsList>

            <TabsContent value="basic" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="drug_name">
                    药品名称 <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="drug_name"
                    value={drugFormData.name || ''}
                    onChange={(e) => updateDrugFormData('name', e.target.value)}
                    placeholder="请输入药品名称"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="common_brands">常见商品名</Label>
                  <Input
                    id="common_brands"
                    value={drugFormData.common_brands || ''}
                    onChange={(e) => updateDrugFormData('common_brands', e.target.value)}
                    placeholder="如：赛乐欣、希舒美"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="drug_pinyin">拼音</Label>
                  <Input
                    id="drug_pinyin"
                    value={drugFormData.pinyin || ''}
                    onChange={(e) => updateDrugFormData('pinyin', e.target.value)}
                    placeholder="留空自动生成"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="drug_pinyin_abbr">拼音首字母</Label>
                  <Input
                    id="drug_pinyin_abbr"
                    value={drugFormData.pinyin_abbr || ''}
                    onChange={(e) => updateDrugFormData('pinyin_abbr', e.target.value)}
                    placeholder="留空自动生成"
                  />
                </div>

                <div className="space-y-2 col-span-2">
                  <Label htmlFor="drug_aliases">别名</Label>
                  <Input
                    id="drug_aliases"
                    value={drugFormData.aliases || ''}
                    onChange={(e) => updateDrugFormData('aliases', e.target.value)}
                    placeholder="多个别名用逗号分隔"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category_ids">所属分类</Label>
                  <Select
                    value={drugFormData.category_ids?.[0]?.toString() || ''}
                    onValueChange={(v) =>
                      updateDrugFormData('category_ids', v ? [Number(v)] : [])
                    }
                  >
                    <SelectTrigger id="category_ids">
                      <SelectValue placeholder="选择分类" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((c) => (
                        <SelectItem key={c.id} value={c.id.toString()}>
                          {c.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="drug_sort_order">排序</Label>
                  <Input
                    id="drug_sort_order"
                    type="number"
                    min={0}
                    value={drugFormData.sort_order ?? 0}
                    onChange={(e) => updateDrugFormData('sort_order', Number(e.target.value))}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="drug_is_hot">热门</Label>
                    <Switch
                      id="drug_is_hot"
                      checked={drugFormData.is_hot ?? false}
                      onCheckedChange={(checked) => updateDrugFormData('is_hot', checked)}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="drug_is_active">启用</Label>
                    <Switch
                      id="drug_is_active"
                      checked={drugFormData.is_active ?? true}
                      onCheckedChange={(checked) => updateDrugFormData('is_active', checked)}
                    />
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="safety" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="pregnancy_level">孕期安全等级</Label>
                  <Select
                    value={drugFormData.pregnancy_level || ''}
                    onValueChange={(v) => updateDrugFormData('pregnancy_level', v)}
                  >
                    <SelectTrigger id="pregnancy_level">
                      <SelectValue placeholder="选择等级" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="A">A - 安全</SelectItem>
                      <SelectItem value="B">B - 较安全</SelectItem>
                      <SelectItem value="C">C - 慎用</SelectItem>
                      <SelectItem value="D">D - 有风险</SelectItem>
                      <SelectItem value="X">X - 禁用</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pregnancy_desc">孕期说明</Label>
                  <Input
                    id="pregnancy_desc"
                    value={drugFormData.pregnancy_desc || ''}
                    onChange={(e) => updateDrugFormData('pregnancy_desc', e.target.value)}
                    placeholder="如：妊娠分级 B"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lactation_level">哺乳期等级</Label>
                  <Select
                    value={drugFormData.lactation_level || ''}
                    onValueChange={(v) => updateDrugFormData('lactation_level', v)}
                  >
                    <SelectTrigger id="lactation_level">
                      <SelectValue placeholder="选择等级" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="L1">L1 - 最安全</SelectItem>
                      <SelectItem value="L2">L2 - 较安全</SelectItem>
                      <SelectItem value="L3">L3 - 中等安全</SelectItem>
                      <SelectItem value="L4">L4 - 可能有害</SelectItem>
                      <SelectItem value="L5">L5 - 禁用</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lactation_desc">哺乳说明</Label>
                  <Input
                    id="lactation_desc"
                    value={drugFormData.lactation_desc || ''}
                    onChange={(e) => updateDrugFormData('lactation_desc', e.target.value)}
                    placeholder="如：哺乳分级 L2"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="children_usable">儿童可用</Label>
                    <Switch
                      id="children_usable"
                      checked={drugFormData.children_usable ?? true}
                      onCheckedChange={(checked) => updateDrugFormData('children_usable', checked)}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="children_desc">儿童用药说明</Label>
                  <Input
                    id="children_desc"
                    value={drugFormData.children_desc || ''}
                    onChange={(e) => updateDrugFormData('children_desc', e.target.value)}
                    placeholder="儿童用药参考说明"
                  />
                </div>
              </div>
            </TabsContent>

            <TabsContent value="content" className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="indications">功效作用/适应症</Label>
                <Input
                  id="indications"
                  value={drugFormData.indications || ''}
                  onChange={(e) => updateDrugFormData('indications', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="contraindications">用药禁忌</Label>
                <Input
                  id="contraindications"
                  value={drugFormData.contraindications || ''}
                  onChange={(e) => updateDrugFormData('contraindications', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="dosage">用法用量</Label>
                <Input
                  id="dosage"
                  value={drugFormData.dosage || ''}
                  onChange={(e) => updateDrugFormData('dosage', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="side_effects">不良反应</Label>
                <Input
                  id="side_effects"
                  value={drugFormData.side_effects || ''}
                  onChange={(e) => updateDrugFormData('side_effects', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="precautions">注意事项</Label>
                <Input
                  id="precautions"
                  value={drugFormData.precautions || ''}
                  onChange={(e) => updateDrugFormData('precautions', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="interactions">药物相互作用</Label>
                <Input
                  id="interactions"
                  value={drugFormData.interactions || ''}
                  onChange={(e) => updateDrugFormData('interactions', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="storage">贮藏方法</Label>
                <Input
                  id="storage"
                  value={drugFormData.storage || ''}
                  onChange={(e) => updateDrugFormData('storage', e.target.value)}
                  placeholder="支持 Markdown 格式"
                />
              </div>
            </TabsContent>

            <TabsContent value="author" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="drug_author_name">作者姓名</Label>
                  <Input
                    id="drug_author_name"
                    value={drugFormData.author_name || ''}
                    onChange={(e) => updateDrugFormData('author_name', e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="drug_author_title">作者职称</Label>
                  <Input
                    id="drug_author_title"
                    value={drugFormData.author_title || ''}
                    onChange={(e) => updateDrugFormData('author_title', e.target.value)}
                    placeholder="如：主治医师"
                  />
                </div>

                <div className="space-y-2 col-span-2">
                  <Label htmlFor="drug_author_avatar">作者头像URL</Label>
                  <Input
                    id="drug_author_avatar"
                    value={drugFormData.author_avatar || ''}
                    onChange={(e) => updateDrugFormData('author_avatar', e.target.value)}
                    placeholder="头像图片链接"
                  />
                </div>

                <div className="space-y-2 col-span-2">
                  <Label htmlFor="drug_reviewer_info">审核信息</Label>
                  <Input
                    id="drug_reviewer_info"
                    value={drugFormData.reviewer_info || ''}
                    onChange={(e) => updateDrugFormData('reviewer_info', e.target.value)}
                    placeholder="如：三甲医生专业编审 · 灵犀健康官方出品"
                  />
                </div>
              </div>
            </TabsContent>
          </Tabs>

          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setDrugModalOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSubmitDrug} disabled={drugSubmitting}>
              {drugSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {editingDrug ? '更新' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Category Edit/Create Dialog */}
      <Dialog open={categoryModalOpen} onOpenChange={setCategoryModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingCategory ? '编辑分类' : '新增分类'}</DialogTitle>
            <DialogDescription>
              {editingCategory ? '修改药品分类信息' : '创建新的药品分类'}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="cat_name">
                分类名称 <span className="text-destructive">*</span>
              </Label>
              <Input
                id="cat_name"
                value={categoryFormData.name || ''}
                onChange={(e) => updateCategoryFormData('name', e.target.value)}
                placeholder="如：热门药品、孕期/哺乳期用药"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="cat_icon">图标</Label>
              <Input
                id="cat_icon"
                value={categoryFormData.icon || ''}
                onChange={(e) => updateCategoryFormData('icon', e.target.value)}
                placeholder="图标名称"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="cat_display_type">显示类型</Label>
              <Select
                value={categoryFormData.display_type || 'grid'}
                onValueChange={(v) => updateCategoryFormData('display_type', v)}
              >
                <SelectTrigger id="cat_display_type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="grid">网格</SelectItem>
                  <SelectItem value="list">列表</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="cat_sort_order">排序</Label>
              <Input
                id="cat_sort_order"
                type="number"
                min={0}
                value={categoryFormData.sort_order ?? 0}
                onChange={(e) => updateCategoryFormData('sort_order', Number(e.target.value))}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="cat_is_active">启用</Label>
                <Switch
                  id="cat_is_active"
                  checked={categoryFormData.is_active ?? true}
                  onCheckedChange={(checked) => updateCategoryFormData('is_active', checked)}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCategoryModalOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSubmitCategory} disabled={categorySubmitting}>
              {categorySubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {editingCategory ? '更新' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Drugs;

import React, { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2, Loader2 } from 'lucide-react';
import { departmentsApi } from '../api';
import { useToast } from '@/components/ui/toast';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';

interface Department {
  id: number;
  name: string;
  description: string;
  icon: string;
  sort_order: number;
  is_active: boolean;
  doctor_count: number;
}

interface FormData {
  name: string;
  description: string;
  icon: string;
  sort_order: number;
  is_active: boolean;
}

const Departments: React.FC = () => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [editingDept, setEditingDept] = useState<Department | null>(null);
  const [formData, setFormData] = useState<FormData>({
    name: '',
    description: '',
    icon: '',
    sort_order: 0,
    is_active: true,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  const { success, error } = useToast();

  useEffect(() => {
    fetchDepartments();
  }, []);

  const fetchDepartments = async () => {
    setLoading(true);
    try {
      const response = await departmentsApi.list();
      setDepartments(response.data);
    } catch (err) {
      error('加载科室列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingDept(null);
    setFormData({
      name: '',
      description: '',
      icon: '',
      sort_order: 0,
      is_active: true,
    });
    setErrors({});
    setModalVisible(true);
  };

  const handleEdit = (record: Department) => {
    setEditingDept(record);
    setFormData({
      name: record.name,
      description: record.description,
      icon: record.icon,
      sort_order: record.sort_order,
      is_active: record.is_active,
    });
    setErrors({});
    setModalVisible(true);
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.name.trim()) {
      newErrors.name = '请输入科室名称';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    try {
      if (editingDept) {
        await departmentsApi.update(editingDept.id, formData);
        success('更新成功');
      } else {
        await departmentsApi.create(formData);
        success('创建成功');
      }
      setModalVisible(false);
      fetchDepartments();
    } catch (err: any) {
      error(err.response?.data?.detail || '操作失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number, doctorCount: number) => {
    if (doctorCount > 0) {
      error('该科室下有医生，无法删除');
      return;
    }

    try {
      await departmentsApi.delete(id);
      success('删除成功');
      fetchDepartments();
    } catch (err: any) {
      error(err.response?.data?.detail || '删除失败');
    }
  };

  const updateFormData = (field: keyof FormData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold tracking-tight">科室管理</h2>
        <Button onClick={handleCreate} className="gap-2">
          <Plus className="h-4 w-4" />
          新增科室
        </Button>
      </div>

      <div className="rounded-lg border border-border bg-surface">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-16">ID</TableHead>
              <TableHead className="w-32">名称</TableHead>
              <TableHead>描述</TableHead>
              <TableHead className="w-40">图标</TableHead>
              <TableHead className="w-20">排序</TableHead>
              <TableHead className="w-20">状态</TableHead>
              <TableHead className="w-20">医生数</TableHead>
              <TableHead className="w-32 text-right">操作</TableHead>
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
            ) : departments.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center text-foreground-secondary">
                  暂无数据
                </TableCell>
              </TableRow>
            ) : (
              departments.map((dept) => (
                <TableRow key={dept.id}>
                  <TableCell className="text-sm">{dept.id}</TableCell>
                  <TableCell className="text-sm font-medium">{dept.name}</TableCell>
                  <TableCell className="text-sm text-foreground-secondary truncate max-w-xs">
                    {dept.description || '-'}
                  </TableCell>
                  <TableCell className="text-sm text-foreground-secondary">
                    {dept.icon || '-'}
                  </TableCell>
                  <TableCell className="text-sm">{dept.sort_order}</TableCell>
                  <TableCell>
                    {dept.is_active ? (
                      <Badge variant="success">启用</Badge>
                    ) : (
                      <Badge variant="secondary">停用</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant={dept.doctor_count > 0 ? "default" : "secondary"}>
                      {dept.doctor_count}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleEdit(dept)}
                        className="h-8 w-8 p-0"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete(dept.id, dept.doctor_count)}
                        disabled={dept.doctor_count > 0}
                        className="h-8 w-8 p-0 text-danger hover:text-danger hover:bg-danger/10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <Dialog open={modalVisible} onOpenChange={setModalVisible}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{editingDept ? '编辑科室' : '新增科室'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">
                名称 <span className="text-danger">*</span>
              </Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => updateFormData('name', e.target.value)}
                placeholder="请输入科室名称"
                className={errors.name ? 'border-danger' : ''}
              />
              {errors.name && (
                <p className="text-xs text-danger">{errors.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">描述</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => updateFormData('description', e.target.value)}
                placeholder="请输入科室描述"
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="icon">图标</Label>
              <Input
                id="icon"
                value={formData.icon}
                onChange={(e) => updateFormData('icon', e.target.value)}
                placeholder="SF Symbols 图标名称"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="sort_order">排序</Label>
              <Input
                id="sort_order"
                type="number"
                min={0}
                value={formData.sort_order}
                onChange={(e) => updateFormData('sort_order', parseInt(e.target.value) || 0)}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => updateFormData('is_active', e.target.checked)}
              />
              <Label htmlFor="is_active" className="cursor-pointer">
                启用状态
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setModalVisible(false)}
              disabled={submitting}
            >
              取消
            </Button>
            <Button onClick={handleSubmit} disabled={submitting} className="gap-2">
              {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {editingDept ? '更新' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Departments;

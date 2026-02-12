/* eslint-disable react-hooks/rules-of-hooks */
import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Search, Plus, Trash2 } from 'lucide-react';
import { doctorApi } from '@/api';
import type { Drug, OrderItem } from '../types';

interface MedicationsStepProps {
  items: OrderItem[];
  onChange: (items: OrderItem[]) => void;
  errors?: Record<string, string>;
}

export const MedicationsStep = ({ items, onChange, errors }: MedicationsStepProps) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Drug[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedDrug, setSelectedDrug] = useState<Drug | null>(null);

  // 当前编辑的药品索引
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const editingItem = editingIndex !== null ? items[editingIndex] : null;

  // 搜索药品
  useEffect(() => {
    const searchDrugs = async () => {
      if (searchQuery.trim().length < 1) {
        setSearchResults([]);
        return;
      }

      setSearching(true);
      try {
        const response = await doctorApi.searchDrugs(searchQuery, 20);
        setSearchResults(response.data || []);
      } catch (error) {
        console.error('搜索药品失败', error);
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    };

    const timer = setTimeout(searchDrugs, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // 添加药品
  const handleAddDrug = () => {
    if (!selectedDrug) return;

    const newItem: OrderItem = {
      item_type: 'drug',
      drug_id: selectedDrug.id,
      name: selectedDrug.name,
      dosage: '',
      frequency: '',
      duration: '',
      notes: '',
      sort_order: items.length,
    };

    onChange([...items, newItem]);
    setSelectedDrug(null);
    setSearchQuery('');
  };

  // 开始编辑药品
  const handleStartEdit = (index: number) => {
    setEditingIndex(index);
  };

  // 保存编辑
  const handleSaveEdit = () => {
    if (editingIndex === null) return;
    setEditingIndex(null);
  };

  // 删除药品
  const handleRemoveItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
    if (editingIndex === index) {
      setEditingIndex(null);
    }
  };

  // 更新药品项
  const handleUpdateItem = (field: keyof OrderItem, value: string) => {
    if (editingIndex === null) return;

    const newItems = [...items];
    newItems[editingIndex] = {
      ...newItems[editingIndex],
      [field]: value,
    };
    onChange(newItems);
  };

  // 常用频率选项
  const FREQUENCY_OPTIONS = [
    { label: '每日1次', value: '每日1次' },
    { label: '每日2次', value: '每日2次' },
    { label: '每日3次', value: '每日3次' },
    { label: '每日4次', value: '每日4次' },
    { label: '隔日1次', value: '隔日1次' },
    { label: '每周1次', value: '每周1次' },
    { label: '必要时', value: '必要时' },
  ];

  // 常用用量选项
  const DOSAGE_OPTIONS = [
    { label: '1片', value: '1片' },
    { label: '2片', value: '2片' },
    { label: '1粒', value: '1粒' },
    { label: '2粒', value: '2粒' },
    { label: '1包', value: '1包' },
    { label: '5ml', value: '5ml' },
    { label: '10ml', value: '10ml' },
  ];

  // 常用时长选项
  const DURATION_OPTIONS = [
    { label: '3天', value: '3天' },
    { label: '5天', value: '5天' },
    { label: '7天', value: '7天' },
    { label: '14天', value: '14天' },
    { label: '30天', value: '30天' },
  ];

  return (
    <div className="space-y-4">
      {/* 添加药品 */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex gap-2">
            <div className="flex-1">
              <Label>添加药品</Label>
              <div className="relative mt-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="搜索药品名称..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Button
              type="button"
              onClick={handleAddDrug}
              disabled={!selectedDrug || items.length >= 10}
              className="mt-6"
            >
              <Plus className="h-4 w-4 mr-1" />
              添加
            </Button>
          </div>

          {/* 搜索结果 */}
          {searchQuery && searchResults.length > 0 && (
            <div className="mt-2 border rounded-md max-h-48 overflow-y-auto">
              {searchResults.map((drug) => (
                <div
                  key={drug.id}
                  className="p-2 hover:bg-muted cursor-pointer flex justify-between items-center"
                  onClick={() => setSelectedDrug(drug)}
                >
                  <span className="font-medium">{drug.name}</span>
                  {selectedDrug?.id === drug.id && (
                    <Badge variant="secondary" className="ml-2">已选择</Badge>
                  )}
                </div>
              ))}
            </div>
          )}

          {searching && (
            <div className="mt-2 text-sm text-muted-foreground text-center">
              搜索中...
            </div>
          )}

          {searchQuery && searchResults.length === 0 && !searching && (
            <div className="mt-2 text-sm text-muted-foreground text-center">
              未找到匹配的药品
            </div>
          )}
        </CardContent>
      </Card>

      {/* 已添加的药品列表 */}
      {items.length > 0 && (
        <Card>
          <CardContent className="pt-4">
            <h3 className="font-medium mb-3">已添加药品 ({items.length})</h3>
            <div className="space-y-3">
              {items.map((item, index) => {
                const isEditing = editingIndex === index;
                return (
                  <div
                    key={index}
                    className={`border rounded-md p-3 ${isEditing ? 'border-primary' : ''}`}
                  >
                    {isEditing ? (
                      // 编辑模式
                      <div className="space-y-3">
                        <div className="flex justify-between items-start">
                          <span className="font-medium text-sm">{item.name}</span>
                          <div className="flex gap-2">
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={handleSaveEdit}
                            >
                              完成
                            </Button>
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditingIndex(null)}
                            >
                              取消
                            </Button>
                          </div>
                        </div>

                        <div className="grid grid-cols-3 gap-3">
                          <div>
                            <Label className="text-xs">用法用量</Label>
                            <Select
                              value={item.dosage || ''}
                              onValueChange={(value) => handleUpdateItem('dosage', value)}
                            >
                              <SelectTrigger className="h-8">
                                <SelectValue placeholder="选择用量" />
                              </SelectTrigger>
                              <SelectContent>
                                {DOSAGE_OPTIONS.map((opt) => (
                                  <SelectItem key={opt.value} value={opt.value}>
                                    {opt.label}
                                  </SelectItem>
                                ))}
                                <SelectItem value="custom">自定义...</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>

                          <div>
                            <Label className="text-xs">用药频率</Label>
                            <Select
                              value={item.frequency || ''}
                              onValueChange={(value) => handleUpdateItem('frequency', value)}
                            >
                              <SelectTrigger className="h-8">
                                <SelectValue placeholder="选择频率" />
                              </SelectTrigger>
                              <SelectContent>
                                {FREQUENCY_OPTIONS.map((opt) => (
                                  <SelectItem key={opt.value} value={opt.value}>
                                    {opt.label}
                                  </SelectItem>
                                ))}
                                <SelectItem value="custom">自定义...</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>

                          <div>
                            <Label className="text-xs">用药时长</Label>
                            <Select
                              value={item.duration || ''}
                              onValueChange={(value) => handleUpdateItem('duration', value)}
                            >
                              <SelectTrigger className="h-8">
                                <SelectValue placeholder="选择时长" />
                              </SelectTrigger>
                              <SelectContent>
                                {DURATION_OPTIONS.map((opt) => (
                                  <SelectItem key={opt.value} value={opt.value}>
                                    {opt.label}
                                  </SelectItem>
                                ))}
                                <SelectItem value="custom">自定义...</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                      </div>
                    ) : (
                      // 查看模式
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <span className="font-medium text-sm">{item.name}</span>
                          <div className="text-xs text-muted-foreground mt-1">
                            {item.dosage && <span className="mr-2">{item.dosage}</span>}
                            {item.frequency && <span className="mr-2">{item.frequency}</span>}
                            {item.duration && <span>{item.duration}</span>}
                          </div>
                          {item.notes && (
                            <div className="text-xs text-muted-foreground mt-1 italic">
                              备注: {item.notes}
                            </div>
                          )}
                        </div>
                        <div className="flex gap-1">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStartEdit(index)}
                          >
                            编辑
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveItem(index)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 提示 */}
      {items.length === 0 && (
        <div className="text-center py-8 text-muted-foreground text-sm">
          尚未添加药品，请从上方搜索添加
        </div>
      )}
    </div>
  );
};

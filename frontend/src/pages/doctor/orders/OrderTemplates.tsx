/* eslint-disable react-hooks/rules-of-hooks */
import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Copy, Save, Loader2 } from 'lucide-react';
import { doctorApi } from '@/api';
import { useToast } from '@/components/ui/toast';
import type { OrderTemplate, BasicInfoData, ScheduleData } from './types';

interface OrderTemplatesProps {
  open: boolean;
  onClose: () => void;
  onSelectTemplate: (basicInfo: BasicInfoData, scheduleData: ScheduleData) => void;
  currentOrderData?: {
    basicInfo: BasicInfoData;
    scheduleData: ScheduleData;
  };
}

export const OrderTemplates = ({
  open,
  onClose,
  onSelectTemplate,
  currentOrderData,
}: OrderTemplatesProps) => {
  const toast = useToast();
  const [templates, setTemplates] = useState<OrderTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState('');
  const [showSaveForm, setShowSaveForm] = useState(false);

  // 加载模板列表
  useEffect(() => {
    if (open) {
      loadTemplates();
    }
  }, [open]);

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const response = await doctorApi.getOrderTemplates();
      setTemplates(response.data || []);
    } catch (error) {
      console.error('加载模板失败', error);
      toast.error('加载模板失败');
    } finally {
      setLoading(false);
    }
  };

  // 应用模板
  const handleApplyTemplate = (template: OrderTemplate) => {
    const { basicInfo, scheduleData } = template.template_data;

    onSelectTemplate(
      {
        order_type: template.order_type,
        title: basicInfo?.title || template.name,
        description: basicInfo?.description,
      },
      {
        schedule_type: scheduleData?.schedule_type || 'once',
        start_date: scheduleData?.start_date || new Date().toISOString().split('T')[0],
        end_date: scheduleData?.end_date,
        reminder_times: scheduleData?.reminder_times || [],
        frequency: scheduleData?.frequency,
        weekdays: scheduleData?.weekdays || [],
      }
    );

    onClose();
    toast.success(`已应用模板：${template.name}`);
  };

  // 保存当前医嘱为模板
  const handleSaveAsTemplate = async () => {
    if (!newTemplateName.trim()) {
      toast.error('请输入模板名称');
      return;
    }

    if (!currentOrderData) {
      toast.error('没有可保存的医嘱内容');
      return;
    }

    setSaving(true);
    try {
      await doctorApi.createOrderTemplate({
        name: newTemplateName.trim(),
        description: `保存于 ${new Date().toLocaleDateString()}`,
        order_type: currentOrderData.basicInfo.order_type || 'medication',
        template_data: {
          basicInfo: currentOrderData.basicInfo,
          scheduleData: currentOrderData.scheduleData,
        },
      });

      toast.success('模板保存成功');
      setNewTemplateName('');
      setShowSaveForm(false);
      loadTemplates(); // 重新加载模板列表
    } catch (error) {
      console.error('保存模板失败', error);
      toast.error('保存模板失败');
    } finally {
      setSaving(false);
    }
  };

  // 获取医嘱类型标签
  const getOrderTypeLabel = (type: string) => {
    const typeMap: Record<string, string> = {
      medication: '用药任务',
      monitoring: '监测任务',
      behavior: '行为任务',
      followup: '复诊任务',
    };
    return typeMap[type] || type;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>医嘱模板</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* 保存当前医嘱为模板 */}
          {!showSaveForm ? (
            <Card className="border-dashed">
              <CardHeader>
                <CardTitle className="text-base">保存当前医嘱为模板</CardTitle>
                <CardDescription>
                  将当前填写的医嘱内容保存为模板，方便下次快速使用
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setShowSaveForm(true)}
                >
                  <Save className="h-4 w-4 mr-2" />
                  保存为模板
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">新建模板</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <Label htmlFor="template-name">模板名称 *</Label>
                  <Input
                    id="template-name"
                    placeholder="例如：高血压常用处方"
                    value={newTemplateName}
                    onChange={(e) => setNewTemplateName(e.target.value)}
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={handleSaveAsTemplate}
                    disabled={saving}
                    className="flex-1"
                  >
                    {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                    保存
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowSaveForm(false);
                      setNewTemplateName('');
                    }}
                    disabled={saving}
                  >
                    取消
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 模板列表 */}
          <div>
            <h3 className="font-medium mb-3">我的模板 ({templates.length})</h3>

            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : templates.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm border rounded-md">
                暂无模板，您可以保存当前医嘱为模板
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                {templates.map((template) => (
                  <Card
                    key={template.id}
                    className="hover:border-primary cursor-pointer transition-colors"
                    onClick={() => handleApplyTemplate(template)}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex justify-between items-start">
                        <CardTitle className="text-base">{template.name}</CardTitle>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleApplyTemplate(template);
                          }}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                      {template.description && (
                        <CardDescription className="text-xs">
                          {template.description}
                        </CardDescription>
                      )}
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-1">
                        <Badge variant="outline" className="text-xs">
                          {getOrderTypeLabel(template.order_type)}
                        </Badge>
                        <div className="text-xs text-muted-foreground mt-2">
                          创建于 {new Date(template.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

import type { BasicInfoData, FormErrors } from '../types';
import { ORDER_TYPE_OPTIONS } from '../types';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { DateInputWrapper } from '../DateInputWrapper';

interface BasicInfoStepProps {
  data: BasicInfoData;
  onChange: (data: BasicInfoData) => void;
  errors: FormErrors;
  isEditing?: boolean;
  onOrderTypeChange?: (orderType: string) => void;
}

export const BasicInfoStep = ({ data, onChange, errors, isEditing = false }: BasicInfoStepProps) => {
  return (
    <div className="space-y-4">
      {/* 编辑模式提示 */}
      {isEditing && (
        <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg">
          <Badge variant="secondary">编辑模式</Badge>
          <span className="text-sm text-muted-foreground">
            医嘱类型不可修改，只能修改标题、描述和结束日期
          </span>
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="order_type">医嘱类型 *</Label>
        {isEditing ? (
          <div className="flex items-center gap-2 p-3 border rounded-lg bg-muted/30">
            <span className="text-foreground">
              {ORDER_TYPE_OPTIONS.find(o => o.value === data.order_type)?.label || data.order_type}
            </span>
            <Badge variant="secondary" className="text-xs">不可修改</Badge>
          </div>
        ) : (
          <Select
            value={data.order_type}
            onValueChange={(value) => {
              onChange({ ...data, order_type: value });
              onOrderTypeChange?.(value);
            }}
          >
            <SelectTrigger id="order_type" className={errors.order_type ? 'border-destructive' : ''}>
              <SelectValue placeholder="请选择医嘱类型" />
            </SelectTrigger>
            <SelectContent>
              {ORDER_TYPE_OPTIONS.map(option => (
                <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        {errors.order_type && <p className="text-sm text-destructive">{errors.order_type}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="title">医嘱标题 *</Label>
        <Input
          id="title"
          placeholder="例如：每日服用降压药"
          value={data.title || ''}
          onChange={(e) => onChange({ ...data, title: e.target.value })}
          className={errors.title ? 'border-destructive' : ''}
        />
        {errors.title && <p className="text-sm text-destructive">{errors.title}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">详细描述</Label>
        <Textarea
          id="description"
          placeholder="请输入医嘱的详细描述，包括用药方法、注意事项等"
          rows={3}
          value={data.description || ''}
          onChange={(e) => onChange({ ...data, description: e.target.value })}
        />
      </div>

      {/* 编辑模式：结束日期 */}
      {isEditing && (
        <div className="space-y-2">
          <Label htmlFor="end_date_edit">结束日期（可选）</Label>
          <DateInputWrapper
            id="end_date_edit"
            value={data.end_date || ''}
            onChange={(value) => onChange({ ...data, end_date: value })}
            placeholder="留空表示长期执行"
          />
          <p className="text-xs text-muted-foreground">
            设置结束日期后，医嘱将在该日期自动停止
          </p>
        </div>
      )}
    </div>
  );
};

import type { BasicInfoData, ScheduleData, OrderItem } from '../types';
import { ORDER_TYPE_OPTIONS, SCHEDULE_TYPE_OPTIONS, WEEKDAY_OPTIONS } from '../types';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';

interface ConfirmStepProps {
  basicInfo: BasicInfoData;
  scheduleData: ScheduleData;
  medications?: OrderItem[];
}

export const ConfirmStep = ({ basicInfo, scheduleData, medications = [] }: ConfirmStepProps) => {
  return (
    <div className="space-y-4">
      <Card className="bg-muted/30">
        <h3 className="font-semibold mb-4">医嘱配置摘要</h3>
        <div className="space-y-3 text-sm">
          <div className="flex">
            <span className="text-muted-foreground w-28">医嘱类型：</span>
            <span>{ORDER_TYPE_OPTIONS.find(o => o.value === basicInfo.order_type)?.label || '-'}</span>
          </div>
          <div className="flex">
            <span className="text-muted-foreground w-28">医嘱标题：</span>
            <span>{basicInfo.title || '-'}</span>
          </div>
          {basicInfo.description && (
            <div className="flex">
              <span className="text-muted-foreground w-28">详细描述：</span>
              <span className="flex-1">{basicInfo.description}</span>
            </div>
          )}
          <Separator />
          <div className="flex">
            <span className="text-muted-foreground w-28">调度类型：</span>
            <span>{SCHEDULE_TYPE_OPTIONS.find(o => o.value === scheduleData.schedule_type)?.label || '一次性'}</span>
          </div>
          <div className="flex">
            <span className="text-muted-foreground w-28">开始日期：</span>
            <span>{scheduleData.start_date || '-'}</span>
          </div>
          {scheduleData.end_date && (
            <div className="flex">
              <span className="text-muted-foreground w-28">结束日期：</span>
              <span>{scheduleData.end_date}</span>
            </div>
          )}
          {scheduleData.frequency && (
            <div className="flex">
              <span className="text-muted-foreground w-28">频次说明：</span>
              <span>{scheduleData.frequency}</span>
            </div>
          )}
          <div className="flex">
            <span className="text-muted-foreground w-28">提醒时间：</span>
            <span>{(scheduleData.reminder_times || []).join(', ') || '-'}</span>
          </div>
          {scheduleData.schedule_type === 'weekly' && (scheduleData.weekdays || []).length > 0 && (
            <div className="flex">
              <span className="text-muted-foreground w-28">重复星期：</span>
              <span>{(scheduleData.weekdays || []).map(w => WEEKDAY_OPTIONS.find(o => o.value === w)?.label).join(', ')}</span>
            </div>
          )}
        </div>
      </Card>

      {/* 药品列表 */}
      {medications && medications.length > 0 && (
        <Card className="bg-muted/30">
          <h3 className="font-semibold mb-4">药品列表 ({medications.length})</h3>
          <div className="space-y-2">
            {medications.map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded-md bg-background">
                <div className="flex-1">
                  <div className="font-medium">{item.name}</div>
                  <div className="text-xs text-muted-foreground">
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
                <Badge variant="outline">
                  药品
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

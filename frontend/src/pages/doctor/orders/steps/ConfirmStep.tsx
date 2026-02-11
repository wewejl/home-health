import type { BasicInfoData, ScheduleData } from '../types';
import { ORDER_TYPE_OPTIONS, SCHEDULE_TYPE_OPTIONS, WEEKDAY_OPTIONS } from '../types';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

interface ConfirmStepProps {
  basicInfo: BasicInfoData;
  scheduleData: ScheduleData;
}

export const ConfirmStep = ({ basicInfo, scheduleData }: ConfirmStepProps) => {
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
    </div>
  );
};

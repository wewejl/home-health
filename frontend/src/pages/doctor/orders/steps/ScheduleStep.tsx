import type { ScheduleData, FormErrors, ScheduleType } from '../types';
import { SCHEDULE_TYPE_OPTIONS, WEEKDAY_OPTIONS } from '../types';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { Plus, Minus } from 'lucide-react';
import { TimeInput } from '../TimeInput';
import { DateInputWrapper } from '../DateInputWrapper';

interface ScheduleStepProps {
  data: ScheduleData;
  scheduleType: ScheduleType;
  onScheduleTypeChange: (type: ScheduleType) => void;
  onChange: (data: ScheduleData) => void;
  errors: FormErrors;
}

export const ScheduleStep = ({ data, scheduleType, onScheduleTypeChange, onChange, errors }: ScheduleStepProps) => {
  const addReminderTime = () => {
    const times = data.reminder_times || [];
    onChange({ ...data, reminder_times: [...times, '08:00'] });
  };

  const removeReminderTime = (index: number) => {
    const times = data.reminder_times || [];
    if (times.length > 1) {
      onChange({ ...data, reminder_times: times.filter((_, i) => i !== index) });
    }
  };

  const updateReminderTime = (index: number, value: string) => {
    const times = data.reminder_times || [];
    const newTimes = [...times];
    newTimes[index] = value;
    onChange({ ...data, reminder_times: newTimes });
  };

  const toggleWeekday = (value: number) => {
    const weekdays = data.weekdays || [];
    if (weekdays.includes(value)) {
      onChange({ ...data, weekdays: weekdays.filter(w => w !== value) });
    } else {
      onChange({ ...data, weekdays: [...weekdays, value] });
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>调度类型 *</Label>
        <div className="flex gap-2">
          {SCHEDULE_TYPE_OPTIONS.map(option => (
            <Button
              key={option.value}
              type="button"
              variant={scheduleType === option.value ? 'default' : 'outline'}
              onClick={() => {
                onScheduleTypeChange(option.value as ScheduleType);
                onChange({ ...data, schedule_type: option.value as ScheduleType });
              }}
            >
              {option.label}
            </Button>
          ))}
        </div>
        {errors.schedule_type && <p className="text-sm text-destructive">{errors.schedule_type}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="start_date">开始日期 *</Label>
          <DateInputWrapper
            id="start_date"
            value={data.start_date || ''}
            onChange={(value) => onChange({ ...data, start_date: value })}
          />
          {errors.start_date && <p className="text-sm text-destructive">{errors.start_date}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="end_date">结束日期（可选）</Label>
          <DateInputWrapper
            id="end_date"
            value={data.end_date || ''}
            onChange={(value) => onChange({ ...data, end_date: value })}
          />
        </div>
      </div>

      <Separator />

      {/* 一次性：单个时间选择器 */}
      {scheduleType === 'once' && (
        <div className="space-y-2">
          <Label>提醒时间 *</Label>
          <TimeInput
            value={data.reminder_times?.[0] || '08:00'}
            onChange={(value) => onChange({ ...data, reminder_times: [value] })}
          />
          {errors.reminder_times && <p className="text-sm text-destructive">{errors.reminder_times}</p>}
        </div>
      )}

      {/* 每日：多个时间选择器 */}
      {scheduleType === 'daily' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="frequency">频次说明</Label>
            <Input
              id="frequency"
              placeholder="如：每日2次"
              value={data.frequency || ''}
              onChange={(e) => onChange({ ...data, frequency: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label>每日提醒时间 *</Label>
            <div className="space-y-2">
              {(data.reminder_times || ['08:00']).map((time, index) => (
                <div key={index} className="flex items-center gap-2">
                  <TimeInput
                    value={time}
                    onChange={(value) => updateReminderTime(index, value)}
                  />
                  {(data.reminder_times || []).length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeReminderTime(index)}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={addReminderTime}
              >
                <Plus className="h-4 w-4 mr-2" />
                添加提醒时间
              </Button>
            </div>
            {errors.reminder_times && <p className="text-sm text-destructive">{errors.reminder_times}</p>}
          </div>
        </>
      )}

      {/* 每周：星期选择 + 时间选择器 */}
      {scheduleType === 'weekly' && (
        <>
          <div className="space-y-2">
            <Label>选择星期 *</Label>
            <div className="flex flex-wrap gap-2">
              {WEEKDAY_OPTIONS.map(option => (
                <label
                  key={option.value}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md border cursor-pointer transition-colors ${
                    (data.weekdays || []).includes(option.value)
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'hover:bg-muted'
                  }`}
                >
                  <Checkbox
                    checked={(data.weekdays || []).includes(option.value)}
                    onChange={() => toggleWeekday(option.value)}
                    className="pointer-events-none"
                  />
                  <span className="text-sm">{option.label}</span>
                </label>
              ))}
            </div>
            {errors.weekdays && <p className="text-sm text-destructive">{errors.weekdays}</p>}
          </div>
          <div className="space-y-2">
            <Label>提醒时间 *</Label>
            <div className="space-y-2">
              {(data.reminder_times || ['08:00']).map((time, index) => (
                <div key={index} className="flex items-center gap-2">
                  <TimeInput
                    value={time}
                    onChange={(value) => updateReminderTime(index, value)}
                  />
                  {(data.reminder_times || []).length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeReminderTime(index)}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={addReminderTime}
              >
                <Plus className="h-4 w-4 mr-2" />
                添加提醒时间
              </Button>
            </div>
            {errors.reminder_times && <p className="text-sm text-destructive">{errors.reminder_times}</p>}
          </div>
        </>
      )}
    </div>
  );
};

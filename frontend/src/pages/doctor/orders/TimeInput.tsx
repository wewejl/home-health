import { Button } from '@/components/ui/button';

interface TimeInputProps {
  value: string;
  onChange: (value: string) => void;
}

export const TimeInput = ({ value, onChange }: TimeInputProps) => {
  const [hours, minutes] = value.split(':').map(Number);

  const handleHoursChange = (delta: number) => {
    let newHours = hours + delta;
    if (newHours < 0) newHours = 23;
    if (newHours > 23) newHours = 0;
    onChange(`${String(newHours).padStart(2, '0')}:${String(minutes || 0).padStart(2, '0')}`);
  };

  const handleMinutesChange = (delta: number) => {
    let newMinutes = (minutes || 0) + delta;
    if (newMinutes < 0) newMinutes = 59;
    if (newMinutes > 59) newMinutes = 0;
    onChange(`${String(hours || 0).padStart(2, '0')}:${String(newMinutes).padStart(2, '0')}`);
  };

  return (
    <div className="flex items-center gap-1 border rounded-md px-2 py-1">
      {/* 小时调整控件 */}
      <Button type="button" variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => handleHoursChange(-1)}>
        -
      </Button>
      <span className="text-sm font-mono w-8 text-center">
        {String(hours || 0).padStart(2, '0')}
      </span>
      <Button type="button" variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => handleHoursChange(1)}>
        +
      </Button>
      <span className="text-xs text-muted-foreground ml-1 mr-2">时</span>

      {/* 分钟调整控件 */}
      <Button type="button" variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => handleMinutesChange(-1)}>
        -
      </Button>
      <span className="text-sm font-mono w-8 text-center">
        {String(minutes || 0).padStart(2, '0')}
      </span>
      <Button type="button" variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => handleMinutesChange(1)}>
        +
      </Button>
      <span className="text-xs text-muted-foreground ml-1">分</span>
    </div>
  );
};

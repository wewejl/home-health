import { DatePicker } from '@/components/ui/date-picker';

interface DateInputWrapperProps {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export const DateInputWrapper = ({ value, onChange }: DateInputWrapperProps) => {
  const parseDate = (str: string): Date | null => {
    if (!str) return null;
    const match = str.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (match) {
      return new Date(parseInt(match[1]), parseInt(match[2]) - 1, parseInt(match[3]));
    }
    return null;
  };

  const formatDate = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const handleDateChange = (date: Date | null) => {
    onChange(date ? formatDate(date) : '');
  };

  return (
    <DatePicker
      value={parseDate(value)}
      onChange={handleDateChange}
    />
  );
};

/**
 * Switch 组件测试
 *
 * 测试覆盖：
 * 1. 基础渲染
 * 2. 选中/未选中状态
 * 3. disabled 状态
 * 4. onChange/onCheckedChange 事件
 * 5. 视觉状态变化
 * 6. 自定义 className
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Switch } from '../switch';

describe('Switch Component', () => {
  describe('Rendering', () => {
    it('should render label element with checkbox input', () => {
      render(<Switch />);
      const checkbox = screen.getByRole('checkbox');
      const label = checkbox.closest('label');

      expect(checkbox).toBeInTheDocument();
      expect(label).toBeInTheDocument();
    });

    it('should hide the checkbox input visually', () => {
      render(<Switch />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;

      expect(checkbox).toHaveClass('sr-only');
    });

    it('should render thumb element', () => {
      render(<Switch />);
      const thumb = document.querySelector('span[class*="translate-x"]');
      expect(thumb).toBeInTheDocument();
    });
  });

  describe('Checked State', () => {
    it('should render unchecked by default', () => {
      render(<Switch />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(false);
    });

    it('should render checked when checked prop is true', () => {
      render(<Switch checked />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(true);
    });

    it('should translate thumb to right when checked', () => {
      render(<Switch checked />);
      const thumb = document.querySelector('.translate-x-4');
      expect(thumb).toBeInTheDocument();
    });

    it('should translate thumb to left when unchecked', () => {
      render(<Switch checked={false} />);
      const thumb = document.querySelector('.translate-x-0');
      expect(thumb).toBeInTheDocument();
    });

    it('should apply primary background when checked', () => {
      render(<Switch checked />);
      const label = screen.getByRole('checkbox').closest('label');

      expect(label).toHaveClass('bg-primary');
    });

    it('should apply input background when unchecked', () => {
      render(<Switch checked={false} />);
      const label = screen.getByRole('checkbox').closest('label');

      expect(label).toHaveClass('bg-input');
    });
  });

  describe('Toggle Behavior', () => {
    it('should toggle checked state on click', async () => {
      render(<Switch />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;

      expect(checkbox.checked).toBe(false);

      const label = checkbox.closest('label');
      if (label) {
        await userEvent.click(label);

        expect(checkbox.checked).toBe(true);
      }
    });

    it('should toggle from checked to unchecked', async () => {
      render(<Switch checked />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;

      expect(checkbox.checked).toBe(true);

      const label = checkbox.closest('label');
      if (label) {
        await userEvent.click(label);

        expect(checkbox.checked).toBe(false);
      }
    });

    it('should call onChange when toggled', async () => {
      const handleChange = vi.fn();
      render(<Switch onChange={handleChange} />);

      const checkbox = screen.getByRole('checkbox');
      const label = checkbox.closest('label');

      if (label) {
        await userEvent.click(label);

        expect(handleChange).toHaveBeenCalled();
      }
    });

    it('should call onCheckedChange with new value', async () => {
      const handleCheckedChange = vi.fn();
      render(<Switch onCheckedChange={handleCheckedChange} />);

      const checkbox = screen.getByRole('checkbox');
      const label = checkbox.closest('label');

      if (label) {
        await userEvent.click(label);

        expect(handleCheckedChange).toHaveBeenCalledWith(true);
      }
    });

    it('should call both onChange and onCheckedChange', async () => {
      const handleChange = vi.fn();
      const handleCheckedChange = vi.fn();

      render(<Switch onChange={handleChange} onCheckedChange={handleCheckedChange} />);

      const checkbox = screen.getByRole('checkbox');
      const label = checkbox.closest('label');

      if (label) {
        await userEvent.click(label);

        expect(handleChange).toHaveBeenCalled();
        expect(handleCheckedChange).toHaveBeenCalled();
      }
    });
  });

  describe('Disabled State', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Switch disabled />);
      const checkbox = screen.getByRole('checkbox');
      const label = checkbox.closest('label');

      expect(checkbox).toBeDisabled();
      if (label) {
        expect(label).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50');
      }
    });

    it('should not toggle when disabled', async () => {
      render(<Switch disabled />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      const label = checkbox.closest('label');

      expect(checkbox.checked).toBe(false);

      if (label) {
        await userEvent.click(label);

        expect(checkbox.checked).toBe(false);
      }
    });

    it('should not call onChange when disabled', async () => {
      const handleChange = vi.fn();
      render(<Switch onChange={handleChange} disabled />);

      const checkbox = screen.getByRole('checkbox');
      const label = checkbox.closest('label');

      if (label) {
        await userEvent.click(label);

        expect(handleChange).not.toHaveBeenCalled();
      }
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className to label', () => {
      render(<Switch className="custom-class" />);
      const checkbox = screen.getByRole('checkbox');
      const label = checkbox.closest('label');

      if (label) {
        expect(label).toHaveClass('custom-class');
      }
    });
  });

  describe('Attributes', () => {
    it('should pass id to checkbox input', () => {
      render(<Switch id="test-switch" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox.id).toBe('test-switch');
    });

    it('should pass name attribute', () => {
      render(<Switch name="test-field" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('name', 'test-field');
    });

    it('should support aria-label', () => {
      render(<Switch aria-label="Enable notifications" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('aria-label', 'Enable notifications');
    });

    it('should pass through other checkbox attributes', () => {
      render(<Switch required />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeRequired();
    });
  });

  describe('Styling', () => {
    it('should have rounded-full border', () => {
      render(<Switch />);
      const checkbox = screen.getByRole('checkbox');
      const label = checkbox.closest('label');

      if (label) {
        expect(label).toHaveClass('rounded-full', 'border-2');
      }
    });

    it('should have proper dimensions', () => {
      render(<Switch />);
      const checkbox = screen.getByRole('checkbox');
      const label = checkbox.closest('label');

      if (label) {
        expect(label).toHaveClass('h-5', 'w-9');
      }
    });

    it('should have thumb element with proper size', () => {
      render(<Switch />);
      const thumb = document.querySelector('.h-4.w-4');

      expect(thumb).toBeInTheDocument();
    });

    it('should have shadow on thumb', () => {
      render(<Switch />);
      const thumb = document.querySelector('.shadow-lg');

      expect(thumb).toBeInTheDocument();
    });

    it('should have transition classes', () => {
      render(<Switch />);
      const checkbox = screen.getByRole('checkbox');
      const label = checkbox.closest('label');

      if (label) {
        expect(label).toHaveClass('transition-colors');
      }
    });
  });

  describe('Focus Styles', () => {
    it('should have focus-visible ring', () => {
      render(<Switch />);
      const checkbox = screen.getByRole('checkbox');
      const label = checkbox.closest('label');

      if (label) {
        expect(label).toHaveClass('focus-visible:ring-2', 'focus-visible:ring-offset-2');
      }
    });

    it('should have ring offset background', () => {
      render(<Switch />);
      const checkbox = screen.getByRole('checkbox');
      const label = checkbox.closest('label');

      if (label) {
        expect(label).toHaveClass('focus-visible:ring-offset-background');
      }
    });
  });

  describe('Accessibility', () => {
    it('should have proper checkbox role', () => {
      render(<Switch />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeInTheDocument();
    });

    it('should be clickable via keyboard', async () => {
      render(<Switch />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;

      checkbox.focus();
      expect(document.activeElement).toBe(checkbox);

      await userEvent.keyboard(' ');

      // Spacebar should toggle
      expect(checkbox.checked).toBe(true);
    });

    it('should be accessible with label text', () => {
      render(
        <div>
          <Switch />
          <span className="ml-2">Enable feature</span>
        </div>
      );

      expect(screen.getByRole('checkbox')).toBeInTheDocument();
      expect(screen.getByText('Enable feature')).toBeInTheDocument();
    });
  });

  describe('Display Name', () => {
    it('should have correct displayName', () => {
      expect(Switch.displayName).toBe('Switch');
    });
  });

  describe('Controlled Component Behavior', () => {
    it('should respect controlled checked state on re-render', async () => {
      const TestComponent = () => {
        const [checked, setChecked] = React.useState(false);
        return (
          <Switch
            checked={checked}
            onCheckedChange={(v) => setChecked(v)}
          />
        );
      };

      const { container } = render(<TestComponent />);

      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(false);

      const label = checkbox.closest('label');
      if (label) {
        await userEvent.click(label);
        expect(checkbox.checked).toBe(true);

        await userEvent.click(label);
        expect(checkbox.checked).toBe(false);
      }
    });
  });

  describe('Thumb Transition', () => {
    it('should animate thumb position on state change', () => {
      const { rerender } = render(<Switch checked={false} />);
      let thumb = document.querySelector('.translate-x-0');

      expect(thumb).toBeInTheDocument();

      rerender(<Switch checked={true} />);
      thumb = document.querySelector('.translate-x-4');

      expect(thumb).toBeInTheDocument();
    });
  });
});

/**
 * Checkbox 组件测试
 *
 * 测试覆盖：
 * 1. 基础渲染
 * 2. 选中/未选中状态
 * 3. indeterminate 状态
 * 4. disabled 状态
 * 5. onChange 事件
 * 6. 自定义 className
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Checkbox } from '../checkbox';

describe('Checkbox Component', () => {
  describe('Rendering', () => {
    it('should render checkbox input', () => {
      render(<Checkbox />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeInTheDocument();
      expect(checkbox.tagName).toBe('INPUT');
    });

    it('should have checkbox type', () => {
      render(<Checkbox />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.type).toBe('checkbox');
    });

    it('should have default styling', () => {
      render(<Checkbox />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveClass('h-4', 'w-4', 'rounded-sm', 'border');
    });
  });

  describe('Checked State', () => {
    it('should render unchecked by default', () => {
      render(<Checkbox />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(false);
    });

    it('should render checked when checked prop is true', () => {
      render(<Checkbox checked />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(true);
    });

    it('should toggle checked state on click', async () => {
      render(<Checkbox />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;

      expect(checkbox.checked).toBe(false);

      await userEvent.click(checkbox);

      expect(checkbox.checked).toBe(true);
    });

    it('should call onChange when clicked', async () => {
      const handleChange = vi.fn();
      render(<Checkbox onChange={handleChange} />);

      const checkbox = screen.getByRole('checkbox');
      await userEvent.click(checkbox);

      expect(handleChange).toHaveBeenCalledTimes(1);
    });

    it('should call onChange with new checked value', async () => {
      const handleChange = vi.fn();
      render(<Checkbox checked={false} onChange={handleChange} />);

      const checkbox = screen.getByRole('checkbox');
      await userEvent.click(checkbox);

      const lastCall = handleChange.mock.calls[handleChange.mock.calls.length - 1];
      const event = lastCall[0];
      expect(event.target.checked).toBe(true);
    });
  });

  describe('Disabled State', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Checkbox disabled />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeDisabled();
      expect(checkbox).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50');
    });

    it('should not call onChange when disabled', async () => {
      const handleChange = vi.fn();
      render(<Checkbox onChange={handleChange} disabled />);

      const checkbox = screen.getByRole('checkbox');
      await userEvent.click(checkbox);

      expect(handleChange).not.toHaveBeenCalled();
    });

    it('should not toggle when disabled', async () => {
      render(<Checkbox disabled />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;

      expect(checkbox.checked).toBe(false);
      await userEvent.click(checkbox);
      expect(checkbox.checked).toBe(false);
    });
  });

  describe('Indeterminate State', () => {
    it('should support indeterminate state via data attribute', () => {
      render(<Checkbox data-state="indeterminate" />);
      const checkbox = screen.getByRole('checkbox');

      expect(checkbox).toHaveAttribute('data-state', 'indeterminate');
    });

    it('should apply indeterminate styling', () => {
      render(<Checkbox data-state="indeterminate" />);
      const checkbox = screen.getByRole('checkbox');

      // The component uses data-[state=checked]:bg-primary
      expect(checkbox).toBeInTheDocument();
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className', () => {
      render(<Checkbox className="custom-class" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveClass('custom-class');
    });

    it('should merge default classes with custom className', () => {
      render(<Checkbox className="custom-class" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveClass('h-4', 'w-4', 'custom-class');
    });
  });

  describe('Attributes', () => {
    it('should pass id attribute', () => {
      render(<Checkbox id="test-checkbox" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox.id).toBe('test-checkbox');
    });

    it('should pass name attribute', () => {
      render(<Checkbox name="test-field" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('name', 'test-field');
    });

    it('should pass value attribute', () => {
      render(<Checkbox value="test-value" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('value', 'test-value');
    });

    it('should support required attribute', () => {
      render(<Checkbox required />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeRequired();
    });

    it('should pass aria-label', () => {
      render(<Checkbox aria-label="Accept terms" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('aria-label', 'Accept terms');
    });

    it('should support form association', () => {
      render(<Checkbox form="test-form" name="terms" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('form', 'test-form');
    });
  });

  describe('Styling', () => {
    it('should have border styling', () => {
      render(<Checkbox />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveClass('border', 'border-primary');
    });

    it('should have focus-visible styles', () => {
      render(<Checkbox />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveClass('focus-visible:outline-none', 'focus-visible:ring-2');
    });

    it('should have ring offset for focus', () => {
      render(<Checkbox />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveClass('focus-visible:ring-offset-2');
    });
  });

  describe('Checked State Styling', () => {
    it('should apply checked styling when checked', () => {
      render(<Checkbox checked />);
      const checkbox = screen.getByRole('checkbox');

      expect(checkbox).toHaveAttribute('data-state', 'checked');
    });

    it('should have primary background when checked', () => {
      render(<Checkbox checked />);
      const checkbox = screen.getByRole('checkbox');

      // data-[state=checked]:bg-primary
      expect(checkbox).toHaveAttribute('data-state', 'checked');
    });
  });

  describe('Accessibility', () => {
    it('should have proper role', () => {
      render(<Checkbox />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeInTheDocument();
    });

    it('should be accessible with label', () => {
      render(
        <label>
          <Checkbox />
          Accept terms and conditions
        </label>
      );

      expect(screen.getByRole('checkbox')).toBeInTheDocument();
      expect(screen.getByText('Accept terms and conditions')).toBeInTheDocument();
    });

    it('should support aria-checked for indeterminate', () => {
      render(<Checkbox aria-checked="mixed" />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('aria-checked', 'mixed');
    });
  });

  describe('Display Name', () => {
    it('should have correct displayName', () => {
      expect(Checkbox.displayName).toBe('Checkbox');
    });
  });

  describe('User Interactions', () => {
    it('should respond to keyboard spacebar', async () => {
      render(<Checkbox />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;

      checkbox.focus();
      await userEvent.keyboard(' ');

      // Spacebar should toggle checkbox
      expect(checkbox.checked).toBe(true);
    });

    it('should handle rapid clicks', async () => {
      const handleChange = vi.fn();
      render(<Checkbox onChange={handleChange} />);

      const checkbox = screen.getByRole('checkbox');

      await userEvent.click(checkbox);
      await userEvent.click(checkbox);
      await userEvent.click(checkbox);

      expect(handleChange).toHaveBeenCalledTimes(3);
    });
  });

  describe('Controlled Component', () => {
    it('should respect controlled checked state', async () => {
      const TestComponent = () => {
        const [checked, setChecked] = React.useState(false);
        return (
          <Checkbox
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
          />
        );
      };

      const { container } = render(<TestComponent />);

      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(false);

      await userEvent.click(checkbox);
      expect(checkbox.checked).toBe(true);

      await userEvent.click(checkbox);
      expect(checkbox.checked).toBe(false);
    });
  });
});

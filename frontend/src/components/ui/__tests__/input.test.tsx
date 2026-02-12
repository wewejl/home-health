/**
 * Input 组件测试
 *
 * 测试覆盖：
 * 1. 基础渲染
 * 2. 输入类型 (text, password, email, number, etc.)
 * 3. 验证状态样式
 * 4. disabled 状态
 * 5. placeholder
 * 6. 值变化事件
 * 7. 自定义 className
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Input } from '../input';

describe('Input Component', () => {
  describe('Rendering', () => {
    it('should render input element', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
      expect(input.tagName).toBe('INPUT');
    });

    it('should render with default type="text"', () => {
      render(<Input />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.type).toBe('text');
    });
  });

  describe('Input Types', () => {
    it('should render password input', () => {
      render(<Input type="password" />);
      const input = screen.getByDisplayValue('') as HTMLInputElement;
      expect(input.type).toBe('password');
    });

    it('should render email input', () => {
      render(<Input type="email" />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.type).toBe('email');
    });

    it('should render number input', () => {
      render(<Input type="number" />);
      const input = screen.getByRole('spinbutton') as HTMLInputElement;
      expect(input.type).toBe('number');
    });

    it('should render tel input', () => {
      render(<Input type="tel" />);
      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.type).toBe('tel');
    });

    it('should render date input', () => {
      render(<Input type="date" />);
      const input = screen.getByRole('textbox') as HTMLInputElement; // date inputs may have different role
      expect(input).toBeInTheDocument();
    });
  });

  describe('Value Handling', () => {
    it('should render with default value', () => {
      render(<Input defaultValue="default value" />);
      const input = screen.getByDisplayValue('default value') as HTMLInputElement;
      expect(input.value).toBe('default value');
    });

    it('should render with controlled value', () => {
      render(<Input value="controlled value" readOnly />);
      const input = screen.getByDisplayValue('controlled value');
      expect(input).toBeInTheDocument();
    });

    it('should call onChange when value changes', async () => {
      const handleChange = vi.fn();
      render(<Input onChange={handleChange} />);

      const input = screen.getByRole('textbox');
      await userEvent.type(input, 'test');

      expect(handleChange).toHaveBeenCalled();
    });

    it('should update value on user input', async () => {
      render(<Input />);

      const input = screen.getByRole('textbox') as HTMLInputElement;
      await userEvent.type(input, 'hello');

      expect(input.value).toBe('hello');
    });
  });

  describe('Placeholder', () => {
    it('should render with placeholder', () => {
      render(<Input placeholder="Enter text" />);
      const input = screen.getByPlaceholderText('Enter text');
      expect(input).toBeInTheDocument();
    });

    it('should show placeholder when empty', () => {
      render(<Input placeholder="Search..." />);
      const input = screen.getByPlaceholderText('Search...') as HTMLInputElement;
      expect(input.value).toBe('');
    });
  });

  describe('States', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Input disabled />);
      const input = screen.getByRole('textbox');
      expect(input).toBeDisabled();
      expect(input).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50');
    });

    it('should be readonly when readOnly prop is true', () => {
      render(<Input readOnly />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('readonly');
    });

    it('should apply focus styles', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('focus-visible:ring-1');
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className', () => {
      render(<Input className="custom-class" />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('custom-class');
    });

    it('should merge default classes with custom className', () => {
      render(<Input className="custom-class" />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('h-9', 'w-full', 'custom-class');
    });
  });

  describe('Attributes', () => {
    it('should pass id attribute', () => {
      render(<Input id="test-input" />);
      const input = screen.getByRole('textbox');
      expect(input.id).toBe('test-input');
    });

    it('should pass name attribute', () => {
      render(<Input name="test-field" />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('name', 'test-field');
    });

    it('should pass aria-label', () => {
      render(<Input aria-label="Search input" />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-label', 'Search input');
    });

    it('should support required attribute', () => {
      render(<Input required />);
      const input = screen.getByRole('textbox');
      expect(input).toBeRequired();
    });

    it('should support min and max for number input', () => {
      render(<Input type="number" min={0} max={100} />);
      const input = screen.getByRole('spinbutton');
      expect(input).toHaveAttribute('min', '0');
      expect(input).toHaveAttribute('max', '100');
    });
  });

  describe('Styles', () => {
    it('should have default input styles', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('rounded-sm', 'border', 'border-input');
    });

    it('should have shadow styling', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('shadow-sm');
    });

    it('should have proper text size', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('text-sm');
    });
  });

  describe('File Input', () => {
    it('should render file input', () => {
      render(<Input type="file" />);
      const input = screen.getByRole('textbox') || screen.getByLabelText(/upload/i);
      expect(document.querySelector('input[type="file"]')).toBeInTheDocument();
    });

    it('should apply file input specific styles', () => {
      render(<Input type="file" />);
      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      expect(input).toHaveClass('file:border-0');
    });
  });

  describe('Accessibility', () => {
    it('should have proper role for text input', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('should be accessible with label association', () => {
      render(
        <label htmlFor="test-input">
          Label
          <Input id="test-input" />
        </label>
      );
      const input = screen.getByRole('textbox');
      expect(input.id).toBe('test-input');
    });
  });
});

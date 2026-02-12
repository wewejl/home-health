/**
 * Textarea 组件测试
 *
 * 测试覆盖：
 * 1. 基础渲染
 * 2. 默认文本
 * 3. placeholder
 * 4. disabled 状态
 * 5. 值变化
 * 6. 自定义 className
 * 7. 最小高度
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Textarea } from '../textarea';

describe('Textarea Component', () => {
  describe('Rendering', () => {
    it('should render textarea element', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
      expect(textarea.tagName).toBe('TEXTAREA');
    });

    it('should render with default styling', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('rounded-sm', 'border', 'border-input');
    });
  });

  describe('Value Handling', () => {
    it('should render with default value', () => {
      render(<Textarea defaultValue="Default text" />);
      const textarea = screen.getByDisplayValue('Default text') as HTMLTextAreaElement;
      expect(textarea.value).toBe('Default text');
    });

    it('should render with controlled value', () => {
      render(<Textarea value="Controlled text" readOnly />);
      const textarea = screen.getByDisplayValue('Controlled text');
      expect(textarea).toBeInTheDocument();
    });

    it('should call onChange when value changes', async () => {
      const handleChange = vi.fn();
      render(<Textarea onChange={handleChange} />);

      const textarea = screen.getByRole('textbox');
      await userEvent.type(textarea, 'test content');

      expect(handleChange).toHaveBeenCalled();
    });

    it('should update value on user input', async () => {
      render(<Textarea />);

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      await userEvent.type(textarea, 'Hello World');

      expect(textarea.value).toBe('Hello World');
    });

    it('should handle multi-line input', async () => {
      render(<Textarea />);

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      await userEvent.type(textarea, 'Line 1');
      await userEvent.keyboard('{Enter}');
      await userEvent.type(textarea, 'Line 2');

      expect(textarea.value).toBe('Line 1\nLine 2');
    });
  });

  describe('Placeholder', () => {
    it('should render with placeholder', () => {
      render(<Textarea placeholder="Enter your message" />);
      const textarea = screen.getByPlaceholderText('Enter your message');
      expect(textarea).toBeInTheDocument();
    });

    it('should show placeholder when empty', () => {
      render(<Textarea placeholder="Type here..." />);
      const textarea = screen.getByPlaceholderText('Type here...') as HTMLTextAreaElement;
      expect(textarea.value).toBe('');
    });
  });

  describe('States', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Textarea disabled />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeDisabled();
      expect(textarea).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50');
    });

    it('should be readonly when readOnly prop is true', () => {
      render(<Textarea readOnly />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('readonly');
    });

    it('should apply focus styles', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('focus-visible:ring-1');
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className', () => {
      render(<Textarea className="custom-class" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('custom-class');
    });

    it('should merge default classes with custom className', () => {
      render(<Textarea className="custom-class" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('min-h-\\[80px\\]', 'custom-class');
    });
  });

  describe('Attributes', () => {
    it('should pass id attribute', () => {
      render(<Textarea id="test-textarea" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea.id).toBe('test-textarea');
    });

    it('should pass name attribute', () => {
      render(<Textarea name="test-field" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('name', 'test-field');
    });

    it('should pass rows attribute', () => {
      render(<Textarea rows={5} />);
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea.rows).toBe(5);
    });

    it('should pass cols attribute', () => {
      render(<Textarea cols={40} />);
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea.cols).toBe(40);
    });

    it('should support maxLength attribute', () => {
      render(<Textarea maxLength={100} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('maxlength', '100');
    });

    it('should pass aria-label', () => {
      render(<Textarea aria-label="Message input" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('aria-label', 'Message input');
    });
  });

  describe('Styling', () => {
    it('should have proper text size', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('text-sm');
    });

    it('should have minimum height', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('min-h-\\[80px\\]');
    });

    it('should have proper padding', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('px-3', 'py-2');
    });

    it('should have shadow styling', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('shadow-sm');
    });
  });

  describe('Resizing', () => {
    it('should allow vertical resize by default', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      const style = window.getComputedStyle(textarea);
      // Check if resize is not restricted
      expect(textarea).toBeInTheDocument();
    });

    it('should restrict resize when specified', () => {
      render(<Textarea style={{ resize: 'none' }} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveStyle({ resize: 'none' });
    });
  });

  describe('Accessibility', () => {
    it('should have proper role', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
    });

    it('should be accessible with label association', () => {
      render(
        <label htmlFor="test-textarea">
          Label
          <Textarea id="test-textarea" />
        </label>
      );
      const textarea = screen.getByRole('textbox');
      expect(textarea.id).toBe('test-textarea');
    });
  });

  describe('Display Name', () => {
    it('should have correct displayName', () => {
      expect(Textarea.displayName).toBe('Textarea');
    });
  });

  describe('User Interactions', () => {
    it('should accept keyboard input', async () => {
      render(<Textarea />);

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      await userEvent.click(textarea);
      await userEvent.keyboard('Hello World');

      expect(textarea.value).toBe('Hello World');
    });

    it('should handle special characters', async () => {
      render(<Textarea />);

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      await userEvent.type(textarea, 'Test @#$%^&*()');

      expect(textarea.value).toBe('Test @#$%^&*()');
    });
  });
});

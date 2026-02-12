/**
 * Button 组件测试
 *
 * 测试覆盖：
 * 1. variants (default, destructive, outline, secondary, ghost, link)
 * 2. sizes (default, sm, lg, icon)
 * 3. disabled 状态
 * 4. asChild 属性
 * 5. 点击事件
 * 6. 自定义 className
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '../button';

describe('Button Component', () => {
  describe('Variants', () => {
    it('should render default variant', () => {
      render(<Button>Default Button</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-primary');
    });

    it('should render destructive variant', () => {
      render(<Button variant="destructive">Destructive</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-danger');
    });

    it('should render outline variant', () => {
      render(<Button variant="outline">Outline</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('border', 'border-border');
    });

    it('should render secondary variant', () => {
      render(<Button variant="secondary">Secondary</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-secondary');
    });

    it('should render ghost variant', () => {
      render(<Button variant="ghost">Ghost</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('hover:bg-accent');
    });

    it('should render link variant', () => {
      render(<Button variant="link">Link</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('text-primary', 'underline-offset-4');
    });
  });

  describe('Sizes', () => {
    it('should render default size', () => {
      render(<Button size="default">Default</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-9', 'px-4');
    });

    it('should render sm size', () => {
      render(<Button size="sm">Small</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-8', 'px-3');
    });

    it('should render lg size', () => {
      render(<Button size="lg">Large</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-10', 'px-8');
    });

    it('should render icon size', () => {
      render(<Button size="icon">Icon</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-9', 'w-9');
    });
  });

  describe('States', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(button).toHaveClass('disabled:opacity-50', 'disabled:pointer-events-none');
    });

    it('should not be disabled by default', () => {
      render(<Button>Enabled</Button>);
      const button = screen.getByRole('button');
      expect(button).not.toBeDisabled();
    });
  });

  describe('Events', () => {
    it('should call onClick handler when clicked', async () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Click me</Button>);

      const button = screen.getByRole('button');
      await userEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should not call onClick when disabled', async () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick} disabled>Disabled</Button>);

      const button = screen.getByRole('button');
      await userEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className', () => {
      render(<Button className="custom-class">Custom</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class');
    });

    it('should merge variant classes with custom className', () => {
      render(<Button variant="destructive" className="custom-class">Mixed</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-danger');
      expect(button).toHaveClass('custom-class');
    });
  });

  describe('asChild Prop', () => {
    it('should render as child element when asChild is true', () => {
      render(
        <Button asChild>
          <a href="/test">Link Button</a>
        </Button>
      );

      const link = screen.getByRole('link');
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '/test');
    });

    it('should render as button when asChild is false', () => {
      render(<Button asChild={false}>Button</Button>);
      const button = screen.getByRole('button');
      expect(button.tagName).toBe('BUTTON');
    });
  });

  describe('Accessibility', () => {
    it('should have proper button role', () => {
      render(<Button>Accessible</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('should support focus-visible styles', () => {
      render(<Button>Focus Test</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('focus-visible:ring-2');
    });
  });

  describe('Content', () => {
    it('should render text content', () => {
      render(<Button>Text Content</Button>);
      expect(screen.getByText('Text Content')).toBeInTheDocument();
    });

    it('should render children elements', () => {
      render(
        <Button>
          <span data-testid="child-span">Child Element</span>
        </Button>
      );
      expect(screen.getByTestId('child-span')).toBeInTheDocument();
    });

    it('should render with icon and text', () => {
      render(
        <Button>
          <svg data-testid="test-icon" />
          <span>Button with Icon</span>
        </Button>
      );
      expect(screen.getByTestId('test-icon')).toBeInTheDocument();
      expect(screen.getByText('Button with Icon')).toBeInTheDocument();
    });
  });
});

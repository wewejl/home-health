/**
 * Alert 组件测试
 *
 * 测试覆盖：
 * 1. Alert 基础渲染
 * 2. variants (default, destructive, warning, success, info)
 * 3. AlertTitle, AlertDescription
 * 4. onClose 关闭按钮
 * 5. icon 图标支持
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  Alert,
  AlertTitle,
  AlertDescription,
} from '../alert';

describe('Alert Components', () => {
  describe('Alert - Variants', () => {
    it('should render default variant', () => {
      render(<Alert>Default Alert</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('bg-background', 'text-foreground');
    });

    it('should render destructive variant', () => {
      render(<Alert variant="destructive">Error Alert</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('border-danger\\/50', 'text-danger');
    });

    it('should render warning variant', () => {
      render(<Alert variant="warning">Warning Alert</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('border-warning\\/50', 'text-warning');
    });

    it('should render success variant', () => {
      render(<Alert variant="success">Success Alert</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('border-success\\/50', 'text-success');
    });

    it('should render info variant', () => {
      render(<Alert variant="info">Info Alert</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('border-info\\/50', 'text-info');
    });
  });

  describe('Alert - Structure', () => {
    it('should render with proper styling', () => {
      render(<Alert>Alert Content</Alert>);
      const alert = screen.getByRole('alert');

      expect(alert).toHaveClass('relative', 'w-full', 'rounded-lg', 'border');
    });

    it('should have flex layout for content', () => {
      render(<Alert>Content</Alert>);
      const flexContainer = screen.getByText('Content').parentElement?.parentElement;

      expect(flexContainer).toHaveClass('flex', 'items-start', 'justify-between');
    });
  });

  describe('Alert - onClose', () => {
    it('should not render close button when onClose is not provided', () => {
      render(<Alert>Alert without close</Alert>);
      const closeButton = screen.queryByRole('button');
      expect(closeButton).not.toBeInTheDocument();
    });

    it('should render close button when onClose is provided', () => {
      const handleClose = vi.fn();
      render(<Alert onClose={handleClose}>Alert with close</Alert>);

      const closeButton = screen.getByRole('button');
      expect(closeButton).toBeInTheDocument();
    });

    it('should call onClose when close button is clicked', async () => {
      const handleClose = vi.fn();
      render(<Alert onClose={handleClose}>Closable Alert</Alert>);

      const closeButton = screen.getByRole('button');
      await userEvent.click(closeButton);

      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('should have opacity transition on close button', () => {
      const handleClose = vi.fn();
      render(<Alert onClose={handleClose}>Alert</Alert>);

      const closeButton = screen.getByRole('button');
      expect(closeButton).toHaveClass('opacity-70', 'hover:opacity-100');
    });
  });

  describe('Alert - Icon', () => {
    it('should render icon when provided', () => {
      const icon = <svg data-testid="test-icon" />;
      render(<Alert icon={icon}>Alert with Icon</Alert>);

      expect(screen.getByTestId('test-icon')).toBeInTheDocument();
    });

    it('should position icon absolutely', () => {
      const icon = <div data-testid="test-icon">Icon</div>;
      render(<Alert icon={icon}>Content</Alert>);

      const renderedIcon = screen.getByTestId('test-icon');
      expect(renderedIcon.parentElement).toHaveClass('absolute', 'left-4');
    });
  });

  describe('AlertTitle', () => {
    it('should render title as h5 element', () => {
      render(
        <Alert>
          <AlertTitle>Alert Title</AlertTitle>
        </Alert>
      );

      const title = screen.getByText('Alert Title');
      expect(title.tagName).toBe('H5');
    });

    it('should have proper styling', () => {
      render(
        <Alert>
          <AlertTitle>Title</AlertTitle>
        </Alert>
      );

      const title = screen.getByText('Title');
      expect(title).toHaveClass('mb-1', 'font-medium');
    });

    it('should have tight tracking', () => {
      render(
        <Alert>
          <AlertTitle>Tight Title</AlertTitle>
        </Alert>
      );

      const title = screen.getByText('Tight Title');
      expect(title).toHaveClass('tracking-tight');
    });

    it('should apply custom className', () => {
      render(
        <Alert>
          <AlertTitle className="custom-title">Custom</AlertTitle>
        </Alert>
      );

      const title = screen.getByText('Custom');
      expect(title).toHaveClass('custom-title');
    });
  });

  describe('AlertDescription', () => {
    it('should render description', () => {
      render(
        <Alert>
          <AlertDescription>Description text</AlertDescription>
        </Alert>
      );

      expect(screen.getByText('Description text')).toBeInTheDocument();
    });

    it('should apply text styling', () => {
      render(
        <Alert>
          <AlertDescription>Description</AlertDescription>
        </Alert>
      );

      const description = screen.getByText('Description');
      expect(description).toHaveClass('text-sm');
    });

    it('should apply paragraph leading', () => {
      render(
        <Alert>
          <AlertDescription>
            <p>Paragraph text</p>
          </AlertDescription>
        </Alert>
      );

      const p = screen.getByText('Paragraph text');
      expect(p.parentElement).toHaveClass('[&_p]:leading-relaxed');
    });

    it('should apply custom className', () => {
      render(
        <Alert>
          <AlertDescription className="custom-desc">Custom</AlertDescription>
        </Alert>
      );

      const description = screen.getByText('Custom');
      expect(description).toHaveClass('custom-desc');
    });
  });

  describe('Complete Alert Structure', () => {
    it('should render complete alert with title and description', () => {
      render(
        <Alert variant="success">
          <AlertTitle>Success!</AlertTitle>
          <AlertDescription>Your changes have been saved.</AlertDescription>
        </Alert>
      );

      expect(screen.getByText('Success!')).toBeInTheDocument();
      expect(screen.getByText('Your changes have been saved.')).toBeInTheDocument();
    });

    it('should render closable alert with all components', () => {
      const handleClose = vi.fn();
      render(
        <Alert variant="warning" onClose={handleClose}>
          <AlertTitle>Warning</AlertTitle>
          <AlertDescription>This is a warning message.</AlertDescription>
        </Alert>
      );

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText('Warning')).toBeInTheDocument();
      expect(screen.getByText('This is a warning message.')).toBeInTheDocument();
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  });

  describe('Display Names', () => {
    it('Alert should have correct displayName', () => {
      expect(Alert.displayName).toBe('Alert');
    });

    it('AlertTitle should have correct displayName', () => {
      expect(AlertTitle.displayName).toBe('AlertTitle');
    });

    it('AlertDescription should have correct displayName', () => {
      expect(AlertDescription.displayName).toBe('AlertDescription');
    });
  });

  describe('Accessibility', () => {
    it('should have alert role', () => {
      render(<Alert>Important message</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
    });

    it('should be accessible with proper semantics', () => {
      render(
        <Alert>
          <AlertTitle>Important</AlertTitle>
          <AlertDescription>Please read this carefully.</AlertDescription>
        </Alert>
      );

      const alert = screen.getByRole('alert');
      expect(Alert).toBeInTheDocument();
    });
  });

  describe('Custom Classes', () => {
    it('should apply custom className to Alert', () => {
      render(<Alert className="custom-alert">Content</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('custom-alert');
    });

    it('should merge variant classes with custom className', () => {
      render(
        <Alert variant="success" className="custom-class">
          Success Message
        </Alert>
      );

      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('border-success\\/50');
      expect(alert).toHaveClass('custom-class');
    });
  });

  describe('Icon Positioning', () => {
    it('should reserve space for icon', () => {
      const icon = <div data-testid="icon">!</div>;
      render(
        <Alert icon={icon}>
          <AlertTitle>Title</AlertTitle>
          <AlertDescription>Description with icon spacing</AlertDescription>
        </Alert>
      );

      const content = screen.getByText('Description with icon spacing');
      const contentParent = content.parentElement?.parentElement;

      // Should have pl-7 when icon is present
      expect(contentParent).toHaveClass('pl-7');
    });

    it('should position icon at top left', () => {
      const icon = <div data-testid="icon">@</div>;
      render(<Alert icon={icon}>Alert message</Alert>);

      const renderedIcon = screen.getByTestId('icon');
      expect(renderedIcon.parentElement).toHaveClass('absolute', 'left-4', 'top-4');
    });
  });

  describe('Border Styles', () => {
    it('should have border based on variant', () => {
      render(<Alert variant="destructive">Error</Alert>);
      const alert = screen.getByRole('alert');

      expect(alert).toHaveClass('border');
      expect(alert).toHaveClass('border-danger\\/50');
    });

    it('should have rounded corners', () => {
      render(<Alert>Rounded Alert</Alert>);
      const alert = screen.getByRole('alert');

      expect(alert).toHaveClass('rounded-lg');
    });
  });
});

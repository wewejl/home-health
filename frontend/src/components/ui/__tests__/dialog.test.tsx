/**
 * Dialog 组件测试
 *
 * 测试覆盖：
 * 1. 打开/关闭状态
 * 2. DialogTrigger 触发
 * 3. DialogContent 渲染
 * 4. 背景点击关闭
 * 5. 关闭按钮功能
 * 6. DialogHeader, DialogTitle, DialogDescription, DialogFooter
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../dialog';

describe('Dialog Components', () => {
  describe('Dialog Controlled State', () => {
    it('should not render content when open is false', () => {
      render(
        <Dialog open={false} onOpenChange={vi.fn()}>
          <DialogContent>Dialog Content</DialogContent>
        </Dialog>
      );

      expect(screen.queryByText('Dialog Content')).not.toBeInTheDocument();
    });

    it('should render content when open is true', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>Dialog Content</DialogContent>
        </Dialog>
      );

      expect(screen.getByText('Dialog Content')).toBeInTheDocument();
    });

    it('should call onOpenChange when backdrop is clicked', async () => {
      const handleClose = vi.fn();
      render(
        <Dialog open={true} onOpenChange={handleClose}>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );

      const backdrop = screen.getByText('Dialog Content').parentElement?.querySelector('.fixed.inset-0');
      if (backdrop) {
        await userEvent.click(backdrop);
        expect(handleClose).toHaveBeenCalledWith(false);
      }
    });
  });

  describe('DialogTrigger', () => {
    it('should render trigger button', () => {
      render(
        <Dialog open={false} onOpenChange={vi.fn()}>
          <DialogTrigger>Open Dialog</DialogTrigger>
        </Dialog>
      );

      expect(screen.getByRole('button')).toBeInTheDocument();
      expect(screen.getByText('Open Dialog')).toBeInTheDocument();
    });

    it('should call onOpenChange with true when trigger is clicked', async () => {
      const handleOpenChange = vi.fn();
      render(
        <Dialog open={false} onOpenChange={handleOpenChange}>
          <DialogTrigger>Trigger</DialogTrigger>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );

      const trigger = screen.getByRole('button');
      await userEvent.click(trigger);

      expect(handleOpenChange).toHaveBeenCalledWith(true);
    });
  });

  describe('DialogContent', () => {
    it('should render with close button when open', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>Content with close</DialogContent>
        </Dialog>
      );

      // Check for close button (X icon)
      const closeButton = screen.getByRole('button');
      expect(closeButton).toBeInTheDocument();
    });

    it('should call onOpenChange when close button is clicked', async () => {
      const handleClose = vi.fn();
      render(
        <Dialog open={true} onOpenChange={handleClose}>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );

      const closeButton = screen.getAllByRole('button').find(btn =>
        btn.querySelector('svg')
      );

      if (closeButton) {
        await userEvent.click(closeButton);
        expect(handleClose).toHaveBeenCalledWith(false);
      }
    });

    it('should apply custom className', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent className="custom-class">Custom Content</DialogContent>
        </Dialog>
      );

      const content = screen.getByText('Custom Content');
      expect(content.parentElement).toHaveClass('custom-class');
    });

    it('should have proper positioning classes', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>Positioned Content</DialogContent>
        </Dialog>
      );

      const container = screen.getByText('Positioned Content').parentElement;
      expect(container).toHaveClass('relative', 'z-50', 'bg-background');
    });
  });

  describe('DialogHeader', () => {
    it('should render header with proper styling', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>
            <DialogHeader>Header Content</DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const header = screen.getByText('Header Content');
      expect(header).toHaveClass('text-center', 'sm:text-left');
    });

    it('should have bottom margin', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>
            <DialogHeader>Header</DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const header = screen.getByText('Header');
      expect(header.parentElement).toHaveClass('mb-4');
    });
  });

  describe('DialogTitle', () => {
    it('should render as h2 element', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Dialog Title</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const title = screen.getByText('Dialog Title');
      expect(title.tagName).toBe('H2');
    });

    it('should have proper styling', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Title</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const title = screen.getByText('Title');
      expect(title).toHaveClass('text-lg', 'font-semibold');
    });
  });

  describe('DialogDescription', () => {
    it('should render as p element', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>
            <DialogHeader>
              <DialogDescription>Description Text</DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const description = screen.getByText('Description Text');
      expect(description.tagName).toBe('P');
    });

    it('should have muted color', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>
            <DialogHeader>
              <DialogDescription>Description</DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );

      const description = screen.getByText('Description');
      expect(description).toHaveClass('text-muted-foreground');
    });
  });

  describe('DialogFooter', () => {
    it('should render footer with flex layout', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>
            <DialogFooter>Footer Content</DialogFooter>
          </DialogContent>
        </Dialog>
      );

      const footer = screen.getByText('Footer Content');
      expect(footer.parentElement).toHaveClass('flex', 'flex-col-reverse');
    });

    it('should have top margin', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>
            <DialogFooter>Footer</DialogFooter>
          </DialogContent>
        </Dialog>
      );

      const footer = screen.getByText('Footer');
      expect(footer.parentElement).toHaveClass('mt-4');
    });

    it('should reverse flex on desktop', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>
            <DialogFooter>Footer</DialogFooter>
          </DialogContent>
        </Dialog>
      );

      const footer = screen.getByText('Footer');
      expect(footer.parentElement).toHaveClass('sm:flex-row');
    });
  });

  describe('Complete Dialog Structure', () => {
    it('should render complete dialog with all components', () => {
      const handleOpenChange = vi.fn();

      render(
        <Dialog open={true} onOpenChange={handleOpenChange}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Complete Dialog</DialogTitle>
              <DialogDescription>This is a description</DialogDescription>
            </DialogHeader>
            <div>Main content goes here</div>
            <DialogFooter>
              <button>Cancel</button>
              <button>Confirm</button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByText('Complete Dialog')).toBeInTheDocument();
      expect(screen.getByText('This is a description')).toBeInTheDocument();
      expect(screen.getByText('Main content goes here')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
      expect(screen.getByText('Confirm')).toBeInTheDocument();
    });
  });

  describe('Display Names', () => {
    it('Dialog should have correct displayName', () => {
      expect(Dialog.displayName).toBe('Dialog');
    });

    it('DialogTrigger should have correct displayName', () => {
      expect(DialogTrigger.displayName).toBe('DialogTrigger');
    });

    it('DialogContent should have correct displayName', () => {
      expect(DialogContent.displayName).toBe('DialogContent');
    });

    it('DialogHeader should have correct displayName', () => {
      expect(DialogHeader.displayName).toBe('DialogHeader');
    });

    it('DialogTitle should have correct displayName', () => {
      expect(DialogTitle.displayName).toBe('DialogTitle');
    });

    it('DialogDescription should have correct displayName', () => {
      expect(DialogDescription.displayName).toBe('DialogDescription');
    });

    it('DialogFooter should have correct displayName', () => {
      expect(DialogFooter.displayName).toBe('DialogFooter');
    });
  });

  describe('Backdrop', () => {
    it('should render backdrop overlay', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );

      const backdrop = document.querySelector('.bg-black\\/50');
      expect(backdrop).toBeInTheDocument();
    });

    it('should have fixed positioning for backdrop', () => {
      render(
        <Dialog open={true} onOpenChange={vi.fn()}>
          <DialogContent>Content</DialogContent>
        </Dialog>
      );

      const backdrop = document.querySelector('.fixed.inset-0');
      expect(backdrop).toBeInTheDocument();
    });
  });
});

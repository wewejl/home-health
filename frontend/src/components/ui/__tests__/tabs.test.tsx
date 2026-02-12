/**
 * Tabs 组件测试
 *
 * 测试覆盖：
 * 1. Tabs 基础渲染
 * 2. TabsList 容器
 * 3. TabsTrigger 标签触发
 * 4. TabsContent 内容面板
 * 5. 受控/非受控模式
 * 6. 标签切换
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '../tabs';

describe('Tabs Components', () => {
  describe('Tabs - Uncontrolled Mode', () => {
    it('should render with default value', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      );

      expect(screen.getByText('Content 1')).toBeInTheDocument();
      expect(screen.queryByText('Content 2')).not.toBeInTheDocument();
    });

    it('should switch content when trigger is clicked', async () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      );

      expect(screen.getByText('Content 1')).toBeInTheDocument();

      const tab2 = screen.getByText('Tab 2');
      await userEvent.click(tab2);

      expect(screen.queryByText('Content 1')).not.toBeInTheDocument();
      expect(screen.getByText('Content 2')).toBeInTheDocument();
    });
  });

  describe('Tabs - Controlled Mode', () => {
    it('should use controlled value', () => {
      const handleChange = vi.fn();
      render(
        <Tabs value="tab1" onValueChange={handleChange}>
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
        </Tabs>
      );

      expect(screen.getByText('Content 1')).toBeInTheDocument();
    });

    it('should call onValueChange when trigger is clicked', async () => {
      const handleChange = vi.fn();
      render(
        <Tabs value="tab1" onValueChange={handleChange}>
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      );

      const tab2 = screen.getByText('Tab 2');
      await userEvent.click(tab2);

      expect(handleChange).toHaveBeenCalledWith('tab2');
    });
  });

  describe('TabsList', () => {
    it('should render list container', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const list = screen.getByText('Tab 1').parentElement;
      expect(list).toBeInTheDocument();
    });

    it('should apply proper styling', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab</TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const list = screen.getByText('Tab').parentElement;
      expect(list).toHaveClass('inline-flex', 'h-10', 'items-center', 'justify-center');
    });

    it('should have background and border', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab</TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const list = screen.getByText('Tab').parentElement;
      expect(list).toHaveClass('bg-secondary', 'border', 'border-border');
    });

    it('should apply custom className', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList className="custom-list">
            <TabsTrigger value="tab1">Tab</TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const list = screen.getByText('Tab').parentElement;
      expect(list).toHaveClass('custom-list');
    });
  });

  describe('TabsTrigger', () => {
    it('should render button element', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Trigger</TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const trigger = screen.getByRole('button');
      expect(trigger).toBeInTheDocument();
    });

    it('should apply active styling when selected', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Active Tab</TabsTrigger>
            <TabsTrigger value="tab2">Inactive Tab</TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const activeTab = screen.getByText('Active Tab');
      const inactiveTab = screen.getByText('Inactive Tab');

      expect(activeTab).toHaveClass('bg-surface', 'text-foreground');
      expect(inactiveTab).not.toHaveClass('bg-surface');
    });

    it('should apply inactive styling when not selected', () => {
      render(
        <Tabs defaultValue="tab2">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const tab1 = screen.getByText('Tab 1');
      const tab2 = screen.getByText('Tab 2');

      expect(tab1).toHaveClass('text-foreground-secondary', 'hover:text-foreground');
      expect(tab2).toHaveClass('bg-surface', 'text-foreground');
    });

    it('should have hover effect', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Hover Tab</TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const tab = screen.getByText('Hover Tab');
      expect(tab).toHaveClass('hover:bg-surface-alt\\/50');
    });

    it('should apply custom className', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1" className="custom-trigger">
              Custom Tab
            </TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const trigger = screen.getByText('Custom Tab');
      expect(trigger).toHaveClass('custom-trigger');
    });
  });

  describe('TabsContent', () => {
    it('should render content when value matches', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsContent value="tab1">Visible Content</TabsContent>
          <TabsContent value="tab2">Hidden Content</TabsContent>
        </Tabs>
      );

      expect(screen.getByText('Visible Content')).toBeInTheDocument();
      expect(screen.queryByText('Hidden Content')).not.toBeInTheDocument();
    });

    it('should return null when value does not match', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsContent value="tab2">Not Visible</TabsContent>
        </Tabs>
      );

      expect(screen.queryByText('Not Visible')).not.toBeInTheDocument();
    });

    it('should apply proper spacing', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsContent value="tab1">Content with margin</TabsContent>
        </Tabs>
      );

      const content = screen.getByText('Content with margin');
      expect(content).toHaveClass('mt-0');
    });

    it('should apply custom className', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsContent value="tab1" className="custom-content">
            Custom Content
          </TabsContent>
        </Tabs>
      );

      const content = screen.getByText('Custom Content');
      expect(content).toHaveClass('custom-content');
    });
  });

  describe('Tab Switching Behavior', () => {
    it('should switch between multiple tabs correctly', async () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
            <TabsTrigger value="tab3">Tab 3</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
          <TabsContent value="tab3">Content 3</TabsContent>
        </Tabs>
      );

      // Initially show tab1 content
      expect(screen.getByText('Content 1')).toBeInTheDocument();

      // Switch to tab2
      await userEvent.click(screen.getByText('Tab 2'));
      expect(screen.getByText('Content 2')).toBeInTheDocument();

      // Switch to tab3
      await userEvent.click(screen.getByText('Tab 3'));
      expect(screen.getByText('Content 3')).toBeInTheDocument();

      // Back to tab1
      await userEvent.click(screen.getByText('Tab 1'));
      expect(screen.getByText('Content 1')).toBeInTheDocument();
    });

    it('should update trigger active states on switch', async () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">First</TabsTrigger>
            <TabsTrigger value="tab2">Second</TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const tab1 = screen.getByText('First');
      const tab2 = screen.getByText('Second');

      // Initially tab1 is active
      expect(tab1).toHaveClass('bg-surface');
      expect(tab2).not.toHaveClass('bg-surface');

      // Switch to tab2
      await userEvent.click(tab2);

      expect(tab1).not.toHaveClass('bg-surface');
      expect(tab2).toHaveClass('bg-surface');
    });
  });

  describe('Display Names', () => {
    it('Tabs should have correct displayName', () => {
      expect(Tabs.displayName).toBe('Tabs');
    });

    it('TabsList should have correct displayName', () => {
      expect(TabsList.displayName).toBe('TabsList');
    });

    it('TabsTrigger should have correct displayName', () => {
      expect(TabsTrigger.displayName).toBe('TabsTrigger');
    });

    it('TabsContent should have correct displayName', () => {
      expect(TabsContent.displayName).toBe('TabsContent');
    });
  });

  describe('Accessibility', () => {
    it('should have proper button role for triggers', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab</TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const triggers = screen.getAllByRole('button');
      expect(triggers.length).toBeGreaterThan(0);
    });

    it('should support keyboard navigation', async () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const triggers = screen.getAllByRole('button');
      triggers[0].focus();

      expect(document.activeElement).toBe(triggers[0]);
    });

    it('should have focus-visible ring', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Focusable Tab</TabsTrigger>
          </TabsList>
        </Tabs>
      );

      const tab = screen.getByText('Focusable Tab');
      expect(tab).toHaveClass('focus-visible:ring-2');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty defaultValue', () => {
      render(
        <Tabs defaultValue="">
          <TabsContent value="">Empty Tab Content</TabsContent>
          <TabsContent value="other">Other Content</TabsContent>
        </Tabs>
      );

      expect(screen.getByText('Empty Tab Content')).toBeInTheDocument();
    });

    it('should handle undefined value gracefully', () => {
      render(
        <Tabs value={undefined} onValueChange={vi.fn()}>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      );

      // Should not crash, should show empty value content or none
      expect(screen.queryByText('Content')).not.toBeInTheDocument();
    });
  });
});

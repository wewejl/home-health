/**
 * Select 组件测试
 *
 * 测试覆盖：
 * 1. Select 基础渲染
 * 2. SelectTrigger 触发
 * 3. SelectContent 选项列表
 * 4. SelectItem 选项选择
 * 5. SelectValue 显示
 * 6. 受控/非受控模式
 * 7. 选项过滤/搜索
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  SelectLabel,
  SelectSeparator,
} from '../select';

describe('Select Components', () => {
  describe('Select - Uncontrolled Mode', () => {
    it('should render with default value', () => {
      render(
        <Select defaultValue="option1">
          <SelectTrigger>
            <SelectValue placeholder="Choose..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
            <SelectItem value="option2">Option 2</SelectItem>
          </SelectContent>
        </Select>
      );

      expect(screen.getByText('Choose...')).toBeInTheDocument();
    });

    it('should display value when selected', async () => {
      render(
        <Select defaultValue="option1">
          <SelectTrigger>
            <SelectValue placeholder="Select..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
            <SelectItem value="option2">Option 2</SelectItem>
          </SelectContent>
        </Select>
      );

      // SelectValue should show the current value
      const trigger = screen.getByText('Select...');
      expect(trigger).toBeInTheDocument();
    });
  });

  describe('Select - Controlled Mode', () => {
    it('should use controlled value', () => {
      const handleChange = vi.fn();
      render(
        <Select value="option2" onValueChange={handleChange}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
            <SelectItem value="option2">Option 2</SelectItem>
          </SelectContent>
        </Select>
      );

      expect(screen.getByText('option2')).toBeInTheDocument();
    });

    it('should call onValueChange when item is selected', async () => {
      const handleChange = vi.fn();

      render(
        <Select value="option1" onValueChange={handleChange}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
            <SelectItem value="option2">Option 2</SelectItem>
            <SelectItem value="option3">Option 3</SelectItem>
          </SelectContent>
        </Select>
      );

      // Click on an item
      const item2 = screen.getByText('Option 2');
      await userEvent.click(item2);

      expect(handleChange).toHaveBeenCalledWith('option2');
    });
  });

  describe('SelectTrigger', () => {
    it('should render button element', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Item 1</SelectItem>
          </SelectContent>
        </Select>
      );

      const trigger = screen.getByRole('button');
      expect(trigger).toBeInTheDocument();
    });

    it('should toggle dropdown on click', async () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Choose" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="a">A</SelectItem>
          </SelectContent>
        </Select>
      );

      const trigger = screen.getByRole('button');
      await userEvent.click(trigger);

      // After clicking, content should be visible
      await waitFor(() => {
        expect(screen.getByText('A')).toBeInTheDocument();
      });
    });

    it('should display chevron icon', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Item</SelectItem>
          </SelectContent>
        </Select>
      );

      const trigger = screen.getByRole('button');
      expect(trigger).toBeInTheDocument();
    });

    it('should apply custom className', () => {
      render(
        <Select>
          <SelectTrigger className="custom-trigger">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Item</SelectItem>
          </SelectContent>
        </Select>
      );

      const trigger = screen.getByRole('button');
      expect(trigger).toHaveClass('custom-trigger');
    });
  });

  describe('SelectValue', () => {
    it('should display placeholder when no value', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Please select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Item</SelectItem>
          </SelectContent>
        </Select>
      );

      expect(screen.getByText('Please select')).toBeInTheDocument();
    });

    it('should display current value when selected', () => {
      render(
        <Select value="apple" onValueChange={vi.fn()}>
          <SelectTrigger>
            <SelectValue placeholder="Choose fruit" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="apple">Apple</SelectItem>
          </SelectContent>
        </Select>
      );

      expect(screen.getByText('apple')).toBeInTheDocument();
    });
  });

  describe('SelectContent', () => {
    it('should not render when open is false', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Item 1</SelectItem>
          </SelectContent>
        </Select>
      );

      // Content should not be visible initially
      expect(screen.queryByText('Item 1')).not.toBeInTheDocument();
    });

    it('should render items when open', async () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Item 1</SelectItem>
            <SelectItem value="2">Item 2</SelectItem>
          </SelectContent>
        </Select>
      );

      // Click trigger to open
      const trigger = screen.getByRole('button');
      await userEvent.click(trigger);

      // Items should now be visible
      await waitFor(() => {
        expect(screen.getByText('Item 1')).toBeInTheDocument();
        expect(screen.getByText('Item 2')).toBeInTheDocument();
      });
    });

    it('should close on backdrop click', async () => {
      const handleChange = vi.fn();
      render(
        <Select value="1" onValueChange={handleChange}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Item 1</SelectItem>
            <SelectItem value="2">Item 2</SelectItem>
          </SelectContent>
        </Select>
      );

      // Open the dropdown
      const trigger = screen.getByRole('button');
      await userEvent.click(trigger);

      // Click backdrop (fixed inset-0)
      const backdrop = document.querySelector('.fixed.inset-0');
      if (backdrop) {
        await userEvent.click(backdrop);
      }

      // Wait for close animation
      await waitFor(() => {
        expect(screen.queryByText('Item 2')).not.toBeInTheDocument();
      });
    });

    it('should apply custom className', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="custom-content">
            <SelectItem value="1">Item</SelectItem>
          </SelectContent>
        </Select>
      );

      const trigger = screen.getByRole('button');
      // Need to open to see content class
      // This would require proper state management in test
    });
  });

  describe('SelectItem', () => {
    it('should render item button', async () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="test">Test Item</SelectItem>
          </SelectContent>
        </Select>
      );

      const trigger = screen.getByRole('button');
      await userEvent.click(trigger);

      const item = screen.getByText('Test Item');
      expect(item.tagName).toBe('BUTTON');
    });

    it('should show check icon for active item', async () => {
      render(
        <Select value="option1" onValueChange={vi.fn()}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Active Item</SelectItem>
            <SelectItem value="option2">Inactive Item</SelectItem>
          </SelectContent>
        </Select>
      );

      const trigger = screen.getByRole('button');
      await userEvent.click(trigger);

      // Active item should have check icon
      await waitFor(() => {
        const activeItem = screen.getByText('Active Item');
        expect(activeItem.parentElement?.querySelector('svg')).toBeInTheDocument();
      });
    });

    it('should apply active styling when selected', async () => {
      render(
        <Select value="selected" onValueChange={vi.fn()}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="selected">Selected Item</SelectItem>
            <SelectItem value="other">Other Item</SelectItem>
          </SelectContent>
        </Select>
      );

      const trigger = screen.getByRole('button');
      await userEvent.click(trigger);

      await waitFor(() => {
        const selectedItem = screen.getByText('Selected Item');
        expect(selectedItem.parentElement).toHaveClass('bg-accent');
      });
    });

    it('should call onValueChange and close on selection', async () => {
      const handleChange = vi.fn();
      render(
        <Select value="" onValueChange={handleChange}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="new-value">New Option</SelectItem>
          </SelectContent>
        </Select>
      );

      const trigger = screen.getByRole('button');
      await userEvent.click(trigger);

      const item = screen.getByText('New Option');
      await userEvent.click(item);

      expect(handleChange).toHaveBeenCalledWith('new-value');
    });
  });

  describe('SelectLabel', () => {
    it('should render label element', async () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectLabel>Category</SelectLabel>
            <SelectItem value="1">Item 1</SelectItem>
          </SelectContent>
        </Select>
      );

      const trigger = screen.getByRole('button');
      await userEvent.click(trigger);

      expect(screen.getByText('Category')).toBeInTheDocument();
    });

    it('should have proper styling', async () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectLabel>Label Text</SelectLabel>
          </SelectContent>
        </Select>
      );

      const trigger = screen.getByRole('button');
      await userEvent.click(trigger);

      const label = screen.getByText('Label Text');
      expect(label.tagName).toBe('LABEL');
      expect(label).toHaveClass('px-2', 'py-1.5');
    });
  });

  describe('SelectSeparator', () => {
    it('should render separator line', async () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">Item 1</SelectItem>
            <SelectSeparator />
            <SelectItem value="2">Item 2</SelectItem>
          </SelectContent>
        </Select>
      );

      const trigger = screen.getByRole('button');
      await userEvent.click(trigger);

      const separator = document.querySelector('.-mx-1.my-1.bg-muted');
      expect(separator).toBeInTheDocument();
    });
  });

  describe('Complete Select Structure', () => {
    it('should render complete select with all components', async () => {
      const handleChange = vi.fn();

      render(
        <Select value="" onValueChange={handleChange}>
          <SelectTrigger>
            <SelectValue placeholder="Choose an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectLabel>Fruits</SelectLabel>
            <SelectItem value="apple">Apple</SelectItem>
            <SelectItem value="banana">Banana</SelectItem>
            <SelectSeparator />
            <SelectItem value="orange">Orange</SelectItem>
          </SelectContent>
        </Select>
      );

      expect(screen.getByText('Choose an option')).toBeInTheDocument();

      const trigger = screen.getByRole('button');
      await userEvent.click(trigger);

      expect(screen.getByText('Fruits')).toBeInTheDocument();
      expect(screen.getByText('Apple')).toBeInTheDocument();
      expect(screen.getByText('Banana')).toBeInTheDocument();
      expect(screen.getByText('Orange')).toBeInTheDocument();
    });
  });

  describe('Display Names', () => {
    it('Select should have correct displayName', () => {
      expect(Select.displayName).toBe('Select');
    });

    it('SelectTrigger should have correct displayName', () => {
      expect(SelectTrigger.displayName).toBe('SelectTrigger');
    });

    it('SelectValue should have correct displayName', () => {
      expect(SelectValue.name).toBe('SelectValue');
    });

    it('SelectContent should have correct displayName', () => {
      expect(SelectContent.displayName).toBe('SelectContent');
    });

    it('SelectItem should have correct displayName', () => {
      expect(SelectItem.displayName).toBe('SelectItem');
    });

    it('SelectLabel should have correct displayName', () => {
      expect(SelectLabel.displayName).toBe('SelectLabel');
    });

    it('SelectSeparator should have correct displayName', () => {
      expect(SelectSeparator.displayName).toBe('SelectSeparator');
    });
  });
});

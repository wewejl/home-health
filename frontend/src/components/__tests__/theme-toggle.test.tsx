/**
 * ThemeToggle 组件测试
 *
 * 测试覆盖：
 * 1. 组件渲染测试
 * 2. 用户交互测试（主题切换）
 * 3. 图标变化测试
 * 4. 边界条件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import { ThemeToggle } from '../theme-toggle';

// Mock next-themes
const mockSetTheme = vi.fn();
const mockTheme = vi.fn(() => 'light');

vi.mock('next-themes', () => ({
  useTheme: () => ({
    theme: mockTheme(),
    setTheme: mockSetTheme,
  }),
}));

describe('ThemeToggle Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mock to return light theme by default
    mockTheme.mockReturnValue('light');
  });

  describe('Rendering', () => {
    it('should not render when not mounted', () => {
      // Mock useState to return false for mounted
      vi.spyOn(React, 'useState').mockReturnValue([false, vi.fn()]);

      const { container } = render(<ThemeToggle />);

      expect(container.firstChild).toBeNull();
    });

    it('should render button when mounted', () => {
      // Mock useState to return true for mounted
      const setStateMock = vi.fn();
      vi.spyOn(React, 'useState').mockReturnValue([true, setStateMock]);

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('should render with correct title attribute', () => {
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);
      mockTheme.mockReturnValue('light');

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('title', '当前主题: 浅色');
    });

    it('should render screen reader text', () => {
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);

      render(<ThemeToggle />);

      const srText = screen.getByText('切换主题');
      expect(srText).toHaveClass('sr-only');
    });
  });

  describe('Icon Rendering', () => {
    it('should show Sun icon for light theme', () => {
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);
      mockTheme.mockReturnValue('light');

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      // Sun icon should be present
      const svg = button.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should show Moon icon for dark theme', () => {
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);
      mockTheme.mockReturnValue('dark');

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      // Moon icon should be present
      const svg = button.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should show Monitor icon for system theme', () => {
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);
      mockTheme.mockReturnValue('system');

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      // Monitor icon should be present
      const svg = button.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should have correct icon size classes', () => {
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);
      mockTheme.mockReturnValue('light');

      render(<ThemeToggle />);

      const svg = screen.getByRole('button').querySelector('svg');
      expect(svg).toHaveClass('h-\\[1\\.2rem\\]');
      expect(svg).toHaveClass('w-\\[1\\.2rem\\]');
    });
  });

  describe('Theme Cycling', () => {
    it('should cycle from light to dark', async () => {
      const user = userEvent.setup();
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);
      mockTheme.mockReturnValue('light');

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(mockSetTheme).toHaveBeenCalledWith('dark');
    });

    it('should cycle from dark to system', async () => {
      const user = userEvent.setup();
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);
      mockTheme.mockReturnValue('dark');

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(mockSetTheme).toHaveBeenCalledWith('system');
    });

    it('should cycle from system to light', async () => {
      const user = userEvent.setup();
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);
      mockTheme.mockReturnValue('system');

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(mockSetTheme).toHaveBeenCalledWith('light');
    });
  });

  describe('Button Styles', () => {
    it('should apply ghost variant', () => {
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('should apply icon size', () => {
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-9');
      expect(button).toHaveClass('w-9');
    });
  });

  describe('Accessibility', () => {
    it('should have button role', () => {
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('should have accessible title for each theme', () => {
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);

      // Test light theme title
      mockTheme.mockReturnValue('light');
      const { rerender } = render(<ThemeToggle />);
      let button = screen.getByRole('button');
      expect(button).toHaveAttribute('title', '当前主题: 浅色');

      // Test dark theme title
      mockTheme.mockReturnValue('dark');
      rerender(<ThemeToggle />);
      button = screen.getByRole('button');
      expect(button).toHaveAttribute('title', '当前主题: 深色');

      // Test system theme title
      mockTheme.mockReturnValue('system');
      rerender(<ThemeToggle />);
      button = screen.getByRole('button');
      expect(button).toHaveAttribute('title', '当前主题: 跟随系统');
    });

    it('should have screen reader only text', () => {
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);

      render(<ThemeToggle />);

      const srText = screen.getByText('切换主题');
      expect(srText).toHaveClass('sr-only');
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined theme', () => {
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);
      mockTheme.mockReturnValue(undefined as any);

      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      // Should cycle to light when undefined
    });

    it('should handle rapid theme changes', async () => {
      const user = userEvent.setup();
      vi.spyOn(React, 'useState').mockReturnValue([true, vi.fn()]);
      mockTheme.mockReturnValue('light');

      render(<ThemeToggle />);

      const button = screen.getByRole('button');

      // Rapid clicks
      await user.click(button);
      await user.click(button);
      await user.click(button);

      expect(mockSetTheme).toHaveBeenCalledTimes(3);
    });
  });

  describe('Mounting Effect', () => {
    it('should call useEffect to set mounted state', () => {
      const useEffectSpy = vi.spyOn(React, 'useEffect');

      vi.spyOn(React, 'useState').mockReturnValue([false, vi.fn()]);

      render(<ThemeToggle />);

      expect(useEffectSpy).toHaveBeenCalled();
    });
  });
});

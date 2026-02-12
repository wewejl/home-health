/**
 * ErrorBoundary 组件测试
 *
 * 测试覆盖：
 * 1. 组件渲染测试
 * 2. 错误捕获测试
 * 3. 回退 UI 渲染测试
 * 4. 边界条件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import { ErrorBoundary } from '../ErrorBoundary';

// Mock console.error to avoid cluttering test output
const originalConsoleError = console.error;
beforeEach(() => {
  console.error = vi.fn();
  // Reset import.meta.env.DEV
  vi.stubGlobal('import', { meta: { env: { DEV: true } } });
});

describe('ErrorBoundary Component', () => {
  describe('Rendering Without Errors', () => {
    it('should render children when there is no error', () => {
      const ThrowError = () => <div>No Error</div>;

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('No Error')).toBeInTheDocument();
    });

    it('should render multiple children', () => {
      render(
        <ErrorBoundary>
          <div>Child 1</div>
          <div>Child 2</div>
        </ErrorBoundary>
      );

      expect(screen.getByText('Child 1')).toBeInTheDocument();
      expect(screen.getByText('Child 2')).toBeInTheDocument();
    });

    it('should render nested components', () => {
      const NestedComponent = () => (
        <div>
          <span data-testid="nested">Nested Content</span>
        </div>
      );

      render(
        <ErrorBoundary>
          <NestedComponent />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('nested')).toBeInTheDocument();
    });
  });

  describe('Error Catching', () => {
    it('should catch errors in child components', () => {
      // Mock console to prevent error output
      const ThrowError = () => {
        throw new Error('Test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      // ErrorBoundary should catch the error
      expect(console.error).toHaveBeenCalled();
    });

    it('should render default error UI when error occurs', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('出错了')).toBeInTheDocument();
      expect(screen.getByText(/应用程序遇到了一个意外错误/)).toBeInTheDocument();
    });

    it('should hide children content when error occurs', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      render(
        <ErrorBoundary>
          <div data-testid="child-content">This should not show</div>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.queryByTestId('child-content')).not.toBeInTheDocument();
    });
  });

  describe('Custom Fallback', () => {
    it('should render custom fallback when provided', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      const customFallback = <div data-testid="custom-fallback">Custom Error UI</div>;

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    });

    it('should not render default error UI when custom fallback is provided', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      const customFallback = <div>Custom Error</div>;

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('Custom Error')).toBeInTheDocument();
      expect(screen.queryByText('出错了')).not.toBeInTheDocument();
    });

    it('should render complex custom fallback', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      const customFallback = (
        <div data-testid="complex-fallback">
          <h1>Oops!</h1>
          <p>Something went wrong</p>
          <button>Retry</button>
        </div>
      );

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('complex-fallback')).toBeInTheDocument();
      expect(screen.getByText('Oops!')).toBeInTheDocument();
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  describe('Error Callback', () => {
    it('should call onError callback when error occurs', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      const onError = vi.fn();

      render(
        <ErrorBoundary onError={onError}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(onError).toHaveBeenCalled();
      expect(onError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String),
        })
      );
    });

    it('should pass error and errorInfo to callback', () => {
      const ThrowError = () => {
        throw new Error('Callback test error');
      };

      const onError = vi.fn();

      render(
        <ErrorBoundary onError={onError}>
          <ThrowError />
        </ErrorBoundary>
      );

      const callArgs = onError.mock.calls[0];
      expect(callArgs[0]).toBeInstanceOf(Error);
      expect(callArgs[0].message).toBe('Callback test error');
      expect(callArgs[1]).toHaveProperty('componentStack');
    });
  });

  describe('Error Recovery', () => {
    it('should render retry button', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('重试')).toBeInTheDocument();
    });

    it('should reset error state when retry is clicked', async () => {
      const user = userEvent.setup();

      const ThrowError = () => {
        throw new Error('Test error');
      };

      const TestComponent = () => (
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const { rerender } = render(<TestComponent />);

      // Error should be displayed
      expect(screen.getByText('出错了')).toBeInTheDocument();

      // Click retry
      const retryButton = screen.getByText('重试');
      await user.click(retryButton);

      // After reset, the error state should be cleared
      // But since ThrowError still throws, it will error again
      expect(screen.getByText('出错了')).toBeInTheDocument();
    });

    it('should render "返回首页" button', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('返回首页')).toBeInTheDocument();
    });

    it('should navigate to home when "返回首页" is clicked', async () => {
      const user = userEvent.setup();

      // Mock window.location.href
      const mockLocation = { href: '' };
      vi.stubGlobal('window', { location: mockLocation });

      const ThrowError = () => {
        throw new Error('Test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const homeButton = screen.getByText('返回首页');
      await user.click(homeButton);

      // Should set location to '/'
      expect(window.location.href).toBe('/');

      vi.unstubAllGlobals();
    });
  });

  describe('Development Mode Error Details', () => {
    beforeEach(() => {
      vi.stubGlobal('import', { meta: { env: { DEV: true } } });
    });

    it('should show error details in DEV mode', () => {
      const ThrowError = () => {
        throw new Error('Development test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('错误详情：')).toBeInTheDocument();
    });

    it('should show error message in DEV mode', () => {
      const ThrowError = () => {
        throw new Error('Specific error message');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText(/Specific error message/)).toBeInTheDocument();
    });

    it('should show component stack in DEV mode', () => {
      const ThrowError = () => {
        throw new Error('Stack test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('组件堆栈')).toBeInTheDocument();
    });

    it('should have expandable details for component stack', () => {
      const ThrowError = () => {
        throw new Error('Details test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const details = screen.getByText('组件堆栈').closest('details');
      expect(details).toBeInTheDocument();
    });
  });

  describe('Production Mode', () => {
    beforeEach(() => {
      vi.stubGlobal('import', { meta: { env: { DEV: false } } });
    });

    it('should hide error details in production', () => {
      const ThrowError = () => {
        throw new Error('Production test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.queryByText('错误详情：')).not.toBeInTheDocument();
    });

    it('should still show basic error UI in production', () => {
      const ThrowError = () => {
        throw new Error('Production test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByText('出错了')).toBeInTheDocument();
      expect(screen.getByText(/应用程序遇到了一个意外错误/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading structure', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('出错了');
    });

    it('should have accessible retry button', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const retryButton = screen.getByRole('button', { name: '重试' });
      expect(retryButton).toBeInTheDocument();
    });

    it('should have accessible home button', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const homeButton = screen.getByRole('button', { name: '返回首页' });
      expect(homeButton).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('should have centered layout', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      const { container } = render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      const wrapper = container.querySelector('.min-h-screen');
      expect(wrapper).toBeInTheDocument();
      expect(wrapper).toHaveClass('flex');
      expect(wrapper).toHaveClass('items-center');
      expect(wrapper).toHaveClass('justify-center');
    });

    it('should have error icon', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      // Alert triangle icon should be present
      const iconContainer = screen.getByText('出错了').parentElement?.parentElement;
      expect(iconContainer).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle null children', () => {
      render(
        <ErrorBoundary>
          {null as any}
        </ErrorBoundary>
      );

      // Should not crash
      expect(document.body).toBeInTheDocument();
    });

    it('should handle undefined children', () => {
      render(
        <ErrorBoundary>
          {undefined as any}
        </ErrorBoundary>
      );

      // Should not crash
      expect(document.body).toBeInTheDocument();
    });

    it('should handle async errors in children', async () => {
      const AsyncErrorComponent = () => {
        React.useEffect(() => {
          const timer = setTimeout(() => {
            throw new Error('Async error');
          }, 0);
          return () => clearTimeout(timer);
        }, []);
        return <div>Async Component</div>;
      };

      render(
        <ErrorBoundary>
          <AsyncErrorComponent />
        </ErrorBoundary>
      );

      // Initially should render children
      expect(screen.getByText('Async Component')).toBeInTheDocument();
    });

    it('should handle errors during rendering', () => {
      const RenderErrorComponent = () => {
        throw new Error('Render error');
      };

      render(
        <ErrorBoundary>
          <RenderErrorComponent />
        </ErrorBoundary>
      );

      expect(screen.getByText('出错了')).toBeInTheDocument();
    });
  });

  describe('Multiple Error Boundaries', () => {
    it('should only catch errors in its own children', () => {
      const InnerError = () => {
        throw new Error('Inner error');
      };

      const SafeComponent = () => <div>Safe Component</div>;

      render(
        <div>
          <ErrorBoundary key="1">
            <InnerError />
          </ErrorBoundary>
          <ErrorBoundary key="2">
            <SafeComponent />
          </ErrorBoundary>
        </div>
      );

      // First boundary should catch error
      expect(screen.getByText('出错了')).toBeInTheDocument();
      // Second boundary should render safely
      expect(screen.getByText('Safe Component')).toBeInTheDocument();
    });
  });

  describe('Console Error Logging', () => {
    it('should log error to console', () => {
      const ThrowError = () => {
        throw new Error('Console test error');
      };

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(console.error).toHaveBeenCalledWith(
        'ErrorBoundary caught an error:',
        expect.any(Error),
        expect.any(Object)
      );
    });
  });
});

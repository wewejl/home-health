import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary 组件
 * 捕获子组件树中的 JavaScript 错误，显示友好的错误界面
 * 而不是让整个应用崩溃白屏
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(_error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 记录错误到控制台
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // 调用自定义错误处理函数
    this.props.onError?.(error, errorInfo);

    // 更新状态以显示错误信息
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // 如果提供了自定义 fallback，使用它
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认错误界面
      return (
        <div className="min-h-screen flex items-center justify-center bg-surface p-4">
          <Card className="w-full max-w-lg p-8 text-center space-y-6">
            <div className="flex justify-center">
              <div className="h-16 w-16 rounded-full bg-danger-light/20 flex items-center justify-center">
                <AlertTriangle className="h-8 w-8 text-danger" />
              </div>
            </div>

            <div className="space-y-2">
              <h1 className="text-2xl font-bold text-foreground">出错了</h1>
              <p className="text-foreground-secondary">
                应用程序遇到了一个意外错误。您可以尝试刷新页面或重新开始。
              </p>
            </div>

            {import.meta.env.DEV && this.state.error && (
              <div className="text-left p-4 rounded-lg bg-surface-alt border border-border">
                <p className="text-sm font-medium text-danger mb-2">错误详情：</p>
                <p className="text-xs text-foreground-secondary font-mono break-all">
                  {this.state.error.toString()}
                </p>
                {this.state.errorInfo && (
                  <details className="mt-2">
                    <summary className="text-xs text-foreground-secondary cursor-pointer">
                      组件堆栈
                    </summary>
                    <pre className="text-xs text-foreground-secondary mt-2 overflow-auto max-h-32">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            <div className="flex gap-3 justify-center">
              <Button
                variant="outline"
                onClick={this.handleReset}
                className="gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                重试
              </Button>
              <Button
                onClick={() => window.location.href = '/'}
                className="gap-2"
              >
                返回首页
              </Button>
            </div>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

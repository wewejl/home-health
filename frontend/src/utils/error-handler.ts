import axios, { AxiosError } from 'axios';

/**
 * API 错误响应接口
 */
interface ApiErrorResponse {
  detail?: string;
  message?: string;
  error?: string;
}

/**
 * 获取友好的错误消息
 */
export function getErrorMessage(error: unknown): string {
  // Axios 网络错误
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorResponse>;

    // 服务器返回了错误响应
    if (axiosError.response) {
      const data = axiosError.response.data;
      const status = axiosError.response.status;

      // 优先使用服务器返回的错误信息
      if (data?.detail) return data.detail;
      if (data?.message) return data.message;
      if (data?.error) return data.error;

      // 根据状态码返回友好提示
      switch (status) {
        case 400:
          return '请求参数错误，请检查输入';
        case 401:
          return '登录已过期，请重新登录';
        case 403:
          return '没有权限执行此操作';
        case 404:
          return '请求的资源不存在';
        case 409:
          return '操作冲突，请刷新后重试';
        case 422:
          return '数据验证失败，请检查输入';
        case 429:
          return '请求过于频繁，请稍后再试';
        case 500:
          return '服务器内部错误，请稍后重试';
        case 502:
        case 503:
        case 504:
          return '服务暂时不可用，请稍后重试';
        default:
          return `请求失败 (${status})`;
      }
    }

    // 网络错误或请求超时
    if (axiosError.request) {
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        return '请求超时，请检查网络连接';
      }
      return '网络连接失败，请检查网络设置';
    }

    // 其他 Axios 错误
    return error.message || '请求失败';
  }

  // 非 Axios 错误
  if (error instanceof Error) {
    return error.message;
  }

  // 未知错误
  return '未知错误，请稍后重试';
}

/**
 * 判断错误是否为网络错误
 */
export function isNetworkError(error: unknown): boolean {
  if (!axios.isAxiosError(error)) return false;
  const axiosError = error as AxiosError;
  return !!axiosError.request && !axiosError.response;
}

/**
 * 判断错误是否为认证错误
 */
export function isAuthError(error: unknown): boolean {
  if (!axios.isAxiosError(error)) return false;
  const axiosError = error as AxiosError;
  return axiosError.response?.status === 401 || false;
}

/**
 * 判断错误是否为服务器错误
 */
export function isServerError(error: unknown): boolean {
  if (!axios.isAxiosError(error)) return false;
  const axiosError = error as AxiosError;
  const status = axiosError.response?.status;
  return status !== undefined && status >= 500 && status < 600;
}

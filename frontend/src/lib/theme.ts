/**
 * 主题工具函数
 *
 * 用于从 CSS 变量获取颜色值，主要供图表组件使用
 */

/**
 * HSL 颜色值解析
 * 输入格式: "199 89% 48%" 或 "199 89% 48% / 1"
 */
interface HSLValue {
  h: number;
  s: number;
  l: number;
  a?: number;
}

function parseHSL(hslString: string): HSLValue | null {
  // 移除空格和注释
  const cleaned = hslString.trim();

  // 匹配 HSL 格式: "h s% l%" 或 "h s% l% / a"
  const match = cleaned.match(/^(\d+)\s+(\d+)%\s+(\d+)%(?:\s*\/\s*([\d.]+))?$/);

  if (!match) {
    return null;
  }

  return {
    h: parseInt(match[1], 10),
    s: parseInt(match[2], 10),
    l: parseInt(match[3], 10),
    a: match[4] ? parseFloat(match[4]) : 1,
  };
}

/**
 * 将 HSL 转换为 RGB
 */
function hslToRgb(hsl: HSLValue): { r: number; g: number; b: number } {
  const h = hsl.h / 360;
  const s = hsl.s / 100;
  const l = hsl.l / 100;

  let r: number, g: number, b: number;

  if (s === 0) {
    r = g = b = l;
  } else {
    const hue2rgb = (p: number, q: number, t: number): number => {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1 / 6) return p + (q - p) * 6 * t;
      if (t < 1 / 2) return q;
      if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
      return p;
    };

    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;

    r = hue2rgb(p, q, h + 1 / 3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1 / 3);
  }

  return {
    r: Math.round(r * 255),
    g: Math.round(g * 255),
    b: Math.round(b * 255),
  };
}

/**
 * 将 RGB 转换为 Hex
 */
function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (n: number): string => {
    const hex = n.toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  };

  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/**
 * 将 CSS HSL 变量值转换为 Hex 颜色
 * @param hslString HSL 字符串，格式: "199 89% 48%"
 * @returns Hex 颜色字符串，格式: "#0EA5E9"
 */
export function hslToHex(hslString: string): string {
  const hsl = parseHSL(hslString);

  if (!hsl) {
    // 解析失败，返回默认颜色
    console.warn(`Failed to parse HSL value: ${hslString}`);
    return '#0EA5E9';
  }

  const rgb = hslToRgb(hsl);
  return rgbToHex(rgb.r, rgb.g, rgb.b);
}

/**
 * 从 CSS 变量获取主题颜色
 *
 * 用于自定义图表组件（CustomLineChart、CustomColumnChart、CustomPieChart）的颜色配置
 * 图表组件基于 Recharts 实现，位于 `frontend/src/components/charts/`
 *
 * @example
 * ```tsx
 * import { getThemeColors } from '@/lib/theme';
 *
 * const colors = getThemeColors();
 * // 使用在图表配置中
 * ```
 */
export function getThemeColors(): Record<string, string> {
  if (typeof document === 'undefined') {
    // SSR 环境，返回默认值
    return {
      colorPrimary: '#0EA5E9',
      colorSuccess: '#10B981',
      colorWarning: '#F59E0B',
      colorError: '#EF4444',
      colorInfo: '#3B82F6',
    };
  }

  const styles = getComputedStyle(document.documentElement);

  const getHexColor = (name: string): string => {
    const hsl = styles.getPropertyValue(`--${name}`).trim();
    return hsl ? hslToHex(hsl) : '#0EA5E9';
  };

  return {
    colorPrimary: getHexColor('primary'),
    colorSuccess: getHexColor('success'),
    colorWarning: getHexColor('warning'),
    colorError: getHexColor('danger'),
    colorInfo: getHexColor('info'),
  };
}

/**
 * 获取当前主题模式
 * @returns 'light' | 'dark' | 'system'
 */
export function getThemeMode(): 'light' | 'dark' {
  if (typeof document === 'undefined') {
    return 'light';
  }

  return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
}

/**
 * 监听主题变化
 * @param callback 主题变化回调
 * @returns 清理函数
 */
export function watchThemeChange(callback: (mode: 'light' | 'dark') => void): () => void {
  if (typeof document === 'undefined') {
    return () => {};
  }

  const observer = new MutationObserver(() => {
    callback(getThemeMode());
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  });

  return () => observer.disconnect();
}

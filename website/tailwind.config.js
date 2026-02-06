/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 灵犀健康品牌色系
        primary: {
          50: '#E6F7FF',
          100: '#BAE7FF',
          200: '#91D5FF',
          300: '#69C0FF',
          400: '#40A9FF',
          500: '#1890FF',
          600: '#096DD9',
          700: '#0050B3',
          800: '#003A8C',
          900: '#002766',
        },
        teal: {
          50: '#E6FFFB',
          100: '#B5F5EC',
          200: '#87E8DE',
          300: '#5DDBD2',
          400: '#36CFC9',
          500: '#13C2C2',
          600: '#08979C',
          700: '#006D75',
          800: '#00474F',
          900: '#002329',
        },
        orange: {
          50: '#FFF7E6',
          100: '#FFE7BA',
          200: '#FFD591',
          300: '#FFC069',
          400: '#FFA940',
          500: '#FA8C16',
          600: '#D46B08',
          700: '#AD4E00',
          800: '#873800',
          900: '#612500',
        },
        success: {
          light: '#95DE64',
          DEFAULT: '#52C41A',
          dark: '#389E0D',
        },
        purple: {
          light: '#B37FEB',
          DEFAULT: '#722ED1',
          dark: '#531DAB',
        },
        background: '#F5F8FA',
        surface: '#FFFFFF',
        text: {
          primary: '#262626',
          secondary: '#8C8C8C',
          muted: '#BFBFBF',
        },
      },
      fontFamily: {
        // 使用优雅的字体组合
        display: ['"Noto Serif SC"', '"Playfair Display"', 'serif'],
        sans: ['"Noto Sans SC"', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Monaco', 'monospace'],
      },
      fontSize: {
        'display': ['4.5rem', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '700' }],
        'hero': ['3.5rem', { lineHeight: '1.2', letterSpacing: '-0.01em', fontWeight: '600' }],
        'h1': ['2.5rem', { lineHeight: '1.3', fontWeight: '600' }],
        'h2': ['2rem', { lineHeight: '1.4', fontWeight: '600' }],
        'h3': ['1.5rem', { lineHeight: '1.5', fontWeight: '500' }],
        'h4': ['1.25rem', { lineHeight: '1.5', fontWeight: '500' }],
        'body-lg': ['1.125rem', { lineHeight: '1.7' }],
        'body': ['1rem', { lineHeight: '1.6' }],
        'body-sm': ['0.875rem', { lineHeight: '1.6' }],
      },
      borderRadius: {
        'sm': '8px',
        'md': '12px',
        'lg': '16px',
        'xl': '24px',
        '2xl': '32px',
        'full': '9999px',
      },
      boxShadow: {
        'card': '0 4px 12px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 8px 24px rgba(24, 144, 255, 0.12)',
        'glow': '0 0 40px rgba(24, 144, 255, 0.15)',
        'glow-teal': '0 0 40px rgba(19, 194, 194, 0.15)',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s infinite',
        'fade-in': 'fadeIn 0.6s ease-out',
        'slide-up': 'slideUp 0.6s ease-out',
        'scale-in': 'scaleIn 0.4s ease-out',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(30px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.9)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #1890FF 0%, #13C2C2 100%)',
        'gradient-warm': 'linear-gradient(135deg, #FA8C16 0%, #F5222D 100%)',
        'gradient-purple': 'linear-gradient(135deg, #722ED1 0%, #1890FF 100%)',
        'gradient-soft': 'linear-gradient(180deg, #F5F8FA 0%, #FFFFFF 100%)',
        'gradient-mesh': 'radial-gradient(at 40% 20%, rgba(24, 144, 255, 0.1) 0px, transparent 50%), radial-gradient(at 80% 0%, rgba(19, 194, 194, 0.1) 0px, transparent 50%), radial-gradient(at 0% 50%, rgba(114, 46, 209, 0.05) 0px, transparent 50%)',
      },
    },
  },
  plugins: [],
}

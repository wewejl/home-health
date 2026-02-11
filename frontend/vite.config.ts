import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  css: {
    postcss: './postcss.config.js',
  },
  // 固定前端端口为 8150
  server: {
    port: 8150,
    host: true,
    strictPort: true,  // 端口被占用时报错而不是自动尝试其他端口
    // 将 /api 请求代理到后端服务
    proxy: {
      '/api': {
        target: 'http://localhost:8100',
        changeOrigin: true,
      },
    },
  },
})

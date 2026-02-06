import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // 固定前端端口为 8150
  server: {
    port: 8150,
    host: true,
    strictPort: true,  // 端口被占用时报错而不是自动尝试其他端口
  },
})

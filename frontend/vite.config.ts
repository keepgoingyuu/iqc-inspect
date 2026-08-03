import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': new URL('./src', import.meta.url).pathname,
    },
  },
  server: {
    // 開發時 API 轉發到 FastAPI;正式部署由後端直接掛載 dist
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})

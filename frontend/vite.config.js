import { defineConfig } from 'vite'
import path from 'path'

// Proxy backend to avoid CORS during development.
export default defineConfig({
  server: {
    port: 5173,
    host: '127.0.0.1',
    proxy: {
      '/hairstyle-assets-orig': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/hairstyle-assets-raw': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/hairstyle-assets': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/hairstyles': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/analyze-face-shape': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/preview': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/validations': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/validation-images': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ui-assets': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})

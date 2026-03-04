// vite.config.ts
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  console.log('Loaded env:', {
    VITE_API_URL: env.VITE_API_URL,
    VITE_IMAGE_BASE_URL: env.VITE_IMAGE_BASE_URL,
    mode
  })
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      open: true, // Auto-open browser in development
    },
    build: {
      outDir: 'dist',
      sourcemap: mode === 'development', // Source maps only in development
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: mode === 'production', // Remove console.log in production
          drop_debugger: true,
        },
      },
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            ui: ['lucide-react', 'framer-motion'],
            state: ['zustand', '@tanstack/react-query'],
          },
        },
      },
    },
    preview: {
      port: 4173,
      open: true,
    },
    envPrefix: 'VITE_',
  }
})
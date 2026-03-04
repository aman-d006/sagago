// vite.config.ts
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Don't use ConfigEnv type, let Vite infer it
export default defineConfig(({ mode }) => {
  // Load env file based on `mode`
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
      open: true,
    },
    build: {
      outDir: 'dist',
      sourcemap: mode === 'development',
      // Simple minification
      minify: true,
      // No terserOptions at all
      rollupOptions: {
        output: {
          // Simple chunk splitting
          manualChunks: (id) => {
            if (id.includes('node_modules')) {
              return 'vendor';
            }
            return null;
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
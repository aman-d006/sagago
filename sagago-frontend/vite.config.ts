// vite.config.ts
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

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
    },
    envPrefix: 'VITE_',
  }
})
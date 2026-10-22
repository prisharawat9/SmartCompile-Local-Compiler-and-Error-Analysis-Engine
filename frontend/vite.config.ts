import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
declare const process: { cwd: () => string; env: Record<string, string | undefined> }

export default defineConfig(({ mode }) => {
  const cwd = typeof process !== 'undefined' && process.cwd ? process.cwd() : '.'
  const env = loadEnv(mode, cwd, '')
  const backendPort = env.VITE_BACKEND_PORT || env.PORT || '8001'
  const backendTarget = env.VITE_BACKEND_URL || `http://127.0.0.1:${backendPort}`

  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true,
        },
      },
    },
  }
})

import path from 'path'
import { defineConfig, loadEnv, type UserConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, path.join(process.cwd(), '..'))

  const cfg: UserConfig = {
    define: {
      __BASE_API_URL__: JSON.stringify(command === 'serve' ? 'api' : ''),
    },
    build: {
      outDir: '../static/app',
    },
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
  }

  console.log(`__BASE_API_URL__: ${cfg.define?.__BASE_API_URL__} `)

  // In dev mode VITE_DEV_BACKEND_HOST should be set to the aiohttp/flask backend host
  // so Vite can forward /app/api/* routes to VITE_DEV_BACKEND_HOST/*.
  if (command === 'serve' && env.VITE_DEV_BACKEND_HOST) {
    cfg.server = {
      proxy: {
        '/app/api': {
          target: env.VITE_DEV_BACKEND_HOST,
          changeOrigin: true,
          rewrite: (p) => {
            const r = p.replace(/^\/app\/api/, '')
            console.log(`Proxy rewrite ${p} -> ${r}`)
            return r
          },
        },
        '/audio': {
          target: env.VITE_DEV_BACKEND_HOST,
          changeOrigin: true,
        },
      },
    }
  }

  return cfg
})

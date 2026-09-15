import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,  // Puerto alternativo
    strictPort: false
  },
  // Si usas Tauri, añade esto también:
  clearScreen: false,
})
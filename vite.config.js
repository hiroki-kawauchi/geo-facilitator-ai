import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "/mapengine-survey/step3/deckgl-linelayer/",
  server: {
    host: '0.0.0.0',  // 外部からアクセスできるように設定
    port: 80,       // 使用するポートを指定
    strictPort: true,
    watch: {
      usePolling: true
    }
  }
});

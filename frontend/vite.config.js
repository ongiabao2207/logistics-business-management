import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api/v1/auth": "http://localhost:8005",
      "/api/v1/accounts": "http://localhost:8005",
      "/api/v1/roles": "http://localhost:8005",
      "/api/v1/contracts": "http://localhost:8001",
    },
  },
});

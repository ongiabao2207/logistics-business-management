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

      "/api/v1/customers": "http://localhost:8006",

      "/api/v1/contracts": "http://localhost:8001",

      "/api/v1/services": "http://localhost:8002",
      "/api/v1/price-lists": "http://localhost:8002",

      "/api/v1/production-periods": "http://localhost:8003",

      "/api/v1/payments": "http://localhost:8004",
      "/api": {
        target: "http://127.0.0.1:8088",
        changeOrigin: true,
      },
      "/.well-known": {
        target: "http://127.0.0.1:8088",
        changeOrigin: true,
      },
    },
  },
});

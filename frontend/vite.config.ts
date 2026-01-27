import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    allowedHosts: ["poke.taconetwork.net"],
    hmr: {
      clientPort: 8080,
    },
  },
});

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // FinancialAuditDashboard.jsx lives at project root; Vite resolves imports from there
  root: ".",
  publicDir: "public",
});

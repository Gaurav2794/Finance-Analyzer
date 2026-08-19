import React from "react";
import ReactDOM from "react-dom/client";
import FinancialAuditDashboard from "../FinancialAuditDashboard.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import "./material-tailwind.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider>
      <FinancialAuditDashboard documentId="b7e3c9a0-1e2f-4a3b-9c1d-77f0a1b2c3d4" />
    </AuthProvider>
  </React.StrictMode>
);

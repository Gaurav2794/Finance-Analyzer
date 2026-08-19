import React from "react";
import ReactDOM from "react-dom/client";
import FinancialAuditDashboard from "../FinancialAuditDashboard.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import "./material-tailwind.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider>
      <FinancialAuditDashboard />
    </AuthProvider>
  </React.StrictMode>
);

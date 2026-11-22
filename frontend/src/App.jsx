import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import { HealthProvider } from "./context/HealthContext.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import AnalyzeComplaint from "./pages/AnalyzeComplaint.jsx";
import PolicyLibrary from "./pages/PolicyLibrary.jsx";
import PromptLab from "./pages/PromptLab.jsx";
import ComplaintHistory from "./pages/ComplaintHistory.jsx";
import Settings from "./pages/Settings.jsx";

export default function App() {
  return (
    <HealthProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="analyze" element={<AnalyzeComplaint />} />
          <Route path="policies" element={<PolicyLibrary />} />
          <Route path="prompt-lab" element={<PromptLab />} />
          <Route path="history" element={<ComplaintHistory />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </HealthProvider>
  );
}

import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import AdminUsers from "./pages/AdminUsers";
import AgentDetail from "./pages/AgentDetail";
import Browse from "./pages/Browse";
import Login from "./pages/Login";
import MyAgents from "./pages/MyAgents";
import Reviews from "./pages/Reviews";
import Skills from "./pages/Skills";
import SsoCallback from "./pages/SsoCallback";
import VersionDetail from "./pages/VersionDetail";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/sso/callback" element={<SsoCallback />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Browse />} />
        <Route path="/my-agents" element={<MyAgents />} />
        <Route path="/agents/:slug" element={<AgentDetail />} />
        <Route path="/agents/:agentSlug/versions/:versionSlug" element={<VersionDetail />} />
        <Route path="/reviews" element={<Reviews />} />
        <Route path="/skills" element={<Skills />} />
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute requireAdmin>
              <AdminUsers />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

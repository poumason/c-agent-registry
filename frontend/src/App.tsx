import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import AdminAgents from "./pages/AdminAgents";
import AdminAgentSummary from "./pages/AdminAgentSummary";
import AdminAgentTemplates from "./pages/AdminAgentTemplates";
import AdminFabs from "./pages/AdminFabs";
import AdminReviewSummary from "./pages/AdminReviewSummary";
import AdminStats from "./pages/AdminStats";
import AdminUsers from "./pages/AdminUsers";
import AdminUserSummary from "./pages/AdminUserSummary";
import AgentDetail from "./pages/AgentDetail";
import Browse from "./pages/Browse";
import Login from "./pages/Login";
import MyAgents from "./pages/MyAgents";
import RegistryMcps from "./pages/RegistryMcps";
import RegistryModels from "./pages/RegistryModels";
import RegistrySkills from "./pages/RegistrySkills";
import ReviewQueue from "./pages/ReviewQueue";
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
        <Route path="/review-queue" element={<ReviewQueue />} />
        <Route
          path="/admin/review-summary"
          element={
            <ProtectedRoute requireAdmin>
              <AdminReviewSummary />
            </ProtectedRoute>
          }
        />
        <Route path="/registry/skills" element={<RegistrySkills />} />
        <Route path="/registry/mcps" element={<RegistryMcps />} />
        <Route path="/registry/models" element={<RegistryModels />} />
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute requireAdmin>
              <AdminUsers />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/agents"
          element={
            <ProtectedRoute requireAdmin>
              <AdminAgents />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/user-summary"
          element={
            <ProtectedRoute requireAdmin>
              <AdminUserSummary />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/agent-summary"
          element={
            <ProtectedRoute requireAdmin>
              <AdminAgentSummary />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/agent-templates"
          element={
            <ProtectedRoute requireAdmin>
              <AdminAgentTemplates />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/fabs"
          element={
            <ProtectedRoute requireAdmin>
              <AdminFabs />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/stats"
          element={
            <ProtectedRoute requireAdmin>
              <AdminStats />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

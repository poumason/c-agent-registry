import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { getStats } from "../api/admin";
import StatCard from "../components/StatCard";
import TrendChart from "../components/TrendChart";

const COLOR_PRIMARY = "var(--color-brand)";
const COLOR_POSITIVE = "var(--chart-good)";
const COLOR_NEGATIVE = "var(--chart-critical)";

const REGISTRY_LABELS: Record<string, { title: string; path: string }> = {
  mcp: { title: "MCP", path: "/registry/mcps" },
  model: { title: "Model", path: "/registry/models" },
  "agent-templates": { title: "Agent Templates", path: "/admin/agent-templates" },
};

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** exponent;
  return `${exponent === 0 ? value : value.toFixed(1)} ${units[exponent]}`;
}

export default function AdminStats() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: getStats,
  });

  if (isLoading) return <div className="loading-state">Loading…</div>;
  if (error || !data) return <p style={{ color: "var(--status-danger-fg)" }}>You don't have permission to view statistics.</p>;

  const versionsTotal = Object.values(data.versionsByStatus).reduce((sum, n) => sum + n, 0);
  const usersTotal = data.usersByRole.admin + data.usersByRole.reviewer + data.usersByRole.member;

  return (
    <div>
      <h1 style={{ fontSize: "var(--p-text-xl)", fontWeight: 700, margin: "0 0 4px" }}>Statistics</h1>
      <p style={{ color: "var(--fg-muted)", fontSize: "var(--p-text-sm)", margin: "0 0 var(--p-space-2)" }}>
        {t("adminStats.description")}
      </p>

      <h2 style={{ fontSize: "var(--p-text-lg)", fontWeight: 700, margin: "var(--p-space-6) 0 var(--p-space-1)" }}>Needs attention</h2>
      <p style={{ color: "var(--fg-muted)", fontSize: "var(--p-text-sm)", margin: "0 0 var(--p-space-2)" }}>
        {t("adminStats.subDescription")}
      </p>
      <div className="stat-grid">
        <StatCard to="/admin/agent-summary" value={data.agentsWithoutProductionCount} label="Agents without an active version" />
        <StatCard to="/admin/user-summary" value={data.disabledUsersCount} label="Disabled users" />
        {Object.entries(data.registryStatus)
          // The SkillHub Registry admin page was removed — its stat card only ever
          // existed to link there, and the backend's placeholder mirror (see
          // app/crud/registry.py) is still consumed elsewhere (VersionDetail's
          // dependency picker), just no longer has an admin status page of its own.
          .filter(([source]) => source !== "skillhub-registry")
          .map(([source, status]) => {
          const meta = REGISTRY_LABELS[source] ?? { title: source, path: "/admin/agent-templates" };
          // agent-templates is still the placeholder mirror — "unreachable syncs"
          // (consecutive_failures) is its real signal. mcp/model are the real
          // availability-sync implementation instead, where "stale" (unavailable)
          // item count is the meaningful number; they have no sync-failure concept.
          const isPlaceholder = source === "agent-templates";
          return (
            <StatCard
              key={source}
              to={meta.path}
              value={isPlaceholder ? status.consecutive_failures : status.stale_count}
              label={isPlaceholder ? `${meta.title}: unreachable syncs` : `${meta.title}: unavailable items`}
              breakdown={isPlaceholder ? `${status.stale_count} stale items` : `${status.total_count} total`}
            />
          );
        })}
      </div>

      <h2 style={{ fontSize: "var(--p-text-lg)", fontWeight: 700, margin: "var(--p-space-6) 0 var(--p-space-2)" }}>Overview</h2>
      <div className="stat-grid">
        <StatCard
          to="/admin/agent-summary"
          value={data.agentsTotal}
          label="Agents"
          breakdown={data.agentsByVisibility.map((v) => `${v.count} ${v.visibility}`).join(" · ")}
        />
        <StatCard value={versionsTotal} label="Versions" breakdown={Object.entries(data.versionsByStatus).map(([k, v]) => `${v} ${k}`).join(" · ")} />
        <StatCard
          to="/admin/user-summary"
          value={usersTotal}
          label="Users"
          breakdown={`${data.usersByRole.admin} admin · ${data.usersByRole.reviewer} reviewer · ${data.usersByRole.member} member`}
        />
        <StatCard to="/review-queue" value={data.pendingReviewCount} label="Pending reviews" />
      </div>

      <h2 style={{ fontSize: "var(--p-text-lg)", fontWeight: 700, margin: "var(--p-space-6) 0 var(--p-space-2)" }}>Trends (last 30 days)</h2>
      <TrendChart title="Agents created" series={[{ label: "Created", color: COLOR_PRIMARY, data: data.trends.agentsCreatedByDay }]} />
      <TrendChart
        title="Reviews"
        series={[
          { label: "Approved", color: COLOR_POSITIVE, data: data.trends.reviewsApprovedByDay },
          { label: "Rejected", color: COLOR_NEGATIVE, data: data.trends.reviewsRejectedByDay },
        ]}
      />

      <h2 style={{ fontSize: "var(--p-text-lg)", fontWeight: 700, margin: "var(--p-space-6) 0 var(--p-space-2)" }}>Review governance (last 30 days)</h2>
      <div className="stat-grid">
        <StatCard value={data.reviewGovernance.approvedLast30Days} label="Approved" />
        <StatCard value={data.reviewGovernance.rejectedLast30Days} label="Rejected" />
        <StatCard
          value={data.reviewGovernance.averageReviewTimeHours === null ? "—" : `${data.reviewGovernance.averageReviewTimeHours}h`}
          label="Avg. review time"
        />
      </div>

      <h2 style={{ fontSize: "var(--p-text-lg)", fontWeight: 700, margin: "var(--p-space-6) 0 var(--p-space-2)" }}>Storage</h2>
      <div className="stat-grid">
        <StatCard value={formatBytes(data.artifactStorageBytes)} label="Artifact storage" />
      </div>
    </div>
  );
}

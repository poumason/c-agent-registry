export type UserRole = "admin" | "reviewer" | "member";
export type UserStatus = "active" | "disabled";
export type AgentVisibility = "private" | "internal" | "public";
export type AssetRole = "owner" | "editor";
export type VersionStatus =
  | "draft"
  | "submitted"
  | "in_review"
  | "approved"
  | "rejected"
  | "active"
  | "archived";
export type ReviewResult = "pending" | "approved" | "rejected";
export type DependencyType = "skill" | "mcp";
// legacy = the first-party skills/mcps tables (Skills & MCP's upload flow).
// registry = an item mirrored via the SkillHub Registry page's external sync — see
// UI_AUDIT.md's registry-migration note. Skill-only; MCP dependencies resolve
// against the mcps table directly (see AvailabilityStatus below) — no separate
// "MCP registry" mirror.
export type DependencySource = "legacy" | "registry";

export type AvailabilityStatus = "available" | "unavailable";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
  updated_at: string;
}

export interface UserListResponse {
  items: User[];
  total: number;
  limit: number;
  offset: number;
}

export type UserSort = "newest" | "oldest" | "name";

export interface Agent {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  provider: string | null;
  visibility: AgentVisibility;
  created_by: string;
  created_at: string;
  updated_at: string;
  icon_path: string | null;
  category: string[];
  hello_msg: string | null;
  example_questions: string[];
  audience: string | null;
  doc_url: string | null;
}

export interface AgentListResponse {
  items: Agent[];
  total: number;
  limit: number;
  offset: number;
}

export type AgentSort = "newest" | "oldest" | "name";

export interface Member {
  id: string;
  user_id: string;
  agent_id: string;
  role: AssetRole;
  created_at: string;
  updated_at: string;
}

// One entry in an agent card's `skills` array (A2A 1.0 shape) — user-authored
// metadata describing a capability, distinct from AgentDependency's skill/mcp
// catalog references.
export interface AgentCardSkillEntry {
  id: string;
  name: string;
  description: string;
  tags: string[];
  examples: string[];
  inputModes: string[];
  outputModes: string[];
}

export interface AgentVersion {
  slug: string;
  agent_id: string;
  version: number;
  streaming: boolean;
  default_input_modes: string[];
  default_output_modes: string[];
  status: VersionStatus;
  package_path: string | null;
  skills: AgentCardSkillEntry[];
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
}

export interface AgentFab {
  fab_id: string;
  agent_version_slug: string;
  url: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentCardInterface {
  url: string;
  protocolBinding: string;
  protocolVersion: string;
}

export interface AgentCardProvider {
  organization: string | null;
  url: string | null;
}

export interface AgentCardCapabilities {
  streaming: boolean;
  pushNotifications: boolean;
  extendedAgentCard: boolean;
}

export interface AgentCard {
  name: string;
  description: string | null;
  supportedInterfaces: AgentCardInterface[];
  provider: AgentCardProvider | null;
  iconUrl: string | null;
  version: string;
  capabilities: AgentCardCapabilities;
  defaultInputModes: string[];
  defaultOutputModes: string[];
  skills: AgentCardSkillEntry[];
}

export interface Review {
  id: string;
  agent_slug: string;
  reviewer_id: string;
  priority: number;
  result: ReviewResult;
  signoff_by: string | null;
  comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminAgentItem {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  visibility: AgentVisibility;
  created_at: string;
  owner_id: string;
  owner_name: string;
  owner_email: string;
}

export interface AdminAgentListResponse {
  items: AdminAgentItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface UserSummary {
  totalUsers: number;
  activeCount: number;
  disabledCount: number;
  usersWithoutAgents: number;
  byRole: { admin: number; reviewer: number; member: number };
  trends: {
    createdByDay: TrendPoint[];
    deletedByDay: TrendPoint[];
  };
  topAgentOwners: { userId: string; userName: string; agentCount: number }[];
  topReviewers: { userId: string; userName: string; reviewCount: number }[];
}

export interface AdminStats {
  agentsTotal: number;
  agentsByVisibility: { visibility: AgentVisibility; count: number }[];
  agentsWithoutProductionCount: number;
  versionsByStatus: Record<string, number>;
  usersTotal: number;
  usersByRole: { admin: number; reviewer: number; member: number };
  disabledUsersCount: number;
  pendingReviewCount: number;
  registryStatus: Record<string, RegistryStatus>;
  trends: {
    agentsCreatedByDay: TrendPoint[];
    reviewsApprovedByDay: TrendPoint[];
    reviewsRejectedByDay: TrendPoint[];
  };
  reviewGovernance: {
    approvedLast30Days: number;
    rejectedLast30Days: number;
    averageReviewTimeHours: number | null;
  };
  artifactStorageBytes: number;
}

export interface AgentSummary {
  total: number;
  withProduction: number;
  withoutProduction: number;
  withoutAnyVersion: number;
  byVisibility: { visibility: AgentVisibility; count: number }[];
}

// mcp/model used to be placeholder sources here too — they're real now (their own
// availability-sync implementation on the mcps/ai_models tables), not part of this
// mirrored-external-registry contract.
export type RegistrySource = "agent-templates" | "skillhub-registry";

export interface RegistryItem {
  id: string;
  name: string;
  version: string | null;
  category: string | null;
  deprecated: boolean;
  last_seen_at: string | null;
}

export interface RegistryStatus {
  total_count: number;
  last_synced_at: string | null;
  consecutive_failures: number;
  stale_count: number;
}

export interface RegistryOverview {
  status: RegistryStatus;
  items: RegistryItem[];
}

export interface ReviewerCandidate {
  id: string;
  name: string;
  email: string;
}

export interface ReviewQueueItem {
  id: string;
  result: ReviewResult;
  priority: number;
  comment: string | null;
  created_at: string;
  updated_at: string;
  agent_slug: string;
  agent_name: string;
  version_slug: string;
  version_number: number;
  reviewer_id: string;
  reviewer_name: string;
  submitted_by_id: string;
  submitted_by_name: string;
  signoff_by_id: string | null;
  signoff_by_name: string | null;
}

export interface ReviewQueueResponse {
  items: ReviewQueueItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface TrendPoint {
  date: string;
  count: number;
}

export interface ReviewSummary {
  pendingCount: number;
  totalApproved: number;
  totalRejected: number;
  last30Days: { approved: number; rejected: number };
  averageReviewTimeHours: number | null;
  trends: {
    approvedByDay: TrendPoint[];
    rejectedByDay: TrendPoint[];
  };
  topReviewers: {
    reviewerId: string;
    reviewerName: string;
    total: number;
    approved: number;
    rejected: number;
  }[];
}

export interface SkillFab {
  skill_id: string;
  fab_id: string;
  created_at: string;
}

export interface Skill {
  id: string;
  name: string;
  version: string;
  description: string | null;
  category: string | null;
  tags: string[];
  created_by: string;
  bucket_path: string;
  mcp_dependency: string[];
  status: AvailabilityStatus;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
  fabs: SkillFab[];
}

export interface Fab {
  id: string;
  fab: string;
}

export interface McpFab {
  mcp_id: string;
  fab_id: string;
  host: string;
  status: AvailabilityStatus;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

// host/status/last_synced_at moved to McpFab — an MCP is now deployed (and synced)
// independently per fab rather than having one global host.
export interface Mcp {
  id: string;
  name: string;
  version: string;
  description: string | null;
  category: string | null;
  tags: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
  fabs: McpFab[];
}

export interface SyncResult<T> {
  synced_at: string;
  total: number;
  available: number;
  unavailable: number;
  items: T[];
}

// `changed` is true when this row's `status` flipped during the sync run that
// produced it — lets the frontend highlight exactly what a sync touched.
export type SkillSyncItem = Skill & { changed: boolean };
export type McpSyncItem = Mcp & { fabs: (McpFab & { changed: boolean })[] };

export interface AIModel {
  id: string;
  name: string;
  provider: string;
  model_id: string;
  description: string | null;
  category: string | null;
  tags: string[];
  created_by: string;
  status: AvailabilityStatus;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentDependency {
  id: string;
  agent_slug: string;
  dependency_id: string;
  type: DependencyType;
  source: DependencySource;
  created_at: string;
}

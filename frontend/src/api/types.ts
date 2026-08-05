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

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
  updated_at: string;
}

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
}

export interface Member {
  id: string;
  user_id: string;
  agent_id: string;
  role: AssetRole;
  created_at: string;
  updated_at: string;
}

export interface AgentVersion {
  slug: string;
  agent_id: string;
  version: number;
  url: string | null;
  streaming: boolean;
  default_input_modes: string[];
  default_output_modes: string[];
  status: VersionStatus;
  package_path: string | null;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
}

export interface Review {
  id: string;
  agent_slug: string;
  reviewer_id: string;
  priority: number;
  result: ReviewResult;
  signoff_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewerCandidate {
  id: string;
  name: string;
  email: string;
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
  created_at: string;
  updated_at: string;
}

export interface Mcp {
  id: string;
  name: string;
  version: string;
  description: string | null;
  category: string | null;
  tags: string[];
  created_by: string;
  host: string;
  created_at: string;
  updated_at: string;
}

export interface AgentDependency {
  id: string;
  agent_slug: string;
  dependency_id: string;
  type: DependencyType;
  created_at: string;
}

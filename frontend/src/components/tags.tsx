import { Tag } from "antd";
import type {
  AgentVisibility,
  AssetRole,
  ReviewResult,
  UserRole,
  UserStatus,
  VersionStatus,
} from "../api/types";

const versionStatusConfig: Record<VersionStatus, { color: string; label: string }> = {
  draft: { color: "default", label: "draft" },
  submitted: { color: "processing", label: "submitted" },
  in_review: { color: "processing", label: "in_review" },
  approved: { color: "success", label: "approved" },
  rejected: { color: "error", label: "rejected" },
  active: { color: "success", label: "active" },
  archived: { color: "default", label: "archived" },
};

export function VersionStatusTag({ status }: { status: VersionStatus }) {
  const cfg = versionStatusConfig[status];
  const solid = status === "active";
  return (
    <Tag color={cfg.color} variant={solid ? "filled" : undefined}>
      {cfg.label}
    </Tag>
  );
}

const visibilityLabel: Record<AgentVisibility, string> = {
  private: "private",
  internal: "internal",
  public: "public",
};

export function VisibilityTag({ visibility }: { visibility: AgentVisibility }) {
  return (
    <Tag color={visibility === "public" ? "blue" : "default"}>
      {visibilityLabel[visibility]}
    </Tag>
  );
}

export function AssetRoleTag({ role }: { role: AssetRole }) {
  return <Tag color={role === "owner" ? "blue" : "default"}>{role}</Tag>;
}

const userRoleColor: Record<UserRole, string> = {
  admin: "blue",
  reviewer: "cyan",
  member: "default",
};

export function UserRoleTag({ role }: { role: UserRole }) {
  return <Tag color={userRoleColor[role]}>{role}</Tag>;
}

export function UserStatusTag({ status }: { status: UserStatus }) {
  return <Tag color={status === "active" ? "success" : "error"}>{status}</Tag>;
}

const reviewResultColor: Record<ReviewResult, string> = {
  pending: "default",
  approved: "success",
  rejected: "error",
};

export function ReviewResultTag({ result }: { result: ReviewResult }) {
  return <Tag color={reviewResultColor[result]}>{result}</Tag>;
}

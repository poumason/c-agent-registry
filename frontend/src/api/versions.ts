import { apiClient } from "./client";
import type {
  AgentCard,
  AgentCardSkillEntry,
  AgentDependency,
  AgentFab,
  AgentVersion,
  DependencySource,
  DependencyType,
} from "./types";

export async function listVersions(agentSlug: string): Promise<AgentVersion[]> {
  const { data } = await apiClient.get<AgentVersion[]>(`/agents/${agentSlug}/versions`);
  return data;
}

export async function getVersion(versionSlug: string): Promise<AgentVersion> {
  const { data } = await apiClient.get<AgentVersion>(`/versions/${versionSlug}`);
  return data;
}

export interface CreateVersionInput {
  streaming?: boolean;
  default_input_modes?: string[];
  default_output_modes?: string[];
}

export async function createVersion(
  agentSlug: string,
  input: CreateVersionInput = {},
): Promise<AgentVersion> {
  const { data } = await apiClient.post<AgentVersion>(
    `/agents/${agentSlug}/versions`,
    input,
  );
  return data;
}

export interface UpdateVersionInput extends CreateVersionInput {
  skills?: AgentCardSkillEntry[];
}

export async function updateVersion(
  versionSlug: string,
  input: UpdateVersionInput,
): Promise<AgentVersion> {
  const { data } = await apiClient.patch<AgentVersion>(`/versions/${versionSlug}`, input);
  return data;
}

export async function submitVersion(
  versionSlug: string,
  reviewerIds: string[],
): Promise<AgentVersion> {
  const { data } = await apiClient.post<AgentVersion>(`/versions/${versionSlug}/submit`, {
    reviewer_ids: reviewerIds,
  });
  return data;
}

export async function activateVersion(versionSlug: string): Promise<AgentVersion> {
  const { data } = await apiClient.post<AgentVersion>(`/versions/${versionSlug}/activate`);
  return data;
}

export async function deactivateVersion(versionSlug: string): Promise<AgentVersion> {
  const { data } = await apiClient.post<AgentVersion>(`/versions/${versionSlug}/deactivate`);
  return data;
}

export async function getDownloadUrl(versionSlug: string): Promise<string> {
  const { data } = await apiClient.get<{ url: string }>(`/versions/${versionSlug}/download`);
  return data.url;
}

export async function listDependencies(versionSlug: string): Promise<AgentDependency[]> {
  const { data } = await apiClient.get<AgentDependency[]>(
    `/versions/${versionSlug}/dependencies`,
  );
  return data;
}

export async function addDependency(
  versionSlug: string,
  dependencyId: string,
  type: DependencyType,
  source: DependencySource = "legacy",
  fabId?: string | null,
): Promise<AgentDependency> {
  const { data } = await apiClient.post<AgentDependency>(
    `/versions/${versionSlug}/dependencies`,
    { dependency_id: dependencyId, type, source, fab_id: fabId ?? null },
  );
  return data;
}

export async function removeDependency(
  versionSlug: string,
  dependencyRowId: string,
): Promise<void> {
  await apiClient.delete(`/versions/${versionSlug}/dependencies/${dependencyRowId}`);
}

export async function listVersionFabs(versionSlug: string): Promise<AgentFab[]> {
  const { data } = await apiClient.get<AgentFab[]>(`/versions/${versionSlug}/fabs`);
  return data;
}

export interface SetVersionFabsEntry {
  fab_id: string;
  url: string;
}

export async function setVersionFabs(
  versionSlug: string,
  fabs: SetVersionFabsEntry[],
): Promise<AgentFab[]> {
  const { data } = await apiClient.put<AgentFab[]>(`/versions/${versionSlug}/fabs`, { fabs });
  return data;
}

export async function getAgentCard(versionSlug: string): Promise<AgentCard> {
  const { data } = await apiClient.get<AgentCard>(`/versions/${versionSlug}/agent-card`);
  return data;
}

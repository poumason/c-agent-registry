import { apiClient } from "./client";
import type { Fab, Mcp, McpFab, McpSyncItem, Skill, SkillFab, SkillSyncItem, SyncResult } from "./types";

export async function listSkills(): Promise<Skill[]> {
  const { data } = await apiClient.get<Skill[]>("/skills");
  return data;
}

export async function syncSkills(): Promise<SyncResult<SkillSyncItem>> {
  const { data } = await apiClient.post<SyncResult<SkillSyncItem>>("/skills/sync");
  return data;
}

export async function listMcps(): Promise<Mcp[]> {
  const { data } = await apiClient.get<Mcp[]>("/mcps");
  return data;
}

export async function syncMcps(): Promise<SyncResult<McpSyncItem>> {
  const { data } = await apiClient.post<SyncResult<McpSyncItem>>("/mcps/sync");
  return data;
}

export interface AssignMcpFabInput {
  fab_id: string;
  host: string;
}

export async function assignMcpFab(mcpId: string, input: AssignMcpFabInput): Promise<McpFab> {
  const { data } = await apiClient.post<McpFab>(`/mcps/${mcpId}/fabs`, input);
  return data;
}

export async function removeMcpFab(mcpId: string, fabId: string): Promise<void> {
  await apiClient.delete(`/mcps/${mcpId}/fabs/${fabId}`);
}

export async function assignSkillFab(skillId: string, fabId: string): Promise<SkillFab> {
  const { data } = await apiClient.post<SkillFab>(`/skills/${skillId}/fabs`, { fab_id: fabId });
  return data;
}

export async function removeSkillFab(skillId: string, fabId: string): Promise<void> {
  await apiClient.delete(`/skills/${skillId}/fabs/${fabId}`);
}

export async function listFabs(): Promise<Fab[]> {
  const { data } = await apiClient.get<Fab[]>("/fabs");
  return data;
}

export interface CreateFabInput {
  fab: string;
}

export async function createFab(input: CreateFabInput): Promise<Fab> {
  const { data } = await apiClient.post<Fab>("/fabs", input);
  return data;
}

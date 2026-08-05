import { apiClient } from "./client";
import type { Agent, AgentVisibility, AssetRole, Member } from "./types";

export async function listAgents(): Promise<Agent[]> {
  const { data } = await apiClient.get<Agent[]>("/agents");
  return data;
}

export async function getAgent(slug: string): Promise<Agent> {
  const { data } = await apiClient.get<Agent>(`/agents/${slug}`);
  return data;
}

export interface CreateAgentInput {
  slug: string;
  name: string;
  description?: string;
  provider?: string;
  visibility: AgentVisibility;
}

export async function createAgent(input: CreateAgentInput): Promise<Agent> {
  const { data } = await apiClient.post<Agent>("/agents", input);
  return data;
}

export async function listMembers(slug: string): Promise<Member[]> {
  const { data } = await apiClient.get<Member[]>(`/agents/${slug}/members`);
  return data;
}

export async function inviteMember(slug: string, userId: string): Promise<Member> {
  const { data } = await apiClient.post<Member>(`/agents/${slug}/members`, {
    user_id: userId,
  });
  return data;
}

export async function removeMember(slug: string, userId: string): Promise<void> {
  await apiClient.delete(`/agents/${slug}/members/${userId}`);
}

export type { AssetRole };

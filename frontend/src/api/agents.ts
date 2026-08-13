import { apiClient } from "./client";
import type { Agent, AgentListResponse, AgentSort, AgentVisibility, AssetRole, Member } from "./types";

export interface ListAgentsParams {
  q?: string;
  sort?: AgentSort;
  visibility?: AgentVisibility;
  limit?: number;
  offset?: number;
}

export async function listAgents(params: ListAgentsParams = {}): Promise<AgentListResponse> {
  const { data } = await apiClient.get<AgentListResponse>("/agents", { params });
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
  icon_path?: string;
  category?: string[];
  hello_msg?: string;
  example_questions?: string[];
}

export async function createAgent(input: CreateAgentInput): Promise<Agent> {
  const { data } = await apiClient.post<Agent>("/agents", input);
  return data;
}

export interface UpdateAgentInput {
  name?: string;
  description?: string;
  provider?: string;
  visibility?: AgentVisibility;
  icon_path?: string;
  category?: string[];
  hello_msg?: string;
  example_questions?: string[];
}

export async function updateAgent(slug: string, input: UpdateAgentInput): Promise<Agent> {
  const { data } = await apiClient.patch<Agent>(`/agents/${slug}`, input);
  return data;
}

export async function deleteAgent(slug: string): Promise<void> {
  await apiClient.delete(`/agents/${slug}`);
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

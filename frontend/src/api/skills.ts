import { apiClient } from "./client";
import type { Mcp, Skill } from "./types";

export async function listSkills(): Promise<Skill[]> {
  const { data } = await apiClient.get<Skill[]>("/skills");
  return data;
}

export interface CreateSkillInput {
  file: File;
  name: string;
  version: string;
  description?: string;
  category?: string;
  tags?: string;
}

export async function createSkill(input: CreateSkillInput): Promise<Skill> {
  const form = new FormData();
  form.set("file", input.file);
  form.set("name", input.name);
  form.set("version", input.version);
  if (input.description) form.set("description", input.description);
  if (input.category) form.set("category", input.category);
  if (input.tags) form.set("tags", input.tags);
  const { data } = await apiClient.post<Skill>("/skills", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function listMcps(): Promise<Mcp[]> {
  const { data } = await apiClient.get<Mcp[]>("/mcps");
  return data;
}

export interface CreateMcpInput {
  name: string;
  version: string;
  host: string;
  description?: string;
  category?: string;
  tags?: string[];
}

export async function createMcp(input: CreateMcpInput): Promise<Mcp> {
  const { data } = await apiClient.post<Mcp>("/mcps", { tags: [], ...input });
  return data;
}

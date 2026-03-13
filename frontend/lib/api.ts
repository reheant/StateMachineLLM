import type { Run, Artifacts, Example } from "./types";

export async function fetchHistory(): Promise<Run[]> {
  const res = await fetch("/api/history");
  if (!res.ok) throw new Error("Failed to fetch history");
  return res.json();
}

export async function fetchArtifacts(folder: string): Promise<Artifacts> {
  const res = await fetch(`/api/artifacts?folder=${encodeURIComponent(folder)}`);
  if (!res.ok) throw new Error("Failed to fetch artifacts");
  return res.json();
}

export async function fetchExamples(): Promise<Example[]> {
  const res = await fetch("/api/examples");
  if (!res.ok) throw new Error("Failed to fetch examples");
  return res.json();
}

export async function fetchModels(): Promise<string[]> {
  const res = await fetch("/api/models");
  if (!res.ok) throw new Error("Failed to fetch models");
  return res.json();
}

export async function fetchDescription(preset: string): Promise<string> {
  const res = await fetch(`/api/description?preset=${encodeURIComponent(preset)}`);
  if (!res.ok) throw new Error("Failed to fetch description");
  const data = await res.json();
  return data.description;
}

export function imageUrl(path: string): string {
  return `/api/image?path=${encodeURIComponent(path)}`;
}

export function fileUrl(path: string): string {
  return `/api/file?path=${encodeURIComponent(path)}`;
}

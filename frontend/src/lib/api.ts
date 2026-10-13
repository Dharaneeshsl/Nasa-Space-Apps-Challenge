import {
  AskResponse,
  ExperimentItem,
  CompareResponse,
  BriefResponse,
  StatusResponse
} from './types';

const API_BASE = '/api';

export async function askQuestion(query: string): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    throw new Error(`Failed to query CombustionLens API: ${res.statusText}`);
  }
  return res.json();
}

export async function getVerifiedExperiments(): Promise<ExperimentItem[]> {
  const res = await fetch(`${API_BASE}/experiments`);
  if (!res.ok) {
    throw new Error(`Failed to fetch verified experiments: ${res.statusText}`);
  }
  return res.json();
}

export async function compareExperiments(id_a: number, id_b: number): Promise<CompareResponse> {
  const res = await fetch(`${API_BASE}/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_a, id_b }),
  });
  if (!res.ok) {
    throw new Error(`Failed to execute comparison: ${res.statusText}`);
  }
  return res.json();
}

export async function getSafetyBrief(question: string): Promise<BriefResponse> {
  const res = await fetch(`${API_BASE}/brief`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    throw new Error(`Failed to generate safety brief: ${res.statusText}`);
  }
  return res.json();
}

export async function getSystemStatus(): Promise<StatusResponse> {
  const res = await fetch(`${API_BASE}/status`);
  if (!res.ok) {
    throw new Error(`Failed to fetch system status: ${res.statusText}`);
  }
  return res.json();
}

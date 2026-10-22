import type {
  CompileResponse,
  StatsResponse,
  HistoryItem,
  HealthResponse,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export async function compileCode(params: {
  source_code: string;
  language?: string;
  force_ai?: boolean;
  provider?: string;
  model?: string;
}): Promise<CompileResponse> {
  const res = await fetch(`${API_BASE}/compile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_code: params.source_code,
      language: params.language || 'python',
      force_ai: Boolean(params.force_ai),
      provider: params.provider || undefined,
      model: params.model || undefined,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message =
      errorData.detail?.message ||
      errorData.detail ||
      `Compilation failed with status ${res.status}`;
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
  }

  return res.json();
}

export async function fetchStats(): Promise<StatsResponse> {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function fetchHistory(limit = 15, offset = 0): Promise<{
  items: HistoryItem[];
  total: number;
}> {
  const res = await fetch(`${API_BASE}/history?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error('Failed to fetch history');
  return res.json();
}

export async function clearCache(): Promise<{ cleared_entries: number; message: string }> {
  const res = await fetch(`${API_BASE}/cache?confirm=true`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to clear cache');
  }
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Failed to fetch health status');
  return res.json();
}

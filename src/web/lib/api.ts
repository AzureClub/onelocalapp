const API_BASE = process.env.API_BASE_URL || "http://localhost:8000";

export type RunMeta = {
  runId: string;
  service: string;
  operation: string;
  mode: "connected" | "disconnected";
  durationMs: number;
  blobResultUri?: string | null;
  blobInputUri?: string | null;
  summary: Record<string, unknown>;
};

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function apiJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  return handle<T>(res);
}

export async function apiForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: form, cache: "no-store" });
  return handle<T>(res);
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  return handle<T>(res);
}

export { API_BASE };

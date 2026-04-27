import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type ServiceHealth = { service: string; mode: string; configured: boolean; ok: boolean; endpoint?: string; error?: string };

async function fetchHealth() {
  const base = process.env.API_BASE_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${base}/services/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as { globalMode: string; services: ServiceHealth[] };
  } catch { return null; }
}

export default async function SettingsPage() {
  const data = await fetchHealth();
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings & Health</h1>
      <Card>
        <CardHeader>
          <CardTitle>
            Global mode: <Badge variant={data?.globalMode === "connected" ? "success" : "warning"}>{data?.globalMode ?? "unknown"}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            {(data?.services ?? []).map((s) => (
              <div key={s.service} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <div className="font-medium">{s.service}</div>
                  <div className="text-xs text-muted-foreground break-all">{s.endpoint ?? "(no endpoint)"}</div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={s.mode === "connected" ? "success" : "warning"}>{s.mode}</Badge>
                  <Badge variant={s.ok ? "success" : "destructive"}>{s.ok ? "ok" : "down"}</Badge>
                </div>
              </div>
            ))}
            {!data && <div className="text-muted-foreground">API not reachable.</div>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

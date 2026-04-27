import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Run = { service: string; mode: string; status: string; durationMs: number };

async function fetchRuns() {
  const base = process.env.API_BASE_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${base}/api/history?limit=500`, { cache: "no-store" });
    if (!res.ok) return [] as Run[];
    return (await res.json()).items as Run[];
  } catch { return [] as Run[]; }
}

function aggregate(runs: Run[]) {
  const byService = new Map<string, { total: number; ok: number; err: number; avg: number }>();
  for (const r of runs) {
    const cur = byService.get(r.service) ?? { total: 0, ok: 0, err: 0, avg: 0 };
    cur.total += 1;
    cur.avg = (cur.avg * (cur.total - 1) + r.durationMs) / cur.total;
    if (r.status === "ok") cur.ok += 1; else cur.err += 1;
    byService.set(r.service, cur);
  }
  return Array.from(byService.entries()).map(([service, v]) => ({ service, ...v, avg: Math.round(v.avg) }));
}

export default async function DashboardPage() {
  const runs = await fetchRuns();
  const rows = aggregate(runs);
  const totalConnected = runs.filter((r) => r.mode === "connected").length;
  const totalDisconnected = runs.filter((r) => r.mode === "disconnected").length;
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card><CardHeader><CardTitle>Total runs</CardTitle></CardHeader><CardContent className="text-3xl font-bold">{runs.length}</CardContent></Card>
        <Card><CardHeader><CardTitle>Connected</CardTitle></CardHeader><CardContent className="text-3xl font-bold text-emerald-500">{totalConnected}</CardContent></Card>
        <Card><CardHeader><CardTitle>Disconnected</CardTitle></CardHeader><CardContent className="text-3xl font-bold text-amber-500">{totalDisconnected}</CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle>By service</CardTitle></CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="py-2 pr-4">Service</th><th className="py-2 pr-4">Total</th>
                <th className="py-2 pr-4">OK</th><th className="py-2 pr-4">Errors</th>
                <th className="py-2 pr-4">Avg duration</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.service} className="border-b">
                  <td className="py-2 pr-4 font-medium">{r.service}</td>
                  <td className="py-2 pr-4">{r.total}</td>
                  <td className="py-2 pr-4 text-emerald-500">{r.ok}</td>
                  <td className="py-2 pr-4 text-destructive">{r.err}</td>
                  <td className="py-2 pr-4">{r.avg} ms</td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={5} className="py-6 text-center text-muted-foreground">No data yet.</td></tr>}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

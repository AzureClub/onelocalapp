import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Run = {
  id: string;
  service: string;
  operation: string;
  mode: string;
  status: string;
  createdAt: string;
  durationMs: number;
  summary?: Record<string, unknown>;
};

async function fetchRuns(searchParams: { service?: string; mode?: string; status?: string }) {
  const base = process.env.API_BASE_URL || "http://localhost:8000";
  const qs = new URLSearchParams();
  if (searchParams.service) qs.set("service", searchParams.service);
  if (searchParams.mode) qs.set("mode", searchParams.mode);
  if (searchParams.status) qs.set("status", searchParams.status);
  qs.set("limit", "100");
  try {
    const res = await fetch(`${base}/api/history?${qs.toString()}`, { cache: "no-store" });
    if (!res.ok) return { items: [] as Run[] };
    return (await res.json()) as { items: Run[] };
  } catch {
    return { items: [] as Run[] };
  }
}

export default async function HistoryPage({ searchParams }: { searchParams: Promise<Record<string, string>> }) {
  const sp = await searchParams;
  const { items } = await fetchRuns(sp);
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">History</h1>
      <Card>
        <CardHeader><CardTitle>Recent runs ({items.length})</CardTitle></CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="py-2 pr-4">When</th><th className="py-2 pr-4">Service</th>
                  <th className="py-2 pr-4">Operation</th><th className="py-2 pr-4">Mode</th>
                  <th className="py-2 pr-4">Status</th><th className="py-2 pr-4">Duration</th>
                  <th className="py-2 pr-4">Summary</th>
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <tr key={r.id} className="border-b hover:bg-accent/40">
                    <td className="py-2 pr-4 whitespace-nowrap">{new Date(r.createdAt).toLocaleString()}</td>
                    <td className="py-2 pr-4">{r.service}</td>
                    <td className="py-2 pr-4">{r.operation}</td>
                    <td className="py-2 pr-4"><Badge variant={r.mode === "connected" ? "success" : "warning"}>{r.mode}</Badge></td>
                    <td className="py-2 pr-4"><Badge variant={r.status === "ok" ? "success" : "destructive"}>{r.status}</Badge></td>
                    <td className="py-2 pr-4">{r.durationMs} ms</td>
                    <td className="py-2 pr-4 max-w-md truncate text-muted-foreground">{r.summary ? JSON.stringify(r.summary) : ""}</td>
                  </tr>
                ))}
                {items.length === 0 && <tr><td colSpan={7} className="py-6 text-center text-muted-foreground">No runs yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

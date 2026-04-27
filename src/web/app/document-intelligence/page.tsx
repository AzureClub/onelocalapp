"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { JsonViewer } from "@/components/json-viewer";

const models = ["prebuilt-read", "prebuilt-layout", "prebuilt-invoice", "prebuilt-receipt", "prebuilt-idDocument"];

export default function DocIntelPage() {
  const [file, setFile] = useState<File | null>(null);
  const [model, setModel] = useState("prebuilt-read");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    if (!file) return;
    setBusy(true); setErr(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("model", model);
      const res = await fetch("/api/proxy/docintel/analyze", { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) { setErr(String(e)); } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Document Intelligence</h1>
      <Card>
        <CardHeader><CardTitle>Analyze document</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <Input type="file" accept="application/pdf,image/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <div className="flex flex-wrap gap-2">
            {models.map((m) => (
              <Button key={m} variant={model === m ? "default" : "outline"} size="sm" onClick={() => setModel(m)}>{m}</Button>
            ))}
          </div>
          <Button onClick={run} disabled={!file || busy}>{busy ? "Analyzing..." : "Analyze"}</Button>
          {err && <div className="text-destructive text-sm">{err}</div>}
          {result ? <JsonViewer data={result} /> : null}
        </CardContent>
      </Card>
    </div>
  );
}

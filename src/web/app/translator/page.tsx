"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { JsonViewer } from "@/components/json-viewer";

export default function TranslatorPage() {
  const [text, setText] = useState("Cześć, jak się masz?");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("en,de,fr");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    setBusy(true); setErr(null);
    try {
      const res = await fetch("/api/proxy/translator/translate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, from: from || undefined, to: to.split(",").map((s) => s.trim()).filter(Boolean) }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) { setErr(String(e)); } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Translator</h1>
      <Card>
        <CardHeader><CardTitle>Translate text</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <Textarea value={text} onChange={(e) => setText(e.target.value)} />
          <div className="grid grid-cols-2 gap-3">
            <Input value={from} onChange={(e) => setFrom(e.target.value)} placeholder="From (auto-detect if empty)" />
            <Input value={to} onChange={(e) => setTo(e.target.value)} placeholder="To (comma-separated, e.g. en,de,fr)" />
          </div>
          <Button onClick={run} disabled={busy}>{busy ? "Translating..." : "Translate"}</Button>
          {err && <div className="text-destructive text-sm">{err}</div>}
          {result ? <JsonViewer data={result} /> : null}
        </CardContent>
      </Card>
    </div>
  );
}

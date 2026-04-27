"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { JsonViewer } from "@/components/json-viewer";

const tasks = [
  { id: "detect", label: "Detect language" },
  { id: "pii", label: "PII Detection" },
  { id: "ner", label: "Named Entity Recognition" },
  { id: "health", label: "Text Analytics for Health" },
] as const;
type Task = (typeof tasks)[number]["id"];

export default function LanguagePage() {
  const [task, setTask] = useState<Task>("detect");
  const [text, setText] = useState("Patient John Doe was prescribed 200mg Ibuprofen for back pain on March 5th.");
  const [language, setLanguage] = useState("en");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    setBusy(true); setErr(null);
    try {
      const body: Record<string, unknown> = { text };
      if (task !== "detect") body.language = language;
      const res = await fetch(`/api/proxy/language/${task}`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) { setErr(String(e)); } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Language</h1>
      <Card>
        <CardHeader><CardTitle>Analyze text</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {tasks.map((t) => (
              <Button key={t.id} variant={task === t.id ? "default" : "outline"} size="sm" onClick={() => setTask(t.id)}>
                {t.label}
              </Button>
            ))}
          </div>
          <Textarea value={text} onChange={(e) => setText(e.target.value)} />
          {task !== "detect" && (
            <Input value={language} onChange={(e) => setLanguage(e.target.value)} placeholder="Language code (e.g. en, pl, de)" />
          )}
          <Button onClick={run} disabled={busy || !text}>{busy ? "Analyzing..." : "Analyze"}</Button>
          {err && <div className="text-destructive text-sm">{err}</div>}
          {result ? <JsonViewer data={result} /> : null}
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { JsonViewer } from "@/components/json-viewer";
import { Badge } from "@/components/ui/badge";

export default function SpeechPage() {
  const [audio, setAudio] = useState<File | null>(null);
  const [language, setLanguage] = useState("en-US");
  const [sttResult, setSttResult] = useState<unknown>(null);
  const [sttBusy, setSttBusy] = useState(false);
  const [sttErr, setSttErr] = useState<string | null>(null);

  async function runSTT() {
    if (!audio) return;
    setSttBusy(true); setSttErr(null);
    try {
      const fd = new FormData();
      fd.append("audio", audio);
      fd.append("language", language);
      const res = await fetch("/api/proxy/speech/stt", { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      setSttResult(await res.json());
    } catch (e) { setSttErr(String(e)); } finally { setSttBusy(false); }
  }

  const [text, setText] = useState("Hello from Azure AI containers running locally.");
  const [voice, setVoice] = useState("en-US-JennyNeural");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [ttsBusy, setTtsBusy] = useState(false);
  const [ttsErr, setTtsErr] = useState<string | null>(null);

  async function runTTS() {
    setTtsBusy(true); setTtsErr(null);
    try {
      const res = await fetch("/api/proxy/speech/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice }),
      });
      if (!res.ok) throw new Error(await res.text());
      const blob = await res.blob();
      setAudioUrl(URL.createObjectURL(blob));
    } catch (e) { setTtsErr(String(e)); } finally { setTtsBusy(false); }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Speech</h1>
        <p className="text-muted-foreground">Speech-to-Text and Neural Text-to-Speech via Azure AI containers.</p>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">Speech-to-Text <Badge variant="outline">speech-stt</Badge></CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input type="file" accept="audio/*" onChange={(e) => setAudio(e.target.files?.[0] ?? null)} />
            <Input value={language} onChange={(e) => setLanguage(e.target.value)} placeholder="en-US" />
            <Button onClick={runSTT} disabled={!audio || sttBusy}>{sttBusy ? "Transcribing..." : "Transcribe"}</Button>
            {sttErr && <div className="text-destructive text-sm">{sttErr}</div>}
            {sttResult ? <JsonViewer data={sttResult} /> : null}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">Text-to-Speech <Badge variant="outline">speech-tts</Badge></CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea value={text} onChange={(e) => setText(e.target.value)} />
            <Input value={voice} onChange={(e) => setVoice(e.target.value)} placeholder="Voice (e.g. en-US-JennyNeural)" />
            <Button onClick={runTTS} disabled={ttsBusy}>{ttsBusy ? "Synthesizing..." : "Synthesize"}</Button>
            {ttsErr && <div className="text-destructive text-sm">{ttsErr}</div>}
            {audioUrl && <audio controls src={audioUrl} className="w-full" />}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

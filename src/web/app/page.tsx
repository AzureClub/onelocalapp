import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

const tiles = [
  { href: "/speech", title: "Speech", desc: "Speech-to-Text and Neural TTS" },
  { href: "/translator", title: "Translator", desc: "Text translation across 100+ languages" },
  { href: "/language", title: "Language", desc: "Detect, PII, NER, Health" },
  { href: "/document-intelligence", title: "Document Intelligence", desc: "Read, Layout, Prebuilt models" },
  { href: "/content-safety", title: "Content Safety", desc: "Text/Image moderation, Prompt Shields" },
];

export default function Home() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Welcome 👋</h1>
        <p className="text-muted-foreground">
          A live demo of Azure AI containerized services. Switch any service between
          <span className="font-medium"> connected </span>
          (running in this Container Apps environment) and
          <span className="font-medium"> disconnected </span>
          (on-premise) by changing environment variables only — no code changes.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {tiles.map((t) => (
          <Link key={t.href} href={t.href}>
            <Card className="transition-shadow hover:shadow-md">
              <CardHeader>
                <CardTitle>{t.title}</CardTitle>
                <CardDescription>{t.desc}</CardDescription>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">Open →</CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

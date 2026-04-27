"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Mic, Languages, FileText, FileSearch, Shield, History, LayoutDashboard, Settings } from "lucide-react";

const items = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/speech", label: "Speech (STT/TTS)", icon: Mic },
  { href: "/translator", label: "Translator", icon: Languages },
  { href: "/language", label: "Language", icon: FileText },
  { href: "/document-intelligence", label: "Document Intelligence", icon: FileSearch },
  { href: "/content-safety", label: "Content Safety", icon: Shield },
  { href: "/history", label: "History", icon: History },
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-64 shrink-0 border-r bg-card md:block">
      <div className="px-6 py-5 border-b">
        <div className="text-xl font-bold tracking-tight">OneLocalApp</div>
        <div className="text-xs text-muted-foreground">Azure AI Containers showcase</div>
      </div>
      <nav className="flex flex-col gap-1 p-3">
        {items.map((it) => {
          const active = pathname === it.href || (it.href !== "/" && pathname.startsWith(it.href));
          const Icon = it.icon;
          return (
            <Link
              key={it.href}
              href={it.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" /> {it.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

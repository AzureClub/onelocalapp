"use client";
import { cn } from "@/lib/utils";
import * as React from "react";

export function Badge({
  variant = "default",
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { variant?: "default" | "outline" | "success" | "warning" | "destructive" }) {
  const styles = {
    default: "bg-primary/10 text-primary border-primary/30",
    outline: "border-border text-foreground",
    success: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
    warning: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30",
    destructive: "bg-destructive/10 text-destructive border-destructive/30",
  } as const;
  return (
    <div
      className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium", styles[variant], className)}
      {...props}
    />
  );
}

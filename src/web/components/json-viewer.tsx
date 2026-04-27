"use client";

import { useEffect, useState } from "react";

export function JsonViewer({ data }: { data: unknown }) {
  const [pretty, setPretty] = useState("");
  useEffect(() => {
    setPretty(JSON.stringify(data, null, 2));
  }, [data]);
  return (
    <pre className="max-h-[600px] overflow-auto rounded-md bg-muted p-4 text-xs leading-relaxed">
      <code>{pretty}</code>
    </pre>
  );
}

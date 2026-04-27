import { getCurrentUser } from "@/lib/auth";
import { Badge } from "@/components/ui/badge";

export async function Header() {
  const user = await getCurrentUser();
  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-6">
      <div className="text-sm text-muted-foreground">Azure AI Containers — connected ↔ disconnected</div>
      <div className="flex items-center gap-3 text-sm">
        {user ? (
          <>
            <Badge variant="success">Signed in</Badge>
            <span className="font-medium">{user.name}</span>
          </>
        ) : (
          <Badge variant="warning">Not authenticated (dev)</Badge>
        )}
      </div>
    </header>
  );
}

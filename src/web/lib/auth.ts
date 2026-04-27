import { headers } from "next/headers";

export type EasyAuthUser = { name: string; email?: string; oid?: string };

export async function getCurrentUser(): Promise<EasyAuthUser | null> {
  const h = await headers();
  const principalHeader = h.get("x-ms-client-principal");
  const id = h.get("x-ms-client-principal-id");
  const name = h.get("x-ms-client-principal-name");
  if (principalHeader) {
    try {
      const decoded = JSON.parse(Buffer.from(principalHeader, "base64").toString("utf8"));
      const claims: Record<string, string> = {};
      for (const c of decoded.claims ?? []) claims[c.typ] = c.val;
      return {
        oid: claims["http://schemas.microsoft.com/identity/claims/objectidentifier"] ?? id ?? "",
        name: name ?? claims["name"] ?? "User",
        email: claims["preferred_username"] ?? claims["email"],
      };
    } catch {
      // fall through
    }
  }
  if (id) return { oid: id, name: name ?? "User" };
  return null;
}

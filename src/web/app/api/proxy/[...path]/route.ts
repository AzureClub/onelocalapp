import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.API_BASE_URL || "http://localhost:8000";

async function proxy(req: NextRequest, params: { path: string[] }) {
  const url = `${API_BASE}/api/${params.path.join("/")}${req.nextUrl.search}`;
  const init: RequestInit = {
    method: req.method,
    headers: filterHeaders(req.headers),
    cache: "no-store",
    // @ts-expect-error duplex is required for streaming bodies
    duplex: "half",
  };
  if (req.method !== "GET" && req.method !== "HEAD") init.body = req.body as unknown as BodyInit;
  const res = await fetch(url, init);
  const headers = new Headers(res.headers);
  headers.delete("content-encoding");
  headers.delete("transfer-encoding");
  return new NextResponse(res.body, { status: res.status, headers });
}

function filterHeaders(h: Headers): Headers {
  const out = new Headers();
  for (const [k, v] of h.entries()) {
    if (["host", "connection", "content-length"].includes(k.toLowerCase())) continue;
    out.set(k, v);
  }
  return out;
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) { return proxy(req, await ctx.params); }
export async function POST(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) { return proxy(req, await ctx.params); }
export async function PUT(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) { return proxy(req, await ctx.params); }
export async function DELETE(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) { return proxy(req, await ctx.params); }

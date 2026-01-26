import { NextResponse } from "next/server";

import { gatewayFetch } from "../../../../lib/gateway";

export const runtime = "nodejs";

export async function GET(req: Request) {
  const orgId = new URL(req.url).searchParams.get("orgId") || undefined;
  const upstream = await gatewayFetch("/v1/me", { method: "GET", orgId, cache: "no-store" });
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") || "application/json" },
  });
}

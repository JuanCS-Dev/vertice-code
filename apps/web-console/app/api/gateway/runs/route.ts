import { NextResponse } from "next/server";

import { gatewayFetch } from "../../../../lib/gateway";

export const runtime = "nodejs";

export async function GET(req: Request) {
  const orgId = req.headers.get("x-vertice-org") || undefined;
  const upstream = await gatewayFetch("/v1/runs", { method: "GET", orgId, cache: "no-store" });
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") || "application/json" },
  });
}

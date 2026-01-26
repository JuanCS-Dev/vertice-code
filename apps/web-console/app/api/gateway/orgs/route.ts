import { NextResponse } from "next/server";

import { gatewayFetch } from "../../../../lib/gateway";

export const runtime = "nodejs";

export async function GET(req: Request) {
  const orgId = req.headers.get("x-vertice-org") || undefined;
  const upstream = await gatewayFetch("/v1/orgs", { method: "GET", orgId, cache: "no-store" });
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") || "application/json" },
  });
}

export async function POST(req: Request) {
  const orgId = req.headers.get("x-vertice-org") || undefined;
  const body = await req.text();
  const contentType = req.headers.get("content-type") || "application/json";
  const upstream = await gatewayFetch("/v1/orgs", {
    method: "POST",
    headers: { "Content-Type": contentType },
    body,
    orgId,
    cache: "no-store",
  });
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") || "application/json" },
  });
}

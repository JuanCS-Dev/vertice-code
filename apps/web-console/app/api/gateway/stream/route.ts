import { NextResponse } from "next/server";

import { gatewayFetch } from "../../../../lib/gateway";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const orgId = req.headers.get("x-vertice-org") || undefined;
  const body = await req.text();

  const upstream = await gatewayFetch("/agui/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    orgId,
    cache: "no-store",
  });

  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text().catch(() => "");
    return new NextResponse(text || "gateway error", { status: upstream.status || 502 });
  }

  return new NextResponse(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}

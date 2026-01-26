import { NextResponse } from "next/server";

import { assertSameOrigin } from "../../../../lib/sameOrigin";

export const runtime = "nodejs";

type SelectOrgRequest = {
  orgId: string;
};

export async function POST(req: Request) {
  try {
    assertSameOrigin(req);
  } catch {
    return new NextResponse("forbidden", { status: 403 });
  }

  const payload = (await req.json().catch(() => null)) as SelectOrgRequest | null;
  const orgId = payload?.orgId?.trim();
  if (!orgId) return new NextResponse("missing orgId", { status: 400 });

  const res = new NextResponse(null, { status: 204 });
  res.cookies.set("vertice_org", orgId, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 30, // 30 days
  });
  return res;
}

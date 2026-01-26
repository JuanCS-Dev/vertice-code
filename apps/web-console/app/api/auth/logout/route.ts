import { NextResponse } from "next/server";

import { assertSameOrigin } from "../../../../lib/sameOrigin";

export const runtime = "nodejs";

export async function POST(req: Request) {
  try {
    assertSameOrigin(req);
  } catch {
    return new NextResponse("forbidden", { status: 403 });
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set("__session", "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  return res;
}

import { NextResponse } from "next/server";

import { getAdminAuth } from "../../../../lib/firebaseAdmin";
import { assertSameOrigin } from "../../../../lib/sameOrigin";

export const runtime = "nodejs";

export async function POST(req: Request) {
  try {
    assertSameOrigin(req);
  } catch {
    return new NextResponse("forbidden", { status: 403 });
  }

  const { idToken } = (await req.json().catch(() => ({}))) as { idToken?: string };
  if (!idToken) {
    return new NextResponse("missing idToken", { status: 400 });
  }

  try {
    const auth = getAdminAuth();
    // Verify token first to fail fast
    await auth.verifyIdToken(idToken, true);
    const expiresIn = 1000 * 60 * 60 * 24 * 7; // 7 days
    const sessionCookie = await auth.createSessionCookie(idToken, { expiresIn });

    const res = NextResponse.json({ ok: true });
    res.cookies.set("__session", sessionCookie, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: Math.floor(expiresIn / 1000),
    });
    return res;
  } catch (e) {
    const msg = e instanceof Error ? e.message : "invalid token";
    return new NextResponse(msg, { status: 401 });
  }
}

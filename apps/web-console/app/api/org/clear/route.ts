import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST() {
  const res = new NextResponse(null, { status: 204 });
  res.cookies.set("vertice_org", "", { path: "/", maxAge: 0 });
  return res;
}

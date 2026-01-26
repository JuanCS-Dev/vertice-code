import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function GET() {
  const cookieStore = await cookies();
  const activeOrgId = cookieStore.get("vertice_org")?.value || null;
  return NextResponse.json({ active_org_id: activeOrgId });
}

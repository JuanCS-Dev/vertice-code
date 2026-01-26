import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = new Set<string>(["/", "/login"]);
const PUBLIC_API_PREFIXES = ["/api/auth/"];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (PUBLIC_PATHS.has(pathname) || pathname.startsWith("/_next")) {
    return NextResponse.next();
  }
  if (PUBLIC_API_PREFIXES.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // CSRF Protection for mutation requests
  if (["POST", "PUT", "PATCH", "DELETE"].includes(req.method)) {
    const origin = req.headers.get("origin");
    const referer = req.headers.get("referer");
    const host = req.headers.get("host");

    // In production, Host header usually contains the domain.
    // Origin should match Host (scheme + host).
    // Note: Cloud Run forwards headers. Next.js might rely on x-forwarded-host.
    // For MVP/Hardening: Ensure Origin/Referer matches the current site if present.
    // If Origin is missing (rare for modern browsers on POST), check Referer.

    // Simple check: if we have an origin, it must end with the host.
    if (origin && host && !origin.includes(host)) {
       return new NextResponse("Forbidden: Origin mismatch", { status: 403 });
    }

    // Strict Referer check if Origin is missing or as secondary check
    if (referer && host && !referer.includes(host)) {
        return new NextResponse("Forbidden: Referer mismatch", { status: 403 });
    }
  }

  const hasSession = req.cookies.get("__session")?.value;
  if (!hasSession) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard", "/cot", "/artifacts", "/command-center", "/settings", "/api/:path*"],
};

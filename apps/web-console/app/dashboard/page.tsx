import "server-only";
import { headers, cookies } from "next/headers";
import { gatewayFetch } from "../../lib/gateway";
import DashboardClient from "../../components/dashboard/DashboardClient";
import { MeResponse } from "../../lib/types/org";

export const runtime = "nodejs";

// Server Component
export default async function DashboardPage() {
    // Fetch initial Org/User data server-side to avoid waterfall
    let initialMe: MeResponse | null = null;

    try {
        // We can't use `gatewayFetch` easily if it relies on internal cookie forwarding without context?
        // Actually `gatewayFetch` uses `cookies()` which works in Server Components.
        const res = await gatewayFetch("/v1/me", { cache: "no-store" });
        if (res.ok) {
            initialMe = await res.json();
        }
    } catch (e) {
        console.error("Failed to fetch initial me data", e);
    }

    return <DashboardClient initialMe={initialMe} />;
}

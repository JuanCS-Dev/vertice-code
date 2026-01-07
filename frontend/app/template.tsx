"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";

export default function Template({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  useEffect(() => {
    // Optional: Scroll reset or analytics triggers here
  }, [pathname]);

  return (
    <div className="animate-fade-in h-full w-full">
      {children}
    </div>
  );
}

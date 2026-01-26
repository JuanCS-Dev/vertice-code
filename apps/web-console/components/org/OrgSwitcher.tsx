"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, ChevronDown, Plus, Building2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { Org } from "../../lib/types/org";
import { CreateOrgDialog } from "./CreateOrgDialog";

interface OrgSwitcherProps {
    currentOrgId?: string;
    initialOrgs?: Org[];
}

export function OrgSwitcher({ currentOrgId, initialOrgs }: OrgSwitcherProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [showCreate, setShowCreate] = useState(false);
    const [orgs, setOrgs] = useState<Org[]>(initialOrgs || []);
    const [loading, setLoading] = useState(false);
    const router = useRouter();
    const menuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // 1. Fetch orgs if not provided initially
        if (!initialOrgs || initialOrgs.length === 0) {
            fetch("/api/gateway/me")
                .then((r) => r.json())
                .then((data) => {
                    setOrgs(data.orgs || []);
                })
                .catch((e) => console.error("Failed to load orgs", e));
        }

        // 2. Close on click outside
        const handleClick = (e: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClick);
        return () => document.removeEventListener("mousedown", handleClick);
    }, [initialOrgs]);

    const activeOrg = orgs.find((o) => o.org_id === currentOrgId) || orgs[0];

    const handleSwitch = async (orgId: string) => {
        setLoading(true);
        try {
            await fetch("/api/org/select", {
                method: "POST",
                body: JSON.stringify({ orgId }),
            });
            setIsOpen(false);
            router.refresh();
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="relative" ref={menuRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/5 transition-colors text-sm border border-transparent hover:border-border-dim"
            >
                <div className="size-6 bg-gradient-to-br from-gray-800 to-gray-900 rounded flex items-center justify-center border border-white/10">
                    <Building2 size={12} className="text-gray-400" />
                </div>
                <div className="flex flex-col items-start leading-none">
                    <span className="text-gray-500 text-[10px] uppercase font-bold tracking-wider">Workspace</span>
                    <span className="text-white font-medium max-w-[100px] truncate">{activeOrg?.name || "Loading..."}</span>
                </div>
                <ChevronDown size={14} className={`text-gray-500 transition-transform ${isOpen ? "rotate-180" : ""}`} />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 5, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 5, scale: 0.95 }}
                        transition={{ duration: 0.1 }}
                        className="absolute top-full left-0 mt-2 w-64 bg-panel border border-border-dim rounded-xl shadow-2xl z-50 overflow-hidden"
                    >
                        <div className="p-2 border-b border-white/5 bg-black/20">
                            <div className="text-xs font-bold text-gray-500 px-2 py-1 uppercase tracking-wider">My Organizations</div>
                        </div>

                        <div className="max-h-64 overflow-y-auto p-1 py-2 space-y-0.5">
                            {orgs.map(org => {
                                const isActive = org.org_id === (currentOrgId || activeOrg?.org_id);
                                return (
                                    <button
                                        key={org.org_id}
                                        disabled={loading}
                                        onClick={() => handleSwitch(org.org_id)}
                                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors group ${isActive ? "bg-primary/10 text-white" : "text-gray-400 hover:text-white hover:bg-white/5"
                                            }`}
                                    >
                                        <div className={`size-4 rounded flex items-center justify-center border ${isActive ? "border-primary bg-primary text-black" : "border-gray-600 bg-transparent"
                                            }`}>
                                            {isActive && <Check size={10} strokeWidth={4} />}
                                        </div>
                                        <div className="flex-1 truncate">
                                            <div className="text-sm font-medium">{org.name}</div>
                                            <div className="text-[10px] opacity-50">{org.role}</div>
                                        </div>
                                    </button>
                                )
                            })}
                        </div>

                        <div className="p-2 border-t border-white/5 bg-black/20">
                            <button
                                onClick={() => { setIsOpen(false); setShowCreate(true); }}
                                className="w-full flex items-center gap-2 justify-center px-3 py-2 rounded-lg border border-dashed border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 hover:bg-white/5 transition-all text-xs font-medium"
                            >
                                <Plus size={14} />
                                Create New Organization
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <CreateOrgDialog isOpen={showCreate} onClose={() => setShowCreate(false)} />
        </div>
    );
}

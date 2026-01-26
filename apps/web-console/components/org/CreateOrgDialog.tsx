"use client";

import { useState } from "react";
import { Plus, X, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

export function CreateOrgDialog({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
    const [name, setName] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) return;

        setLoading(true);
        try {
            const res = await fetch("/api/gateway/orgs", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name }),
            });

            if (!res.ok) throw new Error("Failed to create org");

            const data = await res.json();
            // Auto-switch to new org
            await fetch("/api/org/select", {
                method: "POST",
                body: JSON.stringify({ orgId: data.org_id }),
            });

            onClose();
            setName("");
            router.refresh();
        } catch (err) {
            console.error(err);
            alert("Failed to create organization");
        } finally {
            setLoading(false);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                        onClick={onClose}
                    />
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 10 }}
                        className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none"
                    >
                        <div className="bg-panel border border-border-dim rounded-xl w-full max-w-md p-6 shadow-2xl pointer-events-auto">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-lg font-bold text-white">Create Organization</h3>
                                <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                                    <X size={20} />
                                </button>
                            </div>

                            <form onSubmit={handleCreate}>
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">
                                            Organization Name
                                        </label>
                                        <input
                                            type="text"
                                            value={name}
                                            onChange={(e) => setName(e.target.value)}
                                            placeholder="e.g. Acme Corp"
                                            className="w-full bg-black/20 border border-border-dim rounded-lg px-3 py-2 text-white placeholder-gray-600 focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                                            autoFocus
                                        />
                                    </div>

                                    <div className="flex justify-end gap-2 pt-2">
                                        <button
                                            type="button"
                                            onClick={onClose}
                                            className="px-4 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            type="submit"
                                            disabled={loading || !name.trim()}
                                            className="px-4 py-2 rounded-lg text-sm font-medium bg-primary text-black hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                        >
                                            {loading && <Loader2 size={14} className="animate-spin" />}
                                            Create Data Silo
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}

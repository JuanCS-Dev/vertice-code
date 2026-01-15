'use client';

import { useEffect } from 'react';

export default function GlobalError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error('Global Error:', error);
    }, [error]);

    return (
        <html>
            <body className="bg-black text-white flex items-center justify-center min-h-screen">
                <div className="text-center p-8 border border-white/10 rounded-lg bg-white/5 backdrop-blur">
                    <h2 className="text-2xl font-bold mb-4 text-red-500">Critical System Failure</h2>
                    <p className="mb-6 text-zinc-400">The neural link loop has been detected.</p>
                    <pre className="text-xs text-left bg-black/50 p-4 rounded mb-6 overflow-auto max-w-lg mx-auto">
                        {error.message}
                        {error.digest && `\nDigest: ${error.digest}`}
                    </pre>
                    <button
                        onClick={() => reset()}
                        className="px-6 py-2 bg-primary text-black font-bold rounded hover:opacity-90 transition-opacity"
                    >
                        Reboot System
                    </button>
                </div>
            </body>
        </html>
    );
}

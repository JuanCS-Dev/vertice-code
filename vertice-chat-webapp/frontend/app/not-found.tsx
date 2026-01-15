import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function NotFound() {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-background text-foreground">
            <h1 className="text-9xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-white to-white/10">
                404
            </h1>
            <h2 className="text-2xl font-medium mt-4 mb-2">Void Detected</h2>
            <p className="text-zinc-500 mb-8 max-w-md text-center">
                The projected reality you are looking for has not been manifested in this timeline.
            </p>
            <Link href="/">
                <Button variant="outline" className="border-white/10 hover:bg-white/5">
                    Return to Origin
                </Button>
            </Link>
        </div>
    );
}

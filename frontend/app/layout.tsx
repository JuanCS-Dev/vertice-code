import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { cn } from '@/lib/utils'; // Assuming you have a utils file, usually standard in shadcn/ui setups. If not, I'll inline or create it.

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Vertice Code Web',
  description: 'Sovereign AI Engineering Workbench',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full">
      <body
        className={cn(
          inter.variable,
          jetbrainsMono.variable,
          "font-sans antialiased bg-background text-foreground h-full overflow-hidden selection:bg-accent/20 selection:text-accent"
        )}
      >
        {children}
      </body>
    </html>
  );
}

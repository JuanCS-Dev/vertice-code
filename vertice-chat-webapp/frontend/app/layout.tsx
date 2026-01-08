import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/context/AuthContext';

const inter = Inter({ subsets: ['latin'] });

import { PageTransition } from '@/components/layout/page-transition';
import { WebVitalsMonitor } from '@/components/metrics/web-vitals';
import { AccessibilityChecker } from '@/components/accessibility/accessibility-checker';
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Vertice Chat - Multi-LLM Agentic Chat Platform",
  description: "Experience the future of coding with AI-powered agentic chat, artifacts, and seamless GitHub integration.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <AuthProvider>
      <html lang="en">
        <body
          className={`${geistSans.variable} ${geistMono.variable} antialiased`}
        >
          <PageTransition>{children}</PageTransition>
          <WebVitalsMonitor />
          <AccessibilityChecker />
        </body>
      </html>
    </AuthProvider>
  );
}

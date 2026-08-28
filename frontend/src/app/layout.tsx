import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GridMind OS — Autonomous Grid Intelligence",
  description: "AI-powered grid optimization platform for utilities and enterprises. Monitor, predict, and optimize energy in real time.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen">{children}</body>
    </html>
  );
}

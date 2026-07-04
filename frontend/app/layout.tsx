import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "AI Fitness Coach",
  description: "Your multi-agent fitness and nutrition coach",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-charcoal text-fog min-h-screen">{children}</body>
    </html>
  );
}

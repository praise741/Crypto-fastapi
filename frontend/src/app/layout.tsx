import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/layout/navbar";
import { Analytics } from "@vercel/analytics/next";
import { AuthProvider } from "@/context/auth-context";

export const metadata: Metadata = {
  title: "Market Matrix - Crypto Intelligence Platform",
  description: "Empower your crypto trading with AI-powered predictions, token health analysis, and portfolio tracking.",
  icons: {
    icon: "/logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <body className="font-body antialiased">
        <AuthProvider>
          <Navbar />
          {children}
          <Analytics />
        </AuthProvider>
      </body>
    </html>
  );
}

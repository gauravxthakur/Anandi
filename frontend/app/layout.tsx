import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Inter } from 'next/font/google';
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";

const inter = Inter({ subsets: ['latin'] });

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Auto Fetal Biometry",
  description: "PC-PNDT Form F workflow with AI-assisted fetal biometry",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className={`${inter.className} min-h-full flex flex-col`}>
        <header className="w-full border-b border-border/50 bg-background/80 backdrop-blur-sm">
          <div className="mx-4 flex h-12 items-center sm:mx-6">
            <img
              src="/anandi_logo.png"
              alt="Anandi Logo"
              className="h-6 w-auto object-contain"
            />
          </div>
        </header>
        <main className="flex-1">
          {children}
        </main>
        <Toaster />
      </body>
    </html>
  );
}


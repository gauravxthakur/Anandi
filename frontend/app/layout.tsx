import "./globals.css";
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});


export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html className={cn("font-sans", geist.variable)}>
      <body className="min-h-screen">
        <header className="bg-white p-4 flex items-center justify-center">
          <img src="/anandi_logo.svg" alt="Anandi Logo" className="h-8 w-auto" />
        </header>
        <main className="flex items-center justify-center min-h-[calc(100vh-80px)]">
          {children}
        </main>
      </body>
    </html>
  );
}

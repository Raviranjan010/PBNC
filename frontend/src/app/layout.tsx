import type { Metadata } from "next";
import "@/app/globals.css";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: "PaperMind — Document Intelligence & Question Extraction",
  description: "Extract structured, source-traceable questions and answer keys from exam documents.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-text antialiased">
        <Navbar />
        <div className="flex min-h-[calc(100vh-3.5rem)]">
          <Sidebar />
          <main className="flex-1 overflow-x-hidden p-6 max-w-7xl mx-auto w-full">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

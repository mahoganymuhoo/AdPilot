import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/ui/Sidebar";
import OnboardingGuard from "@/components/ui/OnboardingGuard";

export const metadata: Metadata = {
  title: "AdPilot — E-Ticaret Reklam Yönetimi",
  description: "AI destekli reklam analizi ve optimizasyon sistemi",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body className="flex min-h-screen bg-gray-50">
        <OnboardingGuard>
          <Sidebar />
          <main className="flex-1 p-6 ml-64">{children}</main>
        </OnboardingGuard>
      </body>
    </html>
  );
}

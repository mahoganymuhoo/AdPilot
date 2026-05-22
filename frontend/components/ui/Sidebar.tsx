"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart2, TrendingUp, Lightbulb, Settings, Package,
  Upload, BookOpen, Target, AlertTriangle, Menu, X,
} from "lucide-react";
import clsx from "clsx";
import AnomalyDrawer from "@/components/ui/AnomalyDrawer";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart2 },
  { href: "/products", label: "Ürünler", icon: Package },
  { href: "/insights", label: "AI Öneriler", icon: Lightbulb },
  { href: "/strategies", label: "Stratejiler", icon: Target },
  { href: "/upload", label: "Veri Yükle", icon: Upload },
  { href: "/guide", label: "Nasıl Çalışır?", icon: BookOpen },
  { href: "/settings", label: "Ayarlar", icon: Settings },
];

const UNREAD_ANOMALY_COUNT = 2;

export default function Sidebar() {
  const pathname = usePathname();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const navContent = (
    <>
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            onClick={() => setMobileOpen(false)}
            className={clsx(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
              pathname.startsWith(href)
                ? "bg-green-50 text-green-700"
                : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            )}
          >
            <Icon size={18} />
            <span>{label}</span>
            {href === "/guide" && (
              <span className="ml-auto text-xs bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded-full font-normal">
                Yeni
              </span>
            )}
          </Link>
        ))}
      </nav>

      {/* Anomali Butonu */}
      <div className="px-3 mb-2">
        <button
          onClick={() => { setDrawerOpen(true); setMobileOpen(false); }}
          className={clsx(
            "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
            UNREAD_ANOMALY_COUNT > 0
              ? "bg-orange-50 text-orange-700 hover:bg-orange-100"
              : "text-gray-600 hover:bg-gray-50"
          )}
        >
          <AlertTriangle size={18} />
          <span>Anomali Uyarıları</span>
          {UNREAD_ANOMALY_COUNT > 0 && (
            <span className="ml-auto bg-red-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
              {UNREAD_ANOMALY_COUNT}
            </span>
          )}
        </button>
      </div>

      {/* Alt bilgi */}
      <div className="mx-3 mb-3 p-3 bg-blue-50 rounded-xl border border-blue-100">
        <p className="text-xs font-semibold text-blue-700 mb-1">Metrik nedir?</p>
        <p className="text-xs text-blue-600 leading-relaxed">
          Her metriğin yanındaki{" "}
          <span className="inline-block w-3.5 h-3.5 border border-gray-300 rounded-full text-center text-gray-400 text-[9px] leading-3 align-middle">?</span>
          {" "}ikonuna tıklayarak detaylı açıklama al.
        </p>
      </div>

      <div className="px-4 py-3 border-t border-gray-100">
        <p className="text-xs text-gray-400">v0.1.0 · AdPilot</p>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex fixed top-0 left-0 h-full w-64 bg-white border-r border-gray-200 flex-col z-30">
        <div className="px-6 py-5 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <TrendingUp className="text-green-500" size={22} />
            <span className="text-lg font-bold text-gray-900">AdPilot</span>
          </div>
          <p className="text-xs text-gray-400 mt-0.5">Reklam Analiz Asistanı</p>
        </div>
        {navContent}
      </aside>

      {/* Mobile header bar */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-white border-b border-gray-200 flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="text-green-500" size={20} />
          <span className="text-base font-bold text-gray-900">AdPilot</span>
        </div>
        <div className="flex items-center gap-2">
          {UNREAD_ANOMALY_COUNT > 0 && (
            <button
              onClick={() => setDrawerOpen(true)}
              className="relative p-2 text-orange-600"
            >
              <AlertTriangle size={20} />
              <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center">
                {UNREAD_ANOMALY_COUNT}
              </span>
            </button>
          )}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-2 text-gray-600"
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile menu overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-30">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute top-0 left-0 w-72 h-full bg-white flex flex-col shadow-2xl pt-14">
            {navContent}
          </div>
        </div>
      )}

      {drawerOpen && <AnomalyDrawer onClose={() => setDrawerOpen(false)} />}
    </>
  );
}

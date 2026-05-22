"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart2, TrendingUp, Lightbulb, Settings, Package, Upload, BookOpen, Target } from "lucide-react";
import clsx from "clsx";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart2 },
  { href: "/products", label: "Ürünler", icon: Package },
  { href: "/insights", label: "AI Öneriler", icon: Lightbulb },
  { href: "/strategies", label: "Stratejiler", icon: Target },
  { href: "/upload", label: "Veri Yükle", icon: Upload },
  { href: "/guide", label: "Nasıl Çalışır?", icon: BookOpen },
  { href: "/settings", label: "Ayarlar", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed top-0 left-0 h-full w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="px-6 py-5 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <TrendingUp className="text-green-500" size={22} />
          <span className="text-lg font-bold text-gray-900">AdPilot</span>
        </div>
        <p className="text-xs text-gray-400 mt-0.5">Reklam Analiz Asistanı</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
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

      {/* Alt bilgi kutusu */}
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
    </aside>
  );
}

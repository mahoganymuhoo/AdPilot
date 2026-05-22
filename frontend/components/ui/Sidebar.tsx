"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart2, TrendingUp, Lightbulb, Settings, Package, Upload } from "lucide-react";
import clsx from "clsx";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart2 },
  { href: "/products", label: "Ürünler", icon: Package },
  { href: "/insights", label: "AI Öneriler", icon: Lightbulb },
  { href: "/upload", label: "Veri Yükle", icon: Upload },
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

      <nav className="flex-1 px-3 py-4 space-y-1">
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
            {label}
          </Link>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-gray-100">
        <p className="text-xs text-gray-400">v0.1.0 · AdPilot</p>
      </div>
    </aside>
  );
}

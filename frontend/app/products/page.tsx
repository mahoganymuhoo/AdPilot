"use client";
import { useState } from "react";
import { Package, TrendingUp, TrendingDown, Minus, AlertTriangle } from "lucide-react";
import clsx from "clsx";
import Link from "next/link";
import InfoModal from "@/components/ui/InfoModal";
import { EXPLAINERS } from "@/lib/explainers";

const DEMO_PRODUCTS = [
  {
    id: 1, title: "El Yapımı Seramik Kupa", listing_id: "12345", price: 28.0, cogs: 9.0,
    roas: 4.2, acos: 23.8, break_even_acos: 54, is_profitable: true, trend: "improving",
    inventory: 24, ad_spend_30d: 45.0, revenue_30d: 189.0, anomalies: 0,
    net_profit: 68.4,
  },
  {
    id: 2, title: "Makrome Duvar Süsü", listing_id: "23456", price: 45.0, cogs: 18.0,
    roas: 2.8, acos: 35.7, break_even_acos: 44, is_profitable: true, trend: "stable",
    inventory: 12, ad_spend_30d: 30.0, revenue_30d: 84.0, anomalies: 0,
    net_profit: 12.6,
  },
  {
    id: 3, title: "Örme Bebek Battaniyesi", listing_id: "34567", price: 55.0, cogs: 25.0,
    roas: 1.9, acos: 52.6, break_even_acos: 38, is_profitable: false, trend: "declining",
    inventory: 8, ad_spend_30d: 28.0, revenue_30d: 53.2, anomalies: 1,
    net_profit: -8.2,
  },
  {
    id: 4, title: "Ahşap Fotoğraf Çerçevesi", listing_id: "45678", price: 22.0, cogs: 12.0,
    roas: 0.8, acos: 125.0, break_even_acos: 30, is_profitable: false, trend: "declining",
    inventory: 5, ad_spend_30d: 20.0, revenue_30d: 16.0, anomalies: 2,
    net_profit: -18.6,
  },
];

const trendIcon = {
  improving: <TrendingUp size={14} className="text-green-500" />,
  declining: <TrendingDown size={14} className="text-red-500" />,
  stable: <Minus size={14} className="text-gray-400" />,
};
const trendLabel = { improving: "Yükseliş", declining: "Düşüş", stable: "Sabit" };

// Her metrik için tıklanabilir etiket
function MetricLabel({ label, explainerId }: { label: string; explainerId: string }) {
  const exp = EXPLAINERS[explainerId];
  if (!exp) return <p className="text-xs text-gray-400">{label}</p>;
  return (
    <div className="flex items-center justify-center gap-0.5">
      <p className="text-xs text-gray-400">{label}</p>
      <InfoModal explainer={exp} />
    </div>
  );
}

export default function ProductsPage() {
  const [filter, setFilter] = useState<"all" | "profitable" | "unprofitable">("all");
  const [selected, setSelected] = useState<number | null>(null);

  const filtered = DEMO_PRODUCTS.filter((p) => {
    if (filter === "profitable") return p.is_profitable;
    if (filter === "unprofitable") return !p.is_profitable;
    return true;
  });

  const selectedProduct = DEMO_PRODUCTS.find((p) => p.id === selected);

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Ürünler</h1>
        <p className="text-sm text-gray-500 mt-1">
          Tüm ürünlerin reklam performansı ve kârlılık durumu.
          Metrik adlarına tıklayarak ne anlama geldiğini öğren.
        </p>
      </div>

      {/* Filtreler */}
      <div className="flex gap-2 mb-5">
        {[
          { key: "all", label: "Tümü" },
          { key: "profitable", label: "✓ Karlı" },
          { key: "unprofitable", label: "✗ Zararlı" },
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key as typeof filter)}
            className={clsx(
              "px-3 py-1.5 text-sm rounded-lg border transition-colors",
              filter === f.key
                ? "bg-gray-900 text-white border-gray-900"
                : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"
            )}
          >
            {f.label}
          </button>
        ))}
        <span className="ml-auto text-xs text-gray-400 self-center">
          {filtered.length} ürün · Metrik adlarına tıklayarak öğren
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filtered.map((p) => (
          <div
            key={p.id}
            onClick={() => setSelected(selected === p.id ? null : p.id)}
            className={clsx(
              "bg-white rounded-xl border shadow-sm p-5 cursor-pointer transition-all",
              !p.is_profitable ? "border-red-200 hover:border-red-300" : "border-gray-200 hover:border-gray-300",
              selected === p.id && "ring-2 ring-blue-200"
            )}
          >
            {/* Başlık */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <Package size={16} className="text-gray-400 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-gray-900">{p.title}</p>
                  <p className="text-xs text-gray-400">#{p.listing_id} · ${p.price}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {p.anomalies > 0 && (
                  <span className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
                    <AlertTriangle size={11} />{p.anomalies} anomali
                  </span>
                )}
                <span className={clsx(
                  "text-xs px-2 py-0.5 rounded-full font-medium",
                  p.is_profitable ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                )}>
                  {p.is_profitable ? "Karlı" : "Zararlı"}
                </span>
              </div>
            </div>

            {/* Metrik Grid */}
            <div className="grid grid-cols-4 gap-2 mb-3">
              <div className="bg-gray-50 rounded-lg p-2 text-center">
                <MetricLabel label="ROAS" explainerId="roas" />
                <p className={clsx(
                  "text-sm font-bold mt-0.5",
                  p.roas >= 3 ? "text-green-700" : p.roas >= 2 ? "text-yellow-700" : "text-red-700"
                )}>{p.roas}x</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-2 text-center">
                <MetricLabel label="ACOS" explainerId="acos" />
                <p className={clsx(
                  "text-sm font-bold mt-0.5",
                  p.acos < p.break_even_acos ? "text-green-700" : "text-red-700"
                )}>%{p.acos}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-2 text-center">
                <MetricLabel label="Harcama" explainerId="net_profit" />
                <p className="text-sm font-bold text-gray-900 mt-0.5">${p.ad_spend_30d}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-2 text-center">
                <MetricLabel label="Gelir" explainerId="roas" />
                <p className="text-sm font-bold text-gray-900 mt-0.5">${p.revenue_30d}</p>
              </div>
            </div>

            {/* Break-even çubuğu */}
            <div className="mb-3">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1">
                  <span className="text-xs text-gray-500">Break-even Kontrolü</span>
                  <InfoModal explainer={EXPLAINERS.breakeven_acos} />
                </div>
                <span className={clsx(
                  "text-xs font-medium",
                  p.acos < p.break_even_acos ? "text-green-600" : "text-red-600"
                )}>
                  {p.acos < p.break_even_acos
                    ? `✓ ACOS %${p.acos} < %${p.break_even_acos}`
                    : `✗ ACOS %${p.acos} > %${p.break_even_acos}`}
                </span>
              </div>
              <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={clsx("absolute left-0 h-full rounded-full",
                    p.acos < p.break_even_acos ? "bg-green-400" : "bg-red-400"
                  )}
                  style={{ width: `${Math.min(p.acos, 100)}%` }}
                />
                <div
                  className="absolute top-0 h-full w-0.5 bg-gray-500"
                  style={{ left: `${Math.min(p.break_even_acos, 100)}%` }}
                />
              </div>
            </div>

            {/* Alt satır */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  {trendIcon[p.trend as keyof typeof trendIcon]}
                  <span>{trendLabel[p.trend as keyof typeof trendLabel]}</span>
                  <InfoModal explainer={EXPLAINERS.ema_trend} />
                </span>
                <span>Stok: {p.inventory}</span>
                <span className={clsx(
                  "font-medium",
                  p.net_profit > 0 ? "text-green-600" : "text-red-600"
                )}>
                  Net: {p.net_profit > 0 ? "+" : ""}${p.net_profit}
                  <InfoModal explainer={EXPLAINERS.net_profit} />
                </span>
              </div>
              <Link
                href={`/insights?product=${p.id}`}
                onClick={(e) => e.stopPropagation()}
                className="text-xs font-medium text-blue-600 hover:text-blue-700"
              >
                AI Analizi →
              </Link>
            </div>

            {/* Genişletilmiş bilgi */}
            {selected === p.id && (
              <div className="mt-4 pt-4 border-t border-gray-100 space-y-2">
                <p className="text-xs font-semibold text-gray-600 mb-2">Bu ürün hakkında ne yapmalısın?</p>
                {p.is_profitable && p.roas >= 3.5 && (
                  <div className="bg-green-50 rounded-lg p-3 text-xs text-green-800 leading-relaxed">
                    <span className="font-semibold">✓ Bütçeyi artırabilirsin.</span> ROAS {p.roas}x ile hedefin üzerinde. Break-even ACOS'un (%{p.break_even_acos}) çok üzerinde kâr marjın var.
                  </div>
                )}
                {p.is_profitable && p.roas < 3.5 && p.roas >= 2 && (
                  <div className="bg-blue-50 rounded-lg p-3 text-xs text-blue-800 leading-relaxed">
                    <span className="font-semibold">→ Bütçeyi koru.</span> ROAS {p.roas}x kabul edilebilir. CTR ve dönüşüm oranını iyileştirerek ROAS'ı artırabilirsin.
                  </div>
                )}
                {!p.is_profitable && p.roas >= 1 && (
                  <div className="bg-yellow-50 rounded-lg p-3 text-xs text-yellow-800 leading-relaxed">
                    <span className="font-semibold">⚠ Dikkat!</span> ACOS %{p.acos} break-even ACOS'un (%{p.break_even_acos}) üstünde — her reklam satışında zarar ediyorsun. Bütçeyi %30 azalt ve listing'i iyileştir.
                  </div>
                )}
                {p.roas < 1 && (
                  <div className="bg-red-50 rounded-lg p-3 text-xs text-red-800 leading-relaxed">
                    <span className="font-semibold">✗ Reklamı durdur.</span> ROAS {p.roas}x — reklama harcadığından az kazanıyorsun. Reklamı durdurup ürünü ve fiyatlamayı gözden geçir.
                  </div>
                )}
                {p.anomalies > 0 && (
                  <div className="bg-amber-50 rounded-lg p-3 text-xs text-amber-800 leading-relaxed">
                    <span className="font-semibold">🚨 {p.anomalies} anomali tespit edildi.</span> Bir veya daha fazla metrikte olağandışı değişim var. Anomali Uyarıları bölümünü kontrol et.
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

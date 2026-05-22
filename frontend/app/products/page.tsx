"use client";
import { useState } from "react";
import { Package, TrendingUp, TrendingDown, Minus, AlertTriangle } from "lucide-react";
import clsx from "clsx";
import Link from "next/link";

const DEMO_PRODUCTS = [
  {
    id: 1, title: "El Yapımı Seramik Kupa", listing_id: "12345", price: 28.0, cogs: 9.0,
    roas: 4.2, acos: 23.8, is_profitable: true, trend: "improving", inventory: 24, ad_spend_30d: 45.0,
    revenue_30d: 189.0, anomalies: 0,
  },
  {
    id: 2, title: "Makrome Duvar Süsü", listing_id: "23456", price: 45.0, cogs: 18.0,
    roas: 2.8, acos: 35.7, is_profitable: true, trend: "stable", inventory: 12, ad_spend_30d: 30.0,
    revenue_30d: 84.0, anomalies: 0,
  },
  {
    id: 3, title: "Örme Bebek Battaniyesi", listing_id: "34567", price: 55.0, cogs: 25.0,
    roas: 1.9, acos: 52.6, is_profitable: false, trend: "declining", inventory: 8, ad_spend_30d: 28.0,
    revenue_30d: 53.2, anomalies: 1,
  },
  {
    id: 4, title: "Ahşap Fotoğraf Çerçevesi", listing_id: "45678", price: 22.0, cogs: 12.0,
    roas: 0.8, acos: 125.0, is_profitable: false, trend: "declining", inventory: 5, ad_spend_30d: 20.0,
    revenue_30d: 16.0, anomalies: 2,
  },
];

const trendIcon = {
  improving: <TrendingUp size={14} className="text-green-500" />,
  declining: <TrendingDown size={14} className="text-red-500" />,
  stable: <Minus size={14} className="text-gray-400" />,
};

export default function ProductsPage() {
  const [filter, setFilter] = useState<"all" | "profitable" | "unprofitable">("all");

  const filtered = DEMO_PRODUCTS.filter((p) => {
    if (filter === "profitable") return p.is_profitable;
    if (filter === "unprofitable") return !p.is_profitable;
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Ürünler</h1>
        <p className="text-sm text-gray-500 mt-1">Tüm ürünlerin reklam performansı ve kârlılık durumu.</p>
      </div>

      {/* Filtreler */}
      <div className="flex gap-2 mb-5">
        {[
          { key: "all", label: "Tümü" },
          { key: "profitable", label: "Karlı" },
          { key: "unprofitable", label: "Zararlı" },
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
      </div>

      {/* Ürün Kartları */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filtered.map((p) => (
          <div
            key={p.id}
            className={clsx(
              "bg-white rounded-xl border shadow-sm p-5",
              !p.is_profitable ? "border-red-200" : "border-gray-200"
            )}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <Package size={16} className="text-gray-400 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-gray-900">{p.title}</p>
                  <p className="text-xs text-gray-400">#{p.listing_id}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {p.anomalies > 0 && (
                  <span className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
                    <AlertTriangle size={11} />{p.anomalies} uyarı
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

            <div className="grid grid-cols-4 gap-3 mb-4">
              {[
                { label: "ROAS", value: `${p.roas}x` },
                { label: "ACOS", value: `%${p.acos}` },
                { label: "Harcama", value: `$${p.ad_spend_30d}` },
                { label: "Gelir", value: `$${p.revenue_30d}` },
              ].map((m) => (
                <div key={m.label} className="bg-gray-50 rounded-lg p-2 text-center">
                  <p className="text-xs text-gray-400">{m.label}</p>
                  <p className="text-sm font-bold text-gray-900">{m.value}</p>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                {trendIcon[p.trend as keyof typeof trendIcon]}
                <span>Trend: {p.trend === "improving" ? "Yükseliş" : p.trend === "declining" ? "Düşüş" : "Sabit"}</span>
                <span className="mx-2 text-gray-200">|</span>
                <span>Stok: {p.inventory}</span>
              </div>
              <Link
                href={`/insights?product=${p.id}`}
                className="text-xs font-medium text-green-600 hover:text-green-700"
              >
                AI Analizi →
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

"use client";
import { useState } from "react";
import { Zap, TrendingUp, DollarSign, BarChart2 } from "lucide-react";
import clsx from "clsx";

const DEMO_PRODUCTS = [
  { id: 1, title: "El Yapımı Seramik Kupa", score: 82, recommendation: "priority", roas: 4.2 },
  { id: 2, title: "Makrome Duvar Süsü", score: 65, recommendation: "recommend", roas: 2.8 },
  { id: 3, title: "Örme Bebek Battaniyesi", score: 38, recommendation: "test_small_budget", roas: 1.9 },
  { id: 4, title: "Ahşap Fotoğraf Çerçevesi", score: 15, recommendation: "dont_advertise", roas: 0.8 },
];

const scoreConfig = {
  priority: { label: "Öncelikli Reklam", color: "bg-green-100 text-green-700 border-green-200", bar: "bg-green-500" },
  recommend: { label: "Reklam Öneriliyor", color: "bg-blue-100 text-blue-700 border-blue-200", bar: "bg-blue-500" },
  test_small_budget: { label: "Test Et", color: "bg-yellow-100 text-yellow-700 border-yellow-200", bar: "bg-yellow-400" },
  dont_advertise: { label: "Reklam Verme", color: "bg-red-100 text-red-700 border-red-200", bar: "bg-red-400" },
};

export default function InsightsPage() {
  const [selected, setSelected] = useState<number>(1);
  const selectedProduct = DEMO_PRODUCTS.find((p) => p.id === selected);
  const config = selectedProduct ? scoreConfig[selectedProduct.recommendation as keyof typeof scoreConfig] : null;

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">AI Öneriler</h1>
        <p className="text-sm text-gray-500 mt-1">Hangi ürüne reklam verilmeli? Portföy bütçe optimizasyonu.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ürün Listesi */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Ürünler — Ad Skoru</p>
            </div>
            <div className="divide-y divide-gray-50">
              {DEMO_PRODUCTS.map((p) => {
                const cfg = scoreConfig[p.recommendation as keyof typeof scoreConfig];
                return (
                  <button
                    key={p.id}
                    onClick={() => setSelected(p.id)}
                    className={clsx(
                      "w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors",
                      selected === p.id && "bg-gray-50"
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900 truncate pr-2">{p.title}</span>
                      <span className="text-sm font-bold text-gray-700 shrink-0">{p.score}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5 mb-1.5">
                      <div className={clsx("h-1.5 rounded-full", cfg.bar)} style={{ width: `${p.score}%` }} />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className={clsx("text-xs px-1.5 py-0.5 rounded border", cfg.color)}>{cfg.label}</span>
                      <span className="text-xs text-gray-400">ROAS {p.roas}x</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Detay Paneli */}
        <div className="lg:col-span-2 space-y-4">
          {selectedProduct && config && (
            <>
              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">{selectedProduct.title}</h2>
                    <span className={clsx("text-xs px-2 py-0.5 rounded-full border mt-1 inline-block", config.color)}>
                      {config.label}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-gray-900">{selectedProduct.score}</p>
                    <p className="text-xs text-gray-400">/ 100 puan</p>
                  </div>
                </div>

                {/* Skor çubukları */}
                <div className="space-y-3">
                  {[
                    { label: "Kâr Marjı Uygunluğu", score: 85, icon: <DollarSign size={14} /> },
                    { label: "ROAS Trendi", score: selectedProduct.roas > 3 ? 80 : 40, icon: <TrendingUp size={14} /> },
                    { label: "Görünürlük Potansiyeli", score: 60, icon: <BarChart2 size={14} /> },
                    { label: "Envanter Durumu", score: 70, icon: <Zap size={14} /> },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-1.5 text-xs text-gray-600">
                          {item.icon}{item.label}
                        </div>
                        <span className="text-xs font-medium text-gray-700">{item.score}/100</span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div className={clsx("h-2 rounded-full", config.bar)} style={{ width: `${item.score}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">AI Görünürlük Analizi</h3>
                <div className="bg-blue-50 rounded-lg p-3 text-sm text-blue-800">
                  <p className="font-medium mb-1">Durum: Az görüntülenme, iyi dönüşüm</p>
                  <p className="text-xs leading-relaxed">
                    Bu ürün görüntülendiğinde iyi satıyor, ancak yeterli trafik alamıyor.
                    Reklam ile görünürlük artırılırsa ROAS daha da yükselecek.
                    Önerilen günlük bütçe: <strong>$8/gün</strong>
                  </p>
                </div>
                <p className="text-xs text-gray-400 mt-3">
                  Bu analiz demo verisidir. Gerçek API bağlantısı sonrası AI analizi otomatik üretilecek.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";
import { useState } from "react";
import { Zap, TrendingUp, DollarSign, BarChart2, Eye } from "lucide-react";
import clsx from "clsx";
import InfoModal from "@/components/ui/InfoModal";
import { EXPLAINERS } from "@/lib/explainers";

const DEMO_PRODUCTS = [
  {
    id: 1, title: "El Yapımı Seramik Kupa", score: 82, recommendation: "priority", roas: 4.2,
    scoreDetails: {
      profit_margin: 85, roas_trend: 80, visibility: 72, inventory: 80, seasonal: 70,
    },
    view_situation: "low_views_good_conversion",
    view_diagnosis: "Az görüntülenme ama satış oranı güçlü (%5.8). Reklam ile trafik artırılırsa ROAS daha da yükselir.",
    pre_ad_action: null,
    suggested_budget: 12.0,
  },
  {
    id: 2, title: "Makrome Duvar Süsü", score: 65, recommendation: "recommend", roas: 2.8,
    scoreDetails: {
      profit_margin: 65, roas_trend: 50, visibility: 60, inventory: 55, seasonal: 80,
    },
    view_situation: "balanced",
    view_diagnosis: "Görünürlük ve dönüşüm dengeli. Mevsimsel talep yüksek — iyi zaman.",
    pre_ad_action: null,
    suggested_budget: 7.0,
  },
  {
    id: 3, title: "Örme Bebek Battaniyesi", score: 38, recommendation: "test_small_budget", roas: 1.9,
    scoreDetails: {
      profit_margin: 35, roas_trend: 20, visibility: 55, inventory: 40, seasonal: 50,
    },
    view_situation: "high_views_low_sales",
    view_diagnosis: "500 görüntülenme ama sadece %0.6 dönüşüm. Listing kalitesini artırmadan reklam para kaybettirir.",
    pre_ad_action: "Önce listing'i düzelt: ana fotoğrafı değiştir, fiyatı rakiplerle kıyasla, başlığa daha fazla anahtar kelime ekle.",
    suggested_budget: 3.0,
  },
  {
    id: 4, title: "Ahşap Fotoğraf Çerçevesi", score: 15, recommendation: "dont_advertise", roas: 0.8,
    scoreDetails: {
      profit_margin: 20, roas_trend: 5, visibility: 20, inventory: 25, seasonal: 30,
    },
    view_situation: "low_views_low_conversion",
    view_diagnosis: "Hem görünürlük hem dönüşüm düşük, kâr marjı yetersiz.",
    pre_ad_action: "Fiyatı artır veya üretim maliyetini düşür. Reklam şu an zararlı.",
    suggested_budget: 0,
  },
];

const scoreConfig = {
  priority: { label: "Öncelikli Reklam", color: "bg-green-100 text-green-700 border-green-200", bar: "bg-green-500", dot: "bg-green-500" },
  recommend: { label: "Reklam Öneriliyor", color: "bg-blue-100 text-blue-700 border-blue-200", bar: "bg-blue-500", dot: "bg-blue-500" },
  test_small_budget: { label: "Küçük Bütçe Test Et", color: "bg-yellow-100 text-yellow-700 border-yellow-200", bar: "bg-yellow-400", dot: "bg-yellow-400" },
  dont_advertise: { label: "Reklam Verme", color: "bg-red-100 text-red-700 border-red-200", bar: "bg-red-400", dot: "bg-red-400" },
};

const scoreFactors = [
  {
    key: "profit_margin",
    label: "Kâr Marjı Uygunluğu",
    icon: <DollarSign size={14} />,
    explainerId: "breakeven_acos",
    max: 25,
    description: "Kâr marjın reklam maliyetini karşılayabilir mi? Yüksek marjlı ürünlerde reklam çok daha güvenli.",
  },
  {
    key: "roas_trend",
    label: "ROAS Trendi",
    icon: <TrendingUp size={14} />,
    explainerId: "ema_trend",
    max: 20,
    description: "Son 14 günün 30 günlük ortalamaya göre yükseliş mi, düşüş mü?",
  },
  {
    key: "visibility",
    label: "Görünürlük Potansiyeli",
    icon: <Eye size={14} />,
    explainerId: "view_analysis",
    max: 35,
    description: "Görüntülenme ve satış oranı analizi. Az görüntülenme + iyi dönüşüm = reklam için ideal.",
  },
  {
    key: "inventory",
    label: "Stok Yeterliliği",
    icon: <Zap size={14} />,
    explainerId: "ad_worthiness",
    max: 10,
    description: "Düşük stokla reklam vermek, ürün tükenince bütçe israfı yaratır.",
  },
  {
    key: "seasonal",
    label: "Mevsimsel Uyum",
    icon: <BarChart2 size={14} />,
    explainerId: "ad_worthiness",
    max: 10,
    description: "Bu ürüne şu an talep artışı var mı? Mevsim/trend analizi.",
  },
];

export default function InsightsPage() {
  const [selected, setSelected] = useState<number>(1);
  const selectedProduct = DEMO_PRODUCTS.find((p) => p.id === selected)!;
  const config = scoreConfig[selectedProduct.recommendation as keyof typeof scoreConfig];

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">AI Öneriler</h1>
        <div className="flex items-center gap-2 mt-1">
          <p className="text-sm text-gray-500">Hangi ürüne reklam verilmeli? Her skor faktörüne tıklayarak nasıl hesaplandığını öğren.</p>
          <InfoModal explainer={EXPLAINERS.ad_worthiness} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ürün Listesi */}
        <div className="lg:col-span-1 space-y-3">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Reklam Uygunluk Skoru</p>
              <InfoModal explainer={EXPLAINERS.ad_worthiness} />
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
                      selected === p.id && "bg-blue-50"
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900 truncate pr-2">{p.title}</span>
                      <span className="text-sm font-bold text-gray-700 shrink-0">{p.score}<span className="text-xs font-normal text-gray-400">/100</span></span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5 mb-1.5">
                      <div className={clsx("h-1.5 rounded-full transition-all", cfg.bar)} style={{ width: `${p.score}%` }} />
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

          {/* Bütçe Optimizasyonu Kutusu */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm font-semibold text-gray-700">Bütçe Optimizasyonu</span>
              <InfoModal explainer={EXPLAINERS.budget_optimizer} />
            </div>
            <p className="text-xs text-gray-500 leading-relaxed mb-3">
              Günlük $30 bütçe için önerilen dağılım (ROAS'a göre gradient descent):
            </p>
            {DEMO_PRODUCTS.map((p) => {
              const cfg = scoreConfig[p.recommendation as keyof typeof scoreConfig];
              const budget = p.id === 1 ? 14 : p.id === 2 ? 10 : p.id === 3 ? 5 : 1;
              return (
                <div key={p.id} className="flex items-center gap-2 mb-2">
                  <span className={clsx("w-2 h-2 rounded-full shrink-0", cfg.dot)} />
                  <span className="text-xs text-gray-600 truncate flex-1">{p.title.split(" ").slice(0, 2).join(" ")}</span>
                  <span className="text-xs font-medium text-gray-900">${budget}/gün</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Detay Paneli */}
        <div className="lg:col-span-2 space-y-4">
          {/* Skor Kartı */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <div className="flex items-start justify-between mb-5">
              <div>
                <h2 className="text-lg font-bold text-gray-900">{selectedProduct.title}</h2>
                <span className={clsx("text-xs px-2 py-0.5 rounded-full border mt-1 inline-block", config.color)}>
                  {config.label}
                </span>
              </div>
              <div className="text-right">
                <p className="text-4xl font-bold text-gray-900">{selectedProduct.score}</p>
                <p className="text-xs text-gray-400">/ 100 puan</p>
              </div>
            </div>

            {/* Faktör çubukları */}
            <div className="space-y-4">
              {scoreFactors.map((factor) => {
                const raw = selectedProduct.scoreDetails[factor.key as keyof typeof selectedProduct.scoreDetails];
                const pct = Math.round((raw / 100) * factor.max);
                const exp = EXPLAINERS[factor.explainerId];
                return (
                  <div key={factor.key}>
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-1.5 text-xs text-gray-600">
                        <span className="text-gray-400">{factor.icon}</span>
                        <span>{factor.label}</span>
                        {exp && <InfoModal explainer={exp} />}
                      </div>
                      <span className="text-xs font-medium text-gray-700">{pct}/{factor.max} puan</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div
                        className={clsx("h-2 rounded-full transition-all", config.bar)}
                        style={{ width: `${raw}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{factor.description}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Görünürlük Analizi */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-sm font-semibold text-gray-700">Görünürlük Analizi</h3>
              <InfoModal explainer={EXPLAINERS.view_analysis} />
            </div>

            <ViewSituationCard
              situation={selectedProduct.view_situation}
              diagnosis={selectedProduct.view_diagnosis}
              preAdAction={selectedProduct.pre_ad_action}
            />
          </div>

          {/* Bütçe Önerisi */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Bütçe Önerisi</h3>
            {selectedProduct.suggested_budget > 0 ? (
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600">${selectedProduct.suggested_budget}</p>
                  <p className="text-xs text-gray-400">önerilen günlük bütçe</p>
                </div>
                <div className="flex-1 text-sm text-gray-600 leading-relaxed">
                  Bu bütçe, ürünün ROAS trendi, kâr marjı ve skor faktörlerine dayanarak hesaplanmıştır.
                  Reklam performansını haftada bir kontrol et ve gerekirse güncelle.
                </div>
              </div>
            ) : (
              <div className="bg-red-50 rounded-lg p-3 text-sm text-red-800">
                Bu ürün için şu an reklam önerilmiyor. Yukarıdaki adımları tamamladıktan sonra tekrar kontrol et.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function ViewSituationCard({
  situation, diagnosis, preAdAction,
}: { situation: string; diagnosis: string; preAdAction: string | null }) {
  const configs: Record<string, { emoji: string; title: string; color: string }> = {
    low_views_good_conversion: {
      emoji: "🎯",
      title: "Az Görüntülenme, İyi Dönüşüm",
      color: "bg-green-50 border-green-200 text-green-900",
    },
    high_views_low_sales: {
      emoji: "⚠️",
      title: "Çok Görüntülenme, Az Satış",
      color: "bg-yellow-50 border-yellow-200 text-yellow-900",
    },
    low_views_low_conversion: {
      emoji: "🔴",
      title: "Az Görüntülenme, Az Satış",
      color: "bg-red-50 border-red-200 text-red-900",
    },
    balanced: {
      emoji: "✓",
      title: "Dengeli Durum",
      color: "bg-blue-50 border-blue-200 text-blue-900",
    },
  };

  const cfg = configs[situation] || configs.balanced;

  return (
    <div className={clsx("rounded-xl border p-4", cfg.color)}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{cfg.emoji}</span>
        <span className="text-sm font-semibold">{cfg.title}</span>
      </div>
      <p className="text-sm leading-relaxed mb-3">{diagnosis}</p>

      {preAdAction && (
        <div className="mt-3 pt-3 border-t border-current border-opacity-20">
          <p className="text-xs font-semibold mb-1">Reklam vermeden önce yapılacaklar:</p>
          <p className="text-sm leading-relaxed">{preAdAction}</p>
        </div>
      )}
    </div>
  );
}

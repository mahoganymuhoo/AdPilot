"use client";
import { useState } from "react";
import useSWR from "swr";
import KpiCard from "@/components/ui/KpiCard";
import RoasChart from "@/components/charts/RoasChart";
import SpendRevenueChart from "@/components/charts/SpendRevenueChart";
import InsightPanel from "@/components/ai-panel/InsightPanel";
import { AlertTriangle } from "lucide-react";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

// Demo verisi — API bağlandığında değiştirilecek
const DEMO_CHART_DATA = [
  { date: "01/05", roas: 2.1, ema7: 2.0, ema30: 1.9, ad_spend: 12, revenue: 25 },
  { date: "05/05", roas: 2.8, ema7: 2.3, ema30: 2.1, ad_spend: 15, revenue: 42 },
  { date: "10/05", roas: 3.2, ema7: 2.7, ema30: 2.3, ad_spend: 18, revenue: 58 },
  { date: "15/05", roas: 4.1, ema7: 3.2, ema30: 2.6, ad_spend: 20, revenue: 82 },
  { date: "20/05", roas: 3.8, ema7: 3.5, ema30: 2.9, ad_spend: 22, revenue: 84 },
  { date: "22/05", roas: 4.2, ema7: 3.8, ema30: 3.1, ad_spend: 25, revenue: 105 },
];

const DEMO_INSIGHT = {
  is_profitable: true,
  roas_status: "good",
  recommendation: "increase_budget",
  budget_change_pct: 20,
  reasoning: "ROAS 3.8'e yükseldi ve 7 günlük EMA 30 günlük EMA'nın üzerine çıktı — güçlü yükseliş trendi. Kâr marjınız reklam maliyetini rahatça karşılıyor.",
  red_flags: [],
  action_items: ["Günlük bütçeyi $25'tan $30'a çıkar", "Yüksek performanslı ürünlere odaklan", "CTR düşen ürünlerin listing'ini güncelle"],
  ai_provider: "claude",
};

export default function DashboardPage() {
  const [selectedProduct, setSelectedProduct] = useState<number | null>(null);

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Son 30 günlük reklam performansı</p>
      </div>

      {/* KPI Kartları */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KpiCard
          title="Ortalama ROAS"
          value="3.8x"
          subtitle="Hedef: 3.0x"
          trend="improving"
          status="good"
          badge="Son 30g"
        />
        <KpiCard
          title="ACOS"
          value="%26.3"
          subtitle="Break-even: %35"
          trend="improving"
          status="good"
        />
        <KpiCard
          title="TACoS"
          value="%18.5"
          subtitle="Toplam gelire oranla"
          trend="stable"
          status="neutral"
        />
        <KpiCard
          title="Net Kâr"
          value="$342"
          subtitle="Reklam sonrası"
          trend="improving"
          status="good"
        />
      </div>

      {/* Grafikler + AI Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <div className="lg:col-span-2">
          <RoasChart data={DEMO_CHART_DATA} targetRoas={3.0} />
        </div>
        <InsightPanel insight={DEMO_INSIGHT} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <SpendRevenueChart data={DEMO_CHART_DATA} />

        {/* Anomali Uyarıları */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Anomali Uyarıları</h3>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-yellow-50 border border-yellow-200">
              <AlertTriangle size={16} className="text-yellow-600 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium text-yellow-800">CTR Düşüşü Tespit Edildi</p>
                <p className="text-xs text-yellow-600 mt-0.5">
                  Örme Çanta ürününde CTR %2.1'den %1.3'e düştü. Z-Score: -2.8
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-lg bg-green-50 border border-green-200">
              <AlertTriangle size={16} className="text-green-600 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium text-green-800">ROAS Artışı</p>
                <p className="text-xs text-green-600 mt-0.5">
                  Seramik Kupa ürününde ROAS %40 arttı — bütçe artırımı öneriliyor.
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-400 text-center pt-2">
              Gerçek veriler bağlandığında anomaliler otomatik tespit edilecek.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

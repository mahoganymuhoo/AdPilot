"use client";
import { useState } from "react";
import KpiCard from "@/components/ui/KpiCard";
import RoasChart from "@/components/charts/RoasChart";
import SpendRevenueChart from "@/components/charts/SpendRevenueChart";
import InsightPanel from "@/components/ai-panel/InsightPanel";
import InfoModal from "@/components/ui/InfoModal";
import DateRangePicker, { DateRange } from "@/components/ui/DateRangePicker";
import { AlertTriangle, HelpCircle, Download } from "lucide-react";
import { EXPLAINERS } from "@/lib/explainers";
import { exportDashboardMetrics } from "@/lib/export";

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
  reasoning:
    "ROAS 3.8'e yükseldi ve 7 günlük EMA 30 günlük EMA'nın üzerine çıktı — güçlü yükseliş trendi. Kâr marjınız reklam maliyetini rahatça karşılıyor.",
  red_flags: [],
  action_items: [
    "Günlük bütçeyi $25'tan $30'a çıkar",
    "Yüksek performanslı ürünlere odaklan",
    "CTR düşen ürünlerin listing'ini güncelle",
  ],
  ai_provider: "claude",
};

export default function DashboardPage() {
  const [days, setDays] = useState<DateRange>(30);

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Reklam performansı — metriklerin yanındaki{" "}
            <HelpCircle size={12} className="inline text-gray-400" /> ikonuna tıklayarak ne anlama geldiğini öğren.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <DateRangePicker value={days} onChange={setDays} />
          <button
            onClick={() => exportDashboardMetrics(DEMO_CHART_DATA, days)}
            title="CSV olarak indir"
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors"
          >
            <Download size={15} />
          </button>
        </div>
      </div>

      {/* KPI Kartları */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KpiCard
          title="Ortalama ROAS"
          value="3.8x"
          subtitle="Hedef: 3.0x ✓"
          trend="improving"
          status="good"
          badge={`Son ${days}g`}
          explainer={EXPLAINERS.roas}
        />
        <KpiCard
          title="ACOS"
          value="%26.3"
          subtitle="Break-even: %35 — Karlısın"
          trend="improving"
          status="good"
          explainer={EXPLAINERS.acos}
        />
        <KpiCard
          title="TACoS"
          value="%18.5"
          subtitle="Toplam gelire oranla"
          trend="stable"
          status="neutral"
          explainer={EXPLAINERS.tacos}
        />
        <KpiCard
          title="Net Kâr"
          value="$342"
          subtitle="Tüm masraflar düşüldükten sonra"
          trend="improving"
          status="good"
          explainer={EXPLAINERS.net_profit}
        />
      </div>

      {/* Break-even ACOS Göstergesi */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-700">Break-even ACOS Kontrolü</span>
            <InfoModal explainer={EXPLAINERS.breakeven_acos} />
          </div>
          <span className="text-xs text-green-600 font-medium bg-green-50 px-2 py-0.5 rounded-full">
            Reklamın karlı ✓
          </span>
        </div>
        <div className="relative h-4 bg-gray-100 rounded-full overflow-hidden">
          {/* Mevcut ACOS */}
          <div
            className="absolute left-0 top-0 h-full bg-green-400 rounded-full transition-all"
            style={{ width: "26.3%" }}
          />
          {/* Break-even çizgisi */}
          <div
            className="absolute top-0 h-full w-0.5 bg-red-400"
            style={{ left: "35%" }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>%0</span>
          <span className="text-green-600 font-medium">Mevcut ACOS %26.3</span>
          <span className="text-red-500">Break-even %35</span>
          <span>%100</span>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          ACOS mevcut kâr marjından (%35) düşük kaldığı sürece her reklam satışı sana para kazandırıyor.
        </p>
      </div>

      {/* ROAS Trendi Grafiği + AI Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <div className="lg:col-span-2">
          <RoasChartWithInfo data={DEMO_CHART_DATA} />
        </div>
        <InsightPanel insight={DEMO_INSIGHT} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <SpendRevenueChart data={DEMO_CHART_DATA} />

        {/* Anomali Uyarıları */}
        <AnomalySection />
      </div>
    </div>
  );
}

function RoasChartWithInfo({ data }: { data: typeof DEMO_CHART_DATA }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-1">
        <h3 className="text-sm font-semibold text-gray-700">ROAS Trendi</h3>
        <InfoModal explainer={EXPLAINERS.ema_trend} />
      </div>
      <p className="text-xs text-gray-400 mb-4">
        <span className="inline-block w-3 h-0.5 bg-green-500 mr-1 align-middle" />
        7g EMA (kısa vade) &nbsp;·&nbsp;
        <span className="inline-block w-3 h-0.5 bg-blue-400 mr-1 align-middle" style={{ borderTop: "2px dashed #60a5fa", background: "none" }} />
        30g EMA (uzun vade) — 7g EMA 30g EMA'nın üzerindeyse yükseliş var
      </p>
      {/* RoasChart bileşenini inline render etmek yerine içe aktarıyoruz */}
      <RoasChartInner data={data} />
    </div>
  );
}

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ReferenceLine, ResponsiveContainer,
} from "recharts";

function RoasChartInner({ data }: { data: typeof DEMO_CHART_DATA }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} />
        <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
          formatter={(v: number, name: string) => [
            v.toFixed(2),
            name === "roas" ? "ROAS (günlük)" : name === "ema7" ? "7g EMA" : "30g EMA",
          ]}
        />
        <ReferenceLine y={3.0} stroke="#ef4444" strokeDasharray="4 4" label={{ value: "Hedef 3.0x", fontSize: 10, fill: "#ef4444" }} />
        <Line type="monotone" dataKey="roas" stroke="#d1d5db" strokeWidth={1.5} dot={false} name="roas" />
        <Line type="monotone" dataKey="ema7" stroke="#22c55e" strokeWidth={2.5} dot={false} name="ema7" />
        <Line type="monotone" dataKey="ema30" stroke="#60a5fa" strokeWidth={2} dot={false} name="ema30" strokeDasharray="5 3" />
      </LineChart>
    </ResponsiveContainer>
  );
}

function AnomalySection() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <h3 className="text-sm font-semibold text-gray-700">Anomali Uyarıları</h3>
        <InfoModal explainer={EXPLAINERS.zscore_anomaly} />
      </div>

      <div className="space-y-3">
        <AnomalyCard
          severity="warning"
          title="CTR Ani Düşüş"
          product="Örme Çanta"
          metric="CTR"
          current="%1.3"
          expected="%2.1"
          zscore="-2.8"
          meaning="Reklamın 1000 gösterimde 21 yerine 13 tıklama alıyor. Listing fotoğrafı veya Etsy sıralaması sorun yaratıyor olabilir."
          action="Ana fotoğrafı kontrol et, rakiplerle kıyasla."
        />
        <AnomalyCard
          severity="good"
          title="ROAS Ani Artış"
          product="Seramik Kupa"
          metric="ROAS"
          current="4.2x"
          expected="2.9x"
          zscore="+2.5"
          meaning="Normalden %45 daha iyi performans. Sezonsal talep mi arttı? Bu momentum'u değerlendir."
          action="Bütçeyi geçici olarak artır, trend devam ettiği sürece koru."
        />
      </div>

      <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-100">
        <p className="text-xs text-gray-500 leading-relaxed">
          <span className="font-semibold text-gray-700">Z-Score nedir? </span>
          Bir değerin geçmiş 30 günlük ortalamadan ne kadar uzaklaştığını ölçer.
          ±2.5 üzeri sapma "olağandışı" sayılır ve seni uyarırız.{" "}
          <InfoModal
            explainer={EXPLAINERS.zscore_anomaly}
            trigger={
              <span className="text-blue-500 hover:underline cursor-pointer">Detaylı açıklama →</span>
            }
          />
        </p>
      </div>
    </div>
  );
}

function AnomalyCard({
  severity, title, product, metric, current, expected, zscore, meaning, action,
}: {
  severity: "warning" | "good" | "danger";
  title: string; product: string; metric: string;
  current: string; expected: string; zscore: string;
  meaning: string; action: string;
}) {
  const [expanded, setExpanded] = useState(false);

  const colors = {
    warning: "bg-yellow-50 border-yellow-200 text-yellow-800",
    good: "bg-green-50 border-green-200 text-green-800",
    danger: "bg-red-50 border-red-200 text-red-800",
  };
  const iconColors = {
    warning: "text-yellow-600",
    good: "text-green-600",
    danger: "text-red-600",
  };

  return (
    <button
      onClick={() => setExpanded(!expanded)}
      className={`w-full text-left rounded-lg border p-3 transition-all ${colors[severity]}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-2">
          <AlertTriangle size={15} className={`${iconColors[severity]} mt-0.5 shrink-0`} />
          <div>
            <p className="text-sm font-medium">{title}</p>
            <p className="text-xs opacity-75 mt-0.5">
              {product} · {metric}: {current} (beklenen: {expected}) · Z-Score: {zscore}
            </p>
          </div>
        </div>
        <span className="text-xs opacity-60">{expanded ? "▲" : "▼"}</span>
      </div>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-current border-opacity-20 space-y-2">
          <div>
            <p className="text-xs font-semibold opacity-75 mb-0.5">Ne anlama geliyor?</p>
            <p className="text-xs opacity-80 leading-relaxed">{meaning}</p>
          </div>
          <div>
            <p className="text-xs font-semibold opacity-75 mb-0.5">Ne yapmalısın?</p>
            <p className="text-xs opacity-80 leading-relaxed">{action}</p>
          </div>
        </div>
      )}
    </button>
  );
}

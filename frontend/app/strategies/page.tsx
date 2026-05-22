"use client";
import { useState } from "react";
import { Target, CheckCircle, Clock, AlertTriangle, XCircle, ChevronDown, ChevronUp, TrendingUp, TrendingDown, Minus } from "lucide-react";
import clsx from "clsx";
import { useStrategies, useStrategy } from "@/lib/hooks";
import { PageLoader, PageError, EmptyState } from "@/components/ui/PageStates";

// ---- Demo veri (backend bağlanana kadar fallback) ----
const DEMO_STRATEGIES = [
  {
    id: 1,
    name: "Seramik Kupa — Bütçe Artışı",
    operation_type: "increase_budget",
    status: "active",
    days_elapsed: 6,
    days_remaining: 8,
    goal_summary: "Günlük bütçeyi $12'dan $15'a çıkararak ROAS'ı 4.0'dan 4.8'e taşı",
    initial_metrics: { roas: 4.0, acos: 25.0, daily_revenue: 28.0 },
    target_metrics: { roas: 4.8, acos: 20.0, daily_revenue: 38.0 },
    success_criteria: ["ROAS ≥ 4.8", "ACOS ≤ 20%", "Günlük gelir ≥ $38"],
    checkpoints: [
      {
        id: 1, checked_at: "2026-05-16", status: "on_track", progress_pct: 40,
        current_metrics: { roas: 4.2, acos: 23.8, daily_revenue: 31.0 },
        checkpoint_insight: "Bütçe artışı ilk 3 günde ROAS'ı hafif yükseltti. Trafik arttı, dönüşüm stabil.",
        metric_deltas: { roas_change: +0.2, acos_change: -1.2, revenue_change_pct: +10.7 },
        red_flags: [],
      },
      {
        id: 2, checked_at: "2026-05-19", status: "on_track", progress_pct: 65,
        current_metrics: { roas: 4.5, acos: 22.2, daily_revenue: 34.0 },
        checkpoint_insight: "Güçlü ilerleme. CTR %1.8'den %2.1'e çıktı. Hedefin %65'ine ulaşıldı.",
        metric_deltas: { roas_change: +0.3, acos_change: -1.6, revenue_change_pct: +9.7 },
        red_flags: [],
      },
    ],
    outcome: null,
  },
  {
    id: 2,
    name: "Makrome Süs — Küçük Bütçe Testi",
    operation_type: "test_budget",
    status: "completed",
    days_elapsed: 14,
    days_remaining: 0,
    goal_summary: "$5/gün test bütçesiyle dönüşüm oranını ölç, reklam değerini test et",
    initial_metrics: { roas: 2.8, acos: 35.7, daily_revenue: 12.0 },
    target_metrics: { roas: 3.2, acos: 31.0, daily_revenue: 18.0 },
    success_criteria: ["ROAS ≥ 3.2", "ACOS ≤ 31%", "En az 2 dönüşüm/gün"],
    checkpoints: [
      {
        id: 3, checked_at: "2026-05-09", status: "at_risk", progress_pct: 20,
        current_metrics: { roas: 2.6, acos: 38.5, daily_revenue: 11.0 },
        checkpoint_insight: "ROAS düştü. Mevsimsel baskı veya rakip fiyat değişikliği olabilir.",
        metric_deltas: { roas_change: -0.2, acos_change: +2.8, revenue_change_pct: -8.3 },
        red_flags: ["ROAS hedefin altında", "ACOS artıyor"],
      },
      {
        id: 4, checked_at: "2026-05-12", status: "at_risk", progress_pct: 30,
        current_metrics: { roas: 2.9, acos: 34.5, daily_revenue: 13.5 },
        checkpoint_insight: "Biraz toparlandı ama hedefler için yeterli değil.",
        metric_deltas: { roas_change: +0.3, acos_change: -4.0, revenue_change_pct: +22.7 },
        red_flags: ["Süre bitmeden hedeflere ulaşmak zor"],
      },
    ],
    outcome: {
      outcome: "partial",
      outcome_summary: "Kısmi başarı — ROAS hedefine ulaşılamadı, gelir hedefi %75 karşılandı",
      metric_results: {
        roas_start: 2.8, roas_end: 2.9, roas_target: 3.2, roas_achieved: false,
        acos_start: 35.7, acos_end: 34.5, acos_target: 31.0, acos_achieved: false,
        revenue_change_pct: +12.5,
      },
      what_worked: ["Trafik %18 arttı", "CTR stabil kaldı", "Mevsimsel dip yakalandı"],
      what_failed: ["ROAS hedefine ulaşılamadı", "Dönüşüm oranı beklentinin altında"],
      lessons_learned: [
        "Makrome ürünler için $5/gün bütçe impression için yeterli değil",
        "Bu ürün kategorisi yaz aylarında düşüş yaşıyor — sonbahara kadar bekle",
      ],
      next_strategy_hints: {
        recommended_action: "Eylül'e kadar durdur, sonra $8/gün ile tekrar test et",
        suggested_budget: 8.0,
        focus_area: "timing",
        context_for_next_ai: "Makrome ürün yaz döneminde düşük performans. Sonbahar-kış sezonu için reklam planla.",
      },
    },
  },
];

const statusConfig = {
  active: { label: "Aktif", icon: Clock, color: "text-blue-600 bg-blue-50 border-blue-200" },
  monitoring: { label: "İzleniyor", icon: AlertTriangle, color: "text-yellow-600 bg-yellow-50 border-yellow-200" },
  completed: { label: "Tamamlandı", icon: CheckCircle, color: "text-green-600 bg-green-50 border-green-200" },
  failed: { label: "Başarısız", icon: XCircle, color: "text-red-600 bg-red-50 border-red-200" },
};

const outcomeConfig = {
  success: { label: "Başarılı", color: "text-green-700 bg-green-100 border-green-300" },
  partial: { label: "Kısmi Başarı", color: "text-yellow-700 bg-yellow-100 border-yellow-300" },
  failed: { label: "Başarısız", color: "text-red-700 bg-red-100 border-red-300" },
};

const checkpointStatusConfig = {
  on_track: { label: "Yolunda", color: "text-green-600", dot: "bg-green-500" },
  at_risk: { label: "Riskli", color: "text-yellow-600", dot: "bg-yellow-500" },
  off_track: { label: "Sapma Var", color: "text-red-600", dot: "bg-red-500" },
};

const opTypeLabels: Record<string, string> = {
  increase_budget: "Bütçe Artışı",
  reduce_budget: "Bütçe Düşüşü",
  pause_ads: "Reklam Durdurma",
  test_budget: "Bütçe Testi",
  optimize_listing: "Listing Optimizasyonu",
};

export default function StrategiesPage() {
  const [selected, setSelected] = useState<number>(1);
  const { data: apiData, error: apiError, isLoading } = useStrategies();

  // API'den veri geldiyse kullan, gelmediyse demo
  const strategies = (apiData?.strategies && apiData.strategies.length > 0)
    ? apiData.strategies
    : DEMO_STRATEGIES;

  const strategy = strategies.find((s: any) => s.id === selected) ?? strategies[0];
  const statusCfg = statusConfig[(strategy?.status as keyof typeof statusConfig) ?? "active"];
  const StatusIcon = statusCfg.icon;

  if (isLoading) return <PageLoader label="Stratejiler yükleniyor..." />;

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Strateji Takibi</h1>
        <p className="text-sm text-gray-500 mt-1">
          AI önerisi → Aksiyon → Takip → Sonuç. Her strateji DB'ye kaydedilir, sonraki kararlara beslenir.
        </p>
        {apiError && (
          <p className="text-xs text-amber-600 mt-1">⚠ Backend bağlantısı yok — demo veri gösteriliyor</p>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sol: Strateji Listesi */}
        <div className="lg:col-span-1 space-y-3">
          {strategies.map((s: any) => {
            const cfg = statusConfig[s.status as keyof typeof statusConfig];
            const SIcon = cfg.icon;
            const totalDays = s.days_elapsed + s.days_remaining;
            const progressPct = totalDays > 0 ? Math.round((s.days_elapsed / totalDays) * 100) : 100;

            return (
              <button
                key={s.id}
                onClick={() => setSelected(s.id)}
                className={clsx(
                  "w-full text-left bg-white rounded-xl border shadow-sm p-4 transition-all hover:shadow-md",
                  selected === s.id ? "border-blue-300 ring-1 ring-blue-200" : "border-gray-200"
                )}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1 pr-2">
                    <p className="text-sm font-semibold text-gray-900 leading-tight">{s.name}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{opTypeLabels[s.operation_type] || s.operation_type}</p>
                  </div>
                  <span className={clsx("flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border shrink-0", cfg.color)}>
                    <SIcon size={11} />
                    {cfg.label}
                  </span>
                </div>

                {/* Zaman çubuğu */}
                <div className="mb-2">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>{s.days_elapsed}. gün</span>
                    <span>{s.days_remaining > 0 ? `${s.days_remaining} gün kaldı` : "Tamamlandı"}</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-1.5">
                    <div
                      className={clsx("h-1.5 rounded-full", s.status === "completed" ? "bg-green-500" : "bg-blue-500")}
                      style={{ width: `${progressPct}%` }}
                    />
                  </div>
                </div>

                <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">{s.goal_summary}</p>
                <p className="text-xs text-gray-400 mt-1">{s.checkpoints.length} checkpoint kaydedildi</p>
              </button>
            );
          })}

          {/* Yeni Strateji Başlat */}
          <button className="w-full bg-gray-900 text-white rounded-xl py-3 text-sm font-medium hover:bg-gray-700 transition-colors">
            + Yeni Strateji Başlat
          </button>
        </div>

        {/* Sağ: Detay */}
        <div className="lg:col-span-2 space-y-4">
          {/* Strateji Başlığı */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-gray-900">{strategy.name}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-400">{opTypeLabels[strategy.operation_type]}</span>
                  <span className="text-gray-300">·</span>
                  <span className={clsx("flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border", statusCfg.color)}>
                    <StatusIcon size={11} />
                    {statusCfg.label}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {strategy.checkpoints.length > 0
                    ? `%${strategy.checkpoints[strategy.checkpoints.length - 1].progress_pct}`
                    : "—"}
                </p>
                <p className="text-xs text-gray-400">hedefe ilerleme</p>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 mb-4">
              <p className="text-sm text-blue-900 font-medium">{strategy.goal_summary}</p>
            </div>

            {/* Başlangıç → Hedef Karşılaştırma */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "ROAS", start: strategy.initial_metrics.roas, target: strategy.target_metrics.roas, suffix: "x" },
                { label: "ACOS", start: strategy.initial_metrics.acos, target: strategy.target_metrics.acos, suffix: "%" },
                { label: "Günlük Gelir", start: strategy.initial_metrics.daily_revenue, target: strategy.target_metrics.daily_revenue, suffix: "$", prefix: "$" },
              ].map((m) => (
                <div key={m.label} className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                  <p className="text-xs text-gray-400 mb-1">{m.label}</p>
                  <div className="flex items-center gap-1">
                    <span className="text-sm font-semibold text-gray-600">
                      {m.prefix}{m.start}{m.suffix}
                    </span>
                    <span className="text-gray-300 text-xs">→</span>
                    <span className="text-sm font-bold text-green-600">
                      {m.prefix}{m.target}{m.suffix}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Başarı Kriterleri */}
            <div className="mt-4">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Başarı Kriterleri</p>
              <div className="flex flex-wrap gap-2">
                {strategy.success_criteria.map((c, i) => (
                  <span key={i} className="text-xs bg-gray-100 text-gray-700 px-2.5 py-1 rounded-full border border-gray-200">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Checkpoint Zaman Çizelgesi */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Takip Günlüğü</h3>

            {strategy.checkpoints.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-6">Henüz checkpoint kaydedilmedi.</p>
            ) : (
              <div className="space-y-0">
                {strategy.checkpoints.map((cp, idx) => (
                  <CheckpointCard key={cp.id} cp={cp} idx={idx} isLast={idx === strategy.checkpoints.length - 1} />
                ))}
                {strategy.status === "active" && (
                  <div className="flex gap-4 py-3 pl-1">
                    <div className="flex flex-col items-center w-8 shrink-0">
                      <div className="w-2 h-2 rounded-full border-2 border-dashed border-gray-300" />
                    </div>
                    <p className="text-xs text-gray-400 italic pt-0.5">
                      Sonraki checkpoint: {strategy.days_remaining} gün içinde
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Sonuç Kartı (tamamlanmış stratejiler için) */}
          {strategy.outcome && (
            <OutcomeCard outcome={strategy.outcome} />
          )}
        </div>
      </div>
    </div>
  );
}

function CheckpointCard({ cp, idx, isLast }: { cp: any; idx: number; isLast: boolean }) {
  const [open, setOpen] = useState(idx === 0 ? false : false);
  const cfg = checkpointStatusConfig[cp.status as keyof typeof checkpointStatusConfig] || checkpointStatusConfig.on_track;

  return (
    <div className="flex gap-4">
      {/* Zaman çizelgesi çizgisi */}
      <div className="flex flex-col items-center w-8 shrink-0">
        <div className={clsx("w-3 h-3 rounded-full mt-3.5 shrink-0", cfg.dot)} />
        {!isLast && <div className="w-0.5 bg-gray-200 flex-1 mt-1" />}
      </div>

      <div className="flex-1 pb-4">
        <button
          onClick={() => setOpen(!open)}
          className="w-full text-left bg-gray-50 border border-gray-100 rounded-xl px-4 py-3 hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">{cp.checked_at}</span>
              <span className={clsx("text-xs font-medium", cfg.color)}>{cfg.label}</span>
              <span className="text-xs text-gray-400">· %{cp.progress_pct} tamamlandı</span>
            </div>
            {open ? <ChevronUp size={14} className="text-gray-400" /> : <ChevronDown size={14} className="text-gray-400" />}
          </div>
          <p className="text-sm text-gray-700 mt-1 font-medium">{cp.checkpoint_insight}</p>
        </button>

        {open && (
          <div className="mt-2 bg-white border border-gray-100 rounded-xl px-4 py-3 space-y-3">
            {/* Metrik değişimleri */}
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Metrik Değişimleri</p>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: "ROAS", value: cp.metric_deltas.roas_change, suffix: "x" },
                  { label: "ACOS", value: cp.metric_deltas.acos_change, suffix: "%" },
                  { label: "Gelir", value: cp.metric_deltas.revenue_change_pct, suffix: "%" },
                ].map((d) => (
                  <div key={d.label} className="bg-gray-50 rounded-lg p-2.5 text-center border border-gray-100">
                    <p className="text-xs text-gray-400 mb-1">{d.label}</p>
                    <div className="flex items-center justify-center gap-1">
                      {d.value > 0 ? (
                        <TrendingUp size={12} className="text-green-500" />
                      ) : d.value < 0 ? (
                        <TrendingDown size={12} className="text-red-500" />
                      ) : (
                        <Minus size={12} className="text-gray-400" />
                      )}
                      <span className={clsx(
                        "text-sm font-bold",
                        d.value > 0 ? "text-green-600" : d.value < 0 ? "text-red-600" : "text-gray-600"
                      )}>
                        {d.value > 0 ? "+" : ""}{d.value}{d.suffix}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Mevcut metrikler */}
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Anlık Durum</p>
              <div className="flex gap-4 text-xs">
                <span className="text-gray-600">ROAS: <strong>{cp.current_metrics.roas}x</strong></span>
                <span className="text-gray-600">ACOS: <strong>{cp.current_metrics.acos}%</strong></span>
                <span className="text-gray-600">Gelir/gün: <strong>${cp.current_metrics.daily_revenue}</strong></span>
              </div>
            </div>

            {/* Red flags */}
            {cp.red_flags.length > 0 && (
              <div className="bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                <p className="text-xs font-semibold text-red-700 mb-1">Uyarılar</p>
                {cp.red_flags.map((f: string, i: number) => (
                  <p key={i} className="text-xs text-red-800">• {f}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function OutcomeCard({ outcome }: { outcome: any }) {
  const cfg = outcomeConfig[outcome.outcome as keyof typeof outcomeConfig];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700">AI Nihai Değerlendirmesi</h3>
        <span className={clsx("text-xs px-2.5 py-1 rounded-full border font-semibold", cfg.color)}>
          {cfg.label}
        </span>
      </div>

      <div className="bg-gray-50 rounded-xl px-4 py-3 mb-4 border border-gray-100">
        <p className="text-sm text-gray-800 font-medium">{outcome.outcome_summary}</p>
      </div>

      {/* Metrik sonuçları */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {[
          { label: "ROAS", start: outcome.metric_results.roas_start, end: outcome.metric_results.roas_end, target: outcome.metric_results.roas_target, achieved: outcome.metric_results.roas_achieved, suffix: "x" },
          { label: "ACOS", start: outcome.metric_results.acos_start, end: outcome.metric_results.acos_end, target: outcome.metric_results.acos_target, achieved: outcome.metric_results.acos_achieved, suffix: "%" },
        ].map((m) => (
          <div key={m.label} className={clsx(
            "rounded-xl p-3 border",
            m.achieved ? "bg-green-50 border-green-100" : "bg-red-50 border-red-100"
          )}>
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-semibold text-gray-600">{m.label}</p>
              <span className={clsx("text-xs font-bold", m.achieved ? "text-green-600" : "text-red-600")}>
                {m.achieved ? "✓ Ulaşıldı" : "✗ Ulaşılamadı"}
              </span>
            </div>
            <p className="text-xs text-gray-500">
              {m.start}{m.suffix} → <strong>{m.end}{m.suffix}</strong>
              <span className="text-gray-400 ml-1">(hedef: {m.target}{m.suffix})</span>
            </p>
          </div>
        ))}
      </div>

      {/* Ne işe yaradı / Ne başarısız oldu */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <p className="text-xs font-semibold text-green-700 mb-1">✓ İyi Giden</p>
          {outcome.what_worked.map((w: string, i: number) => (
            <p key={i} className="text-xs text-gray-600 mb-0.5">• {w}</p>
          ))}
        </div>
        <div>
          <p className="text-xs font-semibold text-red-700 mb-1">✗ Başarısız</p>
          {outcome.what_failed.map((f: string, i: number) => (
            <p key={i} className="text-xs text-gray-600 mb-0.5">• {f}</p>
          ))}
        </div>
      </div>

      {/* Öğrenilenleri */}
      <div className="bg-amber-50 border border-amber-100 rounded-xl px-4 py-3 mb-4">
        <p className="text-xs font-semibold text-amber-800 mb-2">💡 Öğrenilenleri</p>
        {outcome.lessons_learned.map((l: string, i: number) => (
          <p key={i} className="text-xs text-amber-900 mb-1">• {l}</p>
        ))}
      </div>

      {/* Bir sonraki strateji için öneri */}
      {outcome.next_strategy_hints && (
        <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3">
          <p className="text-xs font-semibold text-blue-800 mb-2">→ Bir Sonraki Adım (AI Önerisi)</p>
          <p className="text-xs text-blue-900 font-medium mb-1">{outcome.next_strategy_hints.recommended_action}</p>
          <div className="flex gap-3 text-xs text-blue-700 mt-1">
            <span>Önerilen bütçe: <strong>${outcome.next_strategy_hints.suggested_budget}/gün</strong></span>
            <span>·</span>
            <span>Odak: <strong>{outcome.next_strategy_hints.focus_area}</strong></span>
          </div>
          {outcome.next_strategy_hints.context_for_next_ai && (
            <div className="mt-2 pt-2 border-t border-blue-200">
              <p className="text-xs text-blue-600 italic">"{outcome.next_strategy_hints.context_for_next_ai}"</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

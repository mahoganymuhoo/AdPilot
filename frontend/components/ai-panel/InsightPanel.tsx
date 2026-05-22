"use client";
import { AlertTriangle, CheckCircle, TrendingDown, TrendingUp, Zap } from "lucide-react";
import clsx from "clsx";

interface InsightPanelProps {
  insight: {
    is_profitable?: boolean;
    roas_status?: string;
    recommendation?: string;
    budget_change_pct?: number;
    reasoning?: string;
    red_flags?: string[];
    action_items?: string[];
    score?: number;
    pre_ad_action?: string | null;
    ai_provider?: string;
  } | null;
  loading?: boolean;
}

const recommendationConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  increase_budget: { label: "Bütçeyi Artır", color: "bg-green-100 text-green-700", icon: <TrendingUp size={16} /> },
  maintain: { label: "Bütçeyi Koru", color: "bg-blue-100 text-blue-700", icon: <Zap size={16} /> },
  reduce_budget: { label: "Bütçeyi Azalt", color: "bg-yellow-100 text-yellow-700", icon: <TrendingDown size={16} /> },
  pause_ads: { label: "Reklamı Durdur", color: "bg-red-100 text-red-700", icon: <AlertTriangle size={16} /> },
};

export default function InsightPanel({ insight, loading }: InsightPanelProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm animate-pulse">
        <div className="h-4 bg-gray-100 rounded w-32 mb-4" />
        <div className="space-y-2">
          <div className="h-3 bg-gray-100 rounded w-full" />
          <div className="h-3 bg-gray-100 rounded w-4/5" />
        </div>
      </div>
    );
  }

  if (!insight) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm text-center">
        <p className="text-sm text-gray-400">AI analizi için ürün seçin.</p>
      </div>
    );
  }

  const rec = insight.recommendation ? recommendationConfig[insight.recommendation] : null;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700">AI Analizi</h3>
        {insight.ai_provider && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-purple-50 text-purple-600">
            {insight.ai_provider === "claude" ? "Claude" : "OpenAI"}
          </span>
        )}
      </div>

      {/* Karlılık durumu */}
      {insight.is_profitable !== undefined && (
        <div className={clsx(
          "flex items-center gap-2 px-3 py-2 rounded-lg mb-4 text-sm font-medium",
          insight.is_profitable ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
        )}>
          {insight.is_profitable
            ? <CheckCircle size={16} />
            : <AlertTriangle size={16} />}
          {insight.is_profitable ? "Reklam Karlı" : "Reklam Zararlı"}
        </div>
      )}

      {/* Öneri */}
      {rec && (
        <div className={clsx("flex items-center gap-2 px-3 py-2 rounded-lg mb-4 text-sm font-medium", rec.color)}>
          {rec.icon}
          {rec.label}
          {insight.budget_change_pct !== 0 && insight.budget_change_pct !== undefined && (
            <span className="ml-auto font-bold">
              {insight.budget_change_pct > 0 ? `+${insight.budget_change_pct}%` : `${insight.budget_change_pct}%`}
            </span>
          )}
        </div>
      )}

      {/* Reklam öncesi aksiyon */}
      {insight.pre_ad_action && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4 text-xs text-amber-800">
          <span className="font-semibold">Reklam Öncesi: </span>
          {insight.pre_ad_action}
        </div>
      )}

      {/* Gerekçe */}
      {insight.reasoning && (
        <p className="text-sm text-gray-600 mb-4 leading-relaxed">{insight.reasoning}</p>
      )}

      {/* Kırmızı bayraklar */}
      {insight.red_flags && insight.red_flags.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-semibold text-red-600 mb-1">Uyarılar</p>
          <ul className="space-y-1">
            {insight.red_flags.map((flag, i) => (
              <li key={i} className="text-xs text-red-600 flex gap-1.5">
                <span>•</span>{flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Aksiyon adımları */}
      {insight.action_items && insight.action_items.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-600 mb-1">Yapılacaklar</p>
          <ul className="space-y-1">
            {insight.action_items.map((item, i) => (
              <li key={i} className="text-xs text-gray-500 flex gap-1.5">
                <CheckCircle size={12} className="mt-0.5 text-green-400 shrink-0" />{item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

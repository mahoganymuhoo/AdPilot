"use client";
import { useState } from "react";
import { X, AlertTriangle, TrendingDown, TrendingUp, Zap } from "lucide-react";
import clsx from "clsx";

// Demo anomali verisi — SWR bağlandığında API'den gelecek
const DEMO_ANOMALIES = [
  {
    id: 1,
    product_title: "El Yapımı Seramik Kupa",
    metric: "acos",
    z_score: 2.8,
    severity: "high",
    direction: "up",
    detected_at: "2026-05-22T08:30:00Z",
    is_read: false,
    likely_causes: ["Rakip reklam bütçesi artmış olabilir", "Anahtar kelime rekabeti yükseldi"],
    urgency: "high",
    recommended_actions: ["ACOS'u 24 saat izle", "Düşük performanslı anahtar kelimeleri kapat"],
  },
  {
    id: 2,
    product_title: "Makrome Duvar Süsü",
    metric: "ctr",
    z_score: -2.6,
    severity: "medium",
    direction: "down",
    detected_at: "2026-05-21T14:15:00Z",
    is_read: false,
    likely_causes: ["Reklam görseli yenilenmeli", "Başlık güncelliğini yitirmiş olabilir"],
    urgency: "medium",
    recommended_actions: ["Reklam görselini güncelle", "A/B test için yeni başlık dene"],
  },
];

const severityConfig = {
  critical: { color: "text-red-700 bg-red-100 border-red-300", dot: "bg-red-500", label: "Kritik" },
  high: { color: "text-orange-700 bg-orange-100 border-orange-300", dot: "bg-orange-500", label: "Yüksek" },
  medium: { color: "text-yellow-700 bg-yellow-100 border-yellow-300", dot: "bg-yellow-500", label: "Orta" },
  low: { color: "text-blue-700 bg-blue-100 border-blue-300", dot: "bg-blue-400", label: "Düşük" },
};

const metricLabels: Record<string, string> = {
  acos: "ACOS", roas: "ROAS", ctr: "CTR", conversions: "Dönüşüm", ad_spend: "Reklam Harcaması",
};

interface Props {
  onClose: () => void;
}

export default function AnomalyDrawer({ onClose }: Props) {
  const [readIds, setReadIds] = useState<Set<number>>(new Set());
  const [expanded, setExpanded] = useState<number | null>(null);

  const markRead = (id: number) => setReadIds((prev) => new Set([...prev, id]));

  const anomalies = DEMO_ANOMALIES.map((a) => ({
    ...a,
    is_read: a.is_read || readIds.has(a.id),
  }));

  const unreadCount = anomalies.filter((a) => !a.is_read).length;

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      <div className="relative ml-auto w-full max-w-md bg-white h-full shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <AlertTriangle size={18} className="text-orange-500" />
            <h2 className="text-base font-bold text-gray-900">Anomali Uyarıları</h2>
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
                {unreadCount}
              </span>
            )}
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={18} />
          </button>
        </div>

        {/* Anomali listesi */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {anomalies.length === 0 ? (
            <div className="text-center py-12">
              <Zap size={32} className="text-gray-200 mx-auto mb-3" />
              <p className="text-sm text-gray-400">Anomali tespit edilmedi</p>
            </div>
          ) : (
            anomalies.map((anomaly) => {
              const cfg = severityConfig[anomaly.severity as keyof typeof severityConfig] ?? severityConfig.medium;
              const isExp = expanded === anomaly.id;

              return (
                <div
                  key={anomaly.id}
                  className={clsx(
                    "rounded-xl border overflow-hidden transition-all",
                    anomaly.is_read ? "opacity-60" : "",
                    isExp ? "shadow-sm" : ""
                  )}
                >
                  <button
                    onClick={() => {
                      setExpanded(isExp ? null : anomaly.id);
                      if (!anomaly.is_read) markRead(anomaly.id);
                    }}
                    className="w-full text-left px-4 py-3 bg-white hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <div className={clsx("w-2 h-2 rounded-full mt-1.5 shrink-0", cfg.dot)} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className={clsx("text-xs px-1.5 py-0.5 rounded border font-medium", cfg.color)}>
                            {cfg.label}
                          </span>
                          <span className="text-xs text-gray-400">
                            {metricLabels[anomaly.metric] ?? anomaly.metric}
                            {anomaly.direction === "up" ? (
                              <TrendingUp size={11} className="inline ml-1 text-red-400" />
                            ) : (
                              <TrendingDown size={11} className="inline ml-1 text-blue-400" />
                            )}
                          </span>
                          {!anomaly.is_read && (
                            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full shrink-0" />
                          )}
                        </div>
                        <p className="text-sm font-medium text-gray-900">{anomaly.product_title}</p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          Z-Score: {anomaly.z_score > 0 ? "+" : ""}{anomaly.z_score.toFixed(2)} ·{" "}
                          {new Date(anomaly.detected_at).toLocaleString("tr-TR", {
                            month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                          })}
                        </p>
                      </div>
                    </div>
                  </button>

                  {isExp && (
                    <div className="px-4 pb-4 bg-white border-t border-gray-50 space-y-3">
                      <div>
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1 mt-3">Olası Nedenler</p>
                        {anomaly.likely_causes.map((c, i) => (
                          <p key={i} className="text-xs text-gray-700 mb-0.5">• {c}</p>
                        ))}
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Önerilen Aksiyonlar</p>
                        {anomaly.recommended_actions.map((a, i) => (
                          <p key={i} className="text-xs text-gray-700 mb-0.5">→ {a}</p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        <div className="px-5 py-3 border-t border-gray-100">
          <p className="text-xs text-gray-400 text-center">Anomaliler Z-Score &gt; 2.5 eşiğinde tetiklenir</p>
        </div>
      </div>
    </div>
  );
}

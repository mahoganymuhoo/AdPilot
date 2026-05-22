/**
 * CSV export yardımcıları.
 * Tarayıcıda çalışır — Blob + <a> download trick.
 */

function toCsv(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return "";
  const headers = Object.keys(rows[0]);
  const escape = (v: unknown) => {
    const s = v === null || v === undefined ? "" : String(v);
    return s.includes(",") || s.includes('"') || s.includes("\n")
      ? `"${s.replace(/"/g, '""')}"`
      : s;
  };
  const lines = [
    headers.join(","),
    ...rows.map((row) => headers.map((h) => escape(row[h])).join(",")),
  ];
  return lines.join("\n");
}

function downloadCsv(csv: string, filename: string) {
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** Dashboard KPI metriklerini CSV olarak indir */
export function exportDashboardMetrics(chartData: Record<string, unknown>[], days: number) {
  const csv = toCsv(chartData);
  downloadCsv(csv, `adpilot_dashboard_son${days}gun_${today()}.csv`);
}

/** Strateji checkpoint'lerini CSV olarak indir */
export function exportStrategyCheckpoints(strategy: {
  name: string;
  checkpoints: Record<string, unknown>[];
}) {
  if (!strategy.checkpoints.length) return;

  const rows = strategy.checkpoints.map((cp: any) => ({
    tarih: cp.checked_at ?? "",
    durum: cp.status ?? "",
    ilerleme_pct: cp.progress_pct ?? "",
    roas: cp.current_metrics?.roas ?? "",
    acos: cp.current_metrics?.acos ?? "",
    gunluk_gelir: cp.current_metrics?.daily_revenue ?? "",
    roas_degisim: cp.metric_deltas?.roas_change ?? "",
    acos_degisim: cp.metric_deltas?.acos_change ?? "",
    gelir_degisim_pct: cp.metric_deltas?.revenue_change_pct ?? "",
    ai_yorumu: cp.checkpoint_insight ?? "",
    uyarilar: (cp.red_flags ?? []).join(" | "),
  }));

  const csv = toCsv(rows);
  const safeName = strategy.name.replace(/[^a-z0-9À-ɏ]/gi, "_").slice(0, 40);
  downloadCsv(csv, `strateji_${safeName}_${today()}.csv`);
}

/** Ürün metriklerini CSV olarak indir */
export function exportProductMetrics(products: Record<string, unknown>[]) {
  const rows = products.map((p: any) => ({
    urun_id: p.id ?? "",
    urun_adi: p.title ?? "",
    roas: p.roas ?? "",
    acos: p.acos ?? "",
    gunluk_gelir: p.daily_revenue ?? "",
    reklam_harcama: p.ad_spend ?? "",
    donusum: p.conversions ?? "",
    ctr_pct: p.ctr ?? "",
    ad_worthiness_skoru: p.ad_worthiness_score ?? "",
  }));
  const csv = toCsv(rows);
  downloadCsv(csv, `adpilot_urunler_${today()}.csv`);
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

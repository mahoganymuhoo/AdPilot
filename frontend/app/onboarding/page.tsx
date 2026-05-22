"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { TrendingUp, Upload, Link2, FileText, ChevronRight, ChevronLeft, CheckCircle, Loader, AlertCircle } from "lucide-react";
import clsx from "clsx";

// Adım tanımları
const STEPS = [
  { id: "source", label: "Veri Kaynağı" },
  { id: "costs", label: "Maliyetler & Hedefler" },
  { id: "ai", label: "AI Provider" },
  { id: "done", label: "Hazır" },
];

type DataSource = "api" | "csv" | "manual";
type AIProvider = "claude" | "openai";

interface OnboardingState {
  dataSource: DataSource | null;
  etsyApiKey: string;
  etsyShopId: string;
  cogsDefault: string;
  shippingCost: string;
  targetRoas: string;
  dailyBudget: string;
  aiProvider: AIProvider | null;
  apiKey: string;
}

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [state, setState] = useState<OnboardingState>({
    dataSource: null,
    etsyApiKey: "",
    etsyShopId: "",
    cogsDefault: "",
    shippingCost: "",
    targetRoas: "3.0",
    dailyBudget: "30",
    aiProvider: null,
    apiKey: "",
  });

  const set = (key: keyof OnboardingState, value: string) =>
    setState((prev) => ({ ...prev, [key]: value }));

  function canNext(): boolean {
    if (step === 0) return !!state.dataSource;
    if (step === 1) return !!state.cogsDefault && !!state.targetRoas && !!state.dailyBudget;
    if (step === 2) return !!state.aiProvider && !!state.apiKey;
    return true;
  }

  async function handleFinish() {
    setSaving(true);
    setError(null);
    try {
      // Seller kaydı oluştur / güncelle
      await fetch("/api/v1/onboarding/setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          data_source: state.dataSource,
          etsy_api_key: state.etsyApiKey || null,
          etsy_shop_id: state.etsyShopId || null,
          cogs_default: parseFloat(state.cogsDefault),
          shipping_cost: parseFloat(state.shippingCost || "0"),
          target_roas: parseFloat(state.targetRoas),
          daily_budget: parseFloat(state.dailyBudget),
          ai_provider: state.aiProvider,
          ai_api_key: state.apiKey,
        }),
      });
      // Tamamlandı işaretini kaydet
      localStorage.setItem("adpilot_onboarded", "1");
      setStep(3);
    } catch (e: any) {
      setError("Kayıt sırasında hata oluştu. Lütfen tekrar dene.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      {/* Logo */}
      <div className="flex items-center gap-2 mb-8">
        <TrendingUp className="text-green-500" size={28} />
        <span className="text-2xl font-bold text-gray-900">AdPilot</span>
      </div>

      {/* Adım göstergesi */}
      <div className="flex items-center gap-2 mb-8">
        {STEPS.map((s, i) => (
          <div key={s.id} className="flex items-center gap-2">
            <div className={clsx(
              "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors",
              i < step ? "bg-green-500 text-white" :
              i === step ? "bg-gray-900 text-white" :
              "bg-gray-200 text-gray-400"
            )}>
              {i < step ? <CheckCircle size={14} /> : i + 1}
            </div>
            <span className={clsx(
              "text-xs hidden sm:inline",
              i === step ? "text-gray-900 font-semibold" : "text-gray-400"
            )}>
              {s.label}
            </span>
            {i < STEPS.length - 1 && (
              <div className={clsx("w-8 h-0.5 mx-1", i < step ? "bg-green-400" : "bg-gray-200")} />
            )}
          </div>
        ))}
      </div>

      {/* Kart */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 w-full max-w-lg p-8">

        {/* Adım 0: Veri Kaynağı */}
        {step === 0 && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-1">Verilerin nereden geliyor?</h2>
            <p className="text-sm text-gray-500 mb-6">API bağlantın yoksa CSV veya manuel giriş de çalışır.</p>
            <div className="space-y-3">
              {[
                {
                  id: "api" as DataSource,
                  icon: <Link2 size={20} className="text-green-600" />,
                  title: "Etsy API",
                  desc: "Otomatik senkronizasyon. 15 dakikada bir güncellenir.",
                  badge: "Önerilen",
                  badgeColor: "bg-green-100 text-green-700",
                },
                {
                  id: "csv" as DataSource,
                  icon: <Upload size={20} className="text-blue-600" />,
                  title: "CSV Yükle",
                  desc: "Etsy Dashboard → Stats → CSV export. Hızlı başlangıç.",
                  badge: null,
                  badgeColor: "",
                },
                {
                  id: "manual" as DataSource,
                  icon: <FileText size={20} className="text-purple-600" />,
                  title: "Manuel Giriş",
                  desc: "Verileri elle gir. API veya CSV olmadan da çalışır.",
                  badge: null,
                  badgeColor: "",
                },
              ].map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => set("dataSource", opt.id)}
                  className={clsx(
                    "w-full text-left px-5 py-4 rounded-xl border transition-all flex items-start gap-4",
                    state.dataSource === opt.id
                      ? "border-green-400 bg-green-50 ring-1 ring-green-300"
                      : "border-gray-200 hover:border-gray-300"
                  )}
                >
                  <div className="mt-0.5">{opt.icon}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-gray-900">{opt.title}</p>
                      {opt.badge && (
                        <span className={clsx("text-xs px-2 py-0.5 rounded-full font-medium", opt.badgeColor)}>
                          {opt.badge}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">{opt.desc}</p>
                  </div>
                </button>
              ))}
            </div>

            {/* API seçildiyse ek alanlar */}
            {state.dataSource === "api" && (
              <div className="mt-5 space-y-3">
                <div>
                  <label className="text-xs font-semibold text-gray-600 mb-1 block">Etsy API Key</label>
                  <input
                    type="password"
                    value={state.etsyApiKey}
                    onChange={(e) => set("etsyApiKey", e.target.value)}
                    placeholder="etsyv3_uauth_..."
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-300"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-600 mb-1 block">Shop ID</label>
                  <input
                    type="text"
                    value={state.etsyShopId}
                    onChange={(e) => set("etsyShopId", e.target.value)}
                    placeholder="12345678"
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-300"
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Adım 1: Maliyetler & Hedefler */}
        {step === 1 && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-1">Maliyetler & Hedefler</h2>
            <p className="text-sm text-gray-500 mb-6">Break-even ACOS ve karlılık hesabı için gerekli.</p>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-gray-600 mb-1 block">
                    Ortalama COGS ($)
                    <span className="text-gray-400 font-normal ml-1">üretim maliyeti</span>
                  </label>
                  <input
                    type="number"
                    value={state.cogsDefault}
                    onChange={(e) => set("cogsDefault", e.target.value)}
                    placeholder="8.50"
                    min="0"
                    step="0.5"
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-300"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-600 mb-1 block">
                    Kargo Maliyeti ($)
                    <span className="text-gray-400 font-normal ml-1">opsiyonel</span>
                  </label>
                  <input
                    type="number"
                    value={state.shippingCost}
                    onChange={(e) => set("shippingCost", e.target.value)}
                    placeholder="3.50"
                    min="0"
                    step="0.5"
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-300"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-gray-600 mb-1 block">Hedef ROAS</label>
                  <input
                    type="number"
                    value={state.targetRoas}
                    onChange={(e) => set("targetRoas", e.target.value)}
                    placeholder="3.0"
                    min="1"
                    step="0.1"
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-300"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-gray-600 mb-1 block">Günlük Bütçe ($)</label>
                  <input
                    type="number"
                    value={state.dailyBudget}
                    onChange={(e) => set("dailyBudget", e.target.value)}
                    placeholder="30"
                    min="1"
                    step="1"
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-300"
                  />
                </div>
              </div>

              {/* Break-even preview */}
              {state.cogsDefault && (
                <BreakevenPreview
                  cogs={parseFloat(state.cogsDefault)}
                  shipping={parseFloat(state.shippingCost || "0")}
                  targetRoas={parseFloat(state.targetRoas || "3")}
                />
              )}
            </div>
          </div>
        )}

        {/* Adım 2: AI Provider */}
        {step === 2 && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-1">AI Provider Seç</h2>
            <p className="text-sm text-gray-500 mb-6">API key'ini gir. İkisini de girebilirsin, istediğinde değiştirebilirsin.</p>

            <div className="space-y-3 mb-5">
              {[
                {
                  id: "claude" as AIProvider,
                  name: "Claude (Anthropic)",
                  desc: "Derin finansal analiz, extended thinking, prompt caching. Türkçe çok iyi.",
                  placeholder: "sk-ant-...",
                  badge: "Önerilen",
                  badgeColor: "bg-purple-100 text-purple-700",
                },
                {
                  id: "openai" as AIProvider,
                  name: "OpenAI (GPT-4o)",
                  desc: "JSON mode, hızlı yanıt, geniş ekosistem.",
                  placeholder: "sk-...",
                  badge: null,
                  badgeColor: "",
                },
              ].map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => setState((prev) => ({ ...prev, aiProvider: opt.id, apiKey: "" }))}
                  className={clsx(
                    "w-full text-left px-5 py-4 rounded-xl border transition-all",
                    state.aiProvider === opt.id
                      ? "border-green-400 bg-green-50 ring-1 ring-green-300"
                      : "border-gray-200 hover:border-gray-300"
                  )}
                >
                  <div className="flex items-center gap-2 mb-0.5">
                    <p className="text-sm font-semibold text-gray-900">{opt.name}</p>
                    {opt.badge && (
                      <span className={clsx("text-xs px-2 py-0.5 rounded-full font-medium", opt.badgeColor)}>
                        {opt.badge}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500">{opt.desc}</p>
                </button>
              ))}
            </div>

            {state.aiProvider && (
              <div>
                <label className="text-xs font-semibold text-gray-600 mb-1 block">
                  {state.aiProvider === "claude" ? "Anthropic" : "OpenAI"} API Key
                </label>
                <input
                  type="password"
                  value={state.apiKey}
                  onChange={(e) => set("apiKey", e.target.value)}
                  placeholder={state.aiProvider === "claude" ? "sk-ant-api03-..." : "sk-proj-..."}
                  className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-300"
                />
                <p className="text-xs text-gray-400 mt-1">Şifrelenmiş olarak saklanır. Hiçbir zaman paylaşılmaz.</p>
              </div>
            )}

            {error && (
              <div className="flex items-center gap-2 mt-4 bg-red-50 border border-red-100 rounded-xl px-4 py-3 text-sm text-red-700">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}
          </div>
        )}

        {/* Adım 3: Tamamlandı */}
        {step === 3 && (
          <div className="text-center py-4">
            <CheckCircle size={52} className="text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 mb-2">Hazırsın! 🎉</h2>
            <p className="text-sm text-gray-500 mb-6 leading-relaxed">
              Ayarların kaydedildi. Dashboard'a geç, verilerini yükle ve ilk AI analizini çalıştır.
            </p>
            <div className="space-y-2">
              {state.dataSource === "csv" && (
                <button
                  onClick={() => router.push("/upload")}
                  className="w-full bg-blue-600 text-white text-sm font-semibold py-3 rounded-xl hover:bg-blue-700 transition-colors"
                >
                  CSV Yükle →
                </button>
              )}
              {state.dataSource === "manual" && (
                <button
                  onClick={() => router.push("/upload")}
                  className="w-full bg-purple-600 text-white text-sm font-semibold py-3 rounded-xl hover:bg-purple-700 transition-colors"
                >
                  Manuel Veri Gir →
                </button>
              )}
              <button
                onClick={() => router.push("/dashboard")}
                className="w-full bg-gray-900 text-white text-sm font-semibold py-3 rounded-xl hover:bg-gray-700 transition-colors"
              >
                Dashboard'a Git →
              </button>
            </div>
          </div>
        )}

        {/* Navigasyon butonları */}
        {step < 3 && (
          <div className="flex justify-between mt-8">
            <button
              onClick={() => step > 0 ? setStep(step - 1) : router.push("/dashboard")}
              className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-100"
            >
              <ChevronLeft size={16} />
              {step === 0 ? "Atla" : "Geri"}
            </button>

            <button
              onClick={() => {
                if (step === 2) handleFinish();
                else setStep(step + 1);
              }}
              disabled={!canNext() || saving}
              className="flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? (
                <><Loader size={14} className="animate-spin" /> Kaydediliyor...</>
              ) : step === 2 ? (
                <>Tamamla <CheckCircle size={14} /></>
              ) : (
                <>Devam <ChevronRight size={16} /></>
              )}
            </button>
          </div>
        )}
      </div>

      <p className="text-xs text-gray-400 mt-6">
        Daha sonra <span className="font-semibold">Ayarlar</span> sayfasından değiştirebilirsin.
      </p>
    </div>
  );
}

function BreakevenPreview({ cogs, shipping, targetRoas }: { cogs: number; shipping: number; targetRoas: number }) {
  const ETSY_FEE_PCT = 0.065;
  const LISTING_FEE = 0.20;

  // Örnek fiyat tahmini: COGS × 4 (rough)
  const estimatedPrice = cogs * 4;
  const netAfterFees = estimatedPrice * (1 - ETSY_FEE_PCT) - LISTING_FEE - shipping - cogs;
  const profitMarginPct = (netAfterFees / estimatedPrice) * 100;
  const breakEvenAcos = Math.max(0, profitMarginPct);

  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 mt-1">
      <p className="text-xs font-semibold text-blue-800 mb-2">Tahmini Break-even ACOS (örnek fiyat: ${estimatedPrice.toFixed(0)})</p>
      <div className="flex gap-4 text-xs text-blue-700">
        <span>Net kâr: <strong>${netAfterFees.toFixed(2)}</strong></span>
        <span>Kâr marjı: <strong>%{profitMarginPct.toFixed(1)}</strong></span>
        <span>Break-even ACOS: <strong>%{breakEvenAcos.toFixed(1)}</strong></span>
      </div>
      <p className="text-xs text-blue-500 mt-1">ACOS bu değerin altında kalırsa reklam karlıdır.</p>
    </div>
  );
}

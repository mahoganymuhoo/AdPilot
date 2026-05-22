"use client";
import { useState, useEffect } from "react";
import { X, Rocket, ChevronDown, AlertCircle, CheckCircle, Loader } from "lucide-react";
import clsx from "clsx";
import { useRouter } from "next/navigation";

interface Product {
  id: number;
  title: string;
  score: number;
  recommendation: string;
  roas: number;
  suggested_budget: number;
  scoreDetails: Record<string, number>;
}

interface Props {
  product: Product;
  onClose: () => void;
}

const OPERATION_LABELS: Record<string, string> = {
  increase_budget: "Bütçe Artışı",
  test_budget: "Küçük Bütçe Testi",
  optimize_listing: "Listing + Reklam Kombine",
  reduce_budget: "Bütçe Düşüşü",
  pause_ads: "Durdur ve İzle",
};

const TEMPLATES = [
  {
    id: "increase_budget",
    label: "Bütçe Artışı",
    description: "Mevcut bütçeyi %20-30 artır, 14 gün ROAS'ı izle.",
    icon: "📈",
    defaultAction: (p: Product) =>
      `"${p.title}" ürünü için günlük reklam bütçemi $${p.suggested_budget}'dan $${(p.suggested_budget * 1.25).toFixed(1)}'a çıkardım.`,
  },
  {
    id: "test_budget",
    label: "Küçük Bütçe Testi",
    description: "$3-5/gün test bütçesiyle potansiyeli ölç.",
    icon: "🧪",
    defaultAction: (p: Product) =>
      `"${p.title}" için $${Math.min(p.suggested_budget, 5).toFixed(1)}/gün test bütçesiyle reklamı başlattım.`,
  },
  {
    id: "optimize_listing",
    label: "Listing + Reklam",
    description: "Önce listing'i düzelt, sonra reklam ver.",
    icon: "🔧",
    defaultAction: (p: Product) =>
      `"${p.title}" ürününün fotoğrafını ve başlığını güncelledim, ardından $${p.suggested_budget}/gün reklam başlattım.`,
  },
  {
    id: "reduce_budget",
    label: "Bütçe Düşüşü",
    description: "Zararlı ürünün bütçesini azalt, izle.",
    icon: "📉",
    defaultAction: (p: Product) =>
      `"${p.title}" ürünü için günlük bütçeyi $${(p.suggested_budget * 0.5).toFixed(1)}'a düşürdüm.`,
  },
];

export default function LaunchStrategyModal({ product, onClose }: Props) {
  const router = useRouter();
  const [step, setStep] = useState<"template" | "confirm" | "loading" | "success">("template");
  const [selectedTemplate, setSelectedTemplate] = useState<string>("increase_budget");
  const [actionText, setActionText] = useState("");
  const [aiProvider, setAiProvider] = useState<"claude" | "openai">("claude");
  const [error, setError] = useState<string | null>(null);
  const [launchedId, setLaunchedId] = useState<number | null>(null);

  const template = TEMPLATES.find((t) => t.id === selectedTemplate)!;

  useEffect(() => {
    setActionText(template.defaultAction(product));
  }, [selectedTemplate]);

  async function handleLaunch() {
    if (!actionText.trim()) return;
    setStep("loading");
    setError(null);

    try {
      const recommendation = {
        score: product.score,
        recommendation: product.recommendation,
        suggested_budget: product.suggested_budget,
        roas: product.roas,
        operation_type: selectedTemplate,
      };

      const initial_metrics = {
        roas: product.roas,
        ad_worthiness_score: product.score,
        ...product.scoreDetails,
      };

      const seller_context = {
        seller_id: 1,
        target_roas: 3.0,
        daily_budget: 30.0,
      };

      const res = await fetch("/api/v1/strategies/launch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          seller_id: 1,
          product_id: product.id,
          recommendation,
          initial_metrics,
          seller_context,
          action_confirmed: actionText,
          ai_provider: aiProvider,
        }),
      });

      if (!res.ok) throw new Error(`Sunucu hatası: ${res.status}`);
      const data = await res.json();
      setLaunchedId(data.strategy_id);
      setStep("success");
    } catch (e: any) {
      setError(e.message || "Bir hata oluştu.");
      setStep("confirm");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Rocket size={18} className="text-green-600" />
            <h2 className="text-base font-bold text-gray-900">Strateji Başlat</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={18} />
          </button>
        </div>

        <div className="px-6 py-4">
          {/* Ürün özeti */}
          <div className="bg-gray-50 rounded-xl px-4 py-3 mb-5 border border-gray-100">
            <p className="text-xs text-gray-500 mb-0.5">Ürün</p>
            <p className="text-sm font-semibold text-gray-900">{product.title}</p>
            <div className="flex gap-3 mt-1 text-xs text-gray-500">
              <span>Skor: <strong className="text-gray-700">{product.score}/100</strong></span>
              <span>ROAS: <strong className="text-gray-700">{product.roas}x</strong></span>
              <span>Önerilen bütçe: <strong className="text-green-600">${product.suggested_budget}/gün</strong></span>
            </div>
          </div>

          {step === "template" && (
            <>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Strateji Tipi Seç</p>
              <div className="space-y-2 mb-5">
                {TEMPLATES.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setSelectedTemplate(t.id)}
                    className={clsx(
                      "w-full text-left px-4 py-3 rounded-xl border transition-all",
                      selectedTemplate === t.id
                        ? "border-green-400 bg-green-50 ring-1 ring-green-300"
                        : "border-gray-200 hover:border-gray-300 bg-white"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{t.icon}</span>
                      <div>
                        <p className="text-sm font-semibold text-gray-900">{t.label}</p>
                        <p className="text-xs text-gray-500">{t.description}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              <div className="flex justify-end">
                <button
                  onClick={() => setStep("confirm")}
                  className="bg-gray-900 text-white text-sm font-medium px-5 py-2.5 rounded-xl hover:bg-gray-700 transition-colors"
                >
                  Devam →
                </button>
              </div>
            </>
          )}

          {step === "confirm" && (
            <>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Ne yaptın? (AI bunu okuyacak)</p>
              <textarea
                value={actionText}
                onChange={(e) => setActionText(e.target.value)}
                rows={3}
                className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-800 resize-none focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-300 mb-4"
                placeholder="Örnek: Bütçemi $12'dan $15'a çıkardım ve hafta sonu kampanyası seçtim."
              />

              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">AI Provider</p>
              <div className="flex gap-2 mb-5">
                {(["claude", "openai"] as const).map((p) => (
                  <button
                    key={p}
                    onClick={() => setAiProvider(p)}
                    className={clsx(
                      "flex-1 py-2 rounded-xl border text-sm font-medium transition-colors",
                      aiProvider === p
                        ? "border-green-400 bg-green-50 text-green-700"
                        : "border-gray-200 text-gray-600 hover:border-gray-300"
                    )}
                  >
                    {p === "claude" ? "Claude" : "OpenAI"}
                  </button>
                ))}
              </div>

              {error && (
                <div className="flex items-center gap-2 bg-red-50 border border-red-100 rounded-xl px-4 py-3 mb-4 text-sm text-red-700">
                  <AlertCircle size={16} />
                  <span>{error}</span>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => setStep("template")}
                  className="flex-1 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-600 hover:bg-gray-50"
                >
                  ← Geri
                </button>
                <button
                  onClick={handleLaunch}
                  disabled={!actionText.trim()}
                  className="flex-1 bg-green-600 text-white text-sm font-semibold py-2.5 rounded-xl hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  AI ile Strateji Başlat
                </button>
              </div>
            </>
          )}

          {step === "loading" && (
            <div className="flex flex-col items-center py-8 gap-4">
              <Loader size={32} className="text-green-500 animate-spin" />
              <p className="text-sm text-gray-600 text-center">
                AI stratejini analiz ediyor...<br />
                <span className="text-xs text-gray-400">Hedef, takvim ve başarı kriterleri belirleniyor</span>
              </p>
            </div>
          )}

          {step === "success" && (
            <div className="flex flex-col items-center py-6 gap-4">
              <CheckCircle size={40} className="text-green-500" />
              <div className="text-center">
                <p className="text-base font-bold text-gray-900 mb-1">Strateji Başlatıldı!</p>
                <p className="text-sm text-gray-500">
                  AI hedefleri belirledi ve takip takvimi oluşturdu.
                </p>
              </div>
              <button
                onClick={() => router.push(`/strategies`)}
                className="bg-gray-900 text-white text-sm font-medium px-6 py-2.5 rounded-xl hover:bg-gray-700 transition-colors"
              >
                Strateji Takibine Git →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

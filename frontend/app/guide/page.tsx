"use client";
import { useState } from "react";
import InfoModal from "@/components/ui/InfoModal";
import { EXPLAINERS } from "@/lib/explainers";
import clsx from "clsx";

const SECTIONS = [
  {
    id: "metrics",
    title: "📊 Metrikler",
    subtitle: "Her sayının ne anlama geldiği",
    items: [
      { id: "roas", color: "border-l-green-400" },
      { id: "acos", color: "border-l-blue-400" },
      { id: "tacos", color: "border-l-purple-400" },
      { id: "breakeven_acos", color: "border-l-orange-400" },
      { id: "net_profit", color: "border-l-teal-400" },
      { id: "ctr", color: "border-l-pink-400" },
    ],
  },
  {
    id: "algorithms",
    title: "🧮 Algoritmalar",
    subtitle: "Sistemin nasıl çalıştığı",
    items: [
      { id: "ema_trend", color: "border-l-green-400" },
      { id: "zscore_anomaly", color: "border-l-red-400" },
      { id: "ad_worthiness", color: "border-l-blue-400" },
      { id: "budget_optimizer", color: "border-l-purple-400" },
      { id: "view_analysis", color: "border-l-yellow-400" },
      { id: "attribution", color: "border-l-gray-400" },
    ],
  },
];

export default function GuidePage() {
  const [activeSection, setActiveSection] = useState("metrics");
  const [expanded, setExpanded] = useState<string | null>(null);

  const section = SECTIONS.find((s) => s.id === activeSection)!;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Nasıl Çalışır?</h1>
        <p className="text-sm text-gray-500 mt-1">
          AdPilot'un kullandığı tüm metrikler ve algoritmalar — sade bir dille anlatım.
        </p>
      </div>

      {/* Sekme */}
      <div className="flex gap-2 mb-6">
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            onClick={() => { setActiveSection(s.id); setExpanded(null); }}
            className={clsx(
              "px-4 py-2 text-sm font-medium rounded-lg border transition-colors",
              activeSection === s.id
                ? "bg-gray-900 text-white border-gray-900"
                : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"
            )}
          >
            {s.title}
          </button>
        ))}
      </div>

      <p className="text-xs text-gray-400 mb-4">{section.subtitle} — bir karta tıkla, detayları gör</p>

      {/* Kartlar */}
      <div className="space-y-3">
        {section.items.map(({ id, color }) => {
          const exp = EXPLAINERS[id];
          if (!exp) return null;
          const isExpanded = expanded === id;

          return (
            <div
              key={id}
              className={clsx(
                "bg-white rounded-xl border border-gray-200 border-l-4 shadow-sm overflow-hidden transition-all",
                color
              )}
            >
              {/* Özet satırı — tıklanabilir */}
              <button
                onClick={() => setExpanded(isExpanded ? null : id)}
                className="w-full text-left px-5 py-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">{exp.emoji}</span>
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{exp.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{exp.oneLiner}</p>
                  </div>
                </div>
                <span className="text-gray-300 text-xs">{isExpanded ? "▲ Kapat" : "▼ Detay"}</span>
              </button>

              {/* Detay — genişletilince açılır */}
              {isExpanded && (
                <div className="px-5 pb-5 border-t border-gray-100 pt-4 space-y-4">
                  {/* Ne demek */}
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Ne Demek?</p>
                    <p className="text-sm text-gray-700 leading-relaxed">{exp.whatIs}</p>
                  </div>

                  {/* Formül */}
                  {exp.formula && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Formül</p>
                      <div className="bg-gray-50 rounded-lg px-4 py-2.5 font-mono text-sm text-gray-800 border border-gray-200">
                        {exp.formula}
                      </div>
                    </div>
                  )}

                  {/* Nasıl hesaplanıyor */}
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Nasıl Hesaplanıyor?</p>
                    <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{exp.howItWorks}</p>
                  </div>

                  {/* İyi / Kötü */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-green-50 border border-green-100 rounded-xl p-3">
                      <p className="text-xs font-semibold text-green-700 mb-1">✓ İyi Değer</p>
                      <p className="text-xs text-green-800 leading-relaxed">{exp.goodValue}</p>
                    </div>
                    <div className="bg-red-50 border border-red-100 rounded-xl p-3">
                      <p className="text-xs font-semibold text-red-700 mb-1">✗ Kötü Değer</p>
                      <p className="text-xs text-red-800 leading-relaxed">{exp.badValue}</p>
                    </div>
                  </div>

                  {/* Örnek */}
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Gerçek Hayat Örneği</p>
                    <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3">
                      <p className="text-sm text-blue-900 leading-relaxed">{exp.example}</p>
                    </div>
                  </div>

                  {/* Ne yapmalıyım */}
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Ne Yapmalıyım?</p>
                    <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{exp.whatToDo}</p>
                  </div>

                  {/* İpucu */}
                  {exp.tip && (
                    <div className="flex gap-3 bg-amber-50 border border-amber-100 rounded-xl px-4 py-3">
                      <span className="text-base shrink-0">💡</span>
                      <p className="text-sm text-amber-800 leading-relaxed">{exp.tip}</p>
                    </div>
                  )}

                  {/* Tam modal butonu */}
                  <div className="pt-1">
                    <InfoModal
                      explainer={exp}
                      trigger={
                        <span className="text-xs text-blue-500 hover:text-blue-700 hover:underline cursor-pointer">
                          Tam ekranda görüntüle →
                        </span>
                      }
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Alt bilgi */}
      <div className="mt-8 p-5 bg-gray-50 rounded-xl border border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Hızlı Başlangıç</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { step: "1", title: "Veri Gir", desc: "Etsy CSV yükle veya manuel veri gir. API bağlantısı olmadan da çalışır." },
            { step: "2", title: "Kontrol Et", desc: "Dashboard'da ROAS ve ACOS'una bak. Break-even ACOS kontrolünü incele." },
            { step: "3", title: "Harekete Geç", desc: "AI Öneriler'den hangi ürüne bütçe vereceğini öğren." },
          ].map((s) => (
            <div key={s.step} className="flex gap-3">
              <div className="w-7 h-7 bg-gray-900 text-white text-xs font-bold rounded-full flex items-center justify-center shrink-0">
                {s.step}
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900">{s.title}</p>
                <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

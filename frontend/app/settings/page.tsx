"use client";
import { useState } from "react";
import { CheckCircle, Key, Target, DollarSign } from "lucide-react";

export default function SettingsPage() {
  const [aiProvider, setAiProvider] = useState<"claude" | "openai">("claude");
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Ayarlar</h1>
        <p className="text-sm text-gray-500 mt-1">Hesap, AI provider ve hedef değerleri yapılandır.</p>
      </div>

      <div className="space-y-4">
        {/* AI Provider */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Key size={16} className="text-purple-500" />
            <h3 className="text-sm font-semibold text-gray-700">AI Sağlayıcı</h3>
          </div>
          <p className="text-xs text-gray-400 mb-4">
            Hangi AI API'yi kullanmak istediğini seç. API key'ini gir — ikisini de girersen her analizde seçebilirsin.
          </p>

          <div className="grid grid-cols-2 gap-3 mb-4">
            {[
              { id: "claude", label: "Claude (Anthropic)", desc: "Extended thinking, prompt cache" },
              { id: "openai", label: "OpenAI (GPT-4o)", desc: "Geniş kullanıcı tabanı, JSON mode" },
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => setAiProvider(p.id as "claude" | "openai")}
                className={`text-left p-3 rounded-lg border-2 transition-colors ${
                  aiProvider === p.id
                    ? "border-green-400 bg-green-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <p className="text-sm font-medium text-gray-900">{p.label}</p>
                <p className="text-xs text-gray-400 mt-0.5">{p.desc}</p>
              </button>
            ))}
          </div>

          {aiProvider === "claude" && (
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Anthropic API Key</label>
              <input
                type="password"
                placeholder="sk-ant-..."
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-green-400"
              />
            </div>
          )}
          {aiProvider === "openai" && (
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">OpenAI API Key</label>
              <input
                type="password"
                placeholder="sk-..."
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-green-400"
              />
            </div>
          )}
        </div>

        {/* Hedef Değerler */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Target size={16} className="text-blue-500" />
            <h3 className="text-sm font-semibold text-gray-700">Hedef Değerler</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: "Hedef ROAS", key: "target_roas", default: "3.0", hint: "3.0 ve üzeri iyi" },
              { label: "Hedef ACOS (%)", key: "target_acos", default: "30", hint: "Kâr marjının altında olmalı" },
              { label: "Varsayılan COGS (%)", key: "cogs_pct", default: "40", hint: "Gelirin yüzdesi olarak maliyet" },
              { label: "Günlük Bütçe ($)", key: "daily_budget", default: "10", hint: "Toplam günlük reklam bütçesi" },
            ].map((f) => (
              <div key={f.key}>
                <label className="block text-xs font-medium text-gray-600 mb-1">{f.label}</label>
                <input
                  type="number"
                  step="0.1"
                  defaultValue={f.default}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-green-400"
                />
                <p className="text-xs text-gray-400 mt-0.5">{f.hint}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Etsy Bağlantısı */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <DollarSign size={16} className="text-orange-500" />
            <h3 className="text-sm font-semibold text-gray-700">Platform Bağlantısı</h3>
          </div>
          <p className="text-xs text-gray-400 mb-4">
            Etsy API bağlantısı için OAuth akışı başlatılır. API key'in yoksa Veri Yükle sayfasından CSV ile devam edebilirsin.
          </p>
          <button className="px-4 py-2 bg-orange-500 text-white text-sm font-medium rounded-lg hover:bg-orange-600 transition-colors">
            Etsy ile Bağlan
          </button>
          <span className="ml-3 text-xs text-gray-400">veya</span>
          <a href="/upload" className="ml-2 text-xs text-blue-600 hover:underline">CSV yükle</a>
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-6 py-2.5 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors"
          >
            {saved && <CheckCircle size={16} />}
            {saved ? "Kaydedildi!" : "Kaydet"}
          </button>
        </div>
      </div>
    </div>
  );
}

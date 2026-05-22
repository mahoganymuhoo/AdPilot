"use client";
import { useState, useRef } from "react";
import { Upload, FileText, CheckCircle, AlertCircle, Plus } from "lucide-react";
import clsx from "clsx";

type Tab = "csv" | "manual";

const MANUAL_FIELDS = [
  { key: "date", label: "Tarih", placeholder: "2024-01-15", type: "date" },
  { key: "listing_id", label: "Listing ID", placeholder: "12345678", type: "text" },
  { key: "title", label: "Ürün Adı", placeholder: "El Yapımı Kupa", type: "text" },
  { key: "impressions", label: "Gösterim", placeholder: "500", type: "number" },
  { key: "clicks", label: "Tıklama", placeholder: "25", type: "number" },
  { key: "ad_spend", label: "Reklam Harcaması ($)", placeholder: "5.00", type: "number" },
  { key: "revenue", label: "Gelir ($)", placeholder: "22.50", type: "number" },
  { key: "conversions", label: "Satış Adedi", placeholder: "2", type: "number" },
  { key: "views", label: "Organik Görüntülenme", placeholder: "120", type: "number" },
];

export default function UploadPage() {
  const [tab, setTab] = useState<Tab>("csv");
  const [dragOver, setDragOver] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [statusMsg, setStatusMsg] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const [manualRows, setManualRows] = useState([Object.fromEntries(MANUAL_FIELDS.map((f) => [f.key, ""]))]);

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadCsv(file);
  };

  const uploadCsv = async (file: File) => {
    setUploadStatus("uploading");
    setStatusMsg("Yükleniyor...");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("/api/backend/metrics/upload-csv", { method: "POST", body: form });
      const data = await res.json();
      if (res.ok) {
        setUploadStatus("success");
        setStatusMsg(data.message || "Başarıyla yüklendi.");
      } else {
        setUploadStatus("error");
        setStatusMsg(data.detail || "Yükleme hatası.");
      }
    } catch {
      setUploadStatus("error");
      setStatusMsg("Sunucuya ulaşılamıyor. Backend çalışıyor mu?");
    }
  };

  const handleManualSubmit = async () => {
    setUploadStatus("uploading");
    try {
      const res = await fetch("/api/backend/metrics/manual", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(manualRows),
      });
      const data = await res.json();
      if (res.ok) {
        setUploadStatus("success");
        setStatusMsg(data.message);
      } else {
        setUploadStatus("error");
        setStatusMsg(data.detail || "Kayıt hatası.");
      }
    } catch {
      setUploadStatus("error");
      setStatusMsg("Sunucuya ulaşılamıyor.");
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Veri Yükle</h1>
        <p className="text-sm text-gray-500 mt-1">
          Etsy CSV export'u yükle veya manuel veri gir. API bağlantısı olmadan da çalışır.
        </p>
      </div>

      {/* Sekme */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
        {[{ key: "csv", label: "CSV Yükle" }, { key: "manual", label: "Manuel Gir" }].map((t) => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key as Tab); setUploadStatus("idle"); }}
            className={clsx(
              "px-4 py-1.5 rounded-md text-sm font-medium transition-colors",
              tab === t.key ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* CSV Tab */}
      {tab === "csv" && (
        <div className="space-y-4">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleFileDrop}
            onClick={() => fileRef.current?.click()}
            className={clsx(
              "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors",
              dragOver ? "border-green-400 bg-green-50" : "border-gray-300 bg-white hover:border-gray-400"
            )}
          >
            <Upload className="mx-auto mb-3 text-gray-400" size={32} />
            <p className="text-sm font-medium text-gray-700">CSV dosyasını buraya sürükle veya tıkla</p>
            <p className="text-xs text-gray-400 mt-1">Etsy Dashboard → Stats → Export CSV formatı</p>
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && uploadCsv(e.target.files[0])}
            />
          </div>

          <div className="bg-blue-50 rounded-lg p-4 text-xs text-blue-700">
            <p className="font-semibold mb-1">Etsy CSV nasıl indirilir?</p>
            <ol className="list-decimal list-inside space-y-0.5">
              <li>Etsy Shop Manager → Stats</li>
              <li>Tarih aralığı seç</li>
              <li>Download CSV butonuna tıkla</li>
              <li>İndirilen dosyayı buraya yükle</li>
            </ol>
          </div>
        </div>
      )}

      {/* Manuel Tab */}
      {tab === "manual" && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">
          {manualRows.map((row, rowIdx) => (
            <div key={rowIdx} className="grid grid-cols-2 gap-3 pb-4 border-b border-gray-100 last:border-0">
              {MANUAL_FIELDS.map((f) => (
                <div key={f.key}>
                  <label className="block text-xs font-medium text-gray-600 mb-1">{f.label}</label>
                  <input
                    type={f.type}
                    placeholder={f.placeholder}
                    value={row[f.key]}
                    onChange={(e) => {
                      const updated = [...manualRows];
                      updated[rowIdx] = { ...updated[rowIdx], [f.key]: e.target.value };
                      setManualRows(updated);
                    }}
                    className="w-full px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-green-400"
                  />
                </div>
              ))}
            </div>
          ))}

          <div className="flex gap-3">
            <button
              onClick={() => setManualRows([...manualRows, Object.fromEntries(MANUAL_FIELDS.map((f) => [f.key, ""]))])}
              className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700"
            >
              <Plus size={14} /> Satır Ekle
            </button>
            <button
              onClick={handleManualSubmit}
              className="ml-auto px-5 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors"
            >
              Kaydet
            </button>
          </div>
        </div>
      )}

      {/* Durum mesajı */}
      {uploadStatus !== "idle" && (
        <div className={clsx(
          "mt-4 flex items-center gap-2 px-4 py-3 rounded-lg text-sm",
          uploadStatus === "success" ? "bg-green-50 text-green-700" :
          uploadStatus === "error" ? "bg-red-50 text-red-700" :
          "bg-gray-50 text-gray-600"
        )}>
          {uploadStatus === "success" && <CheckCircle size={16} />}
          {uploadStatus === "error" && <AlertCircle size={16} />}
          {uploadStatus === "uploading" && <FileText size={16} />}
          {statusMsg}
        </div>
      )}
    </div>
  );
}

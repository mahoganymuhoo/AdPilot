"use client";
import { useState, useEffect } from "react";
import { X, HelpCircle, BookOpen, Calculator, ThumbsUp, ThumbsDown, Lightbulb, ArrowRight } from "lucide-react";
import type { Explainer } from "@/lib/explainers";

interface InfoModalProps {
  explainer: Explainer;
  trigger?: React.ReactNode;
}

export default function InfoModal({ explainer, trigger }: InfoModalProps) {
  const [open, setOpen] = useState(false);

  // ESC ile kapat
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    if (open) document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open]);

  // Body scroll kilitle
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  return (
    <>
      {/* Tetikleyici */}
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center justify-center"
        title={`${explainer.title} hakkında bilgi al`}
      >
        {trigger ?? (
          <HelpCircle
            size={14}
            className="text-gray-300 hover:text-gray-500 transition-colors cursor-pointer"
          />
        )}
      </button>

      {/* Overlay */}
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
          onClick={(e) => { if (e.target === e.currentTarget) setOpen(false); }}
        >
          {/* Modal */}
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            {/* Başlık */}
            <div className="sticky top-0 bg-white rounded-t-2xl px-6 pt-5 pb-4 border-b border-gray-100 flex items-start justify-between">
              <div>
                <span className="text-2xl mr-2">{explainer.emoji}</span>
                <h2 className="text-lg font-bold text-gray-900 inline">{explainer.title}</h2>
                <p className="text-sm text-gray-500 mt-1">{explainer.oneLiner}</p>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="p-1 rounded-lg hover:bg-gray-100 transition-colors shrink-0 ml-4"
              >
                <X size={18} className="text-gray-400" />
              </button>
            </div>

            <div className="px-6 py-5 space-y-5">
              {/* Ne Demek? */}
              <Section icon={<BookOpen size={15} />} title="Ne Demek?">
                <p className="text-sm text-gray-700 leading-relaxed">{explainer.whatIs}</p>
              </Section>

              {/* Formül */}
              {explainer.formula && (
                <Section icon={<Calculator size={15} />} title="Formül">
                  <div className="bg-gray-50 rounded-lg px-4 py-3 font-mono text-sm text-gray-800 border border-gray-200">
                    {explainer.formula}
                  </div>
                </Section>
              )}

              {/* Nasıl Çalışıyor? */}
              <Section icon={<HelpCircle size={15} />} title="Nasıl Hesaplanıyor?">
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{explainer.howItWorks}</p>
              </Section>

              {/* İyi / Kötü Değer */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-green-50 border border-green-200 rounded-xl p-3">
                  <div className="flex items-center gap-1.5 mb-2">
                    <ThumbsUp size={13} className="text-green-600" />
                    <span className="text-xs font-semibold text-green-700">İyi Değer</span>
                  </div>
                  <p className="text-xs text-green-800 leading-relaxed">{explainer.goodValue}</p>
                </div>
                <div className="bg-red-50 border border-red-200 rounded-xl p-3">
                  <div className="flex items-center gap-1.5 mb-2">
                    <ThumbsDown size={13} className="text-red-600" />
                    <span className="text-xs font-semibold text-red-700">Kötü Değer</span>
                  </div>
                  <p className="text-xs text-red-800 leading-relaxed">{explainer.badValue}</p>
                </div>
              </div>

              {/* Gerçek Hayat Örneği */}
              <Section icon={<ArrowRight size={15} />} title="Gerçek Hayat Örneği">
                <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3">
                  <p className="text-sm text-blue-900 leading-relaxed">{explainer.example}</p>
                </div>
              </Section>

              {/* Ne Yapmalıyım? */}
              <Section icon={<ArrowRight size={15} />} title="Ne Yapmalıyım?">
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{explainer.whatToDo}</p>
              </Section>

              {/* İpucu */}
              {explainer.tip && (
                <div className="flex gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
                  <Lightbulb size={16} className="text-amber-500 shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-800 leading-relaxed">{explainer.tip}</p>
                </div>
              )}
            </div>

            <div className="px-6 pb-5">
              <button
                onClick={() => setOpen(false)}
                className="w-full py-2.5 bg-gray-900 text-white text-sm font-medium rounded-xl hover:bg-gray-700 transition-colors"
              >
                Anladım
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        <span className="text-gray-400">{icon}</span>
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{title}</h3>
      </div>
      {children}
    </div>
  );
}

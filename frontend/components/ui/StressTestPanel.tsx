"use client";
import { useState, useMemo } from "react";
import clsx from "clsx";

interface Props {
  price: number;
  cogs: number;
  shippingCost?: number;
  currentAcos: number;
}

const ETSY_FEE_PCT = 0.065;
const LISTING_FEE = 0.20;

function calcScenario(price: number, cogs: number, shipping: number) {
  const fees = price * ETSY_FEE_PCT + LISTING_FEE;
  const netProfit = price - cogs - shipping - fees;
  const margin = price > 0 ? netProfit / price : 0;
  const breakEvenAcos = Math.max(0, margin * 100);
  return { netProfit, breakEvenAcos, margin };
}

export default function StressTestPanel({ price, cogs, shippingCost = 0, currentAcos }: Props) {
  const [cogsChangePct, setCogsChangePct] = useState(0);

  const newCogs = cogs * (1 + cogsChangePct / 100);
  const base = useMemo(() => calcScenario(price, cogs, shippingCost), [price, cogs, shippingCost]);
  const current = useMemo(() => calcScenario(price, newCogs, shippingCost), [price, newCogs, shippingCost]);

  const isProfitable = currentAcos <= current.breakEvenAcos;
  const marginDelta = current.margin * 100 - base.margin * 100;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">Break-even Stress Test</h3>
          <p className="text-xs text-gray-400 mt-0.5">Maliyetin değişse reklam hala karlı mı?</p>
        </div>
        <span className={clsx(
          "text-xs font-semibold px-2.5 py-1 rounded-full border",
          isProfitable
            ? "bg-green-50 border-green-200 text-green-700"
            : "bg-red-50 border-red-200 text-red-700"
        )}>
          {isProfitable ? "✓ Hala Karlı" : "✗ Zararlıya Döndü"}
        </span>
      </div>

      {/* Slider */}
      <div className="mb-5">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>COGS Değişimi</span>
          <span className={clsx(
            "font-bold",
            cogsChangePct > 0 ? "text-red-600" : cogsChangePct < 0 ? "text-green-600" : "text-gray-600"
          )}>
            {cogsChangePct > 0 ? "+" : ""}{cogsChangePct}%
          </span>
        </div>
        <input
          type="range"
          min={-30}
          max={60}
          step={5}
          value={cogsChangePct}
          onChange={(e) => setCogsChangePct(Number(e.target.value))}
          className="w-full accent-gray-900"
        />
        <div className="flex justify-between text-xs text-gray-300 mt-0.5">
          <span>-30%</span>
          <span>0</span>
          <span>+60%</span>
        </div>
      </div>

      {/* Metrik karşılaştırma */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          {
            label: "COGS",
            before: `$${cogs.toFixed(2)}`,
            after: `$${newCogs.toFixed(2)}`,
            changed: cogsChangePct !== 0,
            worse: cogsChangePct > 0,
          },
          {
            label: "Break-even ACOS",
            before: `%${base.breakEvenAcos.toFixed(1)}`,
            after: `%${current.breakEvenAcos.toFixed(1)}`,
            changed: cogsChangePct !== 0,
            worse: current.breakEvenAcos < base.breakEvenAcos,
          },
          {
            label: "Net Kâr/Satış",
            before: `$${base.netProfit.toFixed(2)}`,
            after: `$${current.netProfit.toFixed(2)}`,
            changed: cogsChangePct !== 0,
            worse: current.netProfit < base.netProfit,
          },
        ].map((m) => (
          <div key={m.label} className={clsx(
            "rounded-xl p-3 border text-center",
            !m.changed ? "bg-gray-50 border-gray-100" :
            m.worse ? "bg-red-50 border-red-100" : "bg-green-50 border-green-100"
          )}>
            <p className="text-xs text-gray-400 mb-1">{m.label}</p>
            <p className="text-xs text-gray-400 line-through">{m.before}</p>
            <p className={clsx(
              "text-sm font-bold",
              !m.changed ? "text-gray-700" : m.worse ? "text-red-700" : "text-green-700"
            )}>
              {m.after}
            </p>
          </div>
        ))}
      </div>

      {/* Break-even ACOS vs mevcut ACOS görsel */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Mevcut ACOS: <strong className="text-gray-700">%{currentAcos.toFixed(1)}</strong></span>
          <span>Break-even: <strong className={isProfitable ? "text-green-600" : "text-red-600"}>
            %{current.breakEvenAcos.toFixed(1)}
          </strong></span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-3 relative">
          {/* Break-even çizgisi */}
          <div
            className="absolute top-0 h-3 w-0.5 bg-gray-500 z-10"
            style={{ left: `${Math.min(current.breakEvenAcos, 100)}%` }}
          />
          {/* Mevcut ACOS */}
          <div
            className={clsx("h-3 rounded-full transition-all", isProfitable ? "bg-green-400" : "bg-red-400")}
            style={{ width: `${Math.min(currentAcos, 100)}%` }}
          />
        </div>
        <p className="text-xs text-gray-400 mt-1">
          {isProfitable
            ? `${(current.breakEvenAcos - currentAcos).toFixed(1)} puan emniyet marjın var.`
            : `ACOS, break-even'i ${(currentAcos - current.breakEvenAcos).toFixed(1)} puan aşıyor.`}
        </p>
      </div>

      {/* Uyarı / Öneri */}
      {cogsChangePct > 0 && (
        <div className={clsx(
          "rounded-xl px-4 py-3 text-xs leading-relaxed",
          isProfitable ? "bg-blue-50 border border-blue-100 text-blue-800" : "bg-red-50 border border-red-100 text-red-800"
        )}>
          {isProfitable
            ? `COGS %${cogsChangePct} artsa bile reklam karlı kalıyor. Kâr marjı ${marginDelta.toFixed(1)} puan düşüyor.`
            : `COGS %${cogsChangePct} artışıyla reklam zararlıya döner. Fiyatı en az $${((newCogs + shippingCost + LISTING_FEE) / (1 - ETSY_FEE_PCT - currentAcos / 100)).toFixed(2)}'a çıkarman gerekir.`}
        </div>
      )}
      {cogsChangePct < 0 && (
        <div className="rounded-xl px-4 py-3 text-xs bg-green-50 border border-green-100 text-green-800 leading-relaxed">
          Maliyet düşüşü kâr marjını {Math.abs(marginDelta).toFixed(1)} puan artırıyor. Elde edilen marjı bütçe artışına yansıtabilirsin.
        </div>
      )}
    </div>
  );
}

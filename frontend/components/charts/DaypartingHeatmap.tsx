"use client";
import { useMemo } from "react";
import clsx from "clsx";

interface Cell {
  hour: number;
  dow: number;
  avg_roas: number;
  avg_ctr: number;
  n: number;
}

interface Props {
  cells: Cell[];
  bestHours: number[];
  bestDays: number[];
  worstHours: number[];
  recommendation: string;
  dowLabels: string[];
}

const HOURS = Array.from({ length: 24 }, (_, i) => i);

function roasColor(roas: number, maxRoas: number): string {
  if (maxRoas === 0) return "bg-gray-50 text-gray-300";
  const ratio = roas / maxRoas;
  if (ratio >= 0.85) return "bg-green-500 text-white";
  if (ratio >= 0.65) return "bg-green-300 text-green-900";
  if (ratio >= 0.45) return "bg-yellow-200 text-yellow-900";
  if (ratio >= 0.25) return "bg-orange-200 text-orange-900";
  if (roas > 0)      return "bg-red-100 text-red-800";
  return "bg-gray-50 text-gray-300";
}

export default function DaypartingHeatmap({
  cells,
  bestHours,
  bestDays,
  worstHours,
  recommendation,
  dowLabels,
}: Props) {
  // (hour, dow) → cell index
  const cellMap = useMemo(() => {
    const m: Record<string, Cell> = {};
    for (const c of cells) m[`${c.hour}-${c.dow}`] = c;
    return m;
  }, [cells]);

  const maxRoas = useMemo(
    () => Math.max(...cells.map((c) => c.avg_roas), 0.01),
    [cells]
  );

  return (
    <div className="space-y-3">
      {/* Öneri */}
      <p className="text-xs text-gray-600 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2">
        {recommendation}
      </p>

      {/* Izgara */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-[10px]">
          <thead>
            <tr>
              <th className="w-8 text-gray-400 font-normal pb-1 text-left">Saat</th>
              {dowLabels.map((d, i) => (
                <th
                  key={i}
                  className={clsx(
                    "px-1 pb-1 font-medium text-center",
                    bestDays.includes(i) ? "text-green-600" : "text-gray-500"
                  )}
                >
                  {d}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {HOURS.map((h) => {
              const isBestHour = bestHours.includes(h);
              const isWorstHour = worstHours.includes(h);
              return (
                <tr key={h}>
                  <td
                    className={clsx(
                      "pr-2 text-right font-medium leading-5",
                      isBestHour ? "text-green-600" : isWorstHour ? "text-red-400" : "text-gray-400"
                    )}
                  >
                    {String(h).padStart(2, "0")}
                  </td>
                  {dowLabels.map((_, d) => {
                    const cell = cellMap[`${h}-${d}`];
                    const roas = cell?.avg_roas ?? 0;
                    return (
                      <td key={d} className="p-0.5">
                        <div
                          title={
                            cell
                              ? `ROAS: ${roas.toFixed(2)} | CTR: ${(cell.avg_ctr * 100).toFixed(2)}% | n=${cell.n}`
                              : "Veri yok"
                          }
                          className={clsx(
                            "w-full h-5 rounded text-center leading-5 cursor-default transition-transform hover:scale-110",
                            roasColor(roas, maxRoas)
                          )}
                        >
                          {roas > 0 ? roas.toFixed(1) : ""}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Renk açıklaması */}
      <div className="flex items-center gap-2 text-[10px] text-gray-500">
        <span>Düşük ROAS</span>
        <div className="flex gap-0.5">
          {["bg-red-100", "bg-orange-200", "bg-yellow-200", "bg-green-300", "bg-green-500"].map((c) => (
            <div key={c} className={clsx("w-4 h-3 rounded", c)} />
          ))}
        </div>
        <span>Yüksek ROAS</span>
        <span className="ml-auto text-gray-400">Hover: detay</span>
      </div>
    </div>
  );
}

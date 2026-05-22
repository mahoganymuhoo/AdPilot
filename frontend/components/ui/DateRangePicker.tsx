"use client";
import { useState } from "react";
import { Calendar, ChevronDown } from "lucide-react";
import clsx from "clsx";

export type DateRange = 7 | 14 | 30 | 90;

const OPTIONS: { label: string; value: DateRange }[] = [
  { label: "Son 7 gün", value: 7 },
  { label: "Son 14 gün", value: 14 },
  { label: "Son 30 gün", value: 30 },
  { label: "Son 90 gün", value: 90 },
];

interface Props {
  value: DateRange;
  onChange: (v: DateRange) => void;
  className?: string;
}

export default function DateRangePicker({ value, onChange, className }: Props) {
  const [open, setOpen] = useState(false);
  const selected = OPTIONS.find((o) => o.value === value) ?? OPTIONS[2];

  return (
    <div className={clsx("relative inline-block text-left", className)}>
      <button
        onClick={() => setOpen((p) => !p)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
      >
        <Calendar size={14} className="text-gray-400" />
        {selected.label}
        <ChevronDown size={14} className={clsx("text-gray-400 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-1 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1">
            {OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => { onChange(opt.value); setOpen(false); }}
                className={clsx(
                  "w-full text-left px-3 py-2 text-sm transition-colors",
                  opt.value === value
                    ? "bg-green-50 text-green-700 font-medium"
                    : "text-gray-700 hover:bg-gray-50"
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

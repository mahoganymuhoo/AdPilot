import clsx from "clsx";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "improving" | "stable" | "declining";
  status?: "good" | "warning" | "danger" | "neutral";
  badge?: string;
}

const statusColors = {
  good: "bg-green-50 border-green-200",
  warning: "bg-yellow-50 border-yellow-200",
  danger: "bg-red-50 border-red-200",
  neutral: "bg-white border-gray-200",
};

const trendIcons = {
  improving: <TrendingUp size={14} className="text-green-500" />,
  declining: <TrendingDown size={14} className="text-red-500" />,
  stable: <Minus size={14} className="text-gray-400" />,
};

export default function KpiCard({ title, value, subtitle, trend, status = "neutral", badge }: KpiCardProps) {
  return (
    <div className={clsx("rounded-xl border p-5 shadow-sm", statusColors[status])}>
      <div className="flex items-start justify-between mb-1">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{title}</p>
        {badge && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{badge}</span>
        )}
      </div>
      <div className="flex items-end gap-2 mt-1">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        {trend && <span className="mb-0.5">{trendIcons[trend]}</span>}
      </div>
      {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
    </div>
  );
}

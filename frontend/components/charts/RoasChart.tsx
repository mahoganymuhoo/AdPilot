"use client";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ReferenceLine, ResponsiveContainer,
} from "recharts";

interface DataPoint {
  date: string;
  roas: number;
  ema7?: number;
  ema30?: number;
}

interface RoasChartProps {
  data: DataPoint[];
  targetRoas?: number;
}

export default function RoasChart({ data, targetRoas = 3.0 }: RoasChartProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">ROAS Trendi (7g / 30g EMA)</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} />
          <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
            formatter={(value: number) => value.toFixed(2)}
          />
          <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
          <ReferenceLine y={targetRoas} stroke="#ef4444" strokeDasharray="4 4" label={{ value: `Hedef ${targetRoas}x`, fontSize: 10 }} />
          <Line type="monotone" dataKey="roas" stroke="#6b7280" strokeWidth={1.5} dot={false} name="ROAS" />
          <Line type="monotone" dataKey="ema7" stroke="#22c55e" strokeWidth={2} dot={false} name="7g EMA" />
          <Line type="monotone" dataKey="ema30" stroke="#3b82f6" strokeWidth={2} dot={false} name="30g EMA" strokeDasharray="5 3" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

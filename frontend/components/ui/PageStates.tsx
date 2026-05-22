"use client";
import { Loader, AlertCircle, InboxIcon } from "lucide-react";

export function PageLoader({ label = "Yükleniyor..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 gap-3">
      <Loader size={28} className="text-gray-400 animate-spin" />
      <p className="text-sm text-gray-400">{label}</p>
    </div>
  );
}

export function PageError({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 gap-3">
      <AlertCircle size={28} className="text-red-400" />
      <p className="text-sm text-red-600 font-medium">Bir hata oluştu</p>
      <p className="text-xs text-gray-400 max-w-xs text-center">{message}</p>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: { label: string; href: string };
}) {
  return (
    <div className="flex flex-col items-center justify-center py-24 gap-3">
      <InboxIcon size={32} className="text-gray-300" />
      <p className="text-sm font-semibold text-gray-600">{title}</p>
      <p className="text-xs text-gray-400 max-w-xs text-center">{description}</p>
      {action && (
        <a
          href={action.href}
          className="mt-2 bg-gray-900 text-white text-xs font-medium px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
        >
          {action.label}
        </a>
      )}
    </div>
  );
}

export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-1/3 mb-3" />
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className={`h-3 bg-gray-100 rounded mb-2 ${i === lines - 1 ? "w-1/2" : "w-full"}`} />
      ))}
    </div>
  );
}

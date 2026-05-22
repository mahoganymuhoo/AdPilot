import useSWR from "swr";
import { api } from "@/lib/api";

const SELLER_ID = 1; // TODO: auth context'ten al

export function useDashboard() {
  return useSWR("dashboard", () => api.getDashboard(SELLER_ID), {
    refreshInterval: 60_000, // 1 dakikada bir yenile
  });
}

export function useProducts() {
  return useSWR("products", () => api.getProducts(SELLER_ID));
}

export function useInsights() {
  return useSWR("insights", () => api.getInsights(SELLER_ID));
}

export function useStrategies() {
  return useSWR("strategies", () => api.getStrategies(SELLER_ID), {
    refreshInterval: 30_000,
  });
}

export function useStrategy(id: number | null) {
  return useSWR(id ? `strategy-${id}` : null, () => api.getStrategy(id!));
}

export function useAnomalies(unread = false) {
  return useSWR(`anomalies-${unread}`, () => api.getAnomalies(SELLER_ID, unread), {
    refreshInterval: 120_000,
  });
}

export function useImpactAnalysis() {
  return useSWR("impact-analysis", () => api.getImpactAnalysis(SELLER_ID));
}

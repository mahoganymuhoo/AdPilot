const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // --- Metrics ---
  getDashboard: (sellerId: number) =>
    req<DashboardData>(`/metrics/dashboard?seller_id=${sellerId}`),

  getProducts: (sellerId: number) =>
    req<{ products: ProductMetric[] }>(`/metrics/products?seller_id=${sellerId}`),

  uploadCsv: (formData: FormData) =>
    fetch(`${BASE}/metrics/upload-csv`, { method: "POST", body: formData }).then((r) => r.json()),

  // --- Insights ---
  getInsights: (sellerId: number) =>
    req<{ products: InsightProduct[] }>(`/insights/products?seller_id=${sellerId}`),

  getAnomalies: (sellerId: number, unread = false) =>
    req<{ anomalies: Anomaly[] }>(`/insights/anomalies?seller_id=${sellerId}&unread=${unread}`),

  getAdWorthiness: (productId: number) =>
    req<AdWorthinessResult>(`/insights/product/${productId}/ad-worthiness`),

  getProfitabilityAI: (productId: number, provider = "claude") =>
    req<AIAnalysis>(`/insights/product/${productId}/profitability-ai?provider=${provider}`),

  getBudgetRecommendation: (body: BudgetRecommendationRequest) =>
    req<BudgetRecommendationResult>(`/insights/budget-recommendation`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // --- Strategies ---
  launchStrategy: (body: LaunchStrategyRequest) =>
    req<LaunchStrategyResponse>(`/strategies/launch`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getStrategies: (sellerId: number) =>
    req<{ strategies: StrategyItem[]; total: number }>(`/strategies/?seller_id=${sellerId}`),

  getStrategy: (id: number) =>
    req<StrategyDetail>(`/strategies/${id}`),

  addCheckpoint: (strategyId: number, body: CheckpointRequest) =>
    req<CheckpointResult>(`/strategies/${strategyId}/checkpoint`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  verdictStrategy: (strategyId: number, body: VerdictRequest) =>
    req<VerdictResult>(`/strategies/${strategyId}/verdict`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getStrategyContext: (strategyId: number) =>
    req<StrategyContext>(`/strategies/${strategyId}/context`),

  getImpactAnalysis: (sellerId: number) =>
    req<ImpactAnalysis>(`/strategies/impact-analysis?seller_id=${sellerId}`),
};

// ---- Types ----

export interface DashboardData {
  roas: number;
  acos: number;
  tacos: number;
  net_profit: number;
  ctr: number;
  ad_spend: number;
  revenue: number;
  break_even_acos: number;
  roas_trend: "improving" | "stable" | "declining";
  anomaly_count: number;
  chart_data: { date: string; roas: number; ema_7: number; ema_30: number }[];
}

export interface ProductMetric {
  id: number;
  title: string;
  roas: number;
  acos: number;
  break_even_acos: number;
  net_profit_per_sale: number;
  ad_spend: number;
  revenue: number;
  ctr: number;
  recommendation: string;
}

export interface InsightProduct {
  id: number;
  title: string;
  score: number;
  recommendation: string;
  roas: number;
  suggested_budget: number;
  scoreDetails: {
    profit_margin: number;
    roas_trend: number;
    visibility: number;
    inventory: number;
    seasonal: number;
  };
  view_situation: string;
  view_diagnosis: string;
  pre_ad_action: string | null;
}

export interface Anomaly {
  id: number;
  product_id: number;
  product_title: string;
  metric: string;
  z_score: number;
  severity: string;
  direction: string;
  detected_at: string;
  is_notified: boolean;
  ai_analysis?: {
    likely_causes: string[];
    urgency: string;
    recommended_actions: string[];
  };
}

export interface AdWorthinessResult {
  score: number;
  recommendation: string;
  view_analysis: {
    situation: string;
    diagnosis: string;
    pre_ad_action: string | null;
  };
  reasoning: string;
  suggested_daily_budget: number;
}

export interface AIAnalysis {
  is_profitable: boolean;
  roas_status: string;
  recommendation: string;
  budget_change_pct: number;
  reasoning: string;
  red_flags: string[];
  action_items: string[];
}

export interface BudgetRecommendationRequest {
  seller_id: number;
  total_budget: number;
  ai_provider?: string;
}

export interface BudgetRecommendationResult {
  allocations: { product_id: number; product_title: string; suggested_budget: number; reason: string }[];
  strategy_summary: string;
  paused_products: string[];
}

export interface LaunchStrategyRequest {
  seller_id: number;
  product_id: number;
  recommendation: Record<string, unknown>;
  initial_metrics: Record<string, unknown>;
  seller_context: Record<string, unknown>;
  action_confirmed: string;
  ai_provider?: string;
  api_key?: string;
}

export interface LaunchStrategyResponse {
  strategy_id: number;
  name: string;
  goal_summary: string;
  target_metrics: Record<string, number>;
  timeline_days: number;
  target_date: string;
  success_criteria: string[];
  confidence: string;
}

export interface StrategyItem {
  id: number;
  name: string;
  operation_type: string;
  status: string;
  days_elapsed: number;
  days_remaining: number;
  target_date: string;
  latest_status: string;
  latest_progress_pct: number;
  goal_summary: string;
  checkpoint_count: number;
}

export interface StrategyDetail {
  strategy: Record<string, unknown>;
  checkpoints: CheckpointRecord[];
  outcome: OutcomeRecord | null;
}

export interface CheckpointRecord {
  id: number;
  checked_at: string;
  current_metrics: Record<string, number>;
  ai_analysis: Record<string, unknown>;
  progress_pct: number;
  status: string;
}

export interface OutcomeRecord {
  outcome: string;
  completed_at: string;
  final_metrics: Record<string, number>;
  ai_verdict: Record<string, unknown>;
  lessons_learned: string[];
  next_strategy_hints: Record<string, unknown>;
}

export interface CheckpointRequest {
  current_metrics: Record<string, number>;
  seller_note?: string;
  ai_provider?: string;
}

export interface CheckpointResult {
  checkpoint_id: number;
  status: string;
  progress_pct: number;
  trend: string;
  checkpoint_insight: string;
  red_flags: string[];
  adjustment_needed: boolean;
  adjustment: Record<string, unknown>;
}

export interface VerdictRequest {
  final_metrics: Record<string, number>;
  ai_provider?: string;
}

export interface VerdictResult {
  outcome: string;
  outcome_summary: string;
  lessons_learned: string[];
  next_strategy_hints: Record<string, unknown>;
}

export interface StrategyContext {
  previous_outcome: string;
  lessons_learned: string[];
  next_strategy_hints: Record<string, unknown>;
  context_for_next_ai: string | null;
}

export interface ImpactStrategyRow {
  strategy_id: number;
  name: string;
  operation_type: string;
  outcome: string;
  impact_score: number;
  ai_confidence: string;
  actual_roas_change_pct: number;
  predicted_roas_change_pct: number;
  completed_at: string | null;
}

export interface ImpactAnalysis {
  seller_id: number;
  total_scored: number;
  overall_impact_score: number | null;
  calibration: {
    total_scored: number;
    accuracy_pct: number;
    high_confidence_accuracy_pct: number;
  };
  by_operation_type: Record<string, { count: number; avg_impact: number }>;
  per_strategy: ImpactStrategyRow[];
}

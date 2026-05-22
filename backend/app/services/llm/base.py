from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Awaitable

ToolExecutor = Callable[[str, dict], Awaitable[dict]]


@dataclass
class AnalysisResult:
    provider: str
    model: str
    insight_type: str
    result_json: dict[str, Any]
    summary_text: str
    prompt_tokens: int
    completion_tokens: int
    cache_hit: bool = False


class LLMProvider(ABC):
    """Tüm AI provider'ların uyguladığı ortak interface."""

    @abstractmethod
    async def analyze_profitability(self, metrics: dict, seller_context: dict) -> AnalysisResult:
        """Reklam kârlılığını yorumla, break-even ACOS hesapla, bütçe önerisi ver."""
        ...

    @abstractmethod
    async def score_ad_worthiness(self, product_metrics: dict, seller_context: dict) -> AnalysisResult:
        """Bu ürüne reklam verilmeli mi? Skor ve gerekçe üret."""
        ...

    @abstractmethod
    async def detect_anomaly_cause(self, anomaly: dict, history: list[dict]) -> AnalysisResult:
        """Anomalinin olası nedenini yorumla ve önlem öner."""
        ...

    @abstractmethod
    async def generate_budget_recommendation(self, products: list[dict], total_budget: float) -> AnalysisResult:
        """Portföy genelinde bütçe dağılımı önerisi yap."""
        ...

    @abstractmethod
    async def launch_strategy(
        self,
        recommendation: dict,
        initial_metrics: dict,
        seller_context: dict,
        action_confirmed: str,
    ) -> AnalysisResult:
        """Satıcı aksiyonu aldı — hedef, takvim ve başarı kriterleri belirle."""
        ...

    @abstractmethod
    async def monitor_strategy(
        self,
        strategy: dict,
        checkpoints: list[dict],
        current_metrics: dict,
        days_elapsed: int,
        days_remaining: int,
    ) -> AnalysisResult:
        """Strateji takip noktası — hedefe gidişatı değerlendir, rota düzelt."""
        ...

    @abstractmethod
    async def verdict_strategy(
        self,
        strategy: dict,
        checkpoints: list[dict],
        final_metrics: dict,
    ) -> AnalysisResult:
        """Süre doldu — hedefe ulaşıldı mı? Karar ver, öğrenilenleri kaydet."""
        ...

    @abstractmethod
    async def analyze_with_tools(
        self,
        question: str,
        seller_context: dict,
        tool_executor: ToolExecutor,
    ) -> AnalysisResult:
        """Claude'un tool'larla kendi veri sorgulayarak derin analiz yapması."""
        ...

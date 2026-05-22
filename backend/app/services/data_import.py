"""
Veri giriş servisleri:
- Mod 1: Etsy API otomatik sync
- Mod 2: CSV yükleme (Etsy export formatı)
- Mod 3: Manuel form girişi
"""
import io
import csv
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any


@dataclass
class NormalizedMetricRow:
    """Tüm veri kaynaklarından gelen ortak format."""
    date: datetime
    listing_id: str
    title: str
    impressions: int
    clicks: int
    ad_spend: float
    revenue: float
    conversions: int
    views: int
    data_source: str  # "api" | "csv" | "manual"


# ─── CSV Parser (Etsy Stats Export) ──────────────────────────────────────────

ETSY_CSV_COLUMN_MAP = {
    # Etsy stats CSV sütun adları → internal alan adları
    "Date": "date",
    "Listing ID": "listing_id",
    "Listing Title": "title",
    "Impressions": "impressions",
    "Visits": "clicks",
    "Orders": "conversions",
    "Revenue": "revenue",
    "Listing Views": "views",
}

AD_SPEND_CSV_COLUMN_MAP = {
    "Date": "date",
    "Listing ID": "listing_id",
    "Ad Spend": "ad_spend",
    "Clicks": "clicks",
    "Impressions": "impressions",
}


def parse_etsy_stats_csv(file_content: bytes) -> list[NormalizedMetricRow]:
    """
    Etsy → Stats → Download CSV dosyasını parse eder.
    Döndürür: NormalizedMetricRow listesi.
    """
    rows: list[NormalizedMetricRow] = []
    text = file_content.decode("utf-8-sig")  # BOM varsa temizle
    reader = csv.DictReader(io.StringIO(text))

    for row in reader:
        try:
            date_str = row.get("Date", "").strip()
            if not date_str:
                continue
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                date = datetime.strptime(date_str, "%m/%d/%Y").replace(tzinfo=timezone.utc)

            rows.append(NormalizedMetricRow(
                date=date,
                listing_id=str(row.get("Listing ID", "")).strip(),
                title=row.get("Listing Title", row.get("Title", "")).strip(),
                impressions=_safe_int(row.get("Impressions", 0)),
                clicks=_safe_int(row.get("Visits", row.get("Clicks", 0))),
                ad_spend=_safe_float(row.get("Ad Spend", row.get("Promoted Spend", 0))),
                revenue=_safe_float(row.get("Revenue", row.get("Total Revenue", 0))),
                conversions=_safe_int(row.get("Orders", row.get("Conversions", 0))),
                views=_safe_int(row.get("Listing Views", row.get("Views", 0))),
                data_source="csv",
            ))
        except Exception:
            continue  # Hatalı satırı atla

    return rows


def parse_manual_entries(entries: list[dict[str, Any]]) -> list[NormalizedMetricRow]:
    """
    Frontend'den gelen manuel form verilerini parse eder.
    entries: [{"date": "2024-01-15", "listing_id": "123", "ad_spend": 5.0, ...}]
    """
    rows: list[NormalizedMetricRow] = []
    for entry in entries:
        try:
            date_raw = entry.get("date")
            if isinstance(date_raw, str):
                date = datetime.strptime(date_raw[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                date = date_raw or datetime.now(timezone.utc)

            rows.append(NormalizedMetricRow(
                date=date,
                listing_id=str(entry.get("listing_id", "")),
                title=entry.get("title", "Bilinmeyen Ürün"),
                impressions=_safe_int(entry.get("impressions", 0)),
                clicks=_safe_int(entry.get("clicks", 0)),
                ad_spend=_safe_float(entry.get("ad_spend", 0)),
                revenue=_safe_float(entry.get("revenue", 0)),
                conversions=_safe_int(entry.get("conversions", 0)),
                views=_safe_int(entry.get("views", 0)),
                data_source="manual",
            ))
        except Exception:
            continue

    return rows


def _safe_int(value: Any) -> int:
    try:
        return int(str(value).replace(",", "").strip() or 0)
    except (ValueError, TypeError):
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(str(value).replace(",", "").replace("$", "").strip() or 0)
    except (ValueError, TypeError):
        return 0.0

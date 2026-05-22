# AdPilot — Geliştirme Yol Haritası

> Son güncelleme: 2026-05-22  
> Mevcut sürüm: v0.2.0  
> Branch: master

---

## Mevcut Durum (v0.1.0)

### Tamamlananlar ✅
- [x] Proje scaffolding (FastAPI + Next.js 15 + TimescaleDB + Redis + Celery)
- [x] Provider-agnostic LLM katmanı (Claude + OpenAI — kullanıcı seçer)
- [x] 4 temel AI analiz metodu: `analyze_profitability`, `score_ad_worthiness`, `detect_anomaly_cause`, `generate_budget_recommendation`
- [x] Claude prompt caching (`cache_control: ephemeral` — %90 token tasarrufu)
- [x] DB modelleri: Seller, Product, Platform, AdMetrics, AnomalyLog, AIInsight
- [x] API endpoint'leri: metrics upload, insights, profitability
- [x] 3 veri giriş modu: Etsy API / CSV upload / Manuel form
- [x] Dashboard sayfası: KPI kartlar, ROAS chart, anomali kartları
- [x] Products sayfası: ürün bazlı metrikler, break-even ACOS progress bar
- [x] Insights sayfası: Ad worthiness score, view analizi, bütçe önerisi
- [x] Guide sayfası: tüm metrik ve algoritmaların interaktif açıklamaları (InfoModal)
- [x] Upload sayfası: CSV drag-drop + manuel satır ekleme
- [x] Settings sayfası: AI provider seçimi, Etsy bağlantısı
- [x] **Strateji sistemi (v0.1.0 son ekleme)**:
  - [x] `Strategy`, `StrategyCheckpoint`, `StrategyOutcome` DB modelleri
  - [x] 3 fazlı AI prompt: `launch_strategy`, `monitor_strategy`, `verdict_strategy`
  - [x] Zincir hafıza: `context_for_next_ai` → bir sonraki stratejiye beslenir
  - [x] REST API: `/strategies/launch`, `/checkpoint`, `/verdict`, `/context`
  - [x] Frontend strateji sayfası: timeline, checkpoint log, outcome kartı
- [x] Tailwind CSS fix (postcss.config.js eksikti)
- [x] Docker Compose: TimescaleDB + Redis + backend + Celery worker/beat

---

## ~~Faz 1 — Kritik Düzeltmeler ve Bağlantılar~~ ✅ TAMAMLANDI (P0)

### 1.1 Strateji Sistemini Kapatma

- [x] **"Bu öneriyi uyguladım" butonu** — `LaunchStrategyModal` insights sayfasına eklendi
- [x] **`context_for_next_ai` zinciri** — `GET /strategies/{id}/context` endpoint + modal zinciri
- [x] **Checkpoint'e satıcı notu alanı** — `seller_note` modelde + API'de + UI'da
- [x] **Celery otomatik checkpoint görevi** — `strategy_monitor.py`, saatlik beat
- [x] **Strateji Şablonları** — 4 şablon: increase/test/optimize/reduce_budget

### 1.2 Frontend Kopuk Bağlantılar

- [x] **SWR ile gerçek API bağlantısı** — `frontend/lib/api.ts` + `frontend/lib/hooks.ts`
- [x] **Loading ve error state** — `PageLoader`, `PageError`, `SkeletonCard` bileşenleri
- [x] **Boş state yönetimi** — `EmptyState` bileşeni

---

## ~~Faz 2 — Yeni Algoritmalar~~ ✅ TAMAMLANDI (P1 + P2)

### ✅ Budget Saturation Curve
- [x] `calculate_saturation_curve()` — logaritmik fit, optimal_budget, diminishing_returns_point
- [x] `GET /api/v1/insights/product/{id}/saturation-curve` endpoint

### ✅ Break-even Stress Test
- [x] `stress_test_breakeven()` — COGS değişim matrisi, safe_up_to_cogs_increase
- [x] `StressTestPanel.tsx` — slider + anlık break-even hesabı
- [x] Onboarding adım 2'de canlı break-even önizleme

### ✅ Listing Kalite Skoru
- [x] `calculate_listing_quality()` — CTR/benchmark, image, video, title, review skorlaması
- [x] `GET /api/v1/insights/product/{id}/listing-quality` endpoint

### ✅ Ürün Yaşam Döngüsü Tespiti
- [x] `detect_product_lifecycle()` — launch/growth/mature/declining via EMA crossover
- [x] `GET /api/v1/insights/product/{id}/lifecycle` endpoint

### ✅ Strateji Başarı Panosu
- [x] `GET /api/v1/strategies/stats` — başarı oranı, operasyon tipine göre breakdown
- [x] AI beslemesi için `ai_context_summary` çıktısı

### ✅ Erken Uyarı — Hedef Projeksiyon
- [x] `project_strategy_outcome()` — lineer regresyon, will_meet_deadline bayrağı
- [x] `GET /api/v1/strategies/{id}/projection` endpoint

### ✅ Mobil Uyumluluk
- [x] `Sidebar.tsx` — `lg:` breakpoint, mobil top header + hamburger + anomali badge
- [x] Mobil overlay menü (slide-in, tıkla kapat)

### Dayparting Analizi (Öncelik: DÜŞÜK — P3'e taşındı)

- [ ] **Backend** — Saatlik/günlük metrik aggregation.
  - `GROUP BY EXTRACT(hour FROM time), EXTRACT(dow FROM time)`
  - Çıktı: heatmap verisi (gün × saat → ortalama CTR/ROAS)
  - Dosya: `backend/app/services/analytics.py`, `backend/app/api/v1/metrics.py`

- [ ] **Frontend** — Isı haritası (recharts custom cell ile).
  - Dosya: `frontend/components/charts/DaypartingHeatmap.tsx`

---

## ~~Faz 3 — Kullanıcı Deneyimi İyileştirmeleri~~ ✅ TAMAMLANDI (P1)

### ✅ Onboarding Wizard
- [x] 4 adımlı wizard: veri kaynağı → maliyetler → AI provider → tamamlandı
- [x] Canlı break-even önizleme (adım 2)
- [x] `OnboardingGuard` → ilk açılışta yönlendir, tamamlandıysa atla
- [x] Dosya: `frontend/app/onboarding/page.tsx`, `frontend/components/ui/OnboardingGuard.tsx`

### ✅ Anomali Bildirimleri
- [x] `AnomalyDrawer.tsx` — sağdan açılan panel, şiddet badge'i, genişletilebilir detay
- [x] Sidebar'da kırmızı badge (okunmamış anomali sayısı)
- [x] Mobil header'da anomali bell butonu
- [x] Demo data hazır, `useAnomalies` hook bağlanmaya hazır

### ✅ Mobil Uyumluluk
- [x] Sidebar hamburger + overlay menü (P2'de tamamlandı, buraya da işaret)

### Dashboard Tarih Filtresi (Öncelik: ORTA — P3'e taşındı)

- [ ] Date range picker — Son 7 / 14 / 30 / 90 gün veya özel aralık
- [ ] Tüm chart ve KPI kartları seçilen aralığa göre yeniden hesaplansın
- [ ] Dosya: `frontend/app/dashboard/page.tsx`, `frontend/components/ui/DateRangePicker.tsx`

### CSV Export (Öncelik: DÜŞÜK)

- [ ] Strateji sonuçlarını CSV/PDF export et
- [ ] Dashboard metriklerini export et
- [ ] Dosya: `frontend/lib/export.ts`, her sayfaya "Export" butonu

---

## Faz 4 — Strateji Sistemini Derinleştirme (Önümüzdeki 2 hafta — P3)

### ~~4.1 Strateji Başarı Oranı Panosu~~ ✅ TAMAMLANDI (P2'de)

### ~~4.2 Erken Uyarı — Hedef Projeksiyon~~ ✅ TAMAMLANDI (P2'de)

### 4.3 Strateji Karşılaştırma

> Aynı ürün için iki farklı stratejiyi yan yana karşılaştır.

- [ ] **Frontend** — Strategies sayfasında "Karşılaştır" mod.
  - Sol / sağ layout, her iki stratejinin checkpoint eğrisi çakışık gösterilir
  - Dosya: `frontend/app/strategies/compare/page.tsx`

### 4.4 Cross-product Strateji Çakışması

> Aynı anda iki ürüne bütçe artışı yapılırsa birinin diğerini etkileyip etkilemediğini tespit et.

- [ ] **Backend** — Aynı kategorideki eş zamanlı aktif stratejileri tara.
  - ROAS korelasyonu negatifse → "Bu iki ürün birbirinin trafiğini çekiyor olabilir" uyarısı
  - Dosya: `backend/app/services/analytics.py`

- [ ] **Frontend** — Strategies sayfasında çakışma uyarısı.

---

## Faz 5 — İleri Özellikler (1+ ay)

### 5.1 Claude Tool Use Entegrasyonu

> AI'nın kendisi veri sorgulayıp daha derin analiz yapması.

- [ ] Tool'lar tanımla: `get_roas_trend`, `get_anomalies`, `get_product_metrics`, `get_competitor_benchmark`
- [ ] Claude'a tool'ları ver → extended thinking ile kullandır
- [ ] Dosya: `backend/app/services/llm/claude_provider.py`, `backend/app/services/llm/tools.py`

### 5.2 Multi-platform Adapter

> Amazon, Shopify, TikTok Shop bağlantısı.

- [ ] Platform adapter interface: `PlatformAdapter(Protocol)` → `get_metrics()`, `get_products()`, `sync()`
- [ ] Etsy adapter (mevcut) → interface'e uyarla
- [ ] Amazon SP-API adapter (taslak)
- [ ] Shopify adapter (taslak)
- [ ] Dosya: `backend/app/services/platforms/`

### 5.3 LSTM Anomali Tespiti

> Z-score yerine öğrenen model.

- [ ] PyTorch LSTM → ROAS zaman serisi üzerinde anomali skoru
- [ ] Eğitim: seller başına, yeterli veri biriktikten sonra devreye gir
- [ ] Z-score ile hibrit: veri azsa Z-score, çoksa LSTM
- [ ] Dosya: `backend/app/services/ml/lstm_anomaly.py`

### 5.4 WebSocket Real-time Dashboard

> Anlık metrik güncellemeleri.

- [ ] FastAPI WebSocket endpoint: `/ws/metrics/{seller_id}`
- [ ] Celery her 15 dakikada sync yaptıktan sonra WS mesajı gönder
- [ ] Frontend: SWR yerine WS bağlantısı, anlık KPI güncelleme
- [ ] Dosya: `backend/app/api/ws.py`, `frontend/lib/websocket.ts`

### 5.5 Prompt Cache Optimizasyonu

> Seller başına kalıcı bağlam önbelleği.

- [ ] Seller profili (shop stats, tüm ürünler, geçmiş stratejiler) → tek seferlik cache
- [ ] `cache_control: ephemeral` → büyük context'lerde saatlik TTL
- [ ] Token maliyet dashboard'u: "Bu ay X token harcandı, Y$ tasarruf edildi"

---

## Teknik Borç

- [x] **Alembic migration** — `002_strategy_tables.py` oluşturuldu ve çalıştırıldı.
- [ ] **Pydantic response schema'ları** — API endpoint'lerin çıktıları için `schemas/` altında response model ekle. Şu an `dict` dönüyor.
- [ ] **Test coverage** — Analytics algoritmaları için birim testler yok. `backend/tests/test_analytics.py` başlat. Bilinen ROAS/ACOS değerleriyle doğrulama yap.
- [ ] **Rate limiting** — LLM provider çağrılarına retry + exponential backoff ekle. Şu an hata fırlatıyor.
- [ ] **API key şifreleme** — `Seller.anthropic_api_key_enc` alanı var ama şifreleme implementasyonu yok. Fernet veya AWS KMS ile şifrele.
- [ ] **`frontend/package-lock.json`** — `.gitignore`'a ekle veya commit'e dahil et (tutarsız).

---

## Öncelik Özeti

```
✅ P0 — TAMAMLANDI:
  → "Bu öneriyi uyguladım" butonu (LaunchStrategyModal)
  → context_for_next_ai zinciri frontend bağlantısı
  → SWR ile gerçek API bağlantısı (api.ts + hooks.ts)
  → Alembic migration (002_strategy_tables.py)

✅ P1 — TAMAMLANDI:
  → Celery otomatik checkpoint görevi (strategy_monitor.py)
  → Onboarding wizard (4 adım + OnboardingGuard)
  → Budget saturation curve (logaritmik fit algoritması)
  → Break-even stress test (StressTestPanel + senaryo matrisi)
  → Anomali bildirimleri (AnomalyDrawer + sidebar badge)

✅ P2 — TAMAMLANDI:
  → Listing kalite skoru (CTR/benchmark + 4 faktör)
  → Ürün yaşam döngüsü tespiti (EMA crossover)
  → Strateji başarı panosu (/strategies/stats)
  → Erken uyarı / hedef projeksiyon (lineer regresyon)
  → Mobil uyumluluk (hamburger + overlay menü)

P3 — Sıradaki:
  → Claude tool use (get_roas_trend, get_anomalies, vb.)
  → Dayparting analizi (saat/gün ısı haritası)
  → Dashboard tarih filtresi (DateRangePicker)
  → Strateji karşılaştırma (yan yana görünüm)
  → CSV export (strateji + dashboard)

P4 — Uzun Vade:
  → Multi-platform adapter (Amazon, Shopify, TikTok)
  → LSTM anomali tespiti (Z-score yerine öğrenen model)
  → WebSocket real-time dashboard
  → Prompt cache optimizasyonu (seller başına kalıcı bağlam)
```

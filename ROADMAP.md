# AdPilot — Geliştirme Yol Haritası

> Son güncelleme: 2026-05-22  
> Mevcut sürüm: v0.1.0  
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

## Faz 1 — Kritik Düzeltmeler ve Bağlantılar (1-2 gün)

> Mevcut özellikler teoride var ama pratikte kopuk. Bu faz bağlantıları kurar.

### 1.1 Strateji Sistemini Kapatma

- [ ] **"Bu öneriyi uyguladım" butonu** — Insights sayfasındaki her ürün kartına ekle.
  - Tıklanınca `LaunchStrategyModal` açılır.
  - Modal: "Ne yaptın?" text alanı (action_confirmed), AI provider seçimi.
  - `POST /api/v1/strategies/launch` çağrısı → redirect `/strategies/{id}`.
  - Dosya: `frontend/app/insights/page.tsx`, yeni `frontend/components/strategy/LaunchStrategyModal.tsx`

- [ ] **`context_for_next_ai` zincirini frontend'e bağla** — Yeni strateji başlatılırken aynı ürünün tamamlanmış son stratejisini çek.
  - `GET /api/v1/strategies/{id}/context` → `seller_context` içine ekle.
  - UI'da "Önceki Strateji Hafızası" collapsed kutucuğu göster.
  - Dosya: `frontend/components/strategy/LaunchStrategyModal.tsx`

- [ ] **Checkpoint'e satıcı notu alanı** — `StrategyCheckpoint` modeline `seller_note: str | None` ekle.
  - API: `CheckpointRequest.seller_note` → prompt'a `<seller_note>` tag'i olarak ekle.
  - UI: checkpoint kartında not alanı göster.
  - Dosya: `backend/app/models/strategy.py`, `backend/app/api/v1/strategies.py`, `frontend/app/strategies/page.tsx`

- [ ] **Celery otomatik checkpoint görevi** — Her saat `active` stratejileri tara.
  - `check_interval_days` geçmişse ve son checkpoint yoksa → metrik çek → `monitor_strategy` çağır → kaydet.
  - Dosya: `backend/app/tasks/strategy_monitor.py`, `backend/app/tasks/celery_app.py`

- [ ] **Strateji Şablonları** — Yeni strateji başlatırken hazır şablon seç.
  - Şablonlar: "Bütçe Artışı (%20)", "Küçük Bütçe Testi", "Listing + Reklam Kombine", "Sezon Testi", "Durdur ve İzle"
  - Her şablon: varsayılan `timeline_days`, `check_interval_days`, `success_criteria` önerileri içerir.
  - Dosya: `frontend/lib/strategy_templates.ts`, `frontend/components/strategy/StrategyTemplateSelector.tsx`

### 1.2 Frontend Kopuk Bağlantılar

- [ ] **SWR ile gerçek API bağlantısı** — Tüm sayfalardaki demo veriler kaldırılıp `useSWR` hook'larına bağlanacak.
  - Dashboard: `GET /api/v1/metrics/dashboard?seller_id=1`
  - Products: `GET /api/v1/metrics/products?seller_id=1`
  - Insights: `GET /api/v1/insights/products?seller_id=1`
  - Strategies: `GET /api/v1/strategies?seller_id=1`
  - Dosya: `frontend/lib/api.ts` (merkezi fetch helper), her sayfa

- [ ] **Loading ve error state** — Her sayfaya skeleton loader ve hata mesajı ekle.
  - Dosya: `frontend/components/ui/SkeletonCard.tsx`, `frontend/components/ui/ErrorBanner.tsx`

- [ ] **Boş state yönetimi** — Veri yokken anlamlı mesaj ve aksiyon göster.
  - "Henüz veri yok → Veri Yükle" CTA butonu
  - Dosya: `frontend/components/ui/EmptyState.tsx`

---

## Faz 2 — Yeni Algoritmalar (1 hafta)

### 2.1 Budget Saturation Curve (Öncelik: YÜKSEK)

> "Daha fazla bütçe harcasam ROAS'ım ne olur?" sorusunu cevaplar.

- [ ] **Backend algoritması** — Geçmiş (bütçe, ROAS) çiftlerine logaritmik fit uygula.
  ```python
  # ROAS = a × ln(budget) + b  →  scipy.optimize.curve_fit
  # Çıktı: optimal_budget, diminishing_returns_point, projected_roas(budget)
  ```
  Dosya: `backend/app/services/analytics.py` → `calculate_saturation_curve()`

- [ ] **API endpoint** — `GET /api/v1/insights/product/{id}/saturation-curve`
  - Girdi: ürün ID
  - Çıktı: eğri noktaları (bütçe → tahmini ROAS), `optimal_budget`, `current_efficiency_pct`

- [ ] **Frontend görselleştirme** — Recharts ile interaktif eğri.
  - X ekseni: günlük bütçe ($), Y ekseni: tahmini ROAS
  - Mevcut bütçe dikey çizgi ile işaretlenir, "Verim azalıyor" noktası vurgulanır
  - Dosya: `frontend/components/charts/SaturationCurveChart.tsx`, `frontend/app/insights/page.tsx`

### 2.2 Break-even Stress Test (Öncelik: YÜKSEK)

> "Maliyetlerim %15 artarsa bu reklam hala karlı mı?"

- [ ] **Backend** — `stress_test_breakeven(product_id, cogs_increase_pct, ad_spend_increase_pct)` fonksiyonu.
  - Senaryo matrisi: COGS +%10/+%20/+%30, mevcut reklam bütçesiyle hesapla.
  - Çıktı: her senaryoda `is_profitable`, yeni `break_even_acos`, `net_profit_per_sale`
  - Dosya: `backend/app/services/analytics.py`

- [ ] **Frontend** — Products sayfasında "Senaryo Analizi" toggle paneli.
  - Slider: COGS değişimi (-%20 → +%50)
  - Anlık güncelleme: break-even ACOS çubuğu kayar, karlılık rengi değişir
  - Dosya: `frontend/app/products/page.tsx`, `frontend/components/ui/StressTestPanel.tsx`

### 2.3 Listing Kalite Skoru (Öncelik: ORTA)

> CTR'ı kategori ortalamasıyla karşılaştırarak listing kalitesini ölç.

- [ ] **Backend** — `calculate_listing_quality_score(product_ctr, category_avg_ctr)` → 0-100 skor.
  - < 0.7x kategori → "Listing zayıf, reklam öncesi düzelt"
  - 0.7-1.3x → "Ortalama"
  - > 1.3x → "Güçlü listing, reklam verimli olacak"
  - Etsy kategorisi bazında benchmark tablosu (manuel başlangıç, zamanla öğrenen)
  - Dosya: `backend/app/services/analytics.py`, `backend/app/models/platform.py` (kategori benchmark)

- [ ] **Frontend** — Products sayfasında her ürün kartına listing kalite badge'i ekle.
  - İkon + kısa açıklama + InfoModal ile detay
  - Dosya: `frontend/app/products/page.tsx`

### 2.4 Ürün Yaşam Döngüsü Tespiti (Öncelik: ORTA)

> ROAS trendi + mevsimsellik → ürünün nerede olduğunu tespit et.

- [ ] **Backend** — `detect_product_lifecycle(roas_history_90d, seasonal_index)` → `launch|growth|mature|declining`
  - Launch: < 30 günlük veri
  - Growth: EMA_7d > EMA_30d ve trend > +%5
  - Mature: EMA'lar birbirine yakın, stabil
  - Declining: EMA_7d < EMA_30d ve trend < -%5 ve sezon değil
  - Dosya: `backend/app/services/analytics.py`

- [ ] **Frontend** — Dashboard ve Products sayfasına lifecycle badge ekle.
  - Her lifecycle için farklı renk + öneri metni
  - Dosya: `frontend/app/dashboard/page.tsx`, `frontend/app/products/page.tsx`

### 2.5 Dayparting Analizi (Öncelik: DÜŞÜK)

> Hangi saat/gün reklamın en verimli olduğunu göster.

- [ ] **Backend** — Saatlik/günlük metrik aggregation.
  - `GROUP BY EXTRACT(hour FROM time), EXTRACT(dow FROM time)`
  - Çıktı: heatmap verisi (gün × saat → ortalama CTR/ROAS)
  - Dosya: `backend/app/services/analytics.py`, `backend/app/api/v1/metrics.py`

- [ ] **Frontend** — Isı haritası (recharts custom cell ile).
  - Dosya: `frontend/components/charts/DaypartingHeatmap.tsx`

---

## Faz 3 — Kullanıcı Deneyimi İyileştirmeleri (1 hafta)

### 3.1 Onboarding Wizard (Öncelik: KRİTİK)

> İlk açılışta kullanıcıyı sisteme dahil et.

- [ ] **Adım 1 — Veri kaynağı seç**: Etsy API / CSV Yükle / Manuel Gir
- [ ] **Adım 2 — COGS ve hedefler**: Ürün başına maliyet, hedef ROAS, günlük bütçe
- [ ] **Adım 3 — AI provider seç**: Claude API key / OpenAI API key gir, test et
- [ ] **Adım 4 — İlk analiz**: Yüklenen veriyle hemen analiz çalıştır, sonucu göster
- [ ] Onboarding tamamlandıysa tekrar gösterme (localStorage flag)
- [ ] Dosya: `frontend/app/onboarding/page.tsx`, `frontend/components/onboarding/`

### 3.2 Anomali Bildirimleri (Öncelik: YÜKSEK)

> Z-score ateşlendi ama kullanıcı haberdar olmuyor.

- [ ] **Backend** — Celery görevi: saatlik anomali taraması → `anomaly_log` tablosuna yaz.
  - `is_notified` flag'i ekle, bildirildikten sonra işaretle.
  - Dosya: `backend/app/tasks/anomaly_scanner.py`

- [ ] **Frontend** — Sidebar'da kırmızı badge (okunmamış anomali sayısı).
  - Tıklanınca anomali listesi açılır, her biri "Neden oldu? Ne yapmalıyım?" ile
  - `GET /api/v1/insights/anomalies?unread=true`
  - Dosya: `frontend/components/ui/Sidebar.tsx`, `frontend/components/ui/AnomalyDrawer.tsx`

### 3.3 Dashboard Tarih Filtresi (Öncelik: ORTA)

- [ ] Date range picker — Son 7 / 14 / 30 / 90 gün veya özel aralık
- [ ] Tüm chart ve KPI kartları seçilen aralığa göre yeniden hesaplansın
- [ ] Dosya: `frontend/app/dashboard/page.tsx`, `frontend/components/ui/DateRangePicker.tsx`

### 3.4 Mobil Uyumluluk (Öncelik: ORTA)

> Fixed sidebar + ml-64 telefonda kırılıyor.

- [ ] Sidebar: mobilde gizle, hamburger menü ile aç/kapat
- [ ] Grid layout'lar: `grid-cols-3` → mobilde `grid-cols-1`
- [ ] KPI kartlar: 2 sütun → mobilde 1 sütun
- [ ] Chart'lar: responsive container zaten var, boyut ayarı yap
- [ ] Dosya: `frontend/components/ui/Sidebar.tsx`, `frontend/app/layout.tsx`

### 3.5 CSV Export (Öncelik: DÜŞÜK)

- [ ] Strateji sonuçlarını CSV/PDF export et
- [ ] Dashboard metriklerini export et
- [ ] Dosya: `frontend/lib/export.ts`, her sayfaya "Export" butonu

---

## Faz 4 — Strateji Sistemini Derinleştirme (2 hafta)

### 4.1 Strateji Başarı Oranı Panosu

> Tamamlanan stratejilerden pattern çıkar, yeni stratejileri besle.

- [ ] **Backend** — `GET /api/v1/strategies/stats?seller_id={id}` endpoint.
  - Operasyon tipine göre başarı oranı
  - Ortalama ilerleme süresi
  - En çok hangi metrik hedefine ulaşılıyor/ulaşılamıyor
  - Dosya: `backend/app/api/v1/strategies.py`

- [ ] **Frontend** — Strategies sayfasına özet istatistik paneli.
  - "Bütçe artışı stratejilerinin %68'i başarılı"
  - "Ortalama hedef süren: 11 gün"
  - Dosya: `frontend/app/strategies/page.tsx`

- [ ] **AI beslemesi** — `launch_strategy` prompt'una istatistik ekle.
  - "Bu satıcının geçmiş 3 bütçe artışı stratejisinin %67'si başarılı oldu." → AI daha gerçekçi hedef koyar

### 4.2 Erken Uyarı — Hedef Projeksiyon

> 3. günde "bu hızla 14 günde hedefe ulaşılamaz" öngörüsü.

- [ ] **Backend** — `project_strategy_outcome(checkpoints, target_metrics, days_remaining)`.
  - Mevcut değişim hızıyla lineer ekstrapolasyon
  - "Bu hızla gidersen ROAS hedefi {X} güne ulaşır" (süre > kalan gün ise uyar)
  - Dosya: `backend/app/services/analytics.py`

- [ ] **Frontend** — Checkpoint kartında projeksiyon göster.
  - "Mevcut hızda: 18. günde hedefe ulaşırsın (hedef: 14 gün) ⚠️"

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

- [ ] **Alembic migration** — `strategies`, `strategy_checkpoints`, `strategy_outcomes` tabloları henüz migration'a eklenmedi. `backend/alembic/versions/002_strategy_tables.py` oluştur.
- [ ] **Pydantic response schema'ları** — API endpoint'lerin çıktıları için `schemas/` altında response model ekle. Şu an `dict` dönüyor.
- [ ] **Test coverage** — Analytics algoritmaları için birim testler yok. `backend/tests/test_analytics.py` başlat. Bilinen ROAS/ACOS değerleriyle doğrulama yap.
- [ ] **Rate limiting** — LLM provider çağrılarına retry + exponential backoff ekle. Şu an hata fırlatıyor.
- [ ] **API key şifreleme** — `Seller.anthropic_api_key_enc` alanı var ama şifreleme implementasyonu yok. Fernet veya AWS KMS ile şifrele.
- [ ] **`frontend/package-lock.json`** — `.gitignore`'a ekle veya commit'e dahil et (tutarsız).

---

## Öncelik Özeti

```
P0 — Bugün / Yarın:
  → "Bu öneriyi uyguladım" butonu (strateji başlatma kopuk)
  → context_for_next_ai zinciri frontend bağlantısı
  → SWR ile gerçek API bağlantısı (demo veriler kaldırılsın)
  → Alembic migration (strategy tabloları DB'de yok)

P1 — Bu Hafta:
  → Celery otomatik checkpoint görevi
  → Onboarding wizard
  → Budget saturation curve
  → Break-even stress test
  → Anomali bildirimleri

P2 — Önümüzdeki 2 Hafta:
  → Listing kalite skoru
  → Ürün yaşam döngüsü tespiti
  → Strateji başarı panosu
  → Erken uyarı / hedef projeksiyon
  → Mobil uyumluluk

P3 — Ay Sonu:
  → Claude tool use
  → Dayparting analizi
  → Strateji karşılaştırma
  → CSV export

P4 — Uzun Vade:
  → Multi-platform adapter
  → LSTM anomali tespiti
  → WebSocket real-time
  → Prompt cache optimizasyonu
```

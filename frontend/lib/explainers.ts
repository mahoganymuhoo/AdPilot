export interface Explainer {
  id: string;
  title: string;
  emoji: string;
  oneLiner: string;          // KPI kartının altında gösterilecek tek satır
  whatIs: string;            // Ne demek?
  formula?: string;          // Formül (varsa)
  howItWorks: string;        // Nasıl hesaplanıyor?
  goodValue: string;         // İyi değer nedir?
  badValue: string;          // Kötü değer nedir?
  example: string;           // Gerçek hayat örneği
  whatToDo: string;          // Ne yapmalıyım?
  tip?: string;              // Ekstra ipucu
}

export const EXPLAINERS: Record<string, Explainer> = {
  roas: {
    id: "roas",
    emoji: "💰",
    title: "ROAS — Reklama Geri Dönüş",
    oneLiner: "Harcadığın 1 dolar kaç dolar getiriyor?",
    whatIs:
      "ROAS (Return on Ad Spend), reklama harcadığın her 1 dolar için ne kadar gelir elde ettiğini gösterir. En temel reklam verimliliği ölçütüdür.",
    formula: "ROAS = Reklam Geliri ÷ Reklam Harcaması",
    howItWorks:
      "Reklama tıklayan müşterilerin yaptığı satışların toplamını, o dönemdeki reklam harcamasına böleriz. Örneğin 50$ harcayıp 200$ gelir elde ettiysen ROAS = 200 ÷ 50 = 4.0 olur.",
    goodValue:
      "3.0x ve üzeri genellikle iyi kabul edilir. 4.0x üzeri mükemmeldir — bütçeyi artırma zamanı.",
    badValue:
      "1.0x'in altı kesinlikle zararlıdır (harcadığından az kazanıyorsun). 1.0–2.0x arası şüphelidir; gerçek kârlılığı hesapla.",
    example:
      "Seramik kupana 1 haftada $30 reklam harcadın, bu reklamlardan $120 satış geldi. ROAS = 120 ÷ 30 = 4.0x. Güzel! Ama ürün maliyetin ve Etsy komisyonu da var, gerçek kârı hesaplamak için Break-even ACOS'a bak.",
    whatToDo:
      "ROAS > 3.5x → Bütçeyi %20 artır. ROAS 2–3x arası → Bütçeyi koru, iyileştirmeye çalış. ROAS < 1.5x → Bütçeyi azalt veya durdur.",
    tip: "ROAS tek başına yeterli değil! Ürün maliyetin yüksekse ROAS 4x olsa bile zarar edebilirsin. Break-even ACOS ile birlikte değerlendir.",
  },

  acos: {
    id: "acos",
    emoji: "📊",
    title: "ACOS — Reklam Satış Maliyeti",
    oneLiner: "Kazandığın her 100 liranın kaçını reklama veriyorsun?",
    whatIs:
      "ACOS (Advertising Cost of Sale), reklam gelirinin yüzde kaçını reklam harcamasına verdiğini gösterir. ROAS'ın tersidir — düşük olması iyidir.",
    formula: "ACOS = (Reklam Harcaması ÷ Reklam Geliri) × 100",
    howItWorks:
      "Reklam harcamanı, o reklamdan gelen gelire böler ve 100 ile çarparız. Örneğin $30 harcayıp $120 gelir elde ettiysen ACOS = (30 ÷ 120) × 100 = %25.",
    goodValue:
      "Break-even ACOS'unun altında olmalı. Kâr marjın %40 ise ACOS'un %40'ın altında olması reklamın karlı olduğunu gösterir.",
    badValue:
      "Break-even ACOS'unu geçen her değer zarardır. Örneğin kâr marjın %35 iken ACOS %50 ise, reklamdan para kaybediyorsun.",
    example:
      "Kupan $28'a satılıyor. Maliyetin (COGS) $9, Etsy komisyonu $1.82, kargo $2 = Toplam maliyet $12.82. Kâr marjın = ($28 - $12.82) ÷ $28 = %54. Break-even ACOS'un %54. ACOS'un %54'ün altında olduğu sürece karlısın.",
    whatToDo:
      "ACOS < Break-even ACOS → Reklam karlı, bütçeyi düşünebilirsin artırmayı. ACOS > Break-even ACOS → Zarar ediyorsun, bütçeyi azalt ya da listing'i iyileştir.",
  },

  tacos: {
    id: "tacos",
    emoji: "🌮",
    title: "TACoS — Toplam Reklam Satış Maliyeti",
    oneLiner: "Tüm gelirine göre reklama ne kadar harcıyorsun?",
    whatIs:
      "TACoS (Total Advertising Cost of Sale), reklam harcamanı YALNIZCA reklam gelirine değil, tüm mağaza gelirine (organik + reklam) böler. Bu, asıl iş sağlığını gösterir.",
    formula: "TACoS = (Toplam Reklam Harcaması ÷ Toplam Mağaza Geliri) × 100",
    howItWorks:
      "Etsy'nin gösterdiği ROAS sadece reklama tıklayan müşterileri sayar. Ama organik müşterilerinden de para kazanıyorsun. TACoS tüm resmi gösterir.",
    goodValue:
      "%10 altı mükemmel. %10–20 arası sağlıklı. %20–30 arası kabul edilebilir ama optimizasyon gerekli.",
    badValue:
      "%30 üzeri tehlikeli bölge. Bu, gelirinizin %30'undan fazlasını reklama verdiğiniz anlamına gelir.",
    example:
      "Bu ay toplam $500 sattın. $300 reklam gelirine tıkladı, $200 organik geldi. $60 reklam harcadın. ROAS = 300 ÷ 60 = 5.0x (harika görünüyor!). Ama TACoS = 60 ÷ 500 = %12 (gerçekten sağlıklı, harika!).",
    whatToDo:
      "TACoS yükseliyorsa organik satışların azalıyor, reklamlara bağımlı hale geliyorsun. Listing SEO'sunu iyileştir, organik satışları artır.",
    tip: "Etsy'nin kendi dashboard'u TACoS göstermez. Sadece AdPilot gibi araçlar bunu hesaplar. Bu yüzden değerli bir metriktir.",
  },

  breakeven_acos: {
    id: "breakeven_acos",
    emoji: "⚖️",
    title: "Break-even ACOS — Başabaş Noktası",
    oneLiner: "ACOS bu değerin altındaysa reklam sana para kazandırıyor.",
    whatIs:
      "Break-even ACOS, reklamın ne zaman karlı olduğunu gösteren eşik değeridir. ACOS bu değerin altındaysa kâr ediyorsun, üstündeyse zarar.",
    formula: "Break-even ACOS = (Fiyat − Tüm Maliyetler) ÷ Fiyat × 100",
    howItWorks:
      "Ürünün fiyatından üretim maliyetini, Etsy komisyonunu (%6.5 + $0.20) ve kargo maliyetini çıkarırız. Kalanın fiyata oranı kâr marjındır. Break-even ACOS = Kâr marjı.",
    goodValue:
      "Break-even ACOS ne kadar yüksekse o kadar iyidir — daha fazla reklam maliyetine dayanabilirsin. %40+ ideal, %20 altı zorlu.",
    badValue:
      "Break-even ACOS düşükse (örn. %15), ACOS'un çok düşük tutman gerekir — bu zorlu bir hedeftir.",
    example:
      "$28 seramik kupa: Maliyet $9 + Etsy fee $1.82 + Kargo $2 = $12.82. Kâr = $28 - $12.82 = $15.18. Break-even ACOS = 15.18 ÷ 28 × 100 = %54.2. Bu demek oluyor ki reklamlara satış başına $15.18'e kadar harcayabilirsin ve hâlâ kârdadasın.",
    whatToDo:
      "Break-even ACOS düşükse önce ürün fiyatını artırmayı veya maliyetlerini düşürmeyi düşün. Düşük marjlı ürünlerde reklam çok risklidir.",
  },

  net_profit: {
    id: "net_profit",
    emoji: "🏦",
    title: "Net Kâr — Gerçek Kazancın",
    oneLiner: "Tüm masraflar çıktıktan sonra cebinde ne kalıyor?",
    whatIs:
      "Net kâr, gelirinden tüm maliyetleri (ürün maliyeti, Etsy komisyonu, kargo, reklam harcaması) çıkardıktan sonra elde ettiğin gerçek kazançtır.",
    formula: "Net Kâr = Gelir − Ürün Maliyeti − Etsy Fee − Kargo − Reklam Harcaması",
    howItWorks:
      "Etsy'nin gösterdiği gelir rakamından tüm masrafları düşeriz. Reklam harcaması da dahil olduğu için bu gerçek 'cebine giren para'dır.",
    goodValue: "Pozitif olması şart. Kâr marjı %20+ sağlıklıdır, %30+ iyidir.",
    badValue: "Negatif net kâr = her satışta para kaybediyorsun. Hemen müdahale gerekir.",
    example:
      "$28 kupa sattın. Maliyet $9, Etsy fee $1.82, Kargo $2, Bu satışa atfedilen reklam $3.50 → Net Kâr = 28 - 9 - 1.82 - 2 - 3.50 = $11.68. ROAS güzel görünse de asıl kazancın budur.",
    whatToDo:
      "Net kâr düşüyorsa: fiyatı artır, maliyetleri düşür, veya reklam harcamasını optimize et. Üç koldan birlikte çalışınca fark yaratırsın.",
  },

  ema_trend: {
    id: "ema_trend",
    emoji: "📈",
    title: "EMA Trendi — Hareketli Ortalama",
    oneLiner: "Performansın gerçekten artıyor mu, yoksa rastgele dalgalanma mı?",
    whatIs:
      "EMA (Exponential Moving Average / Üstel Hareketli Ortalama), son günlere daha fazla ağırlık vererek gerçek trendi günlük dalgalanmalardan ayırt eder. Borsacıların da kullandığı bir yöntemdir.",
    formula: "EMA(bugün) = Bugünkü Değer × k + EMA(dün) × (1 − k)  [k = 2 ÷ (periyot + 1)]",
    howItWorks:
      "7 günlük EMA, son 7 günü ağırlıklı olarak değerlendirerek kısa vadeli trendi gösterir. 30 günlük EMA uzun vadeli yönü gösterir. 7g EMA, 30g EMA'nın üzerine çıktığında yükseliş trendi başlamıştır.",
    goodValue:
      "7 günlük EMA, 30 günlük EMA'nın üzerinde → Yükseliş trendi (yeşil ok). Bu, son performansın genel ortalamanın üstünde olduğunu gösterir.",
    badValue:
      "7 günlük EMA, 30 günlük EMA'nın altında → Düşüş trendi (kırmızı ok). Son performans ortalamanın altında — dikkat et.",
    example:
      "Reklamın 5 gün iyi, 2 gün kötü performans gösterdi. Normal ortalamaya baksan net göremezsin. EMA son 5 güne daha fazla ağırlık verdiği için gerçek iyileşmeyi yakalar.",
    whatToDo:
      "Yükseliş trendi + iyi ROAS → Bütçeyi artırmak için doğru zaman. Düşüş trendi → Reklam metnini, fotoğrafı veya fiyatı gözden geçir.",
    tip: "Günlük dalgalanmalara bakıp panik yapmak yerine EMA trendini takip et. Birkaç kötü günün trendi bozmadığını göreceksin.",
  },

  zscore_anomaly: {
    id: "zscore_anomaly",
    emoji: "🚨",
    title: "Z-Score Anomali Tespiti",
    oneLiner: "Bir metrik normalden çok sapınca seni uyarır.",
    whatIs:
      "Z-Score, bir değerin geçmiş verilerinden ne kadar uzaklaştığını ölçer. Çok yüksek veya çok düşük değerler 'anomali' olarak işaretlenir ve seni uyarır.",
    formula: "Z-Score = (Bugünkü Değer − Ortalama) ÷ Standart Sapma",
    howItWorks:
      "Son 30 günün günlük ROAS, CTR veya dönüşüm oranı ortalaması ve standart sapması hesaplanır. Bugünkü değer bu aralığın çok dışına çıkarsa (Z-Score > 2.5), bir şeyler değişmiş demektir.",
    goodValue:
      "Z-Score 0'a yakın → Normal. Pozitif yönde anomali (Z > 2.5) → Olağanüstü iyi gün, ne yaptığını anla ve tekrarla!",
    badValue:
      "Negatif yönde anomali (Z < -2.5) → Bir şeyler yanlış gidiyor. CTR aniden düştüyse listing sıralaması düşmüş olabilir.",
    example:
      "30 gündür günlük CTR ortalamanın %2.1, standart sapman 0.3. Bugün CTR %1.2 geldi. Z-Score = (1.2 - 2.1) ÷ 0.3 = -3.0. Bu çok nadir görülen bir düşüş — Etsy seni listede aşağı çekmiş olabilir, rekabeti kontrol et.",
    whatToDo:
      "Kırmızı uyarı aldığında: 1) Etsy sıralamanı kontrol et, 2) Rakip fiyatlarına bak, 3) Listing başlık/fotoğrafını güncelle, 4) Sezonsal değişiklik mi incele.",
    tip: "Her dalgalanmaya tepki vermek yerine, sadece istatistiksel olarak anlamlı değişikliklere (yüksek Z-Score) odaklan. Bu seni 'verilere boğulmak'tan kurtarır.",
  },

  ad_worthiness: {
    id: "ad_worthiness",
    emoji: "🎯",
    title: "Reklam Uygunluk Skoru (0–100)",
    oneLiner: "Bu ürüne reklam vermeli misin? 5 faktörü analiz eder.",
    whatIs:
      "Her ürün için 0–100 arasında bir skor hesaplarız. Skor, 5 farklı faktörün ağırlıklı toplamıdır. Yüksek skor → reklam mantıklı. Düşük skor → reklam para kaybettirir.",
    howItWorks:
      "5 faktör değerlendirilir:\n• Kâr Marjı (%40+ = 25 puan)\n• Görünürlük + Dönüşüm Dengesi (max 35 puan)\n• ROAS Trendi (yükseliş = 20 puan)\n• Stok Durumu (20+ stok = 10 puan)\n• Mevsimsel Talep (0–10 puan)",
    goodValue:
      "80–100 → Öncelikli Reklam: Hemen bütçe ver, para kazandıracak. 60–79 → Reklam Öneriliyor: İyi ihtimalle, düşük bütçeyle başla.",
    badValue:
      "0–29 → Reklam Verme: Şartlar uygun değil, önce listing'i veya fiyatı düzelt. 30–59 → Test Et: Küçük bütçeyle dene, önce sonuç gör.",
    example:
      "Makrome Duvar Süsü: Kâr marjı %42 (25 puan) + Yükseliş trendi (20 puan) + Düşük görüntülenme iyi dönüşüm (35 puan) + 12 stok (5 puan) = 85 puan → Öncelikli Reklam!",
    whatToDo:
      "Düşük skor aldıysan, hangi faktörün eksik olduğuna bak. Kâr marjı mı düşük? Fiyat artır. Stok mu az? Üret. Trend mi kötü? Listing'i yenile.",
    tip: "Skor 'reklam karlı mı?' sorusuna değil, 'reklam vermek MANTIKLI MI?' sorusuna cevap verir. Düşük stokla reklam vermek, ürün tükenince para israftır.",
  },

  view_analysis: {
    id: "view_analysis",
    emoji: "👁️",
    title: "Görünürlük Analizi",
    oneLiner: "Çok görüntülenme + az satış = listing sorunu, reklam değil!",
    whatIs:
      "Görünürlük analizi, ürünün görüntülenme sayısı ile satış dönüşümünü karşılaştırır. Reklam vermeden önce asıl sorunu teşhis eder.",
    howItWorks:
      "Dört senaryo analiz edilir:\n• Çok görüntü + az satış → Listing kalitesi sorunu (fiyat, fotoğraf, başlık)\n• Az görüntü + iyi dönüşüm → Reklam ile trafik artırılabilir (en iyi senaryo!)\n• Az görüntü + az satış → Hem listing hem reklam birlikte çalışmalı\n• Dengeli → Normal durum",
    goodValue:
      "Az görüntülenme + iyi dönüşüm oranı (>%5): Ürün sattıkça satıyor ama yeterince görülmüyor. Reklam tam burada işe yarar.",
    badValue:
      "Çok görüntülenme + az satış (<2%): İnsanlar tıklıyor ama satın almıyor. Fotoğraf mı kötü? Fiyat mı yüksek? Açıklama mı yetersiz? Reklam vermeden önce bunu düzelt.",
    example:
      "Örme battaniye 30 günde 500 kez görüntülendi ama sadece 3 satış oldu (%0.6 dönüşüm). Reklam versek daha çok trafik getirir ama dönüşüm hâlâ düşük kalır — para boşa gider. Önce listing'i düzelt, sonra reklam ver.",
    whatToDo:
      "Yüksek görüntülenme + düşük dönüşüm: Fotoğrafları değiştir, fiyatı rakiplerle kıyasla, başlığı ve açıklamayı güncelle. Düşük görüntülenme + yüksek dönüşüm: Reklam vermek için ideal zaman!",
  },

  budget_optimizer: {
    id: "budget_optimizer",
    emoji: "🧮",
    title: "Bütçe Optimizasyonu",
    oneLiner: "Sabit bütçeni en verimli ürünlere otomatik dağıtır.",
    whatIs:
      "Gradient Descent algoritması, belirlediğin günlük toplam bütçeyi portföyündeki ürünler arasında ROAS performansına göre otomatik dağıtır.",
    howItWorks:
      "Her ürünün ROAS değeri ağırlık olarak kullanılır. ROAS 3.5x+ olan ürünler %20 daha fazla bütçe alır. 1.5x altı ürünlerin bütçesi otomatik azaltılır veya sıfırlanır. Her adımda sistematik olarak optimize edilir.",
    goodValue:
      "Düzenli çalıştırıldığında toplam portföy ROAS'ı manuel dağılıma göre ortalama %20–35 daha iyi performans gösterir.",
    badValue:
      "Tüm ürünlerin ROAS'ı düşükse optimizer yine en iyisine verir ama genel sonuç kötü olur — ürün portföyünü gözden geçir.",
    example:
      "Günlük $30 bütçen var. 3 ürünün: Kupa (ROAS 4.2), Makrome (ROAS 2.8), Battaniye (ROAS 1.2). Optimizer: Kupa'ya $16, Makrome'ye $11, Battaniye'ye $3. Battaniye düşük olduğu için minimum alır.",
    whatToDo:
      "Öneriyi kabul ettikten sonra haftalık sonuçlara bak. Düzenli olarak çalıştır çünkü ROAS değerleri değişir ve dağılım güncellenmeli.",
    tip: "Bu matematiksel bir öneridir. AI ek olarak 'neden bu kadar?' sorusunu da yanıtlar — hem sayı hem gerekçe birlikte sunulur.",
  },

  ctr: {
    id: "ctr",
    emoji: "🖱️",
    title: "CTR — Tıklama Oranı",
    oneLiner: "Reklamını görenlerden kaçı tıklıyor?",
    whatIs:
      "CTR (Click-Through Rate / Tıklama Oranı), reklamını kaç kişinin gördüğü ve bunlardan kaçının tıkladığını gösterir. Listing'in çekiciliğinin ölçüsüdür.",
    formula: "CTR = (Tıklama ÷ Gösterim) × 100",
    howItWorks:
      "Etsy'de reklamın 1000 kişiye gösterildi ve 15 kişi tıkladı. CTR = (15 ÷ 1000) × 100 = %1.5.",
    goodValue:
      "Etsy'de %1.5–3% arası iyi kabul edilir. %3+ mükemmeldir — ana fotoğrafın ve başlığın çok etkili.",
    badValue:
      "%0.5 altı düşüktür. İnsanlar görüyor ama ilgi göstermiyor — ana fotoğrafı veya başlığı değiştir.",
    example:
      "CTR %0.5'ten %1.5'e çıkartmak, aynı reklam harcamasıyla 3 kat daha fazla müşteri trafiği demektir. İyi bir fotoğraf değişikliği bunu yapabilir.",
    whatToDo:
      "CTR düşükse: Ana fotoğrafı değiştir (lifestyle fotoğrafı dene), başlığa güçlü anahtar kelimeler ekle, fiyatı rakiplerle karşılaştır.",
  },

  attribution: {
    id: "attribution",
    emoji: "🔗",
    title: "Attribution — Gelir Atfı",
    oneLiner: "Hangi reklam, satışı gerçekten sağladı?",
    whatIs:
      "Bir müşteri satın almadan önce birden fazla reklamına tıklamış olabilir. Attribution modeli, bu satışın kredisini reklamlar arasında nasıl paylaştıracağını belirler.",
    howItWorks:
      "4 model kullanılır:\n• İlk Temas (First Touch): Kredi tamamen ilk reklamın. Farkındalık yaratan reklamı ödüllendirir.\n• Son Temas (Last Touch): Kredi tamamen son reklamın. Satışı kapatan reklamı ödüllendirir.\n• Eşit Dağılım (Linear): Tüm reklamlara eşit kredi.\n• Zaman Ağırlıklı (Time-Decay): Satışa yakın reklamlara daha fazla kredi.",
    goodValue: "Çoğu durumda son temas veya zaman ağırlıklı model, Etsy gibi kısa satın alma döngüsü olan platformlarda daha doğru sonuç verir.",
    badValue: "Yanlış attribution modeli, hangi reklamın gerçekten işe yaradığını gizler ve bütçeni yanlış yönetmene neden olur.",
    example:
      "Müşteri önce 'vintage kupa' reklamına tıkladı (reklam A), 2 gün sonra 'el yapımı kupa' reklamına tıkladı (reklam B) ve satın aldı. Son Temas modeli: kredi tamamen reklam B'nin. Zaman Ağırlıklı: reklam B %70, reklam A %30.",
    whatToDo: "İlk aşamada son temas modelini kullan — basit ve Etsy'de çoğunlukla en doğrusu. İleride birden fazla modeli karşılaştır.",
  },
};

export function getExplainer(id: string): Explainer | undefined {
  return EXPLAINERS[id];
}

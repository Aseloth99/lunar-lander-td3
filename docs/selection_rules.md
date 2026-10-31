# Pre-registered selection rules / Önceden yazılmış seçim kuralları

Each rule was written to its own file **before** that stage's test was run (from v4 on, before that stage's training started); reproduced here verbatim, oldest first, in Turkish (the project's working language).


---

<!-- secim_kurali.md -->
# Ana sonuç seçim kuralı — ÖNCEDEN KAYIT

Yazıldığı an: 2026-10-15 10:40 (Aşama 3 eğitimleri yeni başlamışken). O anda Aşama 3'ün hiçbir doğrulama
sonucu yoktu; test tohumlarına (10000–10099) hiç bakılmamıştı. Bu dosya sonradan değiştirilmeyecek.

**Adaylar** (5 tamamlanmış tohumu olan gruplar):
- `sac/fuel2x` — SAC, zoo ayarı + eğitimde yakıt cezası 2× (**eğitim ödülü değiştirildi**, değerlendirme orijinal ödül)
- `td3/tuned` — TD3, Aşama 2 Optuna ayarı
- `ppo/tuned` — PPO, Aşama 2 Optuna ayarı
- `ppo/zoo` — PPO, zoo ayarı

Referans satırları (aday değil, 5 tohum yok): `sac/zoo` (2 tohum), `td3/zoo` (3 tohum).

**Kural** (yalnızca DOĞRULAMA verisi: tohum başına 100 doğrulama bölümü, doğrulamayla seçilmiş kontrol noktası,
deterministik politika). Sırayla, eşitlikte bir sonrakine geçilir:
1. Tohum başına hedefi sağlayan tohum sayısı (ortalama ≥ 280 VE başarı ≥ %99 VE çakılma = 0) — çok olan önde.
2. Birleşik başarı oranı (puan ≥ 200) — yüksek olan önde.
3. Birleşik çakılma oranı — düşük olan önde.
4. Tohum ortalamalarının ortalaması — yüksek olan önde.

Seçilen grup "ana sonuç" olarak raporlanır ve videosu çekilir. Ardından `FROZEN` dosyası oluşturulur ve
TÜM grupların tüm koşuları test tohumlarında bir kez değerlendirilir; hepsi raporlanır (başarısızlar dahil).
Eğer kazanan `sac/fuel2x` olursa, raporda eğitim ödülünün değiştirildiği ve bunun ilk listede olmayan bir yöntem
olduğu (kullanıcı onayıyla eklendiği) açıkça yazılır; orijinal ödülle eğitilen en iyi aday da ayrıca belirtilir.


---

<!-- secim_kurali_v2.md -->
# Ana sonuç seçim kuralı v2 (çakılma %0 hedefi) — ÖNCEDEN KAYIT

Yazıldığı an: 2026-10-16, Aşama 4 başlarken. Bu anda hiçbir v2 kontrol noktası seçimi, bağımsız doğrulama (5600–5999)
veya yeni test (20000+) sonucu yoktu. Bu dosya sonradan değiştirilmeyecek.

**Bağlam:** Eski test (10000–10099) bir kez kullanıldı ve hedef karşılanmadı. Kullanıcı çakılma %0 istedi. Eski test
bölümleri bundan sonra GELİŞTİRME verisidir (çakılma analizi onlarla yapıldı); yeni iddialar yalnızca yeni test
tohumlarına dayanır.

**Adaylar** (5 tamamlanmış tohum): `sac/fuel2x`, `ppo/tuned`, `td3/tuned`, `td3/v2a`, `td3/v2b`.
Her koşu için kontrol noktası `reselect.py` ile yalnızca 5100–5599 doğrulama bölümleriyle seçilir (`best_policy_v2.pt`).

**Gruplar arası sıralama**, seçimde KULLANILMAYAN bağımsız doğrulama kümesiyle yapılır: 5600–5999 (tohum başına 400
bölüm, seçilmiş kontrol noktası, deterministik). Sırayla, eşitlikte bir sonrakine geçilir:
1. Çakılmasız tohum sayısı: 400 bölümde 0 çakılma VE başarı (≥ 200) ≥ %99 olan tohum sayısı — çok olan önde.
2. 5 tohumdaki toplam çakılma sayısı — az olan önde.
3. Birleşik başarı oranı — yüksek olan önde.
4. Tohum ortalamalarının ortalaması — yüksek olan önde.

Seçim yapıldıktan sonra `FROZEN2` oluşturulur ve TÜM aday grupların tüm koşuları yeni test tohumlarında bir kez
değerlendirilir: resmi test 20000–20099 (100 bölüm, ilk hedef tanımıyla aynı) + ek dayanıklılık testi 20100–20999
(900 bölüm). Hepsi raporlanır.


---

<!-- secim_kurali_v3.md -->
# Ana sonuç seçim kuralı v3 (290 denemesi) — ÖNCEDEN KAYIT

Yazıldığı an: 2026-10-17, Aşama 5 eğitimleri yeni başlamışken. Bu anda hiçbir v3 doğrulama sonucu, 6000–6399
bağımsız doğrulaması veya 30000+ test sonucu yoktu. Bu dosya sonradan değiştirilmeyecek.

**Bağlam:** Mevcut şampiyon `td3/v2b` (yeni test 20000–20099: 0/500 çakılma, ort. 283.1). Kullanıcı ortalamayı 290'a
yaklaştırmayı istedi; çakılma %0 şartı korunur. 20000–20999 kullanıldı; yeni iddialar 30000+ test tohumlarına dayanır.

**Adaylar:** `td3/v2b` (mevcut şampiyon), `td3/v3long`, `td3/v3big`, `td3/v3fuel`† (5'er tohum; † eğitim ödülü
değişti, değerlendirme orijinal). Her koşunun kontrol noktası `reselect.py` ile (5100–5599) seçilir.

**Sıralama verisi:** yeni bağımsız doğrulama 6000–6399 (tohum başına 400 bölüm; seçimde kullanılmaz).

**Kural:**
1. **Uygunluk (güvenlik önce):** 5 tohumun hepsinde 0 çakılma VE her tohumda başarı ≥ %99 olan gruplar uygundur.
2. Uygun gruplar arasında **tohum ortalamalarının ortalaması en yüksek** olan seçilir.
3. Hiçbir grup uygun değilse: toplam çakılma az olan, eşitlikte ortalama yüksek olan.

Yani yeni bir çeşit, şampiyonu ancak çakılmasız kalıp ortalamada geçerse yerinden eder. Seçimden sonra `FROZEN3`
oluşturulur ve 4 grubun tüm koşuları 30000–30099 (resmi) + 30100–30999 (ek) test bölümlerinde bir kez ölçülür.


---

<!-- secim_kurali_v4.md -->
# Ana sonuç seçim kuralı v4 (sınırları zorlama) — ÖNCEDEN KAYIT

Yazıldığı an: 2026-10-18, Aşama 6 eğitimleri yeni başlamışken. Bu anda hiçbir Aşama 6 doğrulama sonucu, 6400–6799
bağımsız doğrulaması veya 40000+ test sonucu yoktu. Bu dosya sonradan değiştirilmeyecek.

**Bağlam:** Şampiyon `td3/v3long` (test 30000–30099: ort. 290.0, 0/500 çakılma). Kullanıcı daha uzun eğitimle sınırları
zorlamak istedi: TD3 büyük ağ 800 bin ve 1,6 milyon, TD3 küçük ağ 1,6 milyon, SAC. Çakılma %0 şartı korunur.
30000–30999 kullanıldı; yeni iddialar 40000+ test tohumlarına dayanır.

**Adaylar** (5'er tohum; "@" sonrası kontrol noktası):
`td3/v3long@v2` (şampiyon), `td3/v4big@800k`, `td3/v4big@1600k`, `td3/v4small@800k`, `td3/v4small@1600k`,
`sac/v4@800k`, `sac/v4@1600k`, `ppo/tuned@v2` (PPO temsilcisi).

**Kontrol noktası seçimi:** `reselect.py`, yalnızca 5100–5599 doğrulama bölümleriyle; 800k için 400k–800k aralığı,
1600k için 800k–1,6M aralığı (sabit öğrenme hızı: 1,6M'lik koşunun 800k anı, 800k'lık bir koşuyla aynı yöntemdir).

**Sıralama verisi:** yeni bağımsız doğrulama 6400–6799 (tohum başına 400 bölüm; seçimde kullanılmaz).

**Kural:**
1. **Uygunluk (güvenlik önce):** 5 tohumun hepsinde 0 çakılma VE her tohumda başarı ≥ %99.
2. Uygunlar arasında **tohum ortalamalarının ortalaması en yüksek** olan seçilir.
3. Hiçbiri uygun değilse: toplam çakılma az olan, eşitlikte ortalama yüksek olan.

Seçimden sonra `FROZEN4` oluşturulur ve tüm adayların tüm koşuları 40000–40099 (resmi) + 40100–40999 (ek) test
bölümlerinde bir kez ölçülür; hepsi raporlanır.


---

<!-- secim_kurali_v4_ek.md -->
# Seçim kuralı v4 — EK (kullanıcı isteği, sonuçlardan ÖNCE)

Yazıldığı an: 2026-10-19 10:55. Bu anda Aşama 6'nın hiçbir kontrol noktası seçimi (800k/1600k), bağımsız doğrulama
(6400–6799) veya test (40000+) sonucu YOKTU (kontrol edildi: val5 dosyası 0, seçim dosyası 0, FROZEN4 yok).

Kullanıcı: "Başarı %99,8 olsun istemiyorum, minimum %100 istiyorum."

`secim_kurali_v4.md`'deki uygunluk şartı bu yüzden sıkılaştırıldı:

1. **Uygunluk:** 5 tohumun hepsinde, bağımsız doğrulamanın 400 bölümünün HEPSİNDE puan ≥ 200 (başarı **%100**) VE 0 çakılma.
2. Uygunlar arasında tohum ortalamalarının ortalaması en yüksek olan seçilir.
3. Hiçbiri uygun değilse: önce toplam çakılma az, sonra 200 altı bölüm sayısı az, sonra ortalama yüksek olan.

Geri kalan her şey (adaylar, kontrol noktası seçimi, veri kümeleri, test) `secim_kurali_v4.md`'deki gibidir.
Not: 2000 bölümde hiç 200 altı olmaması çok sıkı bir şarttır; hiçbir aday uygun çıkmayabilir. Bu durumda 3. madde uygulanır
ve raporda açıkça yazılır.


---

<!-- secim_kurali_v5.md -->
# Ana sonuç seçim kuralı v5 (Aşama 7: "hiç çakılmadan 290 üstü?") — ÖNCEDEN KAYIT

Yazıldığı an: 2026-10-20 16:16, Aşama 7 eğitimleri BAŞLAMADAN önce. Bu anda `runs/td3/v5big` yoktu; 6800–7199
bağımsız doğrulaması ve 50000+ test bölümleri hiçbir ajan için çalıştırılmamıştı (`FROZEN5` yok). Bu dosya sonradan
değiştirilmeyecek.

**Bağlam:** Şampiyon `td3/v4big@800k` (test 40000–40999: ort. 289,9, 5000 bölümde 0 çakılma, hiçbir bölüm 200 altı
değil). `td3/v4big@1600k` 5000 bölümde ≈291 ama 6 çakılma. Kullanıcının sorusu: "Hiç çakılmadan 290 üstü çıkacak mı?"

**Hipotez (kanıtlanmadı):** Aşama 6'da öğrenme hızı sabitti; geç dönemdeki nadir bozulmalar buna bağlı olabilir.
Öğrenme hızı sona doğru sıfıra inerse, 1,6 milyonun yakıt verimi korunurken sağlamlık geri gelebilir.

**Yeni çeşit:** `td3/v5big` = `td3/v4big` ile birebir aynı (TD3, ağ [400,300], 1,6M adım, orijinal ödül, aynı
eğitim tohumları 0–4). Tek fark: öğrenme hızı doğrusal azalır, 1e-3 → 0 (`configs/td3_v5big.json`, `lr_linear=true`).

**Adaylar** (5'er tohum; "@" sonrası kontrol noktası):
`td3/v4big@800k` (şampiyon), `td3/v4big@1600k`, `td3/v5big@800k`, `td3/v5big@1600k`.

**Kontrol noktası seçimi:** `reselect.py`, yalnızca 5100–5599 doğrulama bölümleriyle; 800k için 400k–800k aralığı,
1600k için 800k–1,6M aralığı (Aşama 6 ile aynı). Not: v5big'in 800k anında öğrenme hızı henüz yarıdadır; bu an
800 binlik ayrı bir eğitimle aynı yöntem değildir, yalnızca aynı koşunun bir anı olarak raporlanır.
v4big'in seçilmiş modelleri (Aşama 6'dan) olduğu gibi kullanılır.

**Sıralama verisi:** yeni bağımsız doğrulama 6800–7199 (tohum başına 400 bölüm; kontrol noktası seçiminde kullanılmaz).

**Kural** (Aşama 6'nın v4 + EK kuralıyla aynı):
1. **Uygunluk:** 5 tohumun hepsinde, 400 bağımsız doğrulama bölümünün HEPSİNDE puan ≥ 200 (başarı %100) VE 0 çakılma.
2. Uygunlar arasında **tohum ortalamalarının ortalaması en yüksek** olan seçilir.
3. Hiçbiri uygun değilse: önce toplam çakılma az, sonra 200 altı bölüm sayısı az, sonra ortalama yüksek olan.

**Test:** Seçimden sonra `FROZEN5` oluşturulur ve tüm adayların tüm koşuları 50000–50099 (resmi) + 50100–50999 (ek)
test bölümlerinde bir kez ölçülür; hepsi raporlanır.

**"290 sorusu"nun cevabı (önceden tanımlı):** Ana sonuç resmi testte (50000–50099, 500 bölüm) **0 çakılma**,
**başarı %100** ve **tohum ortalamalarının ortalaması ≥ 290,0** verirse cevap EVET; biri bile tutmazsa HAYIR ve
ne kadar uzak kaldığı yazılır. 5000 bölümlük genişletilmiş test (50000–50999) için aynı üç ölçüt ayrıca raporlanır.
Sonuç ne çıkarsa çıksın (v5big kazanmasa da) olduğu gibi yazılır.


---

<!-- secim_kurali_v6.md -->
# Ana sonuç seçim kuralı v6 (Aşama 8: "erken fren", hedef sıfır çakılma + en yüksek puan) — ÖNCEDEN KAYIT

Yazıldığı an: 2026-10-22 08:50, Aşama 8 eğitimleri BAŞLAMADAN önce. (İlk taslak 2026-10-21 14:30'da tek çeşitle
yazılmıştı; o gün eğitim başlatılmadı. Bugün, hâlâ hiçbir eğitim yokken, ikinci çeşit ve sıralama eklendi.) Bu anda
`runs/td3/v6brake` ve `runs/td3/v6soft` yoktu; 7200–9199 bağımsız doğrulaması ve 60000+ test bölümleri hiçbir ajan için
çalıştırılmamıştı (`FROZEN6` yok). Bu dosya bundan sonra değiştirilmeyecek.

**Bağlam:** Aşama 7 ana sonucu `td3/v4big@1600k` (test 50000–50999: ort. 290,1, 5000'de 2 çakılma). Kalan çakılmaların
13'ünün 13'ü sert inişti: yere değme anında dikey hız normal inişlerin en az %99'undan hızlıydı
(`scripts/crash_analysis_v5.py`). Kullanıcı: "Hiç çakılmaması lazım", "en yüksek puan da olsun".

**Yeni çeşitler** (ikisi de `td3/v4big` ile birebir aynı: TD3, ağ [400,300], 1,6M adım, sabit öğrenme hızı, eğitim
tohumları 0–4). Tek fark YALNIZCA EĞİTİM ödülünde: bir bacak bölümde ilk kez yere değdiğinde, temastan hemen önceki
dikey düşüş hızı |vy| v0'ı aşıyorsa k × (|vy| − v0) ceza (`common.TouchdownPenalty`).
- `td3/v6brake`: güçlü ceza, k = 100, v0 = 0,25 (`configs/td3_v6brake.json`)
- `td3/v6soft`: hafif ceza, k = 50, v0 = 0,30 (`configs/td3_v6soft.json`)
Doğrulama ve test HER ZAMAN orijinal ödülle ve değiştirilmemiş ortamla yapılır.

**Adaylar** (5'er tohum): `td3/v4big@800k`, `td3/v4big@1600k`, `td3/v6brake@800k`, `td3/v6brake@1600k`,
`td3/v6soft@800k`, `td3/v6soft@1600k`.

**Kontrol noktası seçimi:** `reselect.py`, yalnızca 5100–5599 doğrulama bölümleriyle; 800k için 400k–800k, 1600k için
800k–1,6M aralığı (Aşama 6–7 ile aynı). v4big'in seçilmiş modelleri olduğu gibi kullanılır.

**Sıralama verisi:** yeni bağımsız doğrulama 7200–9199 (tohum başına **2000** bölüm, grup başına 10 000; çakılma çok nadir
olduğu için öncekilerden 5 kat büyük). Kontrol noktası seçiminde kullanılmaz.

**Kural (önce güvenlik, sonra puan):**
1. **Uygunluk:** 5 tohumun her birinde doğrulama ortalaması ≥ 280 (ilk hedef).
2. Uygunlar arasında önce **toplam çakılma (10 000 bölüm) en az** olan; eşitlikte **200 altı bölüm sayısı en az**;
   eşitlikte **tohum ortalamalarının ortalaması en yüksek** olan seçilir.
3. Hiçbiri uygun değilse aynı sıralama tüm adaylara uygulanır ve raporda yazılır.

**Test:** Seçimden sonra `FROZEN6` oluşturulur; tüm adayların tüm koşuları 60000–60099 (resmi, 100 bölüm) + 60100–61999
(ek, 1900 bölüm) test bölümlerinde bir kez ölçülür (tohum başına 2000, grup başına 10 000); hepsi raporlanır.

**Önceden tanımlı sorular (cevaplar test sonrası olduğu gibi yazılır):**
- **"Sıfır çakılma?"** Ana sonuç genişletilmiş testte (60000–61999, 10 000 bölüm) hiç çakılmazsa EVET; değilse HAYIR ve
  çakılma sayısı. Not: 10 000'de 0 çakılma gerçek oranın sıfır olduğunu kanıtlamaz; kabaca %0,03'ün altında olduğunu
  gösterir.
- **"Puan ne oldu?"** Ana sonucun aynı 10 000 bölümdeki ortalaması; 290'ın üstünde mi.
- Ek (yalnızca tanı, seçimde kullanılmaz): yere değme hızı nasıl değişti; aynı test bölümlerinde v4big'e göre çakılma
  azaldı mı; ceza puanı ne kadar düşürdü.


---

<!-- secim_kurali_v7.md -->
# Seçim kuralı v7 (Aşama 9: "SAC daha iyi skor çıkartamaz mı?") — ÖNCEDEN KAYIT

Yazıldığı an: 2026-10-26, Aşama 9 eğitimleri BAŞLAMADAN önce. Bu anda `runs/sac/v9big` ve `runs/sac/v9lowent` yoktu;
70000–71999 doğrulaması ve 80000–81999 test bölümleri hiçbir ajan için çalıştırılmamıştı (`FROZEN7` yok). Bu dosya
sonradan değiştirilmeyecek.

**Bağlam:** SAC şimdiye kadar hep küçük ağ ([256,256]) ve γ 0,99 ile eğitildi. Aşama 6'da SAC 1,6M çok güvenliydi
(5000 test bölümünde 0 çakılma) ama puanı TD3'ün altındaydı (≈284). TD3'ü iyileştiren büyük ağ ve γ 0,995 SAC'ta hiç
denenmedi. Hipotez (kanıtlanmadı): SAC'ın düşük puanı kısmen eğitimdeki entropi (rastgelelik) teşvikinden geliyor;
deterministik değerlendirmede bu, yakıt israfı olarak görünüyor.

**Yeni çeşitler** (ikisi de: SAC, ağ [400,300], γ 0,995, lr 3e-4 sabit, tampon 1e6, batch 256, τ 0,01,
güncelleme/veri oranı 0,5, 1,6M adım, orijinal ödül, eğitim tohumları 0–4):
- `sac/v9big`: entropi hedefi otomatik (−2) (`configs/sac_v9big.json`)
- `sac/v9lowent`: entropi hedefi −4 (`configs/sac_v9lowent.json`)

**Kontrol noktası seçimi:** `reselect.py`, yalnızca 5100–5599 doğrulama bölümleriyle; 800k için 400k–800k, 1600k için
800k–1,6M aralığı (önceki aşamalarla aynı).

**Adaylar:** SAC: `sac/v9big@800k`, `sac/v9big@1600k`, `sac/v9lowent@800k`, `sac/v9lowent@1600k`.
Karşılaştırma (aynı yeni test, modelleri değişmeden): `td3/v4big@1600k` (en yüksek puanlı TD3), `td3/v6brake@1600k`
(en güvenli TD3), `sac/v4@1600k` (önceki SAC).

**Sıralama verisi:** yeni bağımsız doğrulama 70000–71999 (tohum başına 2000 bölüm). Kontrol noktası seçiminde kullanılmaz.

**Kurallar:**
1. **SAC şampiyonu (puan sorusu):** SAC adayları arasında, 5 tohumun her birinde doğrulama ortalaması ≥ 280 olanlardan
   tohum ortalamalarının ortalaması en yüksek olan. Hiçbiri uygun değilse en yüksek ortalamalı SAC adayı.
2. **Aşama 9 kural seçimi (güvenlik önce, Aşama 8 ile aynı kural):** BÜTÜN adaylar (SAC + karşılaştırma) arasında
   uygunluk = her tohumda ortalama ≥ 280; sonra en az çakılma, eşitlikte en az 200 altı, eşitlikte en yüksek ortalama.

**Test:** Seçimden sonra `FROZEN7` oluşturulur; bütün adayların bütün koşuları 80000–80099 (resmi, 100 bölüm) +
80100–81999 (ek, 1900 bölüm) test bölümlerinde bir kez ölçülür (tohum başına 2000, grup başına 10 000); hepsi raporlanır.

**Önceden tanımlı sorular (cevaplar olduğu gibi yazılır):**
- **"SAC, TD3'ü puanda geçti mi?"** SAC şampiyonunun genişletilmiş testteki (10 000 bölüm) ortalaması,
  `td3/v4big@1600k`'nın aynı bölümlerdeki ortalamasından yüksekse EVET; değilse HAYIR ve fark yazılır.
- **"Büyük ağ SAC'ı iyileştirdi mi?"** SAC şampiyonu, `sac/v4@1600k`'dan aynı bölümlerde yüksekse EVET.
- **"Düşük entropi işe yaradı mı?"** Aynı uzunlukta (`@1600k`) `sac/v9lowent`, `sac/v9big`'den aynı bölümlerde
  yüksekse EVET.
- Ek (tanı): çakılma sayıları, yakıt ve iniş süresi.


---

<!-- secim_kurali_v8.md -->
# Seçim kuralı v8 (Aşama 10: "SAC daha agresif olsun; hem yüksek puan alsın hem çakılmasın") — ÖNCEDEN KAYIT

Yazıldığı an: 2026-10-26, Aşama 10 eğitimleri BAŞLAMADAN önce. Bu anda `runs/sac/v10brake` ve `runs/sac/v10soft`
yoktu; 90000–91999 doğrulaması ve 100000–101999 test bölümleri hiçbir ajan için çalıştırılmamıştı (`FROZEN8` yok).
Aşama 9 sürüyordu (ilk 6 eğitim ~%57); Aşama 9'un bağımsız doğrulaması (70000–71999) ve testi (80000–81999) henüz
çalıştırılmamıştı. Aşama 9'dan görülen tek bilgi, eğitim sırasındaki kısa doğrulama eğrileriydi (5000–5019, 20 bölüm);
yalnızca eğitimin sağlıklı gittiğini görmek için bakıldı. Bu dosya sonradan değiştirilmeyecek.

**Bağlam:** TD3'te eğitimde sert inişe ek ceza ("erken fren", Aşama 8) aynı 10 000 test bölümünde çakılmayı 8'den 1'e
indirdi, bedeli ~0,8 puandı; hafif çeşidin 800 bin adımlık hali 20 000 doğrulama + test bölümünde hiç çakılmadı. SAC'ta
bu hiç denenmedi. Kullanıcı isteği: SAC'ı daha agresif yapmak (puan için) ve aynı anda çakılmayı önlemek.

**Yeni çeşitler** (ikisi de `sac/v9lowent`'in aynısı: SAC, ağ [400,300], γ 0,995, entropi hedefi −4 (agresif: daha az
rastgelelik), lr 3e-4 sabit, tampon 1e6, batch 256, τ 0,01, güncelleme/veri oranı 0,5, 1,6M adım, eğitim tohumları 0–4;
tek fark YALNIZCA eğitimde sert iniş cezası, `common.TouchdownPenalty`; değerlendirme her zaman orijinal ödülle):
- `sac/v10brake`: güçlü ceza, |vy| > 0,25 ise 100 × fark (`configs/sac_v10brake.json`; `td3/v6brake` ile aynı ceza)
- `sac/v10soft`: hafif ceza, |vy| > 0,30 ise 50 × fark (`configs/sac_v10soft.json`; `td3/v6soft` ile aynı ceza)

**Kontrol noktası seçimi:** `reselect.py`, yalnızca 5100–5599 doğrulama bölümleriyle; 800k için 400k–800k, 1600k için
800k–1,6M aralığı (önceki aşamalarla aynı).

**Adaylar (11):**
- Yeni: `sac/v10brake@800k`, `sac/v10brake@1600k`, `sac/v10soft@800k`, `sac/v10soft@1600k`.
- Karşılaştırma (modelleri değişmeden, aynı yeni testte): `td3/v4big@1600k` (en yüksek puanlı TD3), `td3/v6brake@1600k`
  (en güvenli TD3), `td3/v6soft@800k` (20 000 bölümde sıfır çakılmalı TD3), Aşama 9'un dört SAC adayı
  `sac/v9lowent@800k`, `sac/v9lowent@1600k` (yeni çeşitlerin cezasız hali), `sac/v9big@800k`, `sac/v9big@1600k`.

**Sıralama verisi:** yeni bağımsız doğrulama 90000–91999 (tohum başına 2000 bölüm). Kontrol noktası seçiminde
kullanılmaz.

**Kurallar** (uygunluk her ikisinde de: 5 tohumun her birinde doğrulama ortalaması ≥ 280):
1. **Aşama 10 seçimi (frenli SAC'ların en iyisi):** 4 yeni aday arasında uygun olanlardan en az çakılma, eşitlikte en az
   200 altı, eşitlikte en yüksek ortalama. Hiçbiri uygun değilse aynı sıralama uygunluk aranmadan.
2. **Aşama 10 kural seçimi (genel, güvenlik önce; Aşama 8–9 ile aynı kural):** BÜTÜN 11 aday arasında uygun olanlardan en
   az çakılma, eşitlikte en az 200 altı, eşitlikte en yüksek ortalama.

**Test:** Seçimden sonra `FROZEN8` oluşturulur; bütün adayların bütün koşuları 100000–100099 (resmi, 100 bölüm) +
100100–101999 (ek, 1900 bölüm) test bölümlerinde bir kez ölçülür (tohum başına 2000, aday başına 10 000); hepsi
raporlanır.

**Önceden tanımlı sorular (cevaplar olduğu gibi yazılır; hepsi aynı 10 000 test bölümünde):**
- **"Hem yüksek puan hem sıfır çakılma?"** Kural 1'in seçtiği aday için: ortalaması `td3/v4big@1600k`'nın
  ortalamasından düşük değilse VE hiç çakılmadıysa EVET. Değilse HAYIR; iki şartın her biri ayrı ayrı yazılır.
- **"Fren SAC'ta ne kazandırdı, neye mal oldu?"** `sac/v10brake@1600k` ve `sac/v10soft@1600k`, cezasız hali
  `sac/v9lowent@1600k` ile: çakılma sayıları ve ortalama farkı. (800k için de aynı karşılaştırma ayrıca yazılır.)
- **"Güçlü mü hafif mi?"** `@1600k`'da daha az çakılan; eşitlikte ortalaması yüksek olan.
- **"Frenli SAC, en güvenli TD3 kadar güvenli mi?"** Kural 1'in seçtiği adayın çakılması ≤ `td3/v6brake@1600k`'nınki
  ise EVET.
- Ek: Aşama 9 adayları ve TD3'ler için bu, üçüncü bağımsız test (Aşama 8 ve 9 testlerinden sonra); sonuçlar karşılaştırılır.
- Ek (tanı): yakıt, iniş süresi, yere değme hızı (en sert %5), çakılmaların yeniden oynatılması.

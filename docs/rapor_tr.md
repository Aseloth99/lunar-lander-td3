# Ay'a İniş Ajanı (LunarLander, Derin Pekiştirmeli Öğrenme)

> **Not:** Bu, projenin 10 aşamalık tam Türkçe raporudur (geliştirme sırasında yazıldı). Rapordaki dosya yolları geliştirme klasörüne aittir; o dosyaların hepsi `data/all_stages.tar.gz` arşivinde. Kısa özet: [README_TR.md](../README_TR.md).


Bu proje, bilgisayarın deneme-yanılma ile **bir uzay aracını Ay yüzeyindeki pistine yumuşakça indirmeyi** öğrenmesini
konu alır. Ortam: Gymnasium `LunarLander-v3`, **sürekli kontrol** (motor gücü kademeli ayarlanabilir).


## Kısaca sonuç (güncel: Aşama 10, 30.10.2026)

**İki şampiyon.** Bütün aşamalardan sonra öne çıkan iki ajan var, ikisi de TD3. Biri en yüksek puanı alıyor, öteki hiç
çakılmıyor. İkisi de hiç görülmemiş aynı 10 000 test bölümünde ölçüldü (100000–101999):

| | En yüksek puan | Hiç çakılmayan (ana sonuç) |
|---|---|---|
| Ajan | **TD3 büyük ağ · 1,6 milyon adım** | **TD3 erken fren (hafif ceza)† · 800 bin adım** |
| Ortalama puan | **290,6** | 289,5 |
| Çakılma | 5 / 10 000 | **0 / 10 000** |
| 200'ün altında kalan bölüm | 6 | **0** |
| En kötü bölüm | 33 | **239** |
| Hedef her tohumda tuttu mu?‡ | 5 tohumdan 1'inde | **5 tohumun 5'inde** |
| Bugüne kadarki bütün bağımsız ölçümlerde çakılma | 74 000 bölümde 35 (~2000'de 1) | **40 000 bölümde 0** |

† Eğitim sırasında yere hızlı değmeye ek ceza verildi ("erken fren", Aşama 8). Test oyunun orijinal kurallarıyla yapıldı.
‡ Hedef: her tohumda ortalama ≥ 280, bölümlerin ≥ %99'u ≥ 200 ve hiç çakılma yok.

- **Puan farkı çok küçük: 1,1.** Önceki testlerde de böyleydi: en yüksek puanlı üç ayrı testte (Aşama 8, 9, 10)
  290,6–290,7, hiç çakılmayan iki ayrı testte (Aşama 8, 10) 289,5–289,6 aldı.
- **Güvenlik farkı net.** En yüksek puanlı ajan yaklaşık 2000 bölümde bir çakılıyor. Bu testteki 5 çakılmanın hepsinde
  araç iki ayağıyla pistteydi; yere değdikten 5–9 adım sonra düştü. Yere sert değiyor: en sert %5 inişte yere değme hızı
  0,40 (hiç çakılmayanda 0,34). Hiç çakılmayan ajan Aşama 8'den beri 4 ayrı bağımsız ölçümde (2 doğrulama + 2 test,
  toplam 40 000 bölüm) bir kez bile çakılmadı.
- **Hangisi "en iyi"?** Önceden yazılan kural "önce en az çakılma, sonra puan" der. Bu yüzden ana sonuç "hiç çakılmayan"
  oldu. Puan öne konursa "en yüksek puan" seçilir.





### Aşama 10'un sorusu: "SAC daha agresif olsun; hem yüksek puan alsın hem çakılmasın"

SAC'ın en iyi çeşidine (büyük ağ, düşük entropi) TD3'te işe yarayan "erken fren" eklendi: eğitimde yere hızlı değmeye
ek ceza. İki çeşit eğitildi: güçlü ceza ve hafif ceza, 5'er tohum, 1,6 milyon adım. Eğitimden önce yazılmış sorulara
cevaplar (aynı 10 000 test bölümü):

- **"Hem yüksek puan hem sıfır çakılma?" HAYIR.** Kuralın seçtiği frenli SAC (güçlü ceza · 1,6 milyon) hiç çakılmadı,
  bu şart sağlandı. Ama ortalaması 285,0, yani en yüksek puanlı TD3'ün 5,7 altında; puan şartı sağlanmadı.
- **"Fren SAC'ta ne kazandırdı, neye mal oldu?"** 1,6 milyon adımda çakılmada kazanç yok, çünkü frensiz SAC da bu testte
  hiç çakılmadı. Bedeli ~1 puan: 286,1'den güçlü cezada 285,0'a, hafif cezada 285,2'ye. 800 bin adımda fren zarar verdi:
  güçlü 2, hafif 11 çakılma (frensiz 0), ortalama da düştü.
- **"Güçlü mü hafif mi?" Hafif, kıl payı.** İkisi de hiç çakılmadı; ortalaması yüksek olan hafif (285,2'ye 285,0).
- **"Frenli SAC, en güvenli TD3 kadar güvenli mi?" EVET.** İkisi de 0 çakılma.

| Çeşit (test 100000–101999) | Resmi test ort. ± %95 GA (500) | Çakılma (500) | 10 000'de ort. | 10 000'de çakılma | 10 000'de 200 altı | En kötü bölüm | Doğrulamada çakılma (10 000) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **TD3 erken fren (hafif ceza)† · 800 bin** — hiç çakılmayan (ana sonuç) | 289.6 ± 0.9 | **0** | 289.5 | **0** | **0** | **238.8** | **0** |
| **TD3 büyük ağ · 1,6 milyon** — en yüksek puan | **290.9 ± 0.4** | **0** | **290.6** | 5 | 6 | 33.1 | 2 |
| TD3 erken fren (güçlü ceza)† · 1,6 milyon (Aşama 8'in ana sonucu) | 290.0 ± 0.6 | **0** | 289.9 | **0** | 1 | 185.4 | **0** |
| SAC frenli (güçlü ceza)† · 1,6 milyon — Aşama 10'un frenli SAC seçimi | 285.2 ± 2.7 | **0** | 285.0 | **0** | 2 | 175.4 | **0** |
| SAC frenli (hafif ceza)† · 1,6 milyon | 285.2 ± 3.7 | **0** | 285.2 | **0** | 6 | 167.7 | 1 |
| SAC büyük ağ, düşük entropi · 1,6 milyon (frensiz hali) | 286.3 ± 2.4 | **0** | 286.1 | **0** | **0** | 213.8 | 1 |
| SAC büyük ağ · 1,6 milyon (Aşama 9'un ana sonucu) | 285.5 ± 3.4 | **0** | 285.3 | **0** | **0** | 231.5 | 1 |

800 bin adımdaki dört SAC'ın hiçbiri hedefi tutturamadı (ortalama 229–280, 10 000 bölümde 0–11 çakılma). 11 adayın
hepsinin tablosu `results/final_test8_1000/` klasöründe ve 3'teki sayfada.

**Ne öğrendik?**
- **Fren SAC'ta inişi gerçekten yumuşattı, ama sonuca yansımadı.** En sert %5 inişte yere değme hızı 0,34'ten 0,24'e
  indi (güçlü ceza). SAC zaten neredeyse hiç çakılmadığı için bu bir kazanç olarak görünmedi. Yakıt biraz arttı (yakıta
  giden puan 24,0 → 25,6), puan ~1 düştü.
- **SAC, TD3'ün ~5 puan gerisinde kaldı.** Daha çok yakıt yakıyor (yakıta giden puan ~24–26, TD3'te ~21–22) ve daha
  yavaş iniyor (~180 adım, TD3 ~156–161).
- **Sonuçlar tekrarlanıyor.** TD3'ler ve Aşama 9'un SAC'ları için bu üçüncü bağımsız test oldu. Ortalamalar testten
  teste en fazla 0,2 puan oynadı (en yüksek puanlı TD3: 290,68 · 290,66 · 290,64). Çakılma sayıları ise küçük ve şansa
  bağlı oynuyor (aynı ajan: 8 · 3 · 5).
- Kontrol: `scripts/verify_v8.py` hepsini geçti. İki seçim ham doğrulama verisinden yeniden yapıldı, sıralamalar aynı
  çıktı. Ana sonucun ve frenli SAC seçiminin 500'er test bölümü yeniden oynatıldı, puanlar birebir aynı çıktı. Tablolar:
  `results/final_test8/`, `results/final_test8_1000/`, `results/final_val9/`; tanı: `results/tani_v8.txt`; frenli
  SAC'ın videosu: `results/frenli_sac_v8.gif`.

## Önceki sonuç (Aşama 9: "SAC daha iyi skor çıkaramaz mı?", 28.10.2026)

Soru: **"SAC daha iyi skor çıkaramaz mı?"** SAC'a, TD3'ü iyileştiren iki şey verildi: büyük ağ ([400,300]) ve daha uzağı
gören hedef (γ 0,995). Çeşitlerden birinde ayrıca eğitimdeki rastgelelik azaltıldı (düşük entropi). Eğitimden önce
yazılmış ölçütlere göre cevaplar:

- **"SAC, TD3'ü puanda geçti mi?" HAYIR.** En iyi SAC (büyük ağ, düşük entropi, 1,6 milyon) aynı 10 000 test bölümünde
  ortalama **286,0** aldı. En yüksek puanlı TD3 ise **290,7** aldı (fark −4,7).
- **"Büyük ağ SAC'ı iyileştirdi mi?" EVET, biraz:** eski SAC 284,6 → 286,0 (+1,4).
- **"Düşük entropi işe yaradı mı?" EVET, çok az:** 285,4 → 286,0 (+0,6).

**Sürpriz: yeni ana sonuç bir SAC.** Aşama 8'in kuralı aynen uygulandı: önce en az çakılma, sonra puan. Doğrulamada
(70000–71999, 10 000 bölüm) en az çakılan aday **SAC büyük ağ · 1,6 milyon** oldu: 1 çakılma. İki TD3'ün ikisi de 2
kez çakıldı. 1'e 2 farkı şansla da açıklanabilecek kadar küçük. Ama kural önceden yazıldığı için olduğu gibi uygulandı.

- **Resmi test** (80000–80099, 5 tohum × 100 bölüm): ortalama **286,4 ± 3,6**, **0 çakılma**, her bölüm ≥ 200 (en
  kötüsü 242). İlk hedef 5 tohumun 5'inde sağlandı.
- **Genişletilmiş test** (80000–81999, 5 × 2000 = 10 000 bölüm): ortalama **285,4 ± 3,3**, **1 çakılma**, 1 bölüm 200
  altında. Aşama 8'in ana sonucu (TD3 erken fren) da aynı bölümlerde 1 kez çakıldı, ama ortalaması 4,4 puan yüksek (289,8).

| Çeşit (test 80000–81999) | Resmi test ort. ± %95 GA (500) | Çakılma (500) | 10 000'de ort. | 10 000'de çakılma | 10 000'de 200 altı | Doğrulamada çakılma (10 000) |
|---|---:|---:|---:|---:|---:|---:|
| **SAC büyük ağ · 1,6 milyon** — ana sonuç (güvenlik önce) | **286.4 ± 3.6** | **0** | **285.4** | **1** | 1 | **1** |
| SAC büyük ağ, düşük entropi · 1,6 milyon — SAC şampiyonu (en yüksek puan) | 287.3 ± 2.1 | 0 | 286.0 | 2 | 2 | 3 |
| SAC büyük ağ, düşük entropi · 800 bin | 280.4 ± 7.4 | 0 | 279.5 | 2 | 6 | 4 |
| SAC büyük ağ · 800 bin | 230.3 ± 148.3 | 0 | 228.9 | 8 | 2007 | 7 |
| SAC eski (küçük ağ) · 1,6 milyon | 285.8 ± 1.3 | 0 | 284.6 | **0** | 1 | 2 |
| TD3 büyük ağ · 1,6 milyon (en yüksek puan) | 291.7 ± 0.3 | 0 | **290.7** | 3 | 3 | 2 |
| TD3 erken fren (güçlü ceza)† · 1,6 milyon (Aşama 8'in ana sonucu) | 290.6 ± 1.3 | 0 | 289.8 | 1 | 2 | 2 |

† Eğitim sırasında yere hızlı değmeye ek ceza verildi. Test her satırda oyunun orijinal kurallarıyla yapıldı.

**Ne öğrendik?**
- **SAC neden geride?** Daha çok yakıt yakıyor: yakıta giden puan bölüm başına ~24–26, TD3'te ~21. Ayrıca daha yavaş
  iniyor (~180 adım, TD3 ~156). Aradaki puan farkının çoğu buradan geliyor.
- **SAC'ın bilinen tuzağı görüldü.** "Büyük ağ" çeşidinin 3. tohumu ~1,2 milyon adıma kadar hiç inmedi. Çakılma
  cezasından kaçmak için havada asılı kalıp sürenin dolmasını bekledi. 800 bin adımdaki hâli 2000 doğrulama bölümünün
  hepsinde 200'ün altında kaldı (ortalama 15). Sonra inmeyi öğrendi ve 1,6 milyonda ortalaması 281'e çıktı (en zayıf
  tohum). 800 binde durulsaydı bu çeşit hedefi tutturamazdı.
- **Testte en az çakılan yine eski küçük SAC oldu:** 10 000 test bölümünde 0 çakılma (5 tohumun 5'i çakılmasız). Ama
  doğrulamada 2 kez çakıldığı için kural onu seçmedi. Çakılmalar o kadar nadir ki (10 000 bölümde 0–3), adaylar
  arasındaki farkların çoğu şans.
- **Sırada Aşama 10:** SAC'a TD3'te işe yarayan "erken fren" eklendi. Amaç hem yüksek puan hem çakılmasızlık.
- Kontrol: `scripts/verify_v7.py` hepsini geçti. İki seçim ham doğrulama verisinden yeniden yapıldı. Ana sonucun ve SAC
  şampiyonunun 500'er test bölümü yeniden oynatıldı, puanlar birebir aynı çıktı. Tablolar: `results/final_test7/`,
  `results/final_test7_1000/`, `results/final_val8/`; tanı: `results/tani_v7.txt`.



## Önceki sonuç (Aşama 8: "erken fren çakılmayı sıfırlar mı?", 24.10.2026)

Soru: **"Erken fren çakılmayı sıfırlar mı?"** Eğitimden önce yazılmış ölçüte göre cevap: **HAYIR, ama neredeyse.** Kurala
göre seçilen ajan (TD3 büyük ağ + güçlü erken fren cezası†, 1,6 milyon adım), hiç görülmemiş **10 000 test bölümünde
yalnızca 1 kez** çakıldı. Önceki ana sonuç (aynı ağ, cezasız) **aynı 10 000 bölümde 8 kez** çakıldı. Yani çakılma 8 kat
azaldı, ortalama ise yalnızca 0,7 puan düştü.

- **Resmi test** (60000–60099, 5 tohum × 100 bölüm): ortalama **292,8 ± 0,6**, **0 çakılma**, her bölüm ≥ 200. Bu 100'lük
  küme kolay çıktı: bütün çeşitler burada, 2000'lik ortalamalarından ~3 puan yüksek aldı.
- **Genişletilmiş test** (60000–61999, 5 × 2000 = 10 000 bölüm): ortalama **289,9 ± 0,7**, **1 çakılma (%0,01)**,
  3 bölüm 200'ün altında. Doğrulama ve test birlikte 20 000 bölümde toplam 1 çakılma.
- İlk hedef (her tohumda ortalama ≥ 280, ≥ %99 başarı, 0 çakılma; resmi test) yine **5 tohumun 5'inde** sağlandı.
- Aşama 7'nin sorusu ("hiç çakılmadan 290 üstü?", resmi teste göre) bu turda **EVET** çıktı: 292,8, 0 çakılma, 0 bölüm
  200 altı. Ama bu kolay bir 100'lük kümeydi; asıl ölçü olan 10 000 bölümde ortalama 289,9 ve 1 çakılma var.

| Çeşit (test 60000–61999) | Resmi test ort. ± %95 GA (500) | Çakılma (500) | 10 000'de ort. | 10 000'de çakılma | 10 000'de 200 altı | En sert %5 yere değme hızı |
|---|---:|---:|---:|---:|---:|---:|
| **TD3 erken fren (güçlü ceza)† · 1,6 milyon** — ana sonuç | **292.8 ± 0.6** | **0** | **289.9** | **1** | 3 | 0.29 |
| TD3 erken fren (hafif ceza)† · 800 bin | 292.2 ± 1.2 | 0 | 289.6 | **0** | 0 | 0.34 |
| TD3 erken fren (hafif ceza)† · 1,6 milyon | 293.2 ± 0.8 | 0 | 290.4 | 3 | 5 | 0.36 |
| TD3 erken fren (güçlü ceza)† · 800 bin | 291.6 ± 1.2 | 0 | 288.7 | 1 | 12 | 0.30 |
| TD3 büyük ağ · 1,6 milyon (önceki ana sonuç) | 293.6 ± 0.4 | 0 | 290.7 | 8 | 9 | 0.40 |
| TD3 büyük ağ · 800 bin | 292.3 ± 1.0 | 0 | 289.4 | 3 | 3 | 0.36 |

† Eğitim sırasında, yere belli bir hızdan hızlı değmeye ek ceza verildi. Test her satırda oyunun orijinal kurallarıyla
yapıldı. Yere değme hızı: temastan hemen önceki dikey hız; tohum başına 50 test bölümünden.

**Ne öğrendik?**
- **Erken fren işe yarıyor.** En sert inişler belirgin yavaşladı (en sert %5: 0,40 → 0,29) ve aynı test bölümlerinde
  çakılma 8'den 1'e indi. Bedeli 0,7 puan.
- **Kalan tek çakılma çok zor bir başlangıçta oldu.** Bölüm 61049, üç farklı ajanı birden düşürdü.
- **Hafif cezalı çeşit (800 bin) 20 000 bölümün hiçbirinde çakılmadı** (doğrulama 0/10 000, test 0/10 000; ortalama
  289,6). Önceden yazılan kural onu değil, doğrulamada ortalaması daha yüksek olan güçlü cezalıyı seçti. Test sonucunu
  gördükten sonra seçimi değiştirmiyoruz; yalnızca raporluyoruz.
- **Güçlü ceza 800 binde bazen inip durmuyor:** 200 altı 12 bölümün çoğu çakılma değil, 1000 adım sınırına takılma.
- Kontrol: `scripts/verify_v6.py` (hepsi geçti; ana sonucun 500 test bölümü yeniden oynatıldı, puanlar birebir aynı).
  Tablolar: `results/final_test6/`, `results/final_test6_1000/`, `results/final_val7/`; tanı: `results/yere_degme_v6.txt`.



## Önceki sonuç (Aşama 7: "hiç çakılmadan 290 üstü?", 21.10.2026)

Soru: **"Hiç çakılmadan 290 üstü olur mu?"** Cevap (eğitimden önce yazılmış ölçüte göre): **HAYIR, kıl payı.** İki
şart ayrı ayrı sağlandı, ama aynı anda sağlanmadı:

- Resmi testte (hiç görülmemiş 50000–50099, 5 tohum × 100 bölüm) ana sonuç **0 çakılma** verdi, **her bölüm ≥ 200**;
  ama ortalama **287,2** (290'ın altında).
- Genişletilmiş testte (5 tohum × 1000 bölüm) ortalama **290,1** (290'ın üstünde); ama 5000 bölümde **2 çakılma** var.
- İlk hedef (her tohumda ortalama ≥ 280, ≥ %99 başarı, 0 çakılma) yine **5 tohumun 5'inde** sağlandı.

**Ne denendi:** Aşama 6'nın büyük ağı aynen, tek fark öğrenme hızının sona doğru sıfıra inmesi (`td3/v5big`, 5 tohum,
1,6 milyon adım, ≈ 13 saat). Seçim kuralı ve "290 sorusu"nun ölçütü eğitimden önce yazıldı
(`results/secim_kurali_v5.md`). Test kümesi daha önce hiç kullanılmamıştı. Kural ana sonuç olarak Aşama 6'nın
1,6 milyonluk ajanını seçti: yeni bağımsız doğrulamada (6800–7199, 2000 bölüm) 0 çakılma ve en yüksek ortalama (291,0).

| Çeşit | Resmi test ort. ± %95 GA (500 bölüm) | Çakılma | 5000 bölümde ort. | 5000'de çakılma | 5000'de 200 altı |
|---|---:|---:|---:|---:|---:|
| **TD3 büyük ağ · 1,6 milyon** — ana sonuç (kurala göre) | **287.2 ± 0.4** | **0/500** | 290.1 ± 0.3 | 2 | 2 |
| TD3 büyük ağ + azalan öğrenme hızı · 1,6 milyon (yeni) | 286.3 ± 0.4 | 0/500 | 289.3 ± 0.3 | 1 | 1 |
| TD3 büyük ağ · 800 bin (önceki şampiyon) | 285.8 ± 0.8 | 0/500 | 288.7 ± 0.9 | 2 | 2 |
| TD3 büyük ağ + azalan öğrenme hızı · 800 bin (yeni) | 284.6 ± 0.8 | 0/500 | 287.4 ± 0.7 | 2 | 5 |

**Ne öğrendik?**
- **Azalan öğrenme hızı işe yaramadı.** Yeni çeşit ortalamada ~1 puan geride. Çakılma farkı (1'e karşı 2) çok az sayıda
  olduğu için anlamlı değil. Hipotez desteklenmedi.
- **İlk 100 test bölümü bu kez zor çıktı.** Dört çeşidin hepsi 50000–50099'da, 1000 bölümlük ortalamasından 2,8–3,0
  puan düşük aldı. Bu fark ajandan değil, bölümlerin zorluğundan geliyor. Resmi testte 290'ın altında kalmanın büyük
  kısmı bu şans.
- **Çok nadir çakılma hâlâ var.** Önceki şampiyonun (800 bin) "5000'de 0 çakılma" sonucu bu testte tekrarlanmadı
  (2/5000). İki testin toplamında (10 000 bölüm): 800 bin **2**, 1,6 milyon **8** çakılma (Aşama 6 testinde 6). Kural
  1,6 milyonu seçti, ama uzun vadede **800 bin biraz daha güvenli, 1,6 milyon ~1,4 puan daha yüksek**. İkisi de
  ≈ %0,02–0,08 düzeyinde çakılıyor.
- Aşağıdaki "gerçekçi tavan ≈ 290" tahmini yine tuttu: en iyi ajanlar 290 civarında duruyor.

**Neden hâlâ nadiren çakılıyor?** Aşama 6–7 testlerindeki 13 çakılmanın hepsi yeniden oynatıldı. Bu test bölümleri
zaten kullanılmıştı; burada yalnızca tanı için oynatıldı, seçim yapılmadı (`scripts/crash_analysis_v5.py`,
`results/cakilma_analizi_v5.csv`).
- 13'ünün 13'ü pistin üstünde, bacaklar yere değdikten 5–10 adım sonra oldu. Ekrandan çıkma yok, araç yan yatmış
  değil (açı en çok ~10°).
- Fark **yere değme hızında**. Çakılan bölümlerde araç yaklaşık **iki kat hızlı düşerek** yere değdi: dikey hız
  ortancası −0,49; normal 1000 inişte −0,23 ve normal inişlerin %95'i −0,35'ten yavaş. 13 çakılmanın 13'ü de normal
  inişlerin en az %99'undan hızlı düşüyordu; çoğu yatayda da hızlıydı. Bacaklar bu darbeyi karşılayamıyor, gövde yere
  çarpıyor; ortam bunu çakılma sayıyor.
- **Neden böyle:** Yüksek puanlı ajanlar yakıt tasarrufu için "hızlı düş, son anda fren yap" öğrenmiş. Bazı zor
  başlangıçlarda son an freni yetmiyor. Bir bölüm (50359) 5 farklı ajanı birden düşürdü; yani bu durum belirli zor
  başlangıçlara bağlı.
- Bu, **yakıt (puan) ile güvenlik payı arasında bir takas**: 1,6 milyonluk ajan daha az yakıt harcıyor ve biraz daha
  sık çakılıyor. Daha erken frenlemek çakılmayı azaltabilir ama puanı düşürür (denenmedi).
- Ayrıca 3 bölümde (azalan hız · 800 bin, tohum 3) araç indi ama yan motoru ateşlemeyi sürdürdü, hiç durmadı ve
  1000 adım sınırına takıldı (puan 177–191; çakılma değil).

**Başkalarıyla karşılaştırma (internetteki sonuçlar).** Resmî bir rekor tablosu yok; Gym'in eski liderlik tablosu
puanı değil öğrenme hızını ölçüyordu. Bulabildiğimiz doğrulanabilir yayımlanmış sonuçlar:

| Kaynak | Sürüm | Nasıl ölçülmüş | Ortalama ± std (bölüm başına) |
|---|---|---|---:|
| **Bu proje: TD3 büyük ağ · 1,6 milyon** | v3, sürekli | 5 eğitim tohumu × 1000 yeni bölüm, deterministik | **290,1 ± 19,9** |
| [rl-baselines3-zoo](https://github.com/DLR-RM/rl-baselines3-zoo/blob/master/benchmark.md), TQC (oradaki en iyi) | v2, sürekli | tek koşu, 706 bölüm | 278,0 ± 25,5 |
| rl-baselines3-zoo, PPO | v2, sürekli | tek koşu, 526 bölüm | 270,9 ± 32,1 |
| rl-baselines3-zoo, SAC | v2, sürekli | tek koşu, 672 bölüm | 260,4 ± 65,5 |
| rl-baselines3-zoo, TD3 | v2, sürekli | tek koşu, 337 bölüm | 207,5 ± 67,6 |

- [Hugging Face Deep RL kursu liderlik tablosunda](https://huggingface.co/spaces/huggingface-projects/Deep-Reinforcement-Learning-Leaderboard)
  (ayrık sürüm) tek modeller için 311–331 görülüyor. Ama bunlar yükleyenin kendi bildirdiği, ~10 bölümlük sonuçlar;
  karşılaştırılabilir değil.
- v2 ile v3 birebir aynı değil (v3'te bazı hatalar düzeltildi); karşılaştırma kabadır.
- Bizim en yüksek tek bölümümüz 332,5; 5000 test bölümünün %35'i ≥ 300.
- **Sonuç:** Ortalama ≈ 290, bulabildiğimiz doğrulanabilir sonuçların üstünde ve gerçekçi tavana (kaba tahmin
  ≈ 290–300) yakın. Resmî tablo olmadığı için "rekor" demek doğru olmaz, ama "üst düzey" demek haklı. Ayrıca
  kaynakların neredeyse hiçbiri çakılma oranı vermiyor; biz 10 000 bölümde %0,02–0,08 ölçtük.



## Önceki sonuç (Aşama 6, 19.10.2026)

En iyi yöntem **TD3 büyük ağ, 800 bin adım** oldu (ağ [400,300]; Aşama 5'te 400 bin adımda çakılan büyük ağ bu kez iki
kat uzun eğitildi). Ana sonuç testten önce yazılmış kurala göre seçildi: önce **0 çakılma ve %100 başarı**
(`results/secim_kurali_v4.md` + sonuçlardan önce eklenen `results/secim_kurali_v4_ek.md`), sonra ortalama. Hiç
görülmemiş en yeni test bölümlerinde (40000–40099), 5 tohumun hepsinde:

- **0 çakılma (0/500)**, **başarı %100** (her bölüm ≥ 200; en kötü 243), ortalama **288,5 ± 1,1**.
- İlk hedefin tamamı (ortalama ≥ 280 + ≥ %99 başarı + 0 çakılma) **5 tohumun 5'inde** sağlandı.
- Genişletilmiş test (tohum başına 1000 bölüm, 40000–40999): ortalama **289,9 ± 0,9**, **5000 bölümde 0 çakılma** ve
  **hiçbir bölüm 200'ün altında değil** (en kötü 239).

| Çeşit (en yeni test 40000–40099, 100 bölüm/tohum) | Ort. puan ± %95 GA | Başarı | Çakılma | 5000 bölümde çakılma | 5000'de en kötü |
|---|---:|---:|---:|---:|---:|
| **TD3 büyük ağ · 800 bin** — ana sonuç | **288.5 ± 1.1** | **100%** | **0/500** | **0** | **239** |
| TD3 büyük ağ · 1,6 milyon | 289.1 ± 1.5 | 99.6% | 2/500 | 6 | 29 |
| TD3 küçük ağ · 1,6 milyon | 288.8 ± 2.3 | 99.6% | 2/500 | 8 | 20 |
| TD3 küçük ağ · 800 bin | 287.8 ± 1.3 | 99.8% | 1/500 | 3 | 23 |
| TD3 v3 uzun (önceki şampiyon, aynı testte) | 287.5 ± 2.0 | 99.8% | 1/500 | 4 | 26 |
| SAC uzun · 1,6 milyon | 284.1 ± 1.3 | 100% | 0/500 | 0 | 177 |
| SAC uzun · 800 bin | 278.6 ± 6.0 | 100% | 0/500 | 1 | 48 |
| PPO (Optuna) | 276.5 ± 4.7 | 99.8% | 1/500 | 10 | 33 |

**Neden büyük ağ · 800 bin?** (doğrulama bölümleriyle ölçüldü, `scripts/verify_v4.py`) Ortalaması öncekilere çok yakın
(hepsi ≈ 288–290 bandında); farkı **hiç kötü bölümünün olmaması**. Doğrulamada en kötü bölümü 34 yerine 243; 5000 test
bölümünde tek bir başarısızlık yok. Yakıtı (21,9) ve iniş isabeti (sapma 2,2) da biraz daha iyi.
- **Büyük ağ 400 bin adımda yetersiz eğitilmişti** (Aşama 5'te çakılıyordu); 800 binde en güvenilir çeşit oldu.
- **1,6 milyon adım** ortalamayı biraz artırdı (5000 bölümde ≈ 291, yakıt 20,7) ama nadir çakılmalar geri geldi
  (5000'de 6–8). Çok uzun eğitimde politikanın nadir durumlarda bozulabildiğini düşündürüyor; nedeni ayrıca ölçülmedi.
- **SAC** uzun eğitimle çok güvenli oldu (0 çakılma) ama daha çok yakıt ve daha uzun inişle (175 adım) puanı ~285'te kaldı.
- Aynı testte önceki şampiyon (TD3 v3 uzun) 287,5 ve 1 çakılma verdi; önceki testteki 290,0 / 0 çakılma kısmen şanstı.
  Testten teste ±2 puanlık oynama normal; bu yüzden asıl ölçüt 5000 bölümlük sonuçlar.



## Önceki sonuç (Aşama 5: 290 denemesi, TD3 v3 uzun)

En iyi yöntem **TD3 v3 uzun** oldu: Aşama 4'ün şampiyonu TD3 v2b'nin eğitimi 400 binden **800 bin adıma** sürdürüldü.
Ana sonuç, testten önce yazılmış kurala göre (`results/secim_kurali_v3.md`: önce çakılmasızlık, sonra ortalama) ve
yalnızca doğrulama verisiyle seçildi. Hiç görülmemiş **en yeni** test bölümlerinde (30000–30099), 5 tohumun hepsinde:

- **Ortalama 290,0 ± 2,1**, **0 çakılma (0/500)**, bölümlerin %99,8'i ≥ 200 (en kötü bölüm 86: çakılma değil, düşük puanlı iniş).
- İlk hedefin tamamı (her tohumda ortalama ≥ 280 + ≥ %99 başarı + 0 çakılma) **5 tohumun 5'inde** sağlandı.
- Genişletilmiş test (tohum başına 1000 bölüm, 30000–30999): ortalama 288,2 ± 1,8, **5000 bölümde 1 çakılma (%0,02)**.

| Çeşit (en yeni test 30000–30099, 100 bölüm/tohum) | Ort. puan ± %95 GA | Başarı | Çakılma | Tam hedefi sağlayan tohum |
|---|---:|---:|---:|---:|
| **TD3 v3 uzun (800 bin adım)** — ana sonuç | **290.0 ± 2.1** | 99.8% | **0/500** | **5/5** |
| TD3 v3 büyük ağ ([400,300]) | 284.8 ± 4.2 | 99.8% | 1/500 | 4/5 |
| TD3 v2b (önceki şampiyon, aynı testte) | 284.2 ± 3.5 | 100.0% | 0/500 | 5/5 |
| TD3 v3 + yakıt cezası† | 283.8 ± 6.8 | 99.6% | 1/500 | 3/5 |

**Neden uzun eğitim kazandı?** (doğrulama bölümleriyle ölçüldü) Daha uzun eğitilen ajan **daha az yakıtla**
(26,7 → 22,2), **daha isabetli** (iniş sapması 4,5 → 2,7) ve **daha hızlı** (190 → 160 adım) iniyor. Ödül tam olarak
bunları ödüllendirdiği için puan ~6 arttı. Büyük ağ ve yakıt cezası ise ortalamayı biraz artırırken çakılmasızlığı
koruyamadı (bağımsız doğrulamada yakıt cezalı çeşit 6 çakılma yaptı).



## Önceki sonuç (Aşama 4: çakılma %0, TD3 v2b)

O aşamada en iyi yöntem **TD3 v2b** oldu. Ana sonuç, testten önce yazılmış bir kurala göre ve yalnızca doğrulama
verisiyle seçildi. Hiç görülmemiş yeni test bölümlerinde, 5 farklı eğitimin (tohumun) hepsinde:

- **Resmi test (tohum başına 100 bölüm): 0 çakılma (0/500)**, bölümlerin %100'ü ≥ 200 puan, ortalama **283,1 ± 3,7**,
  en kötü bölüm 233.
- Genişletilmiş test (tohum başına 1000 bölüm): 5000 bölümde **2 çakılma (%0,04)**. İkisi de aynı tohumda (4).
  Yani çakılma, hiç olmasa da çok nadir.
- İlk hedefin tamamı (her tohumda ortalama ≥ 280 + ≥ %99 başarı + 0 çakılma) **5 tohumun 4'ünde** sağlandı. Kalan
  tohumun ortalaması 279,1: hedefin 0,9 puan altında, çakılması sıfır.



## Sonuç tablosu — YENİ test (20000–20099, tohum başına 100 bölüm, rastgelelik olmadan, bir kez ölçüldü)

| Yöntem | Tohum | Ort. puan ± %95 GA | Başarı (≥200) | Çakılma | Çakılmasız tohum | En kötü bölüm | Tam hedefi sağlayan tohum |
|---|---:|---:|---:|---:|---:|---:|---:|
| **TD3 v2b** (ana sonuç) | 5 | **283.1 ± 3.7** | **100.0%** | **0/500** | **5/5** | **233.2** | 4/5 |
| PPO (Optuna ayarı) | 5 | 278.5 ± 6.1 | 99.8% | 1/500 | 4/5 | 69.5 | 2/5 |
| SAC + yakıt cezası† | 5 | 276.1 ± 7.3 | 99.4% | 2/500 | 3/5 | 47.0 | 2/5 |
| TD3 v2a | 5 | 273.9 ± 7.0 | 99.8% | 1/500 | 4/5 | 37.4 | 1/5 |
| TD3 (Optuna ayarı, eski) | 5 | 201.1 ± 191.9 | 79.8% | 0/500 | 5/5* | −125.6 | 1/5 |

**Genişletilmiş test** (20000–20999, tohum başına 1000 bölüm), toplam çakılma: TD3 v2b **2/5000** · TD3 v2a 2/5000 ·
PPO 12/5000 · SAC + yakıt cezası 32/5000. Ayrıntı: `results/final_test2_1000/`.

- *Eski TD3'ün tohum 4'ü hiç öğrenemedi: çakılmıyor ama inmiyor da (havada asılı kalıyor, başarı %0).
- † Eğitimde yakıt cezası 2×. Bu, ilk yöntem listesinde yoktu, kullanıcı onayıyla eklendi. Değerlendirme her
  satırda orijinal ödülle yapıldı.
- **Ort. puan ± %95 GA:** tohum ortalamalarının ortalaması ve güven aralığı. **Çakılma:** bölüm, ortamın −100
  cezasıyla bitti.
- **TD3 v2a / v2b:** Optuna'nın TD3 ayarı + öğrenme hızı 1e-3 (eskisi 2,9e-3) + 10 bin adımlık rastgele başlangıç
  (eskisi 5 bin) + 4×10⁵ adım. v2b'de ayrıca daha büyük ağ: [256,256] (v2a'da [128,128]).

Grafikler (PNG + SVG; renk körlüğüne dayanıklı, doğrulayıcıyla kontrol edildi; gruplar işaret şekliyle de ayrılır):

| | |
|---|---|
| Öğrenme eğrileri (tohum ortalaması + %95 bant) | `results/final_val3/ogrenme_egrileri.png` |
| Yeni test puan dağılımı (tohum noktaları + ortalama) | `results/final_test2/puan_dagilimi.png` |
| Algoritma karşılaştırması (puan, başarı, çakılma) | `results/final_test2/algoritma_karsilastirma.png` |


## Neden en iyisi TD3 v2b?

Bu bölümdeki ölçümler doğrulama bölümleriyle yapıldı, test bölümleri kullanılmadı (`scripts/why_analysis.py`,
`results/neden_analizi.json`).

**1. Çakılmaların kaynağı: iniş sonrası devrilme.** 42 çakılmanın 38'inde iki bacak zaten yerdeydi ve araç neredeyse
durmuştu. Ajan bu anda **yan motoru ateşlemeye devam ediyordu**: çakılan bölümlerde temastan sonraki adımların
PPO'da %100'ünde, SAC'ta %57'sinde (başarılı inişlerde ~%10). Araç ~11° yan yatıyor ve gövdesi yere değiyordu.
Yani sorun sert iniş değil, "indikten sonra durmayı bilmemek".

**2. TD3 iniş sonrası daha az sallanıyor.**

| Ölçüt (doğrulama, grup başına 500 bölüm) | TD3 v2b | TD3 v2a | PPO | SAC + yakıt† |
|---|---:|---:|---:|---:|
| temastan sonra en büyük eğim (ort., radyan) | 0.082 | **0.068** | 0.106 | 0.102 |
| iniş süresi (adım) | **190** | 228 | 246 | 202 |
| yakıt cezası | **26.7** | 33.3 | 32.3 | 26.9 |

İki TD3 varyantı yere değdikten sonra ortalamada daha az yatıyor (0,07–0,08'e karşı ~0,10). Bu, daha az devrilme
demek.

**3. v2b neden v2a'dan iyi?** Aynı güvenlikte, ama daha büyük ağla daha hızlı (190'a karşı 228 adım) ve daha az
yakıtla iniyor (26,7'ye karşı 33,3). Ödül yapısı gereği (aşağıda) bu doğrudan daha yüksek puan demek: 283'e karşı 274.

**4. v2 neden eski TD3'ten iyi?** Eski TD3 ayarında (öğrenme hızı 2,9e-3) 5 tohumun 1'i hiç öğrenemedi. Daha
düşük öğrenme hızı (1e-3) ve daha uzun rastgele başlangıçla **10 koşunun 10'u da öğrendi**. Bu iki değişiklik birlikte
yapıldı; hangisinin daha etkili olduğu ayrıca ölçülmedi.

**5. Çakılmaya duyarlı kontrol noktası seçimi.** Eğitimde puan iniş-çıkış yaptığı için, her koşunun ara kayıtları
arasından, 500 doğrulama bölümünde **en az çakılan** an seçildi (önceden en yüksek ortalamalı an seçiliyordu). Adaylar
önce eğitim sırasındaki 20 bölümlük doğrulama ölçümüyle (5000–5019) süzüldü; test bölümleri hiç kullanılmadı.

**6. Neden TD3 (SAC/PPO değil)? Bu bir hipotez, kanıtlanmadı.** TD3 tek, kesin (deterministik) bir eylem kuralı
öğrenir; değerlendirmede de tam o kural kullanılır. SAC ve PPO ise rastgele dağılımlı bir politika öğrenir;
değerlendirmede bu dağılımın ortalaması kullanılır. Bu ortalama eylem eğitim sırasında birebir denenmemiştir. Nadir
"yere değdikten sonra" durumlarında bu ortalama eylemin yan motoru gereksiz ateşlemesi, gözlenen devrilmelerle
uyumlu. Ama bunu ayrıca test etmedim.

**Neden 280 zor (ödül yapısı)?** Puan kabaca şöyle hesaplanır: 100 (iniş) + başlangıçtaki uzaklık ve hızın
kapatılmasından gelen puan (ortalama ≈ +191) + bitişteki konum puanı (ideal ≈ +20) − yakıt. Kusursuz iniş ve sıfır
yakıtla tavan ≈ 311. TD3 v2b bunun ~27 puanını yakıta harcıyor; 280 üstü puan için hızlı, merkezî ve yakıt tasarruflu
iniş gerekiyor (`scripts/reward_decomposition.py`).

**300 ortalama neden gerçekçi değil?** Ortalama 300 için kayıpların toplamı ~11 puana inmeli. TD3 v2b'nin
iniş sapması kaybı zaten küçük (4,5), yani yakıt ~7'ye inmeliydi. Basit bir "serbest düş, son anda tam güçle fren"
kontrolcüsüyle ölçtüğümüz en az frenleme yakıtı ise ~13–19 (ortanca 17; kaba tahmin, `scripts/ceiling_physics.py`).
Yani düşüşü durdurmak için gereken yakıt bile 300 ortalamaya izin vermiyor; gerçekçi üst sınır ≈ 290. Aşama 5'te TD3 v3
uzun yakıtı 22'ye indirip yeni testte bu sınıra ulaştı (290,0). Yine de iyi ajanlar uygun başlangıçlı bölümlerde
300'ü sık geçiyor: TD3 v2b 5000 test bölümünün %19'unda ≥ 300, en yüksek 326.

## Ne yapıldı? (adım adım)

**Makine.** Tarif edilen makine (RTX 4070, 12 çekirdek) yerine AMD Ryzen 5 7520U (4 çekirdek/8 iş parçacığı, uygun GPU
yok, ~7 GB RAM), WSL Ubuntu 24.04, Python 3.12 kullanıldı. Kurulanlar: torch 2.4.1 (CPU), stable-baselines3 2.4.1,
gymnasium 1.0.0, optuna 4.5.0. Hız ölçümüne (`bench.py`) göre CPU kullanıldı, çoğunlukla 4–6 paralel süreç.

**Dürüstlük kuralları.** Ortam ve ödül değerlendirmede hiç değiştirilmedi. Değerlendirme hep rastgelelik olmadan
(deterministik) yapıldı. Tohum kümeleri birbirinden ayrıktır:

| Küme | Tohumlar | Kullanım |
|---|---|---|
| eğitim | 0–4 (Optuna: 100–111) | her eğitim kendi tohumu |
| doğrulama | 5000–5099, 5100–5599 | kontrol noktası seçimi |
| bağımsız doğrulama | 5600–5999 | gruplar arası sıralama (seçimde kullanılmadı) |
| ilk test | 10000–10099 | Aşama 3 sonunda bir kez. Sonra çakılma analizinde kullanıldığı için artık geliştirme verisi |
| **yeni test** | **20000–20099 (+ ek 20100–20999)** | **en sonda, bir kez** |

Test kodu `FROZEN`/`FROZEN2` dosyası olmadan çalışmayı reddeder; bir koşu aynı testle ikinci kez ölçülemez. Ana
sonuç her iki seferde de testten önce yazılmış kurala göre seçildi (`results/secim_kurali.md`,
`results/secim_kurali_v2.md`).

**Aşama 1 — zoo ayarları (≈11,5 sa).** [rl-baselines3-zoo](https://github.com/DLR-RM/rl-baselines3-zoo)
`LunarLanderContinuous-v3` ayarları doğrulanıp kullanıldı (`configs.py`). SAC ≈268, PPO ≈262, TD3 kararsız
(`results/asama1_zoo/`).

**Aşama 2 — Optuna + yakıt pilotu (≈7,3 sa).** Her algoritmaya 12 deneme (eşit bütçe). Ayrıca tek tohumla yakıt
cezası pilotu (`results/asama2_optuna/OZET.md`).

**Aşama 3 — nihai 5 tohum + ilk test (≈11,3 sa).** İlk testte en iyi düzey ~274–276 ortalama, ~%2 çakılma; hedef
karşılanmadı (`results/final_test_tum/`).

**Aşama 4 — çakılma %0 (≈4 sa eğitim + ≈2 sa değerlendirme).** Önce çakılma nedeni ölçüldü
(`scripts/crash_analysis.py`, `scripts/touchdown_actions.py`). Sonra: TD3 sağlamlaştırma (v2a, v2b; 5'er tohum),
çakılmaya duyarlı kontrol noktası seçimi (`reselect.py`), bağımsız doğrulamayla sıralama (`select_main_v2.py`) ve
yeni testte tek seferlik ölçüm (`scripts/finalize_test2.sh`).

**Aşama 5 — 290 denemesi (≈7,4 sa eğitim + ≈0,8 sa değerlendirme).** TD3 v2b'nin 3 çeşidi, 5'er tohum: uzun eğitim
(v2b koşularını 400 binden 800 bin adıma sürdürme), büyük ağ, eğitimde yakıt cezası†. Seçim önceden yazılmış kurala göre
(`results/secim_kurali_v3.md`), yeni bağımsız doğrulamayla (6000–6399); ardından en yeni test kümesinde (30000–30999)
tek seferlik ölçüm (`scripts/finalize_test3.sh`).

**Aşama 6 — sınırları zorlama (≈35,6 sa eğitim + ≈2 sa değerlendirme).** TD3 büyük ağ ([400,300]), TD3 küçük ağ
([256,256]) ve SAC ([256,256]), hepsi 1,6 milyon adım, 5'er tohum. Öğrenme hızı sabit olduğu için her koşunun 800 bin
adımdaki anı da ayrıca seçildi (`reselect.py --suffix 800k`). Seçim önceden yazılmış kurala göre (başarı %100 şartı
sonuçlardan önce eklendi), yeni bağımsız doğrulamayla (6400–6799); test en yeni kümede (40000–40999,
`scripts/finalize_test4.sh`). Bilgisayar bir kez yeniden başlatıldığı için 5 koşu son kayıtlarından (en fazla 25 bin
adım geri) devam etti.

**Aşama 7 — "hiç çakılmadan 290 üstü?" (≈13,2 sa eğitim + ≈0,7 sa değerlendirme).** TD3 büyük ağ, Aşama 6 ile aynı;
tek fark doğrusal azalan öğrenme hızı (1e-3 → 0; `configs/td3_v5big.json`), 5 tohum, 1,6 milyon adım. Kural ve cevap
ölçütü eğitimden önce yazıldı (`results/secim_kurali_v5.md`); seçim yeni bağımsız doğrulamayla (6800–7199), test en yeni
kümede (50000–50999) bir kez (`scripts/finalize_test5.sh`, eğitim bitince kendiliğinden çalıştı). Kullanılan test
kümeleri artık: 10000–10099, 20000–20999, 30000–30999, 40000–40999, 50000–50999.

**Aşama 8 — "erken fren" (≈31 sa eğitim + ≈1,7 sa değerlendirme).** Kalan çakılmalar sert iniş olduğu için, eğitimde
yere hızlı değmeye ek ceza verilen iki çeşit eğitildi: güçlü (`configs/td3_v6brake.json`, |vy| > 0,25 ise 100 × fark) ve
hafif (`configs/td3_v6soft.json`, |vy| > 0,30 ise 50 × fark). İkisi de 5'er tohum, 1,6 milyon adım
(`common.TouchdownPenalty`). Kural eğitimden önce yazıldı (`results/secim_kurali_v6.md`): önce en az çakılma, sonra en
yüksek puan. Doğrulama 7200–9199 ve test 60000–61999, tohum başına 2000 bölüm (öncekilerden 5 kat büyük). Değerlendirme
orijinal ödülle yapıldı (`scripts/finalize_test6.sh`). En fazla 6 süreç paralel çalıştı. **Kesinti:** 23.10 09:31'de Ubuntu
(WSL) kapandı; uygulama yeniden başlarken onu açık tutan süreçler de kapanmıştı. Tohum 0–2 bitmişti; tohum 3–4'ün 4 koşusu
13:53'te son kayıtlarından (875–900 bin adımdan, en fazla 25 bin adım geri) devam etti. Yöntem aynı, ama kesintisiz bir
koşuyla birebir aynı sayıları vermez. Kullanılan test kümeleri artık: 10000–10099, 20000–20999, 30000–30999,
40000–40999, 50000–50999, 60000–61999.

**Aşama 9 — "SAC daha iyi skor çıkaramaz mı?" (≈51 sa eğitim + ≈6 sa değerlendirme).** SAC'a TD3'ü iyileştiren
ayarlar verildi: ağ [400,300], γ 0,995, sabit öğrenme hızı 3e-4, güncelleme/veri oranı 0,5, 1,6 milyon adım. İki çeşit
eğitildi, 5'er tohum: entropi hedefi otomatik (−2) (`configs/sac_v9big.json`) ve −4 (`configs/sac_v9lowent.json`).
Kural eğitimden önce yazıldı (`results/secim_kurali_v7.md`). Kural 1 en yüksek puanlı SAC'ı seçer. Kural 2, Aşama
8'deki "güvenlik önce" kuralıdır ve bütün adaylara uygulanır (karşılaştırma için TD3'ler ve eski SAC da dahil).
Doğrulama 70000–71999, test 80000–81999, tohum başına 2000 bölüm (`scripts/finalize_test7.sh`). En fazla 6 süreç
paralel çalıştı. Kullanılan test kümeleri artık: 10000–10099, 20000–20999, 30000–30999, 40000–40999, 50000–50999,
60000–61999, 80000–81999.

**Aşama 10 — "frenli SAC" (≈41 sa eğitim + ≈5 sa değerlendirme).** Aşama 9'un düşük entropili SAC'ına
(`sac/v9lowent`) Aşama 8'in iki sert iniş cezası eklendi: güçlü (`configs/sac_v10brake.json`, |vy| > 0,25 ise 100 ×
fark) ve hafif (`configs/sac_v10soft.json`, |vy| > 0,30 ise 50 × fark). 5'er tohum, 1,6 milyon adım. Kural eğitimden
önce yazıldı (`results/secim_kurali_v8.md`). Kural 1 frenli SAC'ların en iyisini seçer. Kural 2 "güvenlik önce"
kuralıdır ve 11 adayın hepsine uygulanır (karşılaştırma için TD3'ler ve Aşama 9'un SAC'ları da dahil). Doğrulama
90000–91999, test 100000–101999, tohum başına 2000 bölüm (`scripts/finalize_test8.sh`). İlk iki koşu Aşama 9 sürerken
onunla birlikte çalıştı; o süre Aşama 9'da sayıldı. En fazla 6 süreç paralel çalıştı. Kullanılan test kümeleri artık:
10000–10099, 20000–20999, 30000–30999, 40000–40999, 50000–50999, 60000–61999, 80000–81999, 100000–101999.

Toplam ≈ 232 saat (duvar saati, yalnızca CPU; Aşama 8 kesintisi hariç). Aşama 1–5'te hiçbir eğitim kesilmedi; Aşama 6'da 5 koşu bir yeniden
başlatma sonrası kayıttan devam etti (yöntem aynı, ama kesintisiz koşuyla birebir aynı sayıları vermez). Aşama 5 sonunda
eski aşamaların ara kayıtları (~4 GB), Aşama 6'dan sonra da Aşama 6'nınkiler (5,5 GB) silindi. Silmeden önce Aşama 6'nın
30 seçiminin hepsi ara kayıttaki dosyasıyla birebir karşılaştırıldı (`results/asama6_ara_kayit_silme.json`). Her koşunun
son modeli (`final.zip`) ve seçilen modelleri (`best_policy*.pt`) duruyor; ama kontrol noktası seçimi (`reselect.py`)
artık yeniden çalıştırılamaz.

## Sınırlılıklar ve dürüstlük notları

- **Çakılma çok nadir ama sıfır değil.** Aşama 6'da TD3 büyük ağ · 800 bin 5000 bölümde 0 çakılma verdi; Aşama 7'nin
  yeni testinde aynı ajan 5000'de 2 çakılma yaptı. Yani "0/5000" kısmen şanstı. İki testin toplamında (10 000 bölüm)
  800 bin %0,02, 1,6 milyon %0,08 çakılma oranında. Aşama 8'in erken fren ajanı 20 000 doğrulama + test bölümünde 1 kez
  çakıldı (%0,005); 10 000 test bölümünde 0 görmemek, gerçek oranın sıfır olduğunu zaten kanıtlamazdı.
- **Resmi test 100 bölüm/tohumdur ve bölüm zorluğu oynar.** Aşama 7'de ilk 100 test bölümü tüm çeşitler için ~3 puan
  zor çıktı. Bu yüzden 1000 bölümlük sonuçlar da hep birlikte raporlanıyor.
- **Ortalama ≈ 288–290 bandında.** Aşama 5'in 290,0'ı tek bir testte ölçülmüştü; aynı ajan yeni testte 287,5 verdi.
  Testten teste ±2 puanlık oynama normal.
- Uzun eğitim çeşidi (v3 uzun), eğitime v2b'nin 400 bin adımdaki kayıtlarından devam etti. Aynı ayarla tek seferde
  800 bin adım eğitmek (`configs/td3_v3long.json`) istatistiksel olarak aynı yöntemdir ama birebir aynı sayıları vermez.
- Aşama 4'te TD3 v2b'de tam hedef 4/5 tohumdaydı (bir tohumda ortalama 279,1).
- **Uyarlanarak geliştirme.** TD3 v2 varyantları, ilk test sonuçları ve çakılma analizi görüldükten sonra tasarlandı.
  Bu yüzden yeni, hiç görülmemiş bir test kümesi kullanıldı; yeni testteki sonuçlar tarafsızdır.
- **Optuna kusuru (benim hatam).** Aşama 2'de paralel işçilerin hepsi aynı rastgele tohumla başladığı için 12 denemede
  yalnızca 5–8 farklı ayar denendi. Kod düzeltildi; arama yeniden yapılmadı.
- **Yakıt cezası** (†) ilk listede olmayan, eğitim ödülünü değiştiren bir yöntemdir. Ana sonuç (TD3 v2b) bunu
  kullanmıyor; orijinal ödülle eğitildi.
- **Az tohumlu referanslar:** SAC zoo 2, TD3 zoo 3 tohum. **Farklı adım bütçeleri:** SAC 5×10⁵, TD3 3–4×10⁵, PPO 10⁶
  adım (zoo önerileri).
- **Denenmeyenler:** GPU karşılaştırması (uygun GPU yok), ayrık eylemli sürüm, gözlem normalizasyonu, LayerNorm'lu
  eleştirmen.
- Aynı tohumla yeniden eğitim büyük ölçüde benzer sonuç verir, ancak farklı makinede birebir aynı sayılar garanti
  edilmez. Değerlendirme ise deterministiktir: ajanlar yeniden oynatıldığında test puanları birebir aynı çıktı.
- "SAC + yakıt cezası" grubunun tohum 0'ı, Aşama 2'deki pilot koşusudur (aynı ayar ve kod).
- Grafikler testten sonra yalnızca renk, sıra, dipnot ve (21.10) yıldız işaretinin boyutu için yeniden çizildi; sayılar
  dondurulmuş test kayıtlarından okunuyor (`scripts/redraw_charts.sh` tabloların birebir aynı kaldığını denetler).
- **Son kontrol:** `scripts/verify_all.py` sonuçları ham kayıtlardan yeniden hesaplar ve ajanları yeniden oynatır;
  hepsi geçti. Kod ayrıca bağımsız olarak gözden geçirildi, sonuçları geçersiz kılan bir hata bulunmadı.

## Nasıl çalıştırılır?

Tüm komutlar WSL Ubuntu'da, proje klasöründe (`cd <proje_klasörü>`) çalıştırılır.

```bash
# 0) Kurulum (bir kez; sudo gerekmez)
curl -fsSL -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
python3 /tmp/get-pip.py --target <proje_klasörü>/.pydeps --break-system-packages
bash scripts/setup_env.sh
python3 check_env.py

# 1) Ana sonucun yöntemini (TD3 büyük ağ [400,300], 800 bin adım) bir tohum için yeniden üret
python3 train.py --algo td3 --seed 0 --tag v4big_yeni --config configs/td3_v4big_800k.json  # eğitim (bu makinede ~8 sa)
python3 reselect.py --run-dir runs/td3/v4big_yeni/seed0                                  # çakılmaya duyarlı seçim (400k-800k)
python3 evaluate.py --run-dir runs/td3/v4big_yeni/seed0 --split val5 --ckpt best_v2      # bağımsız doğrulama

# Diğer örnekler
python3 train.py --algo sac --seed 0                                          # zoo ayarlı SAC
python3 train.py --algo ppo --seed 0 --tag tuned --config configs/tuned_ppo.json
python3 evaluate.py --run-dir runs/sac/zoo/seed0 --split val                  # doğrulama
python3 play.py --group sac/v4@800k                                           # SAC 800 bin'i canlı izle (@1600k: 1,6 milyon)
python3 my_test.py --groups td3/v4big@800k sac/v4@800k --episodes 30          # kendi testin: iki ajanı karşılaştır

# 2) Rapor ve video
python3 report.py --split val3 --groups td3/v2b ppo/tuned --out results/deneme
python3 make_video.py --run-dir runs/td3/v2b/seed0 --ckpt best_v2 --split val --episodes 4 --out results/deneme_video

# Uzun işler arka planda + ilerleme takibi
bash scripts/start_queue.sh jobs/stage4_td3.txt 4     # kuyruk (biteni atlar, yarıda kalana devam eder)
bash scripts/start_status.sh                          # DURUM.md her dakika güncellenir
```

## Dosya düzeni

| Yol | İçerik |
|---|---|
| `train.py`, `evaluate.py`, `reselect.py`, `tune.py`, `report.py`, `make_video.py` | eğitim, değerlendirme, kontrol noktası seçimi, ayar arama, rapor, video |
| `common.py`, `configs.py`, `configs/*.json` | ortam, tohum kümeleri, ölçütler; zoo, Optuna ve v2b ayarları |
| `select_main.py`, `select_main_v2.py`, `results/secim_kurali*.md` | önceden kayıtlı seçim kuralları ve kararlar |
| `runs/<algoritma>/<grup>/seed<k>/` | her koşunun ham verisi: `config.json`, `val_curve.csv` (öğrenme eğrisi), `monitor/` (eğitim bölümleri), `final.zip` (son model), `best_policy_v2.pt` (seçilmiş model), `test2_episodes.csv` / `test2x_episodes.csv` (yeni test bölümlerinin tek tek puanları), `selection_v2.json` |
| `results/final_test2/`, `results/final_test2_1000/`, `results/final_val3/` | güncel tablolar ve grafikler |
| `results/final_test_tum/`, `results/asama1_zoo/`, `results/asama2_*` | önceki aşamaların sonuçları |
| `scripts/` | analiz (çakılma, ödül ayrıştırma, neden analizi) ve yardımcı betikler |
| `DURUM.md` | koşuların son durumu |

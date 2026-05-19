# 📸 AutoPhoto - Zamanlayıcı ile Otomatik Fotoğraf Çekme Sistemi

Bu proje, gerçek zamanlı kamera görüntüsü üzerinden insan yüzünü algılayan ve belirlenen süre boyunca yüz sabit kaldığında otomatik olarak fotoğraf çeken modern arayüzlü bir görüntü işleme uygulamasıdır.

---

# 🛠 Kullanılan Teknolojiler

- Python
- OpenCV
- CustomTkinter
- Pillow (PIL)
- Haar Cascade Face Detection
- Threading

---

# ⚙️ Nasıl Çalışır?

1. Kameradan alınan görüntü gerçek zamanlı olarak işlenir.

2. Performansı artırmak amacıyla görüntü gri seviyeye dönüştürülür.

3. Farklı ışık koşullarında daha iyi sonuç almak için Histogram Eşitleme uygulanır.

4. Haar Cascade algoritması kullanılarak görüntü içerisindeki yüzler tespit edilir.

5. Birden fazla yüz bulunduğunda ekrana en yakın olan yüz (en büyük alan) ana hedef olarak seçilir.

6. Yüz belirlenen minimum boyut kriterini sağlıyorsa otomatik geri sayım sistemi başlatılır.

7. 3 saniyelik geri sayım tamamlandığında fotoğraf otomatik olarak çekilir.

8. Çekilen fotoğraf tarih ve saat bilgisiyle `captures` klasörüne kaydedilir.

9. Uygulama içerisindeki galeri ekranından fotoğraflar görüntülenebilir veya silinebilir.

---

# 📊 Teknik Parametreler

| Parametre | Değer | Açıklama |
|---|---|---|
| `countdown_seconds` | `3` | Fotoğraf çekilmeden önceki bekleme süresi |
| `cooldown` | `2.0` | İki çekim arasındaki minimum bekleme süresi |
| `min_face_area` | `6400` | Minimum yüz algılama alanı |
| `scaleFactor` | `1.1` | Görüntü ölçekleme oranı |
| `minNeighbors` | `5` | Yüz doğrulama komşuluk değeri |
| `minSize` | `60x60` | Minimum yüz boyutu |

---

# 🖥️ Arayüz Özellikleri

- Modern Dark Mode tasarımı
- Kamera başlat / durdur sistemi
- Gerçek zamanlı kamera görüntüsü
- Otomatik fotoğraf çekme
- Scroll destekli galeri sistemi
- Fotoğraf görüntüleme
- Hover destekli fotoğraf silme butonu
- Responsive pencere yapısı

---

# 📂 Proje Yapısı

```bash
AutoPhoto/
│
├── AutoPhoto.py          # Görüntü işleme ve yüz algılama sistemi
├── AutoPhotoGUI.py       # Grafik kullanıcı arayüzü
├── captures/             # Kaydedilen fotoğraflar
└── README.md

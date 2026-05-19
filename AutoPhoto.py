import cv2
import time
import os
import threading

class FaceDetector:
    def __init__(self, save_dir="captures", countdown_seconds=3, cooldown=2.0, min_face_area=6400):
        # Fotoğrafların kaydedileceği klasör
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        
        # Kamera ayarları ve süreleri
        self.countdown_seconds = countdown_seconds
        self.cooldown = cooldown
        self.min_face_area = min_face_area
        
        # OpenCV'nin hazır yüz tanıma modelini yüklüyoruz
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        self.cap = None
        self.running = False
        self.lock = threading.Lock()
        
        # Geri sayım ve bekleme süresi takibi
        self.countdown_active = False
        self.countdown_start = 0.0
        self.last_shot_time = 0.0
        self.captured_until = 0.0
        self.captured_show_seconds = 1.0
        
        # Arayüze veri göndermek için kullanılacak fonksiyonlar
        self.on_frame = None
        self.on_photo_taken = None

    def start(self):
        # Kamerayı ve yüz tanıma işlemini arka planda başlatır
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("HATA: Kamera açılamadı.")
        
        with self.lock:
            self.countdown_active = False
            self.countdown_start = 0.0
            self.last_shot_time = 0.0
            self.captured_until = 0.0
            
        self.running = True
        # Arayüzün donmaması için işlemleri ayrı bir thread çalıştırıyoruz
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()

    def stop(self):
        # Kamerayı ve arka plan işlemlerini güvenli bir şekilde kapatır
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
            
        with self.lock:
            self.countdown_active = False
            self.countdown_start = 0.0

    def _process_loop(self):
        # Kameradan sürekli görüntü alıp yüz tespiti yapan ana döngü
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.01)
                continue

            # Kamerayı ayna efekti ile çeviriyoruz
            frame = cv2.flip(frame, 1)
            original_frame = frame.copy()

            # Yüz tanıma işlemi için görüntüyü siyah-beyaza çeviriyoruz
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
            )

            # Ekranda birden fazla yüz varsa en büyük olanı (kameraya en yakın olanı) seçiyoruz
            biggest = None
            biggest_area = 0
            for (x, y, w, h) in faces:
                area = w * h
                if area > biggest_area:
                    biggest_area = area
                    biggest = (x, y, w, h)

            now = time.time()
            # Yüz bulundu mu ve kameraya yeterince yakın mı kontrolü
            face_detected = biggest is not None and biggest_area >= self.min_face_area

           
            with self.lock:
                if face_detected:
                    x, y, w, h = biggest
                    # Yüzün etrafına yeşil bir kare çiziyoruz
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # Peş peşe sürekli fotoğraf çekmemesi için bekleme süresi kontrolü
                    can_trigger = (now - self.last_shot_time) >= self.cooldown

                    # Geri sayımı başlat
                    if not self.countdown_active and can_trigger:
                        self.countdown_active = True
                        self.countdown_start = now

                    if self.countdown_active:
                        elapsed = now - self.countdown_start
                        kalan_sure = max(0.0, self.countdown_seconds - elapsed)
                        cv2.putText(frame,
                                    f"Fotograf Cekiliyor {kalan_sure:0.1f}s",
                                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50, 255, 50), 2, cv2.LINE_AA)

                        # Süre dolduğunda fotoğrafı kaydet
                        if elapsed >= self.countdown_seconds:
                            filename = time.strftime("face_%Y%m%d_%H%M%S.jpg")
                            path = os.path.join(self.save_dir, filename)
                            cv2.imwrite(path, original_frame)
                            print(f"Kaydedildi: {path}")

                            self.last_shot_time = now
                            self.countdown_active = False
                            self.captured_until = now + self.captured_show_seconds
                            
                            # Arayüze fotoğrafın çekildiği bilgisini yolla
                            if self.on_photo_taken:
                                self.on_photo_taken(path)

                else:
                    # Yüz yoksa geri sayımı iptal et
                    if self.countdown_active:
                        self.countdown_active = False
                    cv2.putText(frame, "Yuz bekleniyor...",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2, cv2.LINE_AA)

                # Fotoğraf çekildikten hemen sonra ekranda kısa süreliğine uyarı göster
                if now < self.captured_until:
                    self._draw_captured(frame)

            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if self.on_frame:
                self.on_frame(frame_rgb)
            
           
            time.sleep(0.01)

    def _draw_captured(self, frame):
        # Fotoğraf çekildiği anda ekrana uyarı yazısı ekler
        h, w = frame.shape[:2]
        text = "FOTOGRAF CEKILDI"

        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 2.0
        thickness = 4

        (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
        x = (w - tw) // 2
        y = (h + th) // 2

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, y - 60), (w, y + 20), (0, 0, 0), -1)
        
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        cv2.putText(frame, text, (x, y), font, scale, (0, 255, 0), thickness, cv2.LINE_AA)

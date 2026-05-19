import customtkinter as ctk
from PIL import Image, ImageTk
import os
import platform
import subprocess
from AutoPhoto import FaceDetector

# Temel tema ayarları
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AutoPhotoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AutoPhoto")
        self.geometry("900x700")
        self.minsize(800, 600)

        # Arayüzü ızgara sistemine bölüyoruz
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sol menü paneli
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="AutoPhoto", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.start_btn = ctk.CTkButton(self.sidebar_frame, text="Kamerayı Başlat", command=self.toggle_camera)
        self.start_btn.grid(row=1, column=0, padx=20, pady=10)

        self.close_btn = ctk.CTkButton(self.sidebar_frame, text="Kamerayı Kapat", command=self.close_camera, fg_color="#C62828", hover_color="#B71C1C")
        self.close_btn.grid(row=2, column=0, padx=20, pady=10)

        self.gallery_btn = ctk.CTkButton(self.sidebar_frame, text="Galeri", command=self.show_gallery_window)
        self.gallery_btn.grid(row=3, column=0, padx=20, pady=10)

        # Ana kamera alanı
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_propagate(False)

        self.video_label = ctk.CTkLabel(self.main_frame, text="Kamera Kapalı")
        self.video_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Yüz tanıma modülünü başlatıyoruz
        self.detector = FaceDetector(save_dir="captures", countdown_seconds=3, cooldown=2.0)
        self.detector.on_frame = self.update_frame
        self.detector.on_photo_taken = self.add_to_gallery_if_open

        self.is_camera_running = False
        self.show_feed = False
        
        self.gallery_window = None
        self.gallery_scrollable_frame = None

    def toggle_camera(self):
        # Kamerayı başlatır veya durdurur
        if not self.is_camera_running:
            try:
                self.show_feed = True
                self.detector.start()
                self.is_camera_running = True
                self.start_btn.configure(text="Kamerayı Durdur")
            except Exception as e:
                print(f"Kamera başlatılamadı: {e}")
        else:
            self.detector.stop()
            self.is_camera_running = False
            self.start_btn.configure(text="Kamerayı Başlat")

    def close_camera(self):
        # Kamerayı tamamen kapatır ve arayüzü sıfırlar
        self.show_feed = False
        if self.is_camera_running:
            self.detector.stop()
            self.is_camera_running = False
        
        self.start_btn.configure(text="Kamerayı Başlat")
        
        # Ekranı güvenli şekilde temizlemek için boş bir görsel oluşturuyoruz
        empty_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        empty_ctk_img = ctk.CTkImage(empty_img, size=(1, 1))
        
        self.video_label.configure(image=empty_ctk_img, text="Kamera Kapalı")
        self.video_label.image = empty_ctk_img

    def update_frame(self, frame_rgb):
        # Kameradan gelen görüntüyü ekrana yansıtır
        try:
            self.after(0, self._set_image, frame_rgb)
        except Exception as e:
            pass

    def _set_image(self, frame_rgb):
        if not self.show_feed:
            return
        
        try:
            img = Image.fromarray(frame_rgb)
            width, height = img.size
            
            # Güncel ve doğru main_frame boyutlarını al
            max_width = self.main_frame.winfo_width() - 20
            max_height = self.main_frame.winfo_height() - 20
            
            if max_width > 100 and max_height > 100:
                ratio = min(max_width/width, max_height/height)
                new_size_physical = (int(width*ratio), int(height*ratio))
                
                
                scale = self.main_frame._get_widget_scaling()
                logical_size = (int(new_size_physical[0] / scale), int(new_size_physical[1] / scale))
                
                # CTkImage'a ham resmi veriyoruz, kendisi logical_size'a göre en yüksek kalitede ayarlıyor.
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=logical_size)
                self.video_label.configure(image=ctk_image, text="")
                self.video_label.image = ctk_image
        except Exception as e:
            pass

    def show_gallery_window(self):
        # Galeri butonuna basıldığında fotoğrafları gösteren pencereyi açar
        if self.gallery_window is None or not self.gallery_window.winfo_exists():
            self.gallery_window = ctk.CTkToplevel(self)
            self.gallery_window.title("Galeri")
            self.gallery_window.geometry("600x500")
            
            self.gallery_window.attributes("-topmost", True)
            self.gallery_window.after(100, lambda: self.gallery_window.attributes("-topmost", False))

            self.gallery_scrollable_frame = ctk.CTkScrollableFrame(self.gallery_window)
            self.gallery_scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            self.gallery_scrollable_frame.grid_columnconfigure((0, 1, 2), weight=1)
            
            self.load_gallery_photos()
        else:
            self.gallery_window.focus()

    def load_gallery_photos(self):
        # Klasördeki fotoğrafları bulup galeriye ekler
        for widget in self.gallery_scrollable_frame.winfo_children():
            widget.destroy()

        save_dir = "captures"
        if os.path.exists(save_dir):
            files = sorted(
                [f for f in os.listdir(save_dir) if f.endswith(('.png', '.jpg', '.jpeg'))],
                key=lambda x: os.path.getmtime(os.path.join(save_dir, x)),
                reverse=True
            )
            
            row = 0
            col = 0
            for f in files:
                self._add_gallery_item_to_grid(os.path.join(save_dir, f), row, col)
                col += 1
                if col > 2:
                    col = 0
                    row += 1

    def add_to_gallery_if_open(self, image_path):
        # Fotoğraf çekildiğinde galeri açıksa yeniler
        self.after(0, self._check_and_refresh_gallery)

    def _check_and_refresh_gallery(self):
        if self.gallery_window is not None and self.gallery_window.winfo_exists():
            self.load_gallery_photos()

    def _add_gallery_item_to_grid(self, image_path, row, col):
        # Galeriye tek bir fotoğrafı ve silme butonunu ekler
        try:
            item_frame = ctk.CTkFrame(self.gallery_scrollable_frame, fg_color="transparent")
            item_frame.grid(row=row, column=col, pady=10, padx=10)

            img = Image.open(image_path)
            img.thumbnail((150, 150))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            
            lbl = ctk.CTkLabel(item_frame, image=ctk_img, text="")
            lbl.pack()
            lbl.bind("<Button-1>", lambda e, path=image_path: self.open_image(path))

            del_btn = ctk.CTkButton(item_frame, text="✕", width=26, height=26, corner_radius=13,
                                    fg_color="#C62828", hover_color="#B71C1C", text_color="white",
                                    font=ctk.CTkFont(size=14, weight="bold"),
                                    command=lambda p=image_path, f=item_frame: self.delete_photo(p, f))
            
            def show_btn(e):
                del_btn.place(relx=0.96, rely=0.04, anchor="ne")
                
            def hide_btn(e):
                x = item_frame.winfo_pointerx() - item_frame.winfo_rootx()
                y = item_frame.winfo_pointery() - item_frame.winfo_rooty()
                if x < 0 or x > item_frame.winfo_width() or y < 0 or y > item_frame.winfo_height():
                    del_btn.place_forget()

            lbl.bind("<Enter>", show_btn)
            lbl.bind("<Leave>", hide_btn)
            del_btn.bind("<Leave>", hide_btn)
            
        except Exception as e:
            print(f"Galeri için görsel yüklenemedi: {e}")

    def delete_photo(self, path, frame):
        # Fotoğrafı silme işlemi
        import tkinter.messagebox as messagebox
        if messagebox.askyesno("Silme Onayı", "Bu fotoğrafı tamamen silmek istediğinize emin misiniz?"):
            try:
                if os.path.exists(path):
                    os.remove(path)
                frame.destroy()
                # Galeriyi yeniden yükleyerek kaymayı engeller
                self.load_gallery_photos()
            except Exception as e:
                print(f"Silme hatası: {e}")

    def open_image(self, path):
        # İşletim sistemine göre görseli açar
        if platform.system() == "Windows":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])

    def on_closing(self):
        # Program kapatılırken çalışan işlemleri durdurur
        if self.is_camera_running:
            self.detector.stop()
        self.destroy()

if __name__ == "__main__":
    app = AutoPhotoApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

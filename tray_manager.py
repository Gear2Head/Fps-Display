import tkinter as tk
from tkinter import ttk, messagebox
import pystray
from PIL import Image, ImageDraw
import threading
import json
import os
from typing import Callable, Optional

class TrayManager:
	"""Sistem tray ikonu ve konfigürasyon yöneticisi."""

	def __init__(self, on_show: Callable[[], None], on_hide: Callable[[], None], on_quit: Callable[[], None]):
		self.on_show = on_show
		self.on_hide = on_hide
		self.on_quit = on_quit
		self.icon = None
		self.config_window = None

	def create_icon_image(self) -> Image.Image:
		"""Tray ikonu oluştur."""
		width = 64
		height = 64
		image = Image.new('RGB', (width, height), color='#1a1a2e')
		dc = ImageDraw.Draw(image)
		
		# OSD yazısı
		dc.text((8, 8), "OSD", fill='#7aa2f7', font_size=12)
		dc.text((8, 24), "CPU", fill='#f7768e', font_size=8)
		dc.text((8, 36), "GPU", fill='#9ece6a', font_size=8)
		dc.text((8, 48), "RAM", fill='#e0af68', font_size=8)
		
		return image

	def create_menu(self) -> pystray.Menu:
		"""Tray menüsü oluştur."""
		return pystray.Menu(
			pystray.MenuItem("Göster", self.on_show, default=True),
			pystray.MenuItem("Gizle", self.on_hide),
			pystray.Menu.SEPARATOR,
			pystray.MenuItem("Ayarlar", self.show_config),
			pystray.MenuItem("Tema", pystray.Menu(
				pystray.MenuItem("Koyu", lambda: self.change_theme("dark")),
				pystray.MenuItem("Açık", lambda: self.change_theme("light")),
				pystray.MenuItem("Özel", lambda: self.change_theme("custom")),
			)),
			pystray.Menu.SEPARATOR,
			pystray.MenuItem("Çıkış", self.on_quit)
		)

	def start(self):
		"""Tray ikonunu başlat."""
		image = self.create_icon_image()
		menu = self.create_menu()
		
		self.icon = pystray.Icon("OSD Overlay", image, "OSD Overlay", menu)
		
		# Ayrı thread'de çalıştır
		thread = threading.Thread(target=self.icon.run, daemon=True)
		thread.start()

	def stop(self):
		"""Tray ikonunu durdur."""
		if self.icon:
			self.icon.stop()

	def show_config(self, icon=None, item=None):
		"""Konfigürasyon penceresini göster."""
		if self.config_window and self.config_window.winfo_exists():
			self.config_window.lift()
			return

		self.config_window = tk.Toplevel()
		self.config_window.title("OSD Overlay Ayarları")
		self.config_window.geometry("400x300")
		self.config_window.resizable(False, False)
		self.config_window.attributes("-topmost", True)

		# Notebook (tab'lar)
		notebook = ttk.Notebook(self.config_window)
		notebook.pack(fill="both", expand=True, padx=10, pady=10)

		# Genel ayarlar
		general_frame = ttk.Frame(notebook)
		notebook.add(general_frame, text="Genel")

		# Yenileme hızı
		ttk.Label(general_frame, text="Yenileme Hızı (ms):").pack(anchor="w", pady=5)
		refresh_var = tk.StringVar(value="500")
		refresh_spin = ttk.Spinbox(general_frame, from_=100, to=5000, textvariable=refresh_var, width=10)
		refresh_spin.pack(anchor="w", pady=5)

		# FPS ayarları
		fps_frame = ttk.LabelFrame(general_frame, text="FPS Ayarları")
		fps_frame.pack(fill="x", pady=10)

		fps_enabled = tk.BooleanVar()
		ttk.Checkbutton(fps_frame, text="FPS gösterimi aktif", variable=fps_enabled).pack(anchor="w")

		ttk.Label(fps_frame, text="Oyun süreci adı:").pack(anchor="w", pady=5)
		process_var = tk.StringVar()
		ttk.Entry(fps_frame, textvariable=process_var, width=30).pack(anchor="w")

		# Güncelleme ayarları
		update_frame = ttk.LabelFrame(general_frame, text="Güncelleme")
		update_frame.pack(fill="x", pady=10)

		update_enabled = tk.BooleanVar(value=True)
		ttk.Checkbutton(update_frame, text="Güncelleme kontrolü", variable=update_enabled).pack(anchor="w")

		# Tema ayarları
		theme_frame = ttk.Frame(notebook)
		notebook.add(theme_frame, text="Tema")

		ttk.Label(theme_frame, text="Tema Seçimi:").pack(anchor="w", pady=5)
		theme_var = tk.StringVar(value="dark")
		theme_combo = ttk.Combobox(theme_frame, textvariable=theme_var, values=["dark", "light", "custom"], state="readonly")
		theme_combo.pack(anchor="w", pady=5)

		# Renk ayarları
		colors_frame = ttk.LabelFrame(theme_frame, text="Renkler")
		colors_frame.pack(fill="x", pady=10)

		color_vars = {}
		color_names = ["CPU", "GPU", "RAM", "FPS"]
		color_keys = ["cpu", "gpu", "ram", "fps"]
		color_defaults = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4"]

		for i, (name, key, default) in enumerate(zip(color_names, color_keys, color_defaults)):
			row = ttk.Frame(colors_frame)
			row.pack(fill="x", pady=2)
			
			ttk.Label(row, text=f"{name}:", width=8).pack(side="left")
			color_vars[key] = tk.StringVar(value=default)
			ttk.Entry(row, textvariable=color_vars[key], width=10).pack(side="left", padx=5)

		# Kaydet butonu
		def save_config():
			config = {
				"refreshMs": int(refresh_var.get()),
				"presentMon": {
					"enabled": fps_enabled.get(),
					"processName": process_var.get()
				},
				"update": {
					"check": update_enabled.get(),
					"url": "https://github.com/Gear2Head/Fps-Display/releases/latest"
				},
				"theme": {
					"name": theme_var.get(),
					"colors": {k: v.get() for k, v in color_vars.items()}
				}
			}
			
			config_path = os.path.join(os.path.dirname(__file__), "config.json")
			with open(config_path, "w", encoding="utf-8") as f:
				json.dump(config, f, indent=2, ensure_ascii=False)
			
			messagebox.showinfo("Başarılı", "Ayarlar kaydedildi!")
			self.config_window.destroy()

		ttk.Button(general_frame, text="Kaydet", command=save_config).pack(pady=10)

	def change_theme(self, theme_name: str):
		"""Tema değiştir."""
		# Bu fonksiyon ana uygulamada tema değişikliğini tetikleyecek
		pass

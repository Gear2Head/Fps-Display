import tkinter as tk
from tkinter import ttk
import math
import time
from typing import Callable, Optional, Dict, Any

class ModernOverlayWindow:
	"""Modern, animasyonlu, tema destekli overlay."""

	def __init__(self, on_close: Optional[Callable[[], None]] = None) -> None:
		self.root = tk.Tk()
		self.root.title("OSD Overlay")
		self.root.attributes("-topmost", True)
		self.root.overrideredirect(True)
		self.root.attributes("-alpha", 0.95)

		self.on_close = on_close
		self.is_locked = False
		self.is_minimized = False
		self.animation_frame = 0
		self.last_animation_time = time.time()

		# Modern tema
		self.theme = {
			"bg": "#0a0a0f",
			"panel": "#1a1a2e", 
			"accent": "#16213e",
			"text": "#e6e6e6",
			"text_secondary": "#a0a0a0",
			"cpu": "#ff6b6b",
			"gpu": "#4ecdc4", 
			"ram": "#45b7d1",
			"fps": "#96ceb4",
			"border": "#2d3748",
			"gradient_start": "#667eea",
			"gradient_end": "#764ba2"
		}

		# Pencere boyutları
		self.width = 420
		self.height = 180
		self.minimized_height = 40

		self.root.geometry(f"{self.width}x{self.height}")
		self.root.configure(bg=self.theme["bg"])

		# Ana canvas
		self.canvas = tk.Canvas(
			self.root, 
			width=self.width, 
			height=self.height,
			bg=self.theme["bg"], 
			highlightthickness=0,
			relief="flat"
		)
		self.canvas.pack()

		# Başlık çubuğu
		self._create_titlebar()

		# Drag ve event binding
		self._setup_events()

		self._last_metrics = None
		self._animation_data = {"cpu": [], "gpu": [], "ram": []}

	def _create_titlebar(self):
		"""Modern başlık çubuğu oluştur."""
		self.titlebar = tk.Frame(
			self.root,
			height=30,
			bg=self.theme["accent"],
			relief="flat"
		)
		self.titlebar.place(x=0, y=0, width=self.width, height=30)
		self.titlebar.bind("<ButtonPress-1>", self._start_move)
		self.titlebar.bind("<B1-Motion>", self._on_move)

		# Başlık metni
		self.title_label = tk.Label(
			self.titlebar,
			text="OSD Overlay",
			fg=self.theme["text"],
			bg=self.theme["accent"],
			font=("Segoe UI", 10, "bold")
		)
		self.title_label.place(x=10, y=5)

		# Kontrol butonları
		self._create_control_buttons()

	def _create_control_buttons(self):
		"""Minimize, lock, close butonları."""
		btn_size = 20
		btn_y = 5
		btn_spacing = 25

		# Minimize butonu
		self.min_btn = tk.Button(
			self.titlebar,
			text="−",
			width=2,
			height=1,
			bg=self.theme["accent"],
			fg=self.theme["text"],
			font=("Segoe UI", 8, "bold"),
			relief="flat",
			command=self._toggle_minimize
		)
		self.min_btn.place(x=self.width - 80, y=btn_y)

		# Lock butonu
		self.lock_btn = tk.Button(
			self.titlebar,
			text="🔒",
			width=2,
			height=1,
			bg=self.theme["accent"],
			fg=self.theme["text"],
			font=("Segoe UI", 8),
			relief="flat",
			command=self._toggle_lock
		)
		self.lock_btn.place(x=self.width - 55, y=btn_y)

		# Close butonu
		self.close_btn = tk.Button(
			self.titlebar,
			text="×",
			width=2,
			height=1,
			bg="#e53e3e",
			fg="white",
			font=("Segoe UI", 10, "bold"),
			relief="flat",
			command=self.close
		)
		self.close_btn.place(x=self.width - 30, y=btn_y)

	def _setup_events(self):
		"""Event binding'leri ayarla."""
		self.canvas.bind("<ButtonPress-1>", self._start_move)
		self.canvas.bind("<B1-Motion>", self._on_move)
		self.root.bind("<Escape>", lambda e: self.close())
		self.root.bind("<KeyPress-l>", self._toggle_lock)
		self.root.bind("<KeyPress-m>", self._toggle_minimize)

	def _toggle_lock(self, _event=None):
		self.is_locked = not self.is_locked
		self.lock_btn.configure(text="🔓" if not self.is_locked else "🔒")

	def _toggle_minimize(self, _event=None):
		self.is_minimized = not self.is_minimized
		if self.is_minimized:
			self.root.geometry(f"{self.width}x{self.minimized_height}")
			self.canvas.configure(height=self.minimized_height)
			self.min_btn.configure(text="+")
		else:
			self.root.geometry(f"{self.width}x{self.height}")
			self.canvas.configure(height=self.height)
			self.min_btn.configure(text="−")

	def _start_move(self, event):
		if self.is_locked:
			return
		self._x = event.x
		self._y = event.y

	def _on_move(self, event):
		if self.is_locked:
			return
		x = event.x_root - self._x
		y = event.y_root - self._y
		self.root.geometry(f"+{x}+{y}")

	def set_text(self, content: str) -> None:
		"""Eski API uyumluluğu için."""
		self._last_metrics = None
		self._draw_fallback(content)

	def set_metrics(self, *, cpu: float, ram_used: float, ram_total: float,
				  gpu_util: Optional[float] = None, gpu_temp: Optional[float] = None,
				  gpu_mem_used: Optional[float] = None, gpu_mem_total: Optional[float] = None,
				  fps: Optional[float] = None, banner: Optional[str] = None) -> None:
		"""Modern metrik gösterimi."""
		self._last_metrics = {
			"cpu": cpu,
			"ram_used": ram_used,
			"ram_total": ram_total,
			"gpu_util": gpu_util,
			"gpu_temp": gpu_temp,
			"gpu_mem_used": gpu_mem_used,
			"gpu_mem_total": gpu_mem_total,
			"fps": fps,
			"banner": banner or "",
		}
		
		# Animasyon verilerini güncelle
		self._update_animation_data()
		self._draw()

	def _update_animation_data(self):
		"""Animasyon için veri güncelle."""
		if not self._last_metrics:
			return
		
		m = self._last_metrics
		self._animation_data["cpu"].append(m["cpu"])
		self._animation_data["gpu"].append(m.get("gpu_util", 0))
		self._animation_data["ram"].append((m["ram_used"] / max(0.1, m["ram_total"])) * 100)
		
		# Son 20 değeri tut
		for key in self._animation_data:
			if len(self._animation_data[key]) > 20:
				self._animation_data[key] = self._animation_data[key][-20:]

	def _draw_gradient_bar(self, x: int, y: int, w: int, h: int, ratio: float, color: str, label: str, icon: str = "") -> None:
		"""Gradient efektli modern bar."""
		ratio = max(0.0, min(1.0, ratio))
		
		# Arka plan
		self.canvas.create_rectangle(x, y, x + w, y + h, fill=self.theme["panel"], outline=self.theme["border"], width=1)
		
		# Gradient bar (basit)
		bar_width = int(w * ratio)
		if bar_width > 0:
			self.canvas.create_rectangle(x + 2, y + 2, x + bar_width - 2, y + h - 2, fill=color, outline="")
		
		# Metin
		text_x = x + 8
		text_y = y + h // 2
		
		# İkon varsa
		if icon:
			self.canvas.create_text(text_x, text_y, text=icon, fill=self.theme["text_secondary"], anchor="w", font=("Segoe UI", 10))
			text_x += 20
		
		# Ana metin
		self.canvas.create_text(text_x, text_y, text=label, fill=self.theme["text"], anchor="w", font=("Segoe UI", 10, "bold"))
		
		# Yüzde değeri (sağda)
		percent_text = f"{ratio*100:.0f}%"
		self.canvas.create_text(x + w - 8, text_y, text=percent_text, fill=self.theme["text_secondary"], anchor="e", font=("Segoe UI", 9))

	def _draw_mini_chart(self, x: int, y: int, w: int, h: int, data: list, color: str) -> None:
		"""Mini grafik çiz."""
		if len(data) < 2:
			return
		
		# Veriyi normalize et
		max_val = max(data) if data else 1
		points = []
		
		for i, val in enumerate(data):
			px = x + int((i / (len(data) - 1)) * w)
			py = y + h - int((val / max_val) * h)
			points.extend([px, py])
		
		if len(points) >= 4:
			self.canvas.create_line(points, fill=color, width=2, smooth=True)

	def _draw_fallback(self, content: str) -> None:
		"""Fallback metin gösterimi."""
		self.canvas.delete("all")
		self.canvas.create_text(
			self.width // 2, self.height // 2, 
			text=content, 
			fill=self.theme["text"], 
			anchor="center", 
			font=("Segoe UI", 12, "bold")
		)

	def _draw(self) -> None:
		"""Ana çizim fonksiyonu."""
		if self.is_minimized:
			return
			
		self.canvas.delete("all")
		
		# Ana panel
		panel_margin = 8
		panel_x = panel_margin
		panel_y = 35
		panel_w = self.width - (panel_margin * 2)
		panel_h = self.height - panel_y - panel_margin
		
		# Panel arka planı
		self.canvas.create_rectangle(
			panel_x, panel_y, panel_x + panel_w, panel_y + panel_h,
			fill=self.theme["panel"], outline=self.theme["border"], width=1
		)
		
		if not self._last_metrics:
			self._draw_fallback("Yükleniyor...")
			return

		m = self._last_metrics
		content_y = panel_y + 15
		bar_height = 20
		bar_spacing = 30
		bar_width = panel_w - 20

		# Banner
		if m.get("banner"):
			self.canvas.create_text(
				panel_x + 10, content_y, 
				text=m["banner"], 
				fill=self.theme["fps"], 
				anchor="w", 
				font=("Segoe UI", 9, "bold")
			)
			content_y += 20

		# CPU
		cpu_ratio = float(m["cpu"]) / 100.0
		self._draw_gradient_bar(
			panel_x + 10, content_y, bar_width, bar_height,
			cpu_ratio, self.theme["cpu"], 
			f"CPU {m['cpu']:.0f}%", "🖥️"
		)
		content_y += bar_spacing

		# RAM
		ram_total = max(0.1, float(m["ram_total"]))
		ram_ratio = float(m["ram_used"]) / ram_total
		self._draw_gradient_bar(
			panel_x + 10, content_y, bar_width, bar_height,
			ram_ratio, self.theme["ram"], 
			f"RAM {m['ram_used']:.1f}/{m['ram_total']:.1f} GB", "💾"
		)
		content_y += bar_spacing

		# GPU
		gpu_util = m.get("gpu_util")
		if gpu_util is not None:
			gpu_label = f"GPU {gpu_util:.0f}%"
			gpu_temp = m.get("gpu_temp")
			if gpu_temp is not None:
				gpu_label += f" | {gpu_temp:.0f}°C"
			gpu_mem_used = m.get("gpu_mem_used")
			gpu_mem_total = m.get("gpu_mem_total")
			if gpu_mem_used is not None and gpu_mem_total is not None and gpu_mem_total > 0:
				gpu_label += f" | {gpu_mem_used:.1f}/{gpu_mem_total:.1f} GB"
			
			self._draw_gradient_bar(
				panel_x + 10, content_y, bar_width, bar_height,
				float(gpu_util) / 100.0, self.theme["gpu"], 
				gpu_label, "🎮"
			)
			content_y += bar_spacing

		# FPS
		fps = m.get("fps")
		if fps is not None:
			self.canvas.create_text(
				panel_x + 10, content_y, 
				text=f"🎯 FPS {fps:.0f}", 
				fill=self.theme["fps"], 
				anchor="w", 
				font=("Segoe UI", 11, "bold")
			)

		# Mini grafikler (sağ alt)
		chart_x = panel_x + panel_w - 80
		chart_y = panel_y + panel_h - 40
		chart_w = 60
		chart_h = 25
		
		if len(self._animation_data["cpu"]) > 1:
			self._draw_mini_chart(chart_x, chart_y, chart_w, chart_h, self._animation_data["cpu"], self.theme["cpu"])

	def loop_once(self) -> None:
		"""Ana döngü."""
		# Animasyon güncellemesi
		current_time = time.time()
		if current_time - self.last_animation_time > 0.1:  # 10 FPS animasyon
			self.animation_frame += 1
			self.last_animation_time = current_time
		
		self.root.update_idletasks()
		self.root.update()

	def close(self) -> None:
		"""Pencereyi kapat."""
		if self.on_close:
			self.on_close()
		self.root.destroy()

# Eski API uyumluluğu için alias
OverlayWindow = ModernOverlayWindow
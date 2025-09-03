import tkinter as tk
from typing import Callable, Optional

class OverlayWindow:
	"""Ustte kalan, saydam, suruklenebilir minimal overlay.

	set_text ile metin; set_metrics ile barli gorunum destekler.
	"""

	def __init__(self, on_close: Optional[Callable[[], None]] = None) -> None:
		self.root = tk.Tk()
		self.root.title("OSD Overlay")
		self.root.attributes("-topmost", True)
		self.root.configure(bg="#0e0e12")
		self.root.attributes("-alpha", 0.95)
		self.root.overrideredirect(True)

		self.on_close = on_close
		self.is_locked = False

		# Tema
		self.color_bg = "#0e0e12"
		self.color_panel = "#16161d"
		self.color_text = "#e6e6e6"
		self.color_accent = "#7aa2f7"
		self.color_cpu = "#f7768e"
		self.color_gpu = "#9ece6a"
		self.color_ram = "#e0af68"
		self.color_fps = "#7dcfff"

		self.canvas = tk.Canvas(self.root, width=360, height=140, bg=self.color_bg, highlightthickness=0)
		self.canvas.pack()

		self.banner = ""
		self.text_fallback = tk.StringVar(value="Yukleniyor...")
		self.label = tk.Label(
			self.root,
			textvariable=self.text_fallback,
			fg=self.color_accent,
			bg=self.color_bg,
			font=("Consolas", 14, "bold"),
			justify="left",
			anchor="w",
			padx=10,
			pady=6,
		)
		self.label.place(x=8, y=8)

		# Drag
		self.canvas.bind("<ButtonPress-1>", self._start_move)
		self.canvas.bind("<B1-Motion>", self._on_move)
		self.root.bind("<Escape>", lambda e: self.close())
		self.root.bind("<KeyPress-l>", self._toggle_lock)

		self._x = 0
		self._y = 0

		self._last_metrics = None

	def _toggle_lock(self, _event=None):
		self.is_locked = not self.is_locked

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
		self.label.configure(text=content)
		self.text_fallback.set(content)
		self._last_metrics = None
		self._draw()

	def set_metrics(self, *, cpu: float, ram_used: float, ram_total: float,
				  gpu_util: Optional[float] = None, gpu_temp: Optional[float] = None,
				  gpu_mem_used: Optional[float] = None, gpu_mem_total: Optional[float] = None,
				  fps: Optional[float] = None, banner: Optional[str] = None) -> None:
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
		self._draw()

	def _draw_bar(self, x: int, y: int, w: int, h: int, ratio: float, color: str, label: str) -> None:
		ratio = max(0.0, min(1.0, ratio))
		self.canvas.create_rectangle(x, y, x + w, y + h, fill=self.color_panel, outline="")
		self.canvas.create_rectangle(x, y, x + int(w * ratio), y + h, fill=color, outline="")
		self.canvas.create_text(x + 6, y + h / 2, text=label, fill=self.color_text, anchor="w", font=("Consolas", 11))

	def _draw(self) -> None:
		self.canvas.delete("all")
		# Panel
		self.canvas.create_rectangle(4, 4, 356, 136, fill=self.color_panel, outline=self.color_accent)

		if not self._last_metrics:
			# Fallback text
			self.canvas.create_text(20, 24, text=self.text_fallback.get(), fill=self.color_accent, anchor="w", font=("Consolas", 14, "bold"))
			return

		m = self._last_metrics
		if m.get("banner"):
			self.canvas.create_text(20, 20, text=m["banner"], fill=self.color_fps, anchor="w", font=("Consolas", 11, "bold"))

		# CPU bar
		cpu = float(m["cpu"]) / 100.0
		self._draw_bar(20, 32, 320, 16, cpu, self.color_cpu, f"CPU {int(m['cpu'])}%")

		# RAM bar
		ram_total = max(0.1, float(m["ram_total"]))
		ram_ratio = float(m["ram_used"]) / ram_total
		self._draw_bar(20, 56, 320, 16, ram_ratio, self.color_ram, f"RAM {m['ram_used']:.1f}/{m['ram_total']:.1f} GB")

		# GPU bar (opsiyonel)
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
			self._draw_bar(20, 80, 320, 16, float(gpu_util) / 100.0, self.color_gpu, gpu_label)

		# FPS
		fps = m.get("fps")
		if fps is not None:
			self.canvas.create_text(20, 110, text=f"FPS {fps:.0f}", fill=self.color_fps, anchor="w", font=("Consolas", 12, "bold"))

		# pencere boyutu
		self.root.geometry("360x140")

	def loop_once(self) -> None:
		self.root.update_idletasks()
		self.root.update()

	def close(self) -> None:
		if self.on_close:
			self.on_close()
		self.root.destroy()
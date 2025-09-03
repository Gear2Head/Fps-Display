import json
import os
import time
import traceback
from typing import Optional

from metrics import SystemMetricsCollector
from ui_overlay import ModernOverlayWindow

try:
	from fps_presentmon import PresentMonReader
except Exception:
	PresentMonReader = None  # type: ignore

try:
	from tray_manager import TrayManager
except Exception:
	TrayManager = None  # type: ignore

try:
	from auto_updater import AutoUpdater
except Exception:
	AutoUpdater = None  # type: ignore

try:
	from performance_optimizer import PerformanceOptimizer, SmartMetricsCollector, BackgroundTaskManager
except Exception:
	PerformanceOptimizer = None  # type: ignore
	SmartMetricsCollector = None  # type: ignore
	BackgroundTaskManager = None  # type: ignore


def load_config() -> dict:
	config_path = os.path.join(os.path.dirname(__file__), "config.json")
	default_cfg = {
		"refreshMs": 500,
		"presentMon": {
			"enabled": False,
			"processName": "",
		},
		"update": {
			"check": True,
			"url": "",
		},
	}
	if not os.path.exists(config_path):
		return default_cfg
	try:
		with open(config_path, "r", encoding="utf-8") as f:
			user_cfg = json.load(f)
		return {**default_cfg, **user_cfg}
	except Exception:
		return default_cfg


def check_update(url: str) -> Optional[str]:
	if not url:
		return None
	try:
		import requests
		resp = requests.get(url, timeout=3)
		if resp.status_code == 200 and "download" in resp.url:
			return "Guncelleme var"
	except Exception:
		return None
	return None


def ensure_logs_dir() -> str:
	logs_dir = os.path.join(os.path.dirname(__file__), "logs")
	os.makedirs(logs_dir, exist_ok=True)
	return os.path.join(logs_dir, "error.log")


def main() -> None:
	config = load_config()
	refresh_ms: int = int(config.get("refreshMs", 500))

	pm_cfg = config.get("presentMon", {}) or {}
	pm_enabled: bool = bool(pm_cfg.get("enabled", False))
	pm_process: str = str(pm_cfg.get("processName", ""))

	update_cfg = config.get("update", {}) or {}
	update_banner: Optional[str] = None
	if bool(update_cfg.get("check", True)):
		update_banner = check_update(str(update_cfg.get("url", "")))

	# Performans optimizatörü
	optimizer = None
	smart_collector = None
	task_manager = None
	
	if PerformanceOptimizer is not None:
		optimizer = PerformanceOptimizer(target_fps=2)
		task_manager = BackgroundTaskManager()
		task_manager.start()

	# Otomatik güncelleme
	updater = None
	if AutoUpdater is not None and bool(update_cfg.get("check", True)):
		updater = AutoUpdater(current_version="2.0.0")
		# İlk güncelleme kontrolü
		try:
			updater.check_and_update()
		except Exception:
			pass

	present_mon: Optional[PresentMonReader] = None
	if pm_enabled and PresentMonReader is not None and pm_process:
		present_mon = PresentMonReader(pm_process)
		present_mon.start()

	# Metrik toplayıcı
	base_collector = SystemMetricsCollector()
	if SmartMetricsCollector is not None and optimizer is not None:
		collector = SmartMetricsCollector(base_collector, optimizer)
	else:
		collector = base_collector

	overlay = ModernOverlayWindow(on_close=None)
	
	# Tray manager
	tray_manager = None
	if TrayManager is not None:
		try:
			tray_manager = TrayManager(
				on_show=lambda: overlay.root.deiconify(),
				on_hide=lambda: overlay.root.withdraw(),
				on_quit=lambda: overlay.close()
			)
			tray_manager.start()
		except Exception:
			tray_manager = None

	# Arka plan görevleri
	if task_manager is not None:
		# Performans optimizasyonu
		task_manager.add_task("optimize", lambda: optimizer.optimize_performance() if optimizer else None, 5.0)
		# Güncelleme kontrolü (her 10 dakikada bir)
		if updater is not None:
			task_manager.add_task("update_check", lambda: updater.check_and_update(), 600.0)

	try:
		frame_count = 0
		while True:
			# Frame süresini güncelle
			if optimizer is not None:
				optimizer.update_frame_time()
			
			# Metrikleri topla
			m = collector.get_metrics()
			fps_val: Optional[float] = None
			if present_mon is not None:
				fps_val = present_mon.read_fps()

			# Performans bilgilerini banner'a ekle
			performance_banner = update_banner
			if optimizer is not None and frame_count % 30 == 0:  # Her 30 frame'de bir
				perf_report = optimizer.get_performance_report()
				if perf_report["optimization_active"]:
					performance_banner = f"⚡ Optimizasyon aktif | {perf_report['avg_cpu']:.0f}% CPU"

			overlay.set_metrics(
				cpu=float(m.get("cpu_percent", 0.0)),
				ram_used=float(m.get("ram_used_gb", 0.0)),
				ram_total=float(m.get("ram_total_gb", 0.0)),
				gpu_util=(None if m.get("gpu_util_percent") is None else float(m.get("gpu_util_percent"))),
				gpu_temp=(None if m.get("gpu_temp_c") is None else float(m.get("gpu_temp_c"))),
				gpu_mem_used=(None if m.get("gpu_mem_used_gb") is None else float(m.get("gpu_mem_used_gb"))),
				gpu_mem_total=(None if m.get("gpu_mem_total_gb") is None else float(m.get("gpu_mem_total_gb"))),
				fps=fps_val,
				banner=performance_banner,
			)

			overlay.loop_once()
			
			# Akıllı yenileme hızı
			if optimizer is not None:
				refresh_ms = optimizer.get_optimal_refresh_rate()
			
			time.sleep(max(0.01, refresh_ms / 1000.0))
			frame_count += 1
			
	except KeyboardInterrupt:
		pass
	except Exception:
		log_path = ensure_logs_dir()
		with open(log_path, "a", encoding="utf-8") as f:
			f.write("\n" + traceback.format_exc() + "\n")
	finally:
		if present_mon is not None:
			present_mon.stop()
		if tray_manager is not None:
			tray_manager.stop()
		if task_manager is not None:
			task_manager.stop()
		base_collector.close()
		overlay.close()


if __name__ == "__main__":
	main()

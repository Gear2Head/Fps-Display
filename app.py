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

	present_mon: Optional[PresentMonReader] = None
	if pm_enabled and PresentMonReader is not None and pm_process:
		present_mon = PresentMonReader(pm_process)
		present_mon.start()

	collector = SystemMetricsCollector()
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

	try:
		while True:
			m = collector.get_metrics()
			fps_val: Optional[float] = None
			if present_mon is not None:
				fps_val = present_mon.read_fps()

			overlay.set_metrics(
				cpu=float(m.get("cpu_percent", 0.0)),
				ram_used=float(m.get("ram_used_gb", 0.0)),
				ram_total=float(m.get("ram_total_gb", 0.0)),
				gpu_util=(None if m.get("gpu_util_percent") is None else float(m.get("gpu_util_percent"))),
				gpu_temp=(None if m.get("gpu_temp_c") is None else float(m.get("gpu_temp_c"))),
				gpu_mem_used=(None if m.get("gpu_mem_used_gb") is None else float(m.get("gpu_mem_used_gb"))),
				gpu_mem_total=(None if m.get("gpu_mem_total_gb") is None else float(m.get("gpu_mem_total_gb"))),
				fps=fps_val,
				banner=update_banner,
			)

			overlay.loop_once()
			time.sleep(max(0.01, refresh_ms / 1000.0))
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
		collector.close()
		overlay.close()


if __name__ == "__main__":
	main()

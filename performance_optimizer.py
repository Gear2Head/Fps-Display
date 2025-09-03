import time
import threading
import queue
import psutil
from typing import Dict, Any, Optional, Callable
from collections import deque
import gc

class PerformanceOptimizer:
	"""Performans optimizasyonu ve akıllı yenileme sistemi."""

	def __init__(self, target_fps: int = 2, max_history: int = 60):
		self.target_fps = target_fps
		self.max_history = max_history
		self.frame_times = deque(maxlen=max_history)
		self.cpu_usage_history = deque(maxlen=max_history)
		self.last_frame_time = time.time()
		
		# Akıllı yenileme
		self.adaptive_refresh = True
		self.min_refresh_ms = 100
		self.max_refresh_ms = 2000
		self.current_refresh_ms = 500
		
		# Performans metrikleri
		self.performance_metrics = {
			"avg_frame_time": 0.0,
			"fps": 0.0,
			"cpu_usage": 0.0,
			"memory_usage": 0.0
		}
		
		# Optimizasyon ayarları
		self.optimization_settings = {
			"enable_gc": True,
			"gc_interval": 30,  # saniye
			"memory_threshold": 100 * 1024 * 1024,  # 100MB
			"cpu_threshold": 80.0,  # %
			"adaptive_refresh": True
		}
		
		self.last_gc_time = time.time()

	def update_frame_time(self):
		"""Frame süresini güncelle."""
		current_time = time.time()
		frame_time = current_time - self.last_frame_time
		self.frame_times.append(frame_time)
		self.last_frame_time = current_time
		
		# Ortalama frame süresi
		if self.frame_times:
			self.performance_metrics["avg_frame_time"] = sum(self.frame_times) / len(self.frame_times)
			self.performance_metrics["fps"] = 1.0 / self.performance_metrics["avg_frame_time"] if self.performance_metrics["avg_frame_time"] > 0 else 0

	def update_cpu_usage(self):
		"""CPU kullanımını güncelle."""
		try:
			cpu_percent = psutil.cpu_percent(interval=None)
			self.cpu_usage_history.append(cpu_percent)
			self.performance_metrics["cpu_usage"] = cpu_percent
			
			# Ortalama CPU kullanımı
			if self.cpu_usage_history:
				avg_cpu = sum(self.cpu_usage_history) / len(self.cpu_usage_history)
				self.performance_metrics["avg_cpu_usage"] = avg_cpu
		except:
			pass

	def update_memory_usage(self):
		"""Bellek kullanımını güncelle."""
		try:
			process = psutil.Process()
			memory_info = process.memory_info()
			self.performance_metrics["memory_usage"] = memory_info.rss
		except:
			pass

	def should_optimize(self) -> bool:
		"""Optimizasyon gerekli mi kontrol et."""
		# CPU yüksekse
		if self.performance_metrics["cpu_usage"] > self.optimization_settings["cpu_threshold"]:
			return True
		
		# Bellek yüksekse
		if self.performance_metrics["memory_usage"] > self.optimization_settings["memory_threshold"]:
			return True
		
		# FPS düşükse
		if self.performance_metrics["fps"] < self.target_fps * 0.8:
			return True
		
		return False

	def optimize_performance(self):
		"""Performans optimizasyonu yap."""
		# Garbage collection
		if self.optimization_settings["enable_gc"]:
			current_time = time.time()
			if current_time - self.last_gc_time > self.optimization_settings["gc_interval"]:
				gc.collect()
				self.last_gc_time = current_time
		
		# Yenileme hızını ayarla
		if self.optimization_settings["adaptive_refresh"]:
			self._adjust_refresh_rate()

	def _adjust_refresh_rate(self):
		"""Yenileme hızını akıllıca ayarla."""
		avg_cpu = self.performance_metrics.get("avg_cpu_usage", 0)
		current_fps = self.performance_metrics["fps"]
		
		# CPU yüksekse yenileme hızını azalt
		if avg_cpu > 70:
			self.current_refresh_ms = min(self.max_refresh_ms, self.current_refresh_ms * 1.2)
		# CPU düşükse yenileme hızını artır
		elif avg_cpu < 30 and current_fps < self.target_fps:
			self.current_refresh_ms = max(self.min_refresh_ms, self.current_refresh_ms * 0.9)
		
		# Sınırları kontrol et
		self.current_refresh_ms = max(self.min_refresh_ms, min(self.max_refresh_ms, self.current_refresh_ms))

	def get_optimal_refresh_rate(self) -> int:
		"""Optimal yenileme hızını döndür."""
		return int(self.current_refresh_ms)

	def get_performance_report(self) -> Dict[str, Any]:
		"""Performans raporu döndür."""
		return {
			"metrics": self.performance_metrics.copy(),
			"refresh_rate": self.current_refresh_ms,
			"optimization_active": self.should_optimize(),
			"frame_count": len(self.frame_times),
			"avg_cpu": sum(self.cpu_usage_history) / len(self.cpu_usage_history) if self.cpu_usage_history else 0
		}

	def reset_metrics(self):
		"""Metrikleri sıfırla."""
		self.frame_times.clear()
		self.cpu_usage_history.clear()
		self.current_refresh_ms = 500
		self.last_gc_time = time.time()

class SmartMetricsCollector:
	"""Akıllı metrik toplayıcı - gereksiz çağrıları önler."""

	def __init__(self, base_collector, optimizer: PerformanceOptimizer):
		self.base_collector = base_collector
		self.optimizer = optimizer
		self.cached_metrics = {}
		self.last_collection_time = 0
		self.collection_interval = 0.5  # 500ms cache

	def get_metrics(self) -> Dict[str, Any]:
		"""Metrikleri akıllıca topla."""
		current_time = time.time()
		
		# Cache kontrolü
		if current_time - self.last_collection_time < self.collection_interval:
			return self.cached_metrics
		
		# Yeni metrikleri topla
		try:
			metrics = self.base_collector.get_metrics()
			self.cached_metrics = metrics
			self.last_collection_time = current_time
			
			# Performans metriklerini güncelle
			self.optimizer.update_cpu_usage()
			self.optimizer.update_memory_usage()
			
			return metrics
		except Exception as e:
			# Hata durumunda cache'i döndür
			return self.cached_metrics

class BackgroundTaskManager:
	"""Arka plan görev yöneticisi."""

	def __init__(self):
		self.tasks = {}
		self.task_queue = queue.Queue()
		self.worker_thread = None
		self.running = False

	def start(self):
		"""Arka plan işleyicisini başlat."""
		if not self.running:
			self.running = True
			self.worker_thread = threading.Thread(target=self._worker, daemon=True)
			self.worker_thread.start()

	def stop(self):
		"""Arka plan işleyicisini durdur."""
		self.running = False
		if self.worker_thread:
			self.worker_thread.join(timeout=1)

	def add_task(self, task_id: str, task_func: Callable, interval: float = 1.0):
		"""Arka plan görevi ekle."""
		self.tasks[task_id] = {
			"func": task_func,
			"interval": interval,
			"last_run": 0
		}

	def remove_task(self, task_id: str):
		"""Arka plan görevini kaldır."""
		if task_id in self.tasks:
			del self.tasks[task_id]

	def _worker(self):
		"""Arka plan işleyici."""
		while self.running:
			try:
				current_time = time.time()
				
				for task_id, task_info in self.tasks.items():
					if current_time - task_info["last_run"] >= task_info["interval"]:
						try:
							task_info["func"]()
							task_info["last_run"] = current_time
						except Exception as e:
							print(f"Arka plan görev hatası ({task_id}): {e}")
				
				time.sleep(0.1)  # 100ms bekle
			except Exception as e:
				print(f"Arka plan işleyici hatası: {e}")
				time.sleep(1)

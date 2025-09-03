import psutil
from typing import Dict, Optional

try:
	from pynvml import (
		nvmlInit,
		nvmlShutdown,
		nvmlDeviceGetHandleByIndex,
		nvmlDeviceGetTemperature,
		nvmlDeviceGetUtilizationRates,
		nvmlDeviceGetMemoryInfo,
		nvmlDeviceGetFanSpeed,
		nvmlDeviceGetClockInfo,
		NVML_TEMPERATURE_GPU,
		NVML_CLOCK_GRAPHICS,
	)
	_NV_AVAILABLE = True
except Exception:
	_NV_AVAILABLE = False


class SystemMetricsCollector:
	"""Toplayici: CPU, RAM ve (varsa) NVIDIA GPU metrikleri."""

	def __init__(self) -> None:
		self._nv_handle = None
		if _NV_AVAILABLE:
			try:
				nvmlInit()
				self._nv_handle = nvmlDeviceGetHandleByIndex(0)
			except Exception:
				self._nv_handle = None

	def close(self) -> None:
		if _NV_AVAILABLE and self._nv_handle is not None:
			try:
				nvmlShutdown()
			except Exception:
				pass

	def get_metrics(self) -> Dict[str, Optional[float]]:
		cpu_percent = psutil.cpu_percent(interval=None)
		virtual_mem = psutil.virtual_memory()
		ram_used_gb = (virtual_mem.total - virtual_mem.available) / (1024 ** 3)
		ram_total_gb = virtual_mem.total / (1024 ** 3)

		metrics: Dict[str, Optional[float]] = {
			"cpu_percent": cpu_percent,
			"ram_used_gb": round(ram_used_gb, 2),
			"ram_total_gb": round(ram_total_gb, 2),
		}

		# GPU (NVIDIA NVML varsa)
		if self._nv_handle is not None:
			try:
				gpu_temp = nvmlDeviceGetTemperature(self._nv_handle, NVML_TEMPERATURE_GPU)
				util = nvmlDeviceGetUtilizationRates(self._nv_handle)
				mem = nvmlDeviceGetMemoryInfo(self._nv_handle)
				fan = nvmlDeviceGetFanSpeed(self._nv_handle)
				clock = nvmlDeviceGetClockInfo(self._nv_handle, NVML_CLOCK_GRAPHICS)

				metrics.update(
					{
						"gpu_temp_c": float(gpu_temp),
						"gpu_util_percent": float(util.gpu),
						"gpu_mem_used_gb": round(mem.used / (1024 ** 3), 2),
						"gpu_mem_total_gb": round(mem.total / (1024 ** 3), 2),
						"gpu_fan_percent": float(fan),
						"gpu_clock_mhz": float(clock),
					}
				)
			except Exception:
				# NVML basarisizsa None birak
				metrics.update(
					{
						"gpu_temp_c": None,
						"gpu_util_percent": None,
						"gpu_mem_used_gb": None,
						"gpu_mem_total_gb": None,
						"gpu_fan_percent": None,
						"gpu_clock_mhz": None,
					}
				)
		else:
			metrics.update(
				{
					"gpu_temp_c": None,
					"gpu_util_percent": None,
					"gpu_mem_used_gb": None,
					"gpu_mem_total_gb": None,
					"gpu_fan_percent": None,
					"gpu_clock_mhz": None,
				}
			)

		return metrics
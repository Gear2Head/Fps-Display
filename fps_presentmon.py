import subprocess
import sys
import re
from typing import Optional

class PresentMonReader:
	"""PresentMon ile FPS okumasi yapar. PresentMon sistemde olmali.

	process_name ornegi: 'witcher3.exe' """

	def __init__(self, process_name: Optional[str] = None) -> None:
		self.process_name = process_name
		self.proc: Optional[subprocess.Popen] = None

	def start(self) -> None:
		if not self.process_name:
			return
		try:
			# CSV satirlari: MsBetweenPresents ...
			self.proc = subprocess.Popen(
				[
					"presentmon",
					"-process_name",
					self.process_name,
					"-output_stdout",
					"-no_csv",
					"-simple",
				],
				shell=True,
				stdout=subprocess.PIPE,
				stderr=subprocess.STDOUT,
				text=True,
			)
		except Exception:
			self.proc = None

	def read_fps(self) -> Optional[float]:
		if self.proc is None or self.proc.stdout is None:
			return None
		try:
			line = self.proc.stdout.readline().strip()
			# Beklenen ornek: "pid 1234, fps 60.1"
			match = re.search(r"fps\s+([0-9]+\.?[0-9]*)", line, re.IGNORECASE)
			if match:
				return float(match.group(1))
		except Exception:
			return None
		return None

	def stop(self) -> None:
		if self.proc:
			try:
				self.proc.terminate()
			except Exception:
				pass
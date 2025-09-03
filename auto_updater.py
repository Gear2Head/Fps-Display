import os
import sys
import json
import subprocess
import tempfile
import shutil
import requests
import hashlib
from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import messagebox, ttk
import threading

class AutoUpdater:
	"""Otomatik güncelleme sistemi."""

	def __init__(self, current_version: str = "2.0.0"):
		self.current_version = current_version
		self.repo_owner = "Gear2Head"
		self.repo_name = "Fps-Display"
		self.update_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
		self.download_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/latest/download/OSD-Overlay-Setup.exe"

	def check_for_updates(self) -> Optional[Dict[str, Any]]:
		"""Güncelleme kontrolü yap."""
		try:
			response = requests.get(self.update_url, timeout=10)
			response.raise_for_status()
			
			release_data = response.json()
			latest_version = release_data.get("tag_name", "").lstrip("v")
			
			if self._is_newer_version(latest_version, self.current_version):
				return {
					"version": latest_version,
					"tag_name": release_data.get("tag_name"),
					"body": release_data.get("body", ""),
					"published_at": release_data.get("published_at"),
					"download_url": self.download_url
				}
		except Exception as e:
			print(f"Güncelleme kontrolü hatası: {e}")
		
		return None

	def _is_newer_version(self, latest: str, current: str) -> bool:
		"""Versiyon karşılaştırması."""
		try:
			latest_parts = [int(x) for x in latest.split(".")]
			current_parts = [int(x) for x in current.split(".")]
			
			# Eksik kısımları 0 ile doldur
			max_len = max(len(latest_parts), len(current_parts))
			latest_parts.extend([0] * (max_len - len(latest_parts)))
			current_parts.extend([0] * (max_len - len(current_parts)))
			
			return latest_parts > current_parts
		except:
			return False

	def download_update(self, download_url: str, progress_callback=None) -> Optional[str]:
		"""Güncelleme dosyasını indir."""
		try:
			response = requests.get(download_url, stream=True, timeout=30)
			response.raise_for_status()
			
			total_size = int(response.headers.get('content-length', 0))
			downloaded = 0
			
			# Geçici dosya oluştur
			temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".exe")
			
			for chunk in response.iter_content(chunk_size=8192):
				if chunk:
					temp_file.write(chunk)
					downloaded += len(chunk)
					
					if progress_callback and total_size > 0:
						progress = (downloaded / total_size) * 100
						progress_callback(progress)
			
			temp_file.close()
			return temp_file.name
			
		except Exception as e:
			print(f"İndirme hatası: {e}")
			return None

	def verify_download(self, file_path: str) -> bool:
		"""İndirilen dosyayı doğrula."""
		try:
			# Basit dosya boyutu kontrolü
			if os.path.getsize(file_path) < 1024 * 1024:  # 1MB'den küçükse şüpheli
				return False
			return True
		except:
			return False

	def install_update(self, installer_path: str) -> bool:
		"""Güncellemeyi kur."""
		try:
			# Kurulum dosyasını çalıştır
			subprocess.Popen([installer_path, "/S"], shell=True)
			return True
		except Exception as e:
			print(f"Kurulum hatası: {e}")
			return False

	def show_update_dialog(self, update_info: Dict[str, Any]) -> bool:
		"""Güncelleme dialog'u göster."""
		root = tk.Tk()
		root.withdraw()  # Ana pencereyi gizle
		
		# Güncelleme penceresi
		update_window = tk.Toplevel(root)
		update_window.title("Güncelleme Mevcut")
		update_window.geometry("500x400")
		update_window.resizable(False, False)
		update_window.attributes("-topmost", True)
		update_window.grab_set()  # Modal yap
		
		# Başlık
		title_label = tk.Label(
			update_window,
			text=f"Yeni Sürüm Mevcut: v{update_info['version']}",
			font=("Segoe UI", 14, "bold"),
			fg="#2d3748"
		)
		title_label.pack(pady=10)
		
		# Mevcut sürüm
		current_label = tk.Label(
			update_window,
			text=f"Mevcut sürüm: v{self.current_version}",
			font=("Segoe UI", 10),
			fg="#718096"
		)
		current_label.pack()
		
		# Changelog
		changelog_frame = tk.Frame(update_window)
		changelog_frame.pack(fill="both", expand=True, padx=20, pady=10)
		
		tk.Label(changelog_frame, text="Değişiklikler:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
		
		changelog_text = tk.Text(
			changelog_frame,
			height=10,
			wrap="word",
			font=("Consolas", 9),
			bg="#f7fafc",
			fg="#2d3748"
		)
		changelog_text.pack(fill="both", expand=True, pady=5)
		
		# Changelog içeriğini ekle
		changelog_content = update_info.get("body", "Değişiklik bilgisi mevcut değil.")
		changelog_text.insert("1.0", changelog_content)
		changelog_text.config(state="disabled")
		
		# Progress bar
		progress_frame = tk.Frame(update_window)
		progress_frame.pack(fill="x", padx=20, pady=10)
		
		progress_label = tk.Label(progress_frame, text="İndiriliyor...", font=("Segoe UI", 9))
		progress_label.pack()
		
		progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
		progress_bar.pack(fill="x", pady=5)
		
		# Butonlar
		button_frame = tk.Frame(update_window)
		button_frame.pack(fill="x", padx=20, pady=10)
		
		result = {"update": False}
		
		def update_progress(percent):
			progress_bar["value"] = percent
			progress_label.config(text=f"İndiriliyor... {percent:.1f}%")
			update_window.update()
		
		def start_update():
			progress_frame.pack(fill="x", padx=20, pady=10)
			update_btn.config(state="disabled")
			later_btn.config(state="disabled")
			
			# Arka planda indirme
			def download_thread():
				try:
					downloaded_file = self.download_update(update_info["download_url"], update_progress)
					
					if downloaded_file and self.verify_download(downloaded_file):
						progress_label.config(text="Kurulum başlatılıyor...")
						update_window.update()
						
						if self.install_update(downloaded_file):
							result["update"] = True
							update_window.quit()
						else:
							messagebox.showerror("Hata", "Kurulum başlatılamadı!")
							update_window.quit()
					else:
						messagebox.showerror("Hata", "İndirilen dosya doğrulanamadı!")
						update_window.quit()
						
				except Exception as e:
					messagebox.showerror("Hata", f"Güncelleme hatası: {e}")
					update_window.quit()
			
			threading.Thread(target=download_thread, daemon=True).start()
		
		def skip_update():
			result["update"] = False
			update_window.quit()
		
		update_btn = tk.Button(
			button_frame,
			text="Güncelle",
			command=start_update,
			bg="#4299e1",
			fg="white",
			font=("Segoe UI", 10, "bold"),
			padx=20
		)
		update_btn.pack(side="right", padx=5)
		
		later_btn = tk.Button(
			button_frame,
			text="Daha Sonra",
			command=skip_update,
			bg="#a0aec0",
			fg="white",
			font=("Segoe UI", 10),
			padx=20
		)
		later_btn.pack(side="right", padx=5)
		
		# İlk başta progress bar'ı gizle
		progress_frame.pack_forget()
		
		# Dialog'u göster
		update_window.mainloop()
		update_window.destroy()
		root.destroy()
		
		return result["update"]

	def check_and_update(self) -> bool:
		"""Güncelleme kontrolü yap ve gerekirse güncelle."""
		update_info = self.check_for_updates()
		
		if update_info:
			return self.show_update_dialog(update_info)
		
		return False

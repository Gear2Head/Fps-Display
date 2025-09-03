# OSD Overlay (CPU/GPU/RAM + FPS)

Bu proje, Windows'ta ekranin ustunde kalan kucuk bir overlay ile CPU, GPU ve RAM kullanimi ile sicaklik gibi verileri gosterir. Opsiyonel olarak PresentMon kuruluysa FPS de gosterebilir.

## Kurulum (gelistirme)

1. Python 3.10+ kurulu olmalidir.
2. Gerekli kutuphaneleri yukleyin:
```bash
pip install -r requirements.txt
```
3. Calistirin:
```bash
python app.py
```

## Paketleme (tek dosya .exe)
```powershell
./build.ps1
```
`dist/OSD-Overlay.exe` olusur.

## Windows Yukleyici (NSIS)
- `installer.nsi` derlenince `OSD-Overlay-Setup.exe` olusur.

## Online Launcher (Bootstrapper)
- `launcher_config.json` icinde `installerUrl` (Latest download) ve opsiyonel `sha256` verin.
- `installerUrl` (ornek, sizin repo):
```
https://github.com/Gear2Head/Fps-Display/releases/latest/download/OSD-Overlay-Setup.exe
```
- `launcher.nsi` derlenince `OSD-Overlay-Launcher.exe` indirip calistirir. SHA-256 dogrulamasi varsa indirme sonra kontrol edilir.

## Barindirma: GitHub Releases
- Tag atinca Actions otomatik release ve assetlari olusturur.
- Sabit indirme URL:
```
https://github.com/Gear2Head/Fps-Display/releases/latest/download/OSD-Overlay-Setup.exe
```

## Guncelleme Kontrolu ve Loglar
- `config.json` -> `update.url` latest release sayfasini isaret eder; uygulama baslangicta kisaca kontrol edip banner gosterir.
- Hatalar `logs/error.log` dosyasina yazilir.

## FPS (opsiyonel)
```json
{
  "refreshMs": 500,
  "presentMon": { "enabled": true, "processName": "oyun.exe" }
}
```
PresentMon PATH'te olmalidir.

## Kisa Yollar
- Overlay konumunu surukleyerek degistirebilirsiniz.
- `L` tusu: Kilitle/Serbest birak (kilitliyken suruklenemez).
- `Esc` tusu: Cikis.

## Notlar
- Uygulama yalnizca Windows icin optimize edilmistir (ustte kalma ve saydamlik ozellikleri).
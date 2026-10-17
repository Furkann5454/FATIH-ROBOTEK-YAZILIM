# FATIH ROBOTEK YAZILIM — Modüler Proje

Bu repo, yüklenen orijinal 12 Python betiğindeki **uçuş ve GPS fonksiyonlarını, görev parametrelerini ve farklı çalışma profillerini koruyarak** modüler yapıya ayırır. Fonksiyon gövdelerinin AST karşılaştırması doğrulanmıştır. Bu, **SITL/gerçek uçuşta birebir aynı davranışın ispatı değildir**. Kod üretiminde algoritma veya uçuş parametreleri bilinçli olarak değiştirilmemiştir, ancak çalıştırma arayüzü değişmiştir.

## Dizinler

```text
robotek/
  __main__.py, cli.py, runtime.py, profiles.json, gps_collector.py
  components/
    geometry.py, gps.py, flight.py, safety.py, landing.py, operator.py, mission.py
ROBOTEK/
  Robotek_Ardupilot_Land.py, Robotek_Simplegoto_land.py
  Inemezsek/   # Dört görev profili için kısa giriş betiği
GPS_Alma/
  GPS_Al.py   # GPS aracı için kısa giriş betiği
saha_konumlar.txt
tests/
  test_robotek.py
requirements.txt
pyproject.toml
```

**Hiçbir eski kod kopyası, yedek dizini veya `legacy/original` arşivi bulunmaz.** Önceki `Yedekler/` betiklerinin farklı görev davranışları atılmamıştır: `yedek_0`, `yedek_1`, `yedek_3`, `yedek_4`, `yedek_5` isimleriyle **profillerde** tutulur. Bu isimler yalnızca profil kimliğidir; dosya yedeği değildir. `profiles.json` içindeki `source` değerleri, kaldırılmış eski dosyaların tarihsel kaynak yolunu tanımlar.

## Komutlar (Ubuntu / Python 3.10 tavsiye)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m unittest discover -s tests -v

# Drone bağlantısı yapmaz:
python3 -m robotek list
python3 -m robotek show --profile ardupilot_land
python3 -m robotek run --profile ardupilot_land

# SITL/cihaz bağlantısı kurar ve uçuş komutu gönderebilir:
python3 -m robotek run --profile ardupilot_land --connection udp:127.0.0.1:14550 --execute

# Diğer profil örneği (eski Yedekler/ davranışı, ama kod yedeği yok):
python3 -m robotek run --profile yedek_3 --connection udp:127.0.0.1:14550 --execute
```

Eski `ROBOTEK/` ve `GPS_Alma/` betikleri yeni modüler giriş noktasına yönlendirir. Uçuş betikleri artık bağlantı/başlatma için ayrıca `--execute` ister. Bu bilinçli CLI güvenlik farkıdır; önceki otomatik başlatma korunmamıştır. `GPS_Alma/GPS_Al.py` eski davranışla bağlantıyı doğrudan açar.

Uçuş güvenliği: Profilde kayıtlı **gerçek saha koordinatları**, irtifa sınırları ve failsafe davranışları aynen tutulmuştur. SITL başlangıç yeri ile profil koordinatlarını eşleştirmeden uçuş başlatmayın. `--execute` öncesinde görevleri, bağlantıyı ve failsafe'leri gözden geçirin. Bu paket gerçek uçuşla doğrulanmış değildir.

## GitHub'daki mevcut içeriğin yerini almak

Aşağıdaki örnek, ZIP'i çıkardığınız dizinin içeriğini klonlanmış repoya `rsync --delete` ile aktarır; `.git` klasörünü saklar, gereksiz arşiv/yedek dosyası oluşturmaz:

```bash
cd ~/Downloads
unzip -q FATIH-ROBOTEK-YAZILIM-MODULER-v3.zip
git clone https://github.com/Furkann5454/FATIH-ROBOTEK-YAZILIM.git FATIH-ROBOTEK-GITHUB
rsync -a --delete --exclude='.git/' ~/Downloads/FATIH-ROBOTEK-YAZILIM-MODULER-v3/ ~/Downloads/FATIH-ROBOTEK-GITHUB/
cd ~/Downloads/FATIH-ROBOTEK-GITHUB
git add -A
git commit -m "refactor: moduler mimariye gecis"
git push origin main
```

Bu işlemler GitHub'ın **görünen güncel dosyalarını** tamamen değiştirir. Git geçmişindeki eski commitler otomatik olarak silinmez; eski içeriğe ait yeni bir ZIP veya yedek branch oluşturulmaz.

"""GPS point collection and averaging extracted from GPS_Al.py."""
import time
import sys
from dronekit import connect

def baglan(self):
    print("Drone'a baglaniliyor...")
    print('Baglanti:', self.config.BAGLANTI_ADRESI)
    if self.config.BAUD is None:
        vehicle = connect(self.config.BAGLANTI_ADRESI, wait_ready=True, timeout=60)
    else:
        vehicle = connect(self.config.BAGLANTI_ADRESI, wait_ready=True, baud=self.config.BAUD, timeout=60)
    print('Baglandi.')
    return vehicle

def gps_hazir_bekle(self, vehicle):
    print('GPS hazir olmasi bekleniyor...')
    while True:
        konum = vehicle.location.global_relative_frame
        gps = vehicle.gps_0
        print(f'GPS Fix: {gps.fix_type} | Uydu: {gps.satellites_visible} | EKF: {vehicle.ekf_ok} | Lat: {konum.lat} | Lon: {konum.lon}')
        if konum.lat is not None and konum.lon is not None and (gps.fix_type is not None) and (gps.fix_type >= 3) and vehicle.ekf_ok:
            print('GPS hazir.')
            return
        time.sleep(1)

def gps_ortalama_al(self, vehicle):
    latlar = []
    lonlar = []
    print(f'{self.config.ORNEK_SAYISI} adet GPS ornegi aliniyor...')
    for i in range(self.config.ORNEK_SAYISI):
        konum = vehicle.location.global_relative_frame
        if konum.lat is not None and konum.lon is not None:
            latlar.append(konum.lat)
            lonlar.append(konum.lon)
        print(f'{i + 1}/{self.config.ORNEK_SAYISI} | Lat: {konum.lat} | Lon: {konum.lon}')
        time.sleep(self.config.ORNEK_ARALIGI)
    if len(latlar) == 0:
        print('GPS verisi alinamadi.')
        return (None, None)
    lat_ort = sum(latlar) / len(latlar)
    lon_ort = sum(lonlar) / len(lonlar)
    return (lat_ort, lon_ort)

def main(self):
    vehicle = self.baglan()
    try:
        self.gps_hazir_bekle(vehicle)
        sayac = 1
        while True:
            komut = input("\nNoktaya drone'u koy. GPS almak icin ENTER, cikmak icin q yaz: ")
            if komut.lower() == 'q':
                break
            lat, lon = self.gps_ortalama_al(vehicle)
            if lat is None:
                continue
            print('\n==============================')
            print(f'NOKTA_{sayac}')
            print(f'lat = {lat:.8f}')
            print(f'lon = {lon:.8f}')
            print('------------------------------')
            print("Python'a yapistirmalik:")
            print('{')
            print(f'    "isim": "Hedef_{sayac}",')
            print(f'    "lat": {lat:.8f},')
            print(f'    "lon": {lon:.8f}')
            print('}')
            print('==============================\n')
            sayac += 1
    finally:
        print('Baglanti kapatiliyor...')
        vehicle.close()

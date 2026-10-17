"""Landing implementations; migrated verbatim in behavior from the original versions.

Each suffixed implementation is selected by a mission profile at runtime.
Configuration reads and sibling calls use the controller instance.
Original control flow was migrated to this module; no archive copies are shipped.
"""

import math
import sys
import time
import termios
import tty
import select
from dronekit import VehicleMode, LocationGlobalRelative
from pymavlink import mavutil

# inis_sonrasi_bekle implementation 4903442c421c
def inis_sonrasi_bekle_v4903442c421c(self, sure, nokta_adi):
    if sure <= 0:
        return
    print(f'{nokta_adi} noktasinda {sure} saniye bekleniyor...')
    for kalan in range(sure, 0, -1):
        print(f'Kalan sure: {kalan}')
        time.sleep(1)
    print('Bekleme tamamlandi.')

# land_ol implementation 3a728dbd6387
def land_ol_v3a728dbd6387(self, vehicle, inis_lat, inis_lon, bekleme_suresi=0, zaman_asimi=40):
    print('Inis basliyor...')
    if vehicle.mode.name != 'GUIDED':
        vehicle.mode = VehicleMode('GUIDED')
        while vehicle.mode.name != 'GUIDED':
            print('GUIDED mod bekleniyor...')
            time.sleep(0.5)
    if inis_lat is None or inis_lon is None:
        print('Inis icin hedef konum alinamadi.')
        return False
    print(f'Inis hedef koordinati: Lat={inis_lat:.8f}, Lon={inis_lon:.8f}')
    print('1 metreye iniliyor...')
    hedef_1m = LocationGlobalRelative(inis_lat, inis_lon, 1.0)
    self.simpleGotoMavlink(vehicle, hedef_1m, hedef_1m.alt)
    baslangic_zamani = time.time()
    while True:
        yukseklik = vehicle.location.global_relative_frame.alt
        print(f'Simple_goto inis 1m | Yukseklik: {yukseklik:.2f} m | ARM: {vehicle.armed} | Mod: {vehicle.mode.name}')
        if not vehicle.armed:
            print('Drone zaten DISARM durumda.')
            return True
        if yukseklik <= 1.2:
            print('1 metre bolgesine ulasildi.')
            break
        if time.time() - baslangic_zamani > zaman_asimi:
            print('1 metreye inis zaman asimina girdi.')
            break
        if vehicle.mode.name != 'GUIDED':
            print('Drone GUIDED moddan cikti. Inis iptal.')
            return False
        time.sleep(0.3)
    print(f'{self.config.YAKIN_INIS_IRTIFA:.2f} metre civarinda LAND gecisi hazirlaniyor...')
    hedef_yakin = LocationGlobalRelative(inis_lat, inis_lon, self.config.YAKIN_INIS_IRTIFA)
    self.simpleGotoMavlink(vehicle, hedef_yakin, hedef_yakin.alt)
    ikinci_asama_baslangic = time.time()
    son_komut_zamani = time.time()
    while True:
        yukseklik = vehicle.location.global_relative_frame.alt
        print(f'Simple_goto inis {self.config.YAKIN_INIS_IRTIFA:.2f}m | Yukseklik: {yukseklik:.2f} m | ARM: {vehicle.armed} | Mod: {vehicle.mode.name}')
        if not vehicle.armed:
            print('Drone zaten DISARM durumda.')
            return True
        if yukseklik <= self.config.LAND_GECIS_IRTIFA:
            print('Drone yere yaklasti. LAND moduna geciliyor...')
            break
        if time.time() - son_komut_zamani > 1.0:
            self.simpleGotoMavlink(vehicle, hedef_yakin, hedef_yakin.alt)
            son_komut_zamani = time.time()
        if time.time() - ikinci_asama_baslangic > 20:
            print('Yakin inis zaman asimina girdi. LAND moduna geciliyor...')
            break
        if vehicle.mode.name != 'GUIDED':
            print('Drone GUIDED moddan cikti. Inis iptal.')
            return False
        time.sleep(0.3)
    vehicle.mode = VehicleMode('LAND')
    while vehicle.mode.name != 'LAND':
        print('LAND mod bekleniyor...')
        time.sleep(0.2)
    yerde_aday_baslangic = None
    bekleme_baslangic = None
    land_baslangic = time.time()
    disarm_bekleme_suresi = 0
    disarm_yazildi = False
    arm_bekleme_mesaji_yazildi = False
    son_land_yukseklik = None
    son_land_kontrol_zamani = time.time()
    land_kurtarma_deneme_sayisi = 0
    while True:
        yukseklik = vehicle.location.global_relative_frame.alt
        hiz = vehicle.groundspeed
        if hiz is None:
            hiz = 0
        print(f'LAND son asama | Yukseklik: {yukseklik:.2f} m | Hiz: {hiz:.2f} m/s | ARM: {vehicle.armed} | Mod: {vehicle.mode.name}')
        yerde_gibi = yukseklik <= self.config.YERDE_KABUL_IRTIFA and hiz <= self.config.YERDE_KABUL_HIZ
        if vehicle.armed and vehicle.mode.name == 'LAND' and (not yerde_gibi) and (land_kurtarma_deneme_sayisi < self.config.LAND_KURTARMA_MAX_DENEME):
            if son_land_yukseklik is None:
                son_land_yukseklik = yukseklik
                son_land_kontrol_zamani = time.time()
            else:
                gecen_sure = time.time() - son_land_kontrol_zamani
                irtifa_farki = abs(son_land_yukseklik - yukseklik)
                if gecen_sure >= self.config.LAND_TAKILMA_SURESI:
                    if yukseklik > self.config.YERDE_KABUL_IRTIFA and irtifa_farki <= self.config.LAND_TAKILMA_IRTIFA_FARKI:
                        land_kurtarma_deneme_sayisi += 1
                        kurtarma_sonuc = self.land_takilma_kurtarma(vehicle, inis_lat, inis_lon)
                        if not kurtarma_sonuc:
                            print('LAND takilma kurtarma basarisiz.')
                            return False
                        yerde_aday_baslangic = None
                        bekleme_baslangic = None
                        arm_bekleme_mesaji_yazildi = False
                        son_land_yukseklik = vehicle.location.global_relative_frame.alt
                        son_land_kontrol_zamani = time.time()
                        land_baslangic = time.time()
                        continue
                    son_land_yukseklik = yukseklik
                    son_land_kontrol_zamani = time.time()
        if yerde_gibi:
            if yerde_aday_baslangic is None:
                yerde_aday_baslangic = time.time()
                print('Drone yerde gibi. Yerde onay suresi basladi...')
            yerde_aday_suresi = time.time() - yerde_aday_baslangic
            bekleme_baslat_sarti = yerde_aday_suresi >= self.config.YERDE_ONAY_SURESI and (yukseklik <= self.config.BEKLEME_BASLAT_IRTIFA or not vehicle.armed)
            if bekleme_baslat_sarti and bekleme_baslangic is None:
                bekleme_baslangic = time.time()
                print('Bekleme sayaci basladi.')
            if not vehicle.armed and (not disarm_yazildi):
                disarm_bekleme_suresi = time.time() - yerde_aday_baslangic
                print(f"Drone DISARM oldu. Yerde kabulden disarm'a kadar gecen sure: {disarm_bekleme_suresi:.2f} sn")
                disarm_yazildi = True
            if bekleme_baslangic is not None:
                yerde_gecen_sure = time.time() - bekleme_baslangic
                if yerde_gecen_sure >= bekleme_suresi:
                    if vehicle.armed:
                        if not arm_bekleme_mesaji_yazildi:
                            print('Yerde bekleme tamamlandi ama drone hala ARM durumda. ArduPilot otomatik DISARM bekleniyor...')
                            arm_bekleme_mesaji_yazildi = True
                    else:
                        print(f'Inis ve yerde bekleme tamamlandi. Istenen bekleme: {bekleme_suresi:.2f} sn | Yerde gecen sure: {yerde_gecen_sure:.2f} sn | ARM: {vehicle.armed}')
                        return True
        else:
            yerde_aday_baslangic = None
            bekleme_baslangic = None
            arm_bekleme_mesaji_yazildi = False
        if time.time() - land_baslangic > zaman_asimi + bekleme_suresi + 20:
            print('LAND son asama zaman asimina girdi.')
            return False
        time.sleep(0.2)

# land_ol implementation 3d995af3602f
def land_ol_v3d995af3602f(self, vehicle, bekleme_suresi=0, zaman_asimi=90):
    print('Direkt LAND inisi basliyor...')
    print('GUIDED ile alcalma yok. Direkt LAND moduna geciliyor...')
    vehicle.mode = VehicleMode('LAND')
    land_mod_baslangic = time.time()
    while vehicle.mode.name != 'LAND':
        print('LAND mod bekleniyor...')
        if time.time() - land_mod_baslangic > 5:
            print('LAND moda gecilemedi.')
            return False
        time.sleep(0.2)
    yerde_aday_baslangic = None
    bekleme_baslangic = None
    land_baslangic = time.time()
    arm_bekleme_mesaji_yazildi = False
    while True:
        yukseklik = vehicle.location.global_relative_frame.alt
        hiz = vehicle.groundspeed
        if hiz is None:
            hiz = 0
        print(f'LAND | Yukseklik: {yukseklik:.2f} m | Hiz: {hiz:.2f} m/s | ARM: {vehicle.armed} | Mod: {vehicle.mode.name}')
        if not vehicle.armed:
            print('Drone DISARM oldu. Inis tamamlandi.')
            return True
        yerde_gibi = yukseklik <= self.config.YERDE_KABUL_IRTIFA and hiz <= self.config.YERDE_KABUL_HIZ
        if yerde_gibi:
            if yerde_aday_baslangic is None:
                yerde_aday_baslangic = time.time()
                print('Drone yerde gibi. Yerde onay suresi basladi...')
            yerde_aday_suresi = time.time() - yerde_aday_baslangic
            if yerde_aday_suresi >= self.config.YERDE_ONAY_SURESI and bekleme_baslangic is None:
                bekleme_baslangic = time.time()
                print('Bekleme sayaci basladi.')
            if bekleme_baslangic is not None:
                yerde_gecen_sure = time.time() - bekleme_baslangic
                if yerde_gecen_sure >= bekleme_suresi:
                    if vehicle.armed:
                        if not arm_bekleme_mesaji_yazildi:
                            print('Yerde bekleme tamamlandi ama drone hala ARM durumda. ArduPilot otomatik DISARM bekleniyor...')
                            arm_bekleme_mesaji_yazildi = True
                    else:
                        print('Inis ve yerde bekleme tamamlandi.')
                        return True
        else:
            yerde_aday_baslangic = None
            bekleme_baslangic = None
            arm_bekleme_mesaji_yazildi = False
        if time.time() - land_baslangic > zaman_asimi + bekleme_suresi:
            print('LAND zaman asimina girdi.')
            return False
        time.sleep(0.2)

# land_ol implementation 77097538b55d
def land_ol_v77097538b55d(self, vehicle, inis_lat, inis_lon, zaman_asimi=40):
    print('Inis basliyor...')
    if vehicle.mode.name != 'GUIDED':
        vehicle.mode = VehicleMode('GUIDED')
        while vehicle.mode.name != 'GUIDED':
            print('GUIDED mod bekleniyor...')
            time.sleep(0.5)
    if inis_lat is None or inis_lon is None:
        print('Inis icin hedef konum alinamadi.')
        return False
    print(f'Inis hedef koordinati: Lat={inis_lat:.8f}, Lon={inis_lon:.8f}')
    print('1 metreye iniliyor...')
    hedef_1m = LocationGlobalRelative(inis_lat, inis_lon, 1.0)
    self.simpleGotoMavlink(vehicle, hedef_1m, hedef_1m.alt, self.config.YAVAS_HIZ)
    baslangic_zamani = time.time()
    while True:
        yukseklik = vehicle.location.global_relative_frame.alt
        print(f'Simple_goto inis 1m | Yukseklik: {yukseklik:.2f} m | ARM: {vehicle.armed} | Mod: {vehicle.mode.name}')
        if not vehicle.armed:
            print('Drone zaten DISARM durumda.')
            return True
        if yukseklik <= 1.2:
            print('1 metre bolgesine ulasildi.')
            break
        if time.time() - baslangic_zamani > zaman_asimi:
            print('1 metreye inis zaman asimina girdi.')
            break
        if vehicle.mode.name != 'GUIDED':
            print('Drone GUIDED moddan cikti. Inis iptal.')
            return False
        time.sleep(0.3)
    print('0.2 metreye iniliyor...')
    hedef_02m = LocationGlobalRelative(inis_lat, inis_lon, 0.2)
    self.simpleGotoMavlink(vehicle, hedef_02m, hedef_02m.alt, self.config.YAVAS_HIZ)
    ikinci_asama_baslangic = time.time()
    while True:
        yukseklik = vehicle.location.global_relative_frame.alt
        print(f'Simple_goto inis 0.2m | Yukseklik: {yukseklik:.2f} m | ARM: {vehicle.armed} | Mod: {vehicle.mode.name}')
        if not vehicle.armed:
            print('Drone zaten DISARM durumda.')
            return True
        if yukseklik <= 0.7:
            print('Drone yere yaklasti. LAND moduna geciliyor...')
            break
        if time.time() - ikinci_asama_baslangic > 15:
            print('0.2 metreye inis zaman asimina girdi. LAND moduna geciliyor...')
            break
        if vehicle.mode.name != 'GUIDED':
            print('Drone GUIDED moddan cikti. Inis iptal.')
            return False
        time.sleep(0.3)
    vehicle.mode = VehicleMode('LAND')
    while vehicle.mode.name != 'LAND':
        print('LAND mod bekleniyor...')
        time.sleep(0.2)
    yerde_baslangic = None
    land_baslangic = time.time()
    disarm_gonderildi = False
    while True:
        yukseklik = vehicle.location.global_relative_frame.alt
        hiz = vehicle.groundspeed
        if hiz is None:
            hiz = 0
        print(f'LAND son asama | Yukseklik: {yukseklik:.2f} m | Hiz: {hiz:.2f} m/s | ARM: {vehicle.armed} | Mod: {vehicle.mode.name}')
        if not vehicle.armed:
            print('Drone indi ve DISARM oldu.')
            return True
        yerde_gibi = yukseklik <= 0.3 and hiz <= 0.25
        if yerde_gibi:
            if yerde_baslangic is None:
                yerde_baslangic = time.time()
            if time.time() - yerde_baslangic > 0.8 and (not disarm_gonderildi):
                print('Drone yerde kabul edildi. ArduPilot otomatik DISARM bekleniyor...')
                disarm_gonderildi = True
        else:
            yerde_baslangic = None
        if time.time() - land_baslangic > 20:
            print('LAND son asama zaman asimina girdi.')
            return False
        time.sleep(0.2)

# land_ol implementation 7f1d5f5e2055
def land_ol_v7f1d5f5e2055(self, vehicle, inis_lat, inis_lon, bekleme_suresi=0, disarm_bekle=False, erken_arm=False, zaman_asimi=40):
    print('Inis basliyor...')
    if vehicle.mode.name != 'GUIDED':
        vehicle.mode = VehicleMode('GUIDED')
        while vehicle.mode.name != 'GUIDED':
            print('GUIDED mod bekleniyor...')
            time.sleep(0.5)
    if inis_lat is None or inis_lon is None:
        print('Inis icin hedef konum alinamadi.')
        return (False, 0)
    print(f'Inis hedef koordinati: Lat={inis_lat:.8f}, Lon={inis_lon:.8f}')
    print('1 metreye iniliyor...')
    hedef_1m = LocationGlobalRelative(inis_lat, inis_lon, 1.0)
    self.simpleGotoMavlink(vehicle, hedef_1m, hedef_1m.alt)
    baslangic_zamani = time.time()
    while True:
        yukseklik = vehicle.location.global_relative_frame.alt
        print(f'Simple_goto inis 1m | Yukseklik: {yukseklik:.2f} m | ARM: {vehicle.armed} | Mod: {vehicle.mode.name}')
        if not vehicle.armed:
            print('Drone zaten DISARM durumda.')
            return (True, 0)
        if yukseklik <= 1.2:
            print('1 metre bolgesine ulasildi.')
            break
        if time.time() - baslangic_zamani > zaman_asimi:
            print('1 metreye inis zaman asimina girdi.')
            break
        if vehicle.mode.name != 'GUIDED':
            print('Drone GUIDED moddan cikti. Inis iptal.')
            return (False, 0)
        time.sleep(0.3)
    print('0.5 metre civarinda LAND gecisi hazirlaniyor...')
    hedef_yakin = LocationGlobalRelative(inis_lat, inis_lon, 0.5)
    self.simpleGotoMavlink(vehicle, hedef_yakin, hedef_yakin.alt)
    ikinci_asama_baslangic = time.time()
    while True:
        yukseklik = vehicle.location.global_relative_frame.alt
        print(f'Simple_goto inis 0.5m | Yukseklik: {yukseklik:.2f} m | ARM: {vehicle.armed} | Mod: {vehicle.mode.name}')
        if not vehicle.armed:
            print('Drone zaten DISARM durumda.')
            return (True, 0)
        if yukseklik <= 0.6:
            print('Drone yere yaklasti. LAND moduna geciliyor...')
            break
        if time.time() - ikinci_asama_baslangic > 15:
            print('0.5 metreye inis zaman asimina girdi. LAND moduna geciliyor...')
            break
        if vehicle.mode.name != 'GUIDED':
            print('Drone GUIDED moddan cikti. Inis iptal.')
            return (False, 0)
        time.sleep(0.3)
    vehicle.mode = VehicleMode('LAND')
    while vehicle.mode.name != 'LAND':
        print('LAND mod bekleniyor...')
        time.sleep(0.2)
    yerde_aday_baslangic = None
    bekleme_baslangic = None
    land_baslangic = time.time()
    disarm_bekleme_suresi = 0
    disarm_yazildi = False
    arm_bekleme_mesaji_yazildi = False
    erken_arm_tamamlandi = False
    erken_arm_son_deneme = 0
    while True:
        yukseklik = vehicle.location.global_relative_frame.alt
        hiz = vehicle.groundspeed
        if hiz is None:
            hiz = 0
        print(f'LAND son asama | Yukseklik: {yukseklik:.2f} m | Hiz: {hiz:.2f} m/s | ARM: {vehicle.armed} | Mod: {vehicle.mode.name}')
        yerde_gibi = yukseklik <= self.config.YERDE_KABUL_IRTIFA and hiz <= self.config.YERDE_KABUL_HIZ
        if yerde_gibi:
            if yerde_aday_baslangic is None:
                yerde_aday_baslangic = time.time()
                print('Drone yerde gibi. Yerde onay suresi basladi...')
            yerde_aday_suresi = time.time() - yerde_aday_baslangic
            bekleme_baslat_sarti = yerde_aday_suresi >= self.config.YERDE_ONAY_SURESI and (yukseklik <= self.config.BEKLEME_BASLAT_IRTIFA or not vehicle.armed)
            if bekleme_baslat_sarti and bekleme_baslangic is None:
                bekleme_baslangic = time.time()
                print('Bekleme sayaci basladi.')
            if not vehicle.armed and (not disarm_yazildi):
                disarm_bekleme_suresi = time.time() - yerde_aday_baslangic
                print(f"Drone DISARM oldu. Yerde kabulden disarm'a kadar gecen sure: {disarm_bekleme_suresi:.2f} sn")
                disarm_yazildi = True
            if bekleme_baslangic is not None:
                yerde_gecen_sure = time.time() - bekleme_baslangic
                kalan_bekleme_suresi = bekleme_suresi - yerde_gecen_sure
                if erken_arm and (not disarm_bekle) and (bekleme_suresi > 0) and (not vehicle.armed) and (not erken_arm_tamamlandi) and (kalan_bekleme_suresi <= self.config.ERKEN_ARM_KALAN_SURE) and (time.time() - erken_arm_son_deneme >= 1.0):
                    erken_arm_son_deneme = time.time()
                    print('Bekleme bitmeden tekrar ARM hazirligi basliyor...')
                    if vehicle.mode.name != 'GUIDED':
                        vehicle.mode = VehicleMode('GUIDED')
                        time.sleep(0.5)
                    if vehicle.is_armable:
                        vehicle.armed = True
                        arm_baslangic_zamani = time.time()
                        while not vehicle.armed and time.time() - arm_baslangic_zamani < self.config.ERKEN_ARM_KALAN_SURE:
                            print('Bekleme suresi icinde ARM olmasi bekleniyor...')
                            time.sleep(0.2)
                        if vehicle.armed:
                            print('Bekleme suresi icinde tekrar ARM edildi.')
                            erken_arm_tamamlandi = True
                        else:
                            print('Bekleme suresi icinde ARM tamamlanamadi.')
                    else:
                        print('Drone erken ARM icin armable degil.')
                if yerde_gecen_sure >= bekleme_suresi:
                    if vehicle.armed and disarm_bekle:
                        if not arm_bekleme_mesaji_yazildi:
                            print('Yerde bekleme tamamlandi ama drone hala ARM durumda. ArduPilot otomatik DISARM bekleniyor...')
                            arm_bekleme_mesaji_yazildi = True
                    else:
                        if vehicle.armed and (not disarm_bekle):
                            vehicle.mode = VehicleMode('GUIDED')
                            print('Bekleme tamamlandi. Drone ARM durumda, kalkis akisina geciliyor...')
                        print(f'Inis ve yerde bekleme tamamlandi. Istenen bekleme: {bekleme_suresi:.2f} sn | Yerde gecen sure: {yerde_gecen_sure:.2f} sn | ARM: {vehicle.armed}')
                        return (True, disarm_bekleme_suresi)
        else:
            yerde_aday_baslangic = None
            bekleme_baslangic = None
            arm_bekleme_mesaji_yazildi = False
        if time.time() - land_baslangic > zaman_asimi + bekleme_suresi + 15:
            print('LAND son asama zaman asimina girdi.')
            return (False, disarm_bekleme_suresi)
        time.sleep(0.2)

# land_takilma_kurtarma implementation f230c65304ce
def land_takilma_kurtarma_vf230c65304ce(self, vehicle, inis_lat, inis_lon):
    print('LAND modunda alcalma durdu. Kisa GUIDED kurtarma uygulanıyor...')
    vehicle.mode = VehicleMode('GUIDED')
    guided_baslangic = time.time()
    while vehicle.mode.name != 'GUIDED':
        print('GUIDED mod bekleniyor...')
        if time.time() - guided_baslangic > 5:
            print('GUIDED moda gecilemedi. Kurtarma basarisiz.')
            return False
        time.sleep(0.2)
    hedef_kurtarma = LocationGlobalRelative(inis_lat, inis_lon, self.config.LAND_KURTARMA_IRTIFA)
    kurtarma_baslangic = time.time()
    son_komut_zamani = 0
    while time.time() - kurtarma_baslangic < self.config.LAND_KURTARMA_SURESI:
        if time.time() - son_komut_zamani > 0.5:
            self.simpleGotoMavlink(vehicle, hedef_kurtarma, hedef_kurtarma.alt)
            son_komut_zamani = time.time()
        yukseklik = vehicle.location.global_relative_frame.alt
        print(f'GUIDED kurtarma | Yukseklik: {yukseklik:.2f} m | ARM: {vehicle.armed} | Mod: {vehicle.mode.name}')
        if not vehicle.armed:
            print('Drone DISARM oldu. Kurtarma sonlandiriliyor.')
            return True
        if yukseklik <= self.config.YERDE_KABUL_IRTIFA:
            print('GUIDED kurtarma yeterince alcaltildi. LAND moduna donuluyor...')
            break
        time.sleep(0.2)
    vehicle.mode = VehicleMode('LAND')
    land_baslangic = time.time()
    while vehicle.mode.name != 'LAND':
        print('LAND mod bekleniyor...')
        if time.time() - land_baslangic > 5:
            print('LAND moda geri gecilemedi.')
            return False
        time.sleep(0.2)
    print('Kurtarma tamamlandi. LAND moduna geri donuldu.')
    return True

# wpnav_speed_dn_ayarla implementation 43b449256723
def wpnav_speed_dn_ayarla_v43b449256723(self, vehicle, hiz_cm_s):
    if hiz_cm_s < 10:
        hiz_cm_s = 10
    if hiz_cm_s > 500:
        hiz_cm_s = 500
    print(f'WPNAV_SPEED_DN ayarlaniyor: {hiz_cm_s} cm/s')
    msg = vehicle.message_factory.param_set_encode(0, 0, b'WPNAV_SPEED_DN', float(hiz_cm_s), mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
    vehicle.send_mavlink(msg)
    vehicle.flush()
    time.sleep(0.5)

"""Safety implementations; migrated verbatim in behavior from the original versions.

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

# failsafe_durum_kontrol implementation 162ec4b7bbaf
def failsafe_durum_kontrol_v162ec4b7bbaf(self, vehicle, home_noktasi):
    if not self.config.WATCHDOG_AKTIF:
        return (True, 'Watchdog kapali')
    mevcut = vehicle.location.global_relative_frame
    if vehicle.mode.name not in ['GUIDED', 'LAND', 'RTL']:
        return (False, f'Beklenmeyen mod: {vehicle.mode.name}')
    if mevcut.lat is None or mevcut.lon is None:
        return (False, 'GPS konumu yok')
    if vehicle.gps_0.fix_type is not None and vehicle.gps_0.fix_type < 3:
        return (False, f'GPS fix zayif: {vehicle.gps_0.fix_type}')
    if not vehicle.ekf_ok:
        return (False, 'EKF sagliksiz')
    if mevcut.alt > self.config.MAKS_IRTIFA:
        return (False, f'Irtifa limiti asildi: {mevcut.alt:.2f} m')
    home_konum = LocationGlobalRelative(home_noktasi['lat'], home_noktasi['lon'], 0)
    home_uzaklik = self.mesafe_hesapla_metre(mevcut, home_konum)
    if home_uzaklik > self.config.MAKS_HOME_MESAFESI:
        return (False, f'Alan disi riski: {home_uzaklik:.2f} m')
    if self.config.BATARYA_KONTROL_AKTIF and vehicle.battery is not None and (vehicle.battery.voltage is not None):
        if vehicle.battery.voltage < self.config.MIN_BATARYA_VOLTAJ:
            return (False, f'Batarya dusuk: {vehicle.battery.voltage:.2f} V')
    return (True, 'Guvenli')

# failsafe_durum_kontrol implementation 503dc8b89997
def failsafe_durum_kontrol_v503dc8b89997(self, vehicle, home_noktasi):
    if not self.config.WATCHDOG_AKTIF:
        return (True, 'Watchdog kapali')
    mevcut = vehicle.location.global_relative_frame
    if mevcut.lat is None or mevcut.lon is None:
        print('UYARI: GPS konumu yok | Goreve devam ediliyor.')
        return (True, 'GPS konumu yok ama devam')
    if vehicle.gps_0.fix_type is not None and vehicle.gps_0.fix_type < 3:
        print(f'UYARI: GPS fix zayif: {vehicle.gps_0.fix_type} | Goreve devam ediliyor.')
    if not vehicle.ekf_ok:
        print('UYARI: EKF sagliksiz gorunuyor | Goreve devam ediliyor.')
    if mevcut.alt > self.config.MAKS_IRTIFA:
        return (False, f'Irtifa limiti asildi: {mevcut.alt:.2f} m')
    home_konum = LocationGlobalRelative(home_noktasi['lat'], home_noktasi['lon'], 0)
    home_uzaklik = self.mesafe_hesapla_metre(mevcut, home_konum)
    if home_uzaklik > self.config.MAKS_HOME_MESAFESI:
        return (False, f'Alan disi riski: {home_uzaklik:.2f} m')
    return (True, 'Guvenli')

# failsafe_durum_kontrol implementation be0fd87a8cfa
def failsafe_durum_kontrol_vbe0fd87a8cfa(self, vehicle, home_noktasi):
    if not self.config.WATCHDOG_AKTIF:
        return (True, 'Watchdog kapali')
    mevcut = vehicle.location.global_relative_frame
    if mevcut.lat is None or mevcut.lon is None:
        return (False, 'GPS konumu yok')
    if vehicle.gps_0.fix_type is not None and vehicle.gps_0.fix_type < 3:
        return (False, f'GPS fix zayif: {vehicle.gps_0.fix_type}')
    if not vehicle.ekf_ok:
        return (False, 'EKF sagliksiz')
    if mevcut.alt > self.config.MAKS_IRTIFA:
        return (False, f'Irtifa limiti asildi: {mevcut.alt:.2f} m')
    home_konum = LocationGlobalRelative(home_noktasi['lat'], home_noktasi['lon'], 0)
    home_uzaklik = self.mesafe_hesapla_metre(mevcut, home_konum)
    if home_uzaklik > self.config.MAKS_HOME_MESAFESI:
        return (False, f'Alan disi riski: {home_uzaklik:.2f} m')
    return (True, 'Guvenli')

# failsafe_durum_kontrol implementation ebd10d3ee91e
def failsafe_durum_kontrol_vebd10d3ee91e(self, vehicle, home_noktasi):
    if not self.config.WATCHDOG_AKTIF:
        return (True, 'Watchdog kapali')
    mevcut = vehicle.location.global_relative_frame
    if vehicle.mode.name not in ['GUIDED', 'LAND', 'RTL']:
        return (False, f'Beklenmeyen mod: {vehicle.mode.name}')
    if mevcut.lat is None or mevcut.lon is None:
        return (False, 'GPS konumu yok')
    if vehicle.gps_0.fix_type is not None and vehicle.gps_0.fix_type < 3:
        return (False, f'GPS fix zayif: {vehicle.gps_0.fix_type}')
    if not vehicle.ekf_ok:
        return (False, 'EKF sagliksiz')
    if mevcut.alt > self.config.MAKS_IRTIFA:
        return (False, f'Irtifa limiti asildi: {mevcut.alt:.2f} m')
    home_konum = LocationGlobalRelative(home_noktasi['lat'], home_noktasi['lon'], 0)
    home_uzaklik = self.mesafe_hesapla_metre(mevcut, home_konum)
    if home_uzaklik > self.config.MAKS_HOME_MESAFESI:
        return (False, f'Alan disi riski: {home_uzaklik:.2f} m')
    return (True, 'Guvenli')

# failsafe_uygula implementation 87c5ed25e24f
def failsafe_uygula_v87c5ed25e24f(self, vehicle, sebep):
    print(f'FAILSAFE TETIKLENDI: {sebep}')
    if not vehicle.armed:
        print('Drone zaten armed degil.')
        return False
    if self.config.RTL_KULLAN and ('Batarya' in sebep or 'Alan disi' in sebep):
        print('RTL moduna geciliyor...')
        vehicle.mode = VehicleMode('RTL')
        return False
    print('LAND moduna geciliyor...')
    vehicle.mode = VehicleMode('LAND')
    return False

# failsafe_uygula implementation f066bcd31305
def failsafe_uygula_vf066bcd31305(self, vehicle, sebep):
    print(f'FAILSAFE TETIKLENDI: {sebep}')
    if not vehicle.armed:
        print('Drone zaten armed degil.')
        return False
    if self.config.RTL_KULLAN and 'Alan disi' in sebep:
        print('RTL moduna geciliyor...')
        vehicle.mode = VehicleMode('RTL')
        return False
    print('LAND moduna geciliyor...')
    vehicle.mode = VehicleMode('LAND')
    return False

# gorev_iptal_guvenli_mod implementation 115c385b0907
def gorev_iptal_guvenli_mod_v115c385b0907(self, vehicle, sebep):
    print(f'Gorev iptal edildi: {sebep}')
    if not vehicle.armed:
        return False
    if vehicle.mode.name in ['RTL', 'LAND']:
        print(f'Drone zaten guvenli modda: {vehicle.mode.name}')
        return False
    return self.failsafe_uygula(vehicle, sebep)

# gorev_iptal_guvenli_mod implementation 23f36dd5a313
def gorev_iptal_guvenli_mod_v23f36dd5a313(self, vehicle, sebep):
    print(f'Gorev iptal edildi: {sebep}')
    if not vehicle.armed:
        return False
    if vehicle.mode.name in ['RTL', 'LAND']:
        print(f'Drone zaten guvenli modda: {vehicle.mode.name}')
        return False
    print('Gorev durduruldu. Mevcut moda dokunulmuyor.')
    return False

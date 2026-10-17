"""Gps implementations; migrated verbatim in behavior from the original versions.

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

# ardupilot_home_ayarla implementation 44bd247b177d
def ardupilot_home_ayarla_v44bd247b177d(self, vehicle, home_noktasi):
    home_alt = home_noktasi.get('alt', None)
    if home_alt is None:
        home_alt = vehicle.location.global_frame.alt
    if home_alt is None:
        home_alt = 0
    msg = vehicle.message_factory.command_long_encode(0, 0, mavutil.mavlink.MAV_CMD_DO_SET_HOME, 0, 0, 0, 0, 0, home_noktasi['lat'], home_noktasi['lon'], home_alt)
    vehicle.send_mavlink(msg)
    vehicle.flush()
    print(f"ArduPilot HOME ayarlandi: {home_noktasi['lat']:.8f}, {home_noktasi['lon']:.8f}, Alt={home_alt:.2f}")

# konum_hazir_mi implementation 7c4f05b10316
def konum_hazir_mi_v7c4f05b10316(self, vehicle):
    print('GPS ve EKF kontrol ediliyor...')
    baslangic_zamani = time.time()
    while True:
        konum = vehicle.location.global_relative_frame
        gps = vehicle.gps_0
        lat_lon_var = konum.lat is not None and konum.lon is not None
        gps_fix_var = gps.fix_type is not None and gps.fix_type >= 3
        ekf_hazir = vehicle.ekf_ok
        print(f'GPS Fix: {gps.fix_type} | EKF: {ekf_hazir} | Konum: {konum.lat}, {konum.lon}')
        if lat_lon_var and gps_fix_var and ekf_hazir:
            print('GPS ve EKF hazir.')
            return True
        if time.time() - baslangic_zamani > 120:
            print('GPS veya EKF hazir olmadi.')
            return False
        time.sleep(1)

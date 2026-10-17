"""Geometry implementations; migrated verbatim in behavior from the original versions.

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

# mesafe_hesapla_metre implementation ae2c85b9282d
def mesafe_hesapla_metre_vae2c85b9282d(self, konum1, konum2):
    dlat = konum2.lat - konum1.lat
    dlon = konum2.lon - konum1.lon
    ortalama_lat = math.radians((konum1.lat + konum2.lat) / 2)
    metre_lat = dlat * 111320
    metre_lon = dlon * 111320 * math.cos(ortalama_lat)
    return math.sqrt(metre_lat ** 2 + metre_lon ** 2)

# mesafe_hesapla_metre implementation e42f4c632afa
def mesafe_hesapla_metre_ve42f4c632afa(self, konum1, konum2):
    if konum1.lat is None or konum1.lon is None or konum2.lat is None or (konum2.lon is None):
        return float('inf')
    dlat = konum2.lat - konum1.lat
    dlon = konum2.lon - konum1.lon
    ortalama_lat = math.radians((konum1.lat + konum2.lat) / 2)
    metre_lat = dlat * 111320
    metre_lon = dlon * 111320 * math.cos(ortalama_lat)
    return math.sqrt(metre_lat ** 2 + metre_lon ** 2)

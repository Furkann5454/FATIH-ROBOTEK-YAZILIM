"""Operator implementations; migrated verbatim in behavior from the original versions.

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

# b_tusu_bekle implementation 0c4a6c9d514b
def b_tusu_bekle_v0c4a6c9d514b(self):
    print('\n================================')
    print('>> b tusu bekleniyor...')
    print('>> Gorevi baslatmak icin terminalde b tusuna bas')
    print('================================\n')
    fd = sys.stdin.fileno()
    eski_ayar = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            tus = sys.stdin.read(1).lower()
            if tus == 'b':
                print('\n>> b tusu algilandi.')
                print('>> Gorev baslatiliyor...\n')
                return
            else:
                print('>> Sadece b tusuna basinca gorev baslar.')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, eski_ayar)

# sureli_tus_kontrolu implementation 8f090c31e851
def sureli_tus_kontrolu_v8f090c31e851(self, izinli_tuslar, sure_saniye):
    """
    Belirlenen süre içinde r/h gelirse döndürür.
    Tuş gelmezse None döner ve normal akış devam eder.
    """
    print('\n--------------------------------')
    print(f'Komut penceresi: {sure_saniye:.1f} sn')
    print('r = ayni HEDEF konumuna tekrar git')
    print("h = HOME konumuna git / HOME'u tekrar dene")
    print('Tusa basmazsan normal akis devam eder.')
    print('--------------------------------\n')
    fd = sys.stdin.fileno()
    eski_ayar = termios.tcgetattr(fd)
    baslangic = time.time()
    try:
        tty.setcbreak(fd)
        while time.time() - baslangic < sure_saniye:
            kalan = sure_saniye - (time.time() - baslangic)
            print(f'Komut bekleniyor... kalan: {kalan:.1f} sn', end='\r')
            okunabilir, _, _ = select.select([sys.stdin], [], [], 0.1)
            if okunabilir:
                tus = sys.stdin.read(1).lower()
                if tus in izinli_tuslar:
                    print(f'\nKomut alindi: {tus}\n')
                    return tus
                print(f'\nGecersiz tus: {tus}. Sadece {izinli_tuslar}\n')
        print('\nKomut gelmedi. Normal akis devam ediyor.\n')
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, eski_ayar)

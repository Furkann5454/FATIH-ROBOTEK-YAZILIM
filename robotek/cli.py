"""Safe command-line entry point. Listing and inspection never connect to a drone."""
from __future__ import annotations

import argparse
import json

from .runtime import get_profile, profiles, run_gps, run_mission


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="robotek", description="FATIH ROBOTEK modul gorev yonetimi"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="Profilleri listele (baglanti yok)")
    view = sub.add_parser("show", help="Bir profilin ayarlarini goster (baglanti yok)")
    view.add_argument("--profile", required=True, help="Profil adi")
    flight = sub.add_parser("run", help="Bir profili gercek/SITL araca baglayarak calistir")
    flight.add_argument("--profile", required=True, help="Profil adi")
    flight.add_argument("--connection", help="MAVLink baglanti adresini gecersiz kil")
    flight.add_argument("--repeats", type=int, help="Varsayilan gorev tekrari yerine bu degeri kullan")
    flight.add_argument("--execute", action="store_true", help="Canli baglanti ve gorevi acikca onayla")
    gps = sub.add_parser("gps", help="GPS konumlarini ornekle")
    gps.add_argument("--connection", default="tcp:192.168.30.3:5760")
    gps.add_argument("--baud", type=int)
    gps.add_argument("--samples", type=int, default=20)
    gps.add_argument("--interval", type=float, default=0.2)
    gps.add_argument("--execute", action="store_true", help="Canli GPS baglantisini acikca onayla")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    if args.command == "list":
        for name, profile in profiles().items():
            print(f"{name:19}  {profile['source']} (tekrar: {profile['repeats']})")
        return 0
    if args.command == "show":
        try:
            p = get_profile(args.profile)
        except ValueError as exc:
            parser.error(str(exc))
        print(json.dumps({
            "profile": args.profile, "source": p["source"],
            "repeats": p["repeats"], "wait_for_b": p["wait_for_b"],
            "interrupt_land": p["interrupt_land"], "settings": p["settings"]
        }, indent=2, ensure_ascii=False))
        return 0
    if args.command == "run":
        try:
            p = get_profile(args.profile)
        except ValueError as exc:
            parser.error(str(exc))
        if args.repeats is not None and args.repeats < 1:
            parser.error("--repeats en az 1 olmali")
        if not args.execute:
            print(f"Hazir: {args.profile} | hedef sayisi: {len(p['settings']['GOREV_NOKTALARI'])}"
                  f" | tekrar: {args.repeats or p['repeats']}")
            print("Baglanti ve ucus BASLATILMADI. Yalnizca SITL/dogrulama sonrasinda --execute kullanin.")
            return 0
        run_mission(args.profile, connection=args.connection, repeats=args.repeats)
        return 0
    if args.command == "gps":
        if args.samples < 1 or args.interval < 0:
            parser.error("--samples >= 1 ve --interval >= 0 olmali")
        if not args.execute:
            print("GPS baglantisi BASLATILMADI. Canli baglanti icin --execute kullanin.")
            return 0
        run_gps(connection=args.connection, baud=args.baud,
                samples=args.samples, interval=args.interval)
        return 0
    return 1

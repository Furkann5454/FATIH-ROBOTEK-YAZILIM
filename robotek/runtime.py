"""Profile loading and composition of the original, deduplicated flight behaviors.

No drone libraries are imported until a controller is explicitly instantiated.
Each invocation receives its own copy of the original settings and waypoints.
"""
from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

_PROFILE_FILE = Path(__file__).with_name("profiles.json")


def profiles() -> dict[str, dict[str, Any]]:
    """Return mission profiles, preserving all original parameters and targets."""
    return json.loads(_PROFILE_FILE.read_text(encoding="utf-8"))


def get_profile(name: str) -> dict[str, Any]:
    available = profiles()
    if name not in available:
        raise ValueError(f"Bilinmeyen profil: {name}. Mevcut profiller: {', '.join(available)}")
    return available[name]


def make_settings(source: dict[str, Any]) -> SimpleNamespace:
    values = copy.deepcopy(source)
    for key, value in values.items():
        if isinstance(value, dict) and set(value) == {"$alias"}:
            values[key] = values[value["$alias"]]
    return SimpleNamespace(**values)


def build_controller(profile_name: str):
    """Build a controller by composing the selected original function variants.

    The implementation for every function originates from its corresponding
    original script; shared implementations are stored only once.
    """
    profile = get_profile(profile_name)
    selected = {}
    for method_name, spec in profile["methods"].items():
        module = importlib.import_module(f"robotek.components.{spec['module']}")
        selected[method_name] = getattr(module, spec["implementation"])

    cls = type("MissionController", (object,), selected)
    instance = cls()
    instance.config = make_settings(profile["settings"])
    return instance


def run_mission(profile_name: str, *, connection: str | None = None,
                repeats: int | None = None) -> None:
    """Connect and execute the original profile's mission sequence.

    This function must be called only from the CLI's explicit --execute path.
    """
    from dronekit import connect, VehicleMode

    profile = get_profile(profile_name)
    controller = build_controller(profile_name)
    connection = connection or controller.config.BAGLANTI_ADRESI
    count = profile["repeats"] if repeats is None else repeats
    if count < 1:
        raise ValueError("repeats 1 veya daha buyuk olmali")

    print("Drone baglaniyor...")
    print("Baglanti adresi:", connection)
    vehicle = connect(connection, wait_ready=True, timeout=60)
    try:
        print("Drone baglandi.")
        print("Mod:", vehicle.mode.name)
        print("Armed:", vehicle.armed)
        print("Konum:", vehicle.location.global_relative_frame)
        if profile["wait_for_b"]:
            controller.b_tusu_bekle()
        for _ in range(count):
            controller.Gorevler(vehicle)
    except KeyboardInterrupt:
        print("Kullanici tarafindan durduruldu.")
        if profile["interrupt_land"]:
            if vehicle.armed:
                print("Drone LAND moduna aliniyor...")
                vehicle.mode = VehicleMode("LAND")
        else:
            print("Mevcut moda dokunulmuyor.")
    finally:
        print("Vehicle kapatiliyor...")
        vehicle.close()


def run_gps(*, connection: str, baud: int | None = None,
            samples: int = 20, interval: float = 0.2) -> None:
    """Run the original GPS averaging tool with configurable sample settings."""
    if samples < 1 or interval < 0:
        raise ValueError("samples >= 1 ve interval >= 0 olmali")
    module = importlib.import_module("robotek.gps_collector")
    collector_cls = type("GPSCollector", (object,), {
        fn: getattr(module, fn)
        for fn in ("baglan", "gps_hazir_bekle", "gps_ortalama_al", "main")
    })
    collector = collector_cls()
    collector.config = SimpleNamespace(
        BAGLANTI_ADRESI=connection, BAUD=baud,
        ORNEK_SAYISI=samples, ORNEK_ARALIGI=interval
    )
    collector.main()

"""Offline tests: no drone/SITL connection is established."""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import io
import json
import math
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

from robotek.cli import main
from robotek.runtime import build_controller, get_profile, make_settings, profiles, run_gps

ROOT = Path(__file__).resolve().parents[1]


class LocationGlobalRelative:
    def __init__(self, lat, lon, alt):
        self.lat, self.lon, self.alt = lat, lon, alt


class VehicleMode:
    def __init__(self, name):
        self.name = name


class ReverseBindings(ast.NodeTransformer):
    """Undo only the intentional self/config binding changes for AST parity."""
    def visit_Attribute(self, node):
        if (isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == 'self' and node.value.attr == 'config'):
            return ast.copy_location(ast.Name(id=node.attr, ctx=ast.Load()), node)
        if isinstance(node.value, ast.Name) and node.value.id == 'self':
            return ast.copy_location(ast.Name(id=node.attr, ctx=ast.Load()), node)
        return self.generic_visit(node)


class ModularTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch_modules = patch.dict(sys.modules, {
            'dronekit': SimpleNamespace(LocationGlobalRelative=LocationGlobalRelative,
                                          VehicleMode=VehicleMode,
                                          connect=MagicMock()),
            'pymavlink': SimpleNamespace(mavutil=SimpleNamespace(mavlink=SimpleNamespace())),
        })
        cls.patch_modules.start()

    @classmethod
    def tearDownClass(cls):
        cls.patch_modules.stop()

    def test_profiles_complete_and_no_backup_files(self):
        self.assertEqual(len(profiles()), 11)
        self.assertFalse((ROOT / 'legacy').exists())
        self.assertFalse((ROOT / 'Yedekler').exists())
        for p in ROOT.rglob('*'):
            self.assertFalse(p.is_file() and p.suffix in ('.bak', '.orig', '.old'), p)

    def test_modular_function_signatures_match_original_ast_hashes(self):
        # Profile mappings embed SHA-256 of the *original* unmodified AST.
        for profile_name, profile in profiles().items():
            for name, spec in profile['methods'].items():
                with self.subTest(profile=profile_name, function=name):
                    impl_source = (ROOT / 'robotek' / 'components' / (spec['module'] + '.py')).read_text()
                    match = next(n for n in ast.parse(impl_source).body
                                 if isinstance(n, ast.FunctionDef) and n.name == spec['implementation'])
                    recovered = copy.deepcopy(match)
                    recovered.args.args.pop(0)
                    recovered.name = name
                    recovered = ReverseBindings().visit(recovered)
                    digest = hashlib.sha256(ast.dump(recovered, include_attributes=False).encode()).hexdigest()
                    self.assertEqual(digest[:12], spec['implementation'].rsplit('_v', 1)[-1])
                    self.assertTrue(callable(getattr(build_controller(profile_name), name)))

    def test_original_configuration_fingerprints(self):
        # Fixed digests calculated from original source constants before any refactor.
        expected = {'ardupilot_land': '1af29bfa9dbdc0f1d2c95a83b11609b55a41b7d73fec9379105ecc116048aa5a', 'simplegoto_land': 'fe41dd40f476a97c329154afaf6e1b9462050c50c5717476a76aa8557c9b65eb', 'inis_tekrar_1': '1af29bfa9dbdc0f1d2c95a83b11609b55a41b7d73fec9379105ecc116048aa5a', 'inis_tekrar_2': '2fe905f1d7a42e0b79b30f7250e532eca7f220c1ca2a24e5d6693eb02b0c1184', 'inis_tekrar_3': 'f043e78fea814c8f264f96c41dc85457cede8a2357ee550a68ce9131da610ccd', 'inis_tekrar_4': 'c5fe14817dab4c882bf59078238405872091411aa0de533e18a6f0d769809c5d', 'yedek_0': 'c0e9baad6b7a459a22cb400c9fa13974f6397bc24159192cdfe4168c1bc2903b', 'yedek_1': '14ee9b893691dfe2efb64c840c74d349aec7ff6b6c3d853d18ed2dc95f6f4726', 'yedek_3': 'a31f88fb7bada47f7d0f6bb337770439392daa38f95af31b3b4e6c0f6aad456c', 'yedek_4': '4f9adf26f572178dde858c97a674ea1225fb9d746b9f6132de30911cc28d518c', 'yedek_5': '76429f9bf064b3ba387456563b2ac494c3f4ab9c3b5b5f59bf85d405b3d43886'}
        self.assertEqual(set(profiles()), set(expected))
        for name, data in profiles().items():
            digest = hashlib.sha256(json.dumps(data['settings'], ensure_ascii=False,
                          sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            self.assertEqual(digest, expected[name], name)

    def test_profile_unique_mutable_settings(self):
        a = build_controller('ardupilot_land')
        b = build_controller('ardupilot_land')
        a.config.HOME_NOKTASI['alt'] = 51
        a.config.GOREV_NOKTALARI[0]['lat'] = 0
        self.assertNotIn('alt', b.config.HOME_NOKTASI)
        self.assertNotEqual(a.config.GOREV_NOKTALARI[0]['lat'],
                            b.config.GOREV_NOKTALARI[0]['lat'])
        y = build_controller('yedek_1')
        self.assertIs(y.config.GUVENLI_INIS_NOKTASI, y.config.HOME_NOKTASI)

    def test_all_profiles_have_mission_controller(self):
        for name in profiles():
            with self.subTest(name=name):
                controller = build_controller(name)
                self.assertTrue(callable(controller.Gorevler))
                self.assertTrue(callable(controller.arm_ve_takeoff))
                self.assertTrue(callable(controller.land_ol))
                self.assertGreater(len(controller.config.GOREV_NOKTALARI), 0)

    def test_variation_of_targets_and_flight_modes_retained(self):
        p = profiles()
        self.assertEqual(p['ardupilot_land']['repeats'], 4)
        self.assertEqual(p['simplegoto_land']['repeats'], 3)
        self.assertFalse(p['yedek_3']['wait_for_b'])
        self.assertTrue(p['yedek_3']['interrupt_land'])
        self.assertFalse(p['ardupilot_land']['interrupt_land'])
        self.assertEqual([p['inis_tekrar_'+str(i)]['settings']['GOREV_NOKTALARI'][0]['isim']
                          for i in range(1, 5)], [f'Hedef_{i}' for i in range(1, 5)])
        self.assertNotEqual(p['ardupilot_land']['methods']['land_ol']['implementation'],
                            p['simplegoto_land']['methods']['land_ol']['implementation'])
        self.assertEqual(p['inis_tekrar_1']['methods'],p['inis_tekrar_4']['methods'])

    def test_geometry_and_none_coordinates(self):
        vehicle = build_controller('ardupilot_land')
        x = LocationGlobalRelative(40.0, 30.0, 0)
        y = LocationGlobalRelative(40.001, 30.0, 0)
        self.assertAlmostEqual(vehicle.mesafe_hesapla_metre(x,y),111.32, places=1)
        self.assertEqual(vehicle.mesafe_hesapla_metre(x,LocationGlobalRelative(None,30,0)),float('inf'))

    def test_failsafe_geofence_and_altitude_original_logic(self):
        controller = build_controller('ardupilot_land')
        home = controller.config.HOME_NOKTASI
        vehicle = SimpleNamespace(
            location=SimpleNamespace(global_relative_frame=LocationGlobalRelative(home['lat'],home['lon'],10)),
            gps_0=SimpleNamespace(fix_type=3), ekf_ok=True)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(controller.failsafe_durum_kontrol(vehicle,home),(True,'Guvenli'))
            vehicle.location.global_relative_frame.alt=41
            self.assertFalse(controller.failsafe_durum_kontrol(vehicle,home)[0])
            vehicle.location.global_relative_frame.alt=10
            vehicle.location.global_relative_frame.lat += 0.01
            self.assertIn('Alan disi',controller.failsafe_durum_kontrol(vehicle,home)[1])

    def test_preview_does_not_connect(self):
        from dronekit import connect
        connect.reset_mock()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(['list']),0)
            self.assertEqual(main(['show','--profile','ardupilot_land']),0)
            self.assertEqual(main(['run','--profile','ardupilot_land']),0)
            self.assertEqual(main(['gps']),0)
        connect.assert_not_called()

    def test_gps_collector_calculates_average_without_a_drone(self):
        module = importlib.import_module('robotek.gps_collector')
        collector = SimpleNamespace(config=SimpleNamespace(ORNEK_SAYISI=3,ORNEK_ARALIGI=0))
        pos = LocationGlobalRelative(40.0,30.0,0)
        fake = SimpleNamespace(location=SimpleNamespace(global_relative_frame=pos))
        with patch.object(module.time, 'sleep', return_value=None), redirect_stdout(io.StringIO()):
            lat, lon = module.gps_ortalama_al(collector,fake)
        self.assertEqual((lat,lon),(40.,30.))


    def test_gps_collector_uses_original_connection_configuration(self):
        from robotek.runtime import run_gps
        from dronekit import connect
        fake = MagicMock()
        fake.gps_0.fix_type = 3
        fake.ekf_ok = True
        fake.location.global_relative_frame.lat = 40
        fake.location.global_relative_frame.lon = 30
        connect.return_value = fake
        with patch('builtins.input', return_value='q'), redirect_stdout(io.StringIO()):
            run_gps(connection='udp:127.0.0.1:14550', baud=57600)
        connect.assert_called_with('udp:127.0.0.1:14550', wait_ready=True,
                                   baud=57600, timeout=60)
        fake.close.assert_called_once()

    def test_mission_runner_uses_profile_repeat_count_and_closes(self):
        from dronekit import connect
        vehicle = MagicMock()
        vehicle.mode.name = 'GUIDED'
        vehicle.armed = False
        connect.reset_mock()
        connect.return_value = vehicle
        controller = MagicMock()
        controller.config.BAGLANTI_ADRESI = 'tcp:192.168.30.3:5760'
        with patch('robotek.runtime.build_controller', return_value=controller),redirect_stdout(io.StringIO()):
            self.assertEqual(main(['run','--profile','ardupilot_land','--execute']),0)
        connect.assert_called_once_with('tcp:192.168.30.3:5760',wait_ready=True, timeout=60)
        controller.b_tusu_bekle.assert_called_once()
        self.assertEqual(controller.Gorevler.call_count,4)
        vehicle.close.assert_called_once()

    def test_keyboard_interrupt_legacy_land_behavior_and_close(self):
        from dronekit import connect
        vehicle = MagicMock()
        vehicle.armed = True
        vehicle.mode.name = 'GUIDED'
        connect.return_value = vehicle
        controller = MagicMock()
        controller.Gorevler.side_effect = KeyboardInterrupt
        with patch('robotek.runtime.build_controller',return_value=controller),redirect_stdout(io.StringIO()):
            self.assertEqual(main(['run','--profile','yedek_3','--execute']),0)
        self.assertEqual(vehicle.mode.name,'LAND')
        vehicle.close.assert_called_once()

    def test_active_compatibility_wrappers_present(self):
        for name, info in profiles().items():
            if name.startswith('yedek_'):
                continue  # Historical mission variants are profiles, not backup files.
            wrapper = ROOT / info['source']
            self.assertTrue(wrapper.is_file())
            self.assertIn(f'"{name}"', wrapper.read_text())


if __name__ == '__main__':
    unittest.main()

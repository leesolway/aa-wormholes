from django.core.management import call_command
from django.test import TestCase

from wormholes import services
from wormholes.models import WormholeSystem
from wormholes.tests.utils import create_solar_system


class IdentifyWormholeCodeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("wormholes_loaddata")

    def test_identifies_known_code_case_insensitively(self):
        self.assertEqual(services.identify_wormhole_code("k162").code, "K162")
        self.assertEqual(services.identify_wormhole_code("K162").code, "K162")

    def test_unknown_code_returns_none(self):
        self.assertIsNone(services.identify_wormhole_code("ZZZZ"))
        self.assertIsNone(services.identify_wormhole_code(""))

    def test_drifter_static_is_identified_as_drifter(self):
        # N062: a static found inside Drifter systems, leading to a C5.
        self.assertTrue(services.is_drifter_wormhole_code("N062"))

    def test_drifter_entrance_from_k_space_is_identified_as_drifter(self):
        # B735: a k-space wandering hole known to lead into Barbican (Drifter) space.
        self.assertTrue(services.is_drifter_wormhole_code("B735"))

    def test_ordinary_wormhole_is_not_identified_as_drifter(self):
        self.assertFalse(services.is_drifter_wormhole_code("A009"))

    def test_unknown_code_is_not_a_drifter_wormhole(self):
        self.assertFalse(services.is_drifter_wormhole_code("ZZZZ"))


class WormholeClassForSolarSystemTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.j111613 = create_solar_system(31002318, "J111613", wormhole_class_id_raw=2)
        cls.jita = create_solar_system(30000142, "Jita", wormhole_class_id_raw=None, security_status=0.9)
        call_command("wormholes_loaddata")

    def test_resolves_class_from_raw_id(self):
        wormhole_class = services.wormhole_class_for_solar_system(self.j111613)
        self.assertEqual(wormhole_class.slug, "c2")

    def test_returns_none_for_non_wormhole_system(self):
        self.assertIsNone(services.wormhole_class_for_solar_system(self.jita))

    def test_wormhole_system_info_returns_none_when_not_seeded(self):
        self.assertIsNone(services.wormhole_system_info(self.jita))

    def test_wormhole_system_info_returns_row_for_seeded_system(self):
        info = services.wormhole_system_info(self.j111613)
        self.assertIsInstance(info, WormholeSystem)

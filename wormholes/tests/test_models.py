from eve_sde.models import Constellation, Region
from django.core.management import call_command
from django.test import TestCase

from wormholes.models import ShatteredConstellation, WormholeClass, WormholeSystem, WormholeType
from wormholes.tests.utils import create_solar_system


class WormholeClassTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("wormholes_loaddata")

    def test_drifter_classes_are_flagged_as_drifter(self):
        for slug in ("sentinel", "barbican", "vidette", "conflux", "redoubt"):
            with self.subTest(slug=slug):
                self.assertTrue(WormholeClass.objects.get(slug=slug).is_drifter)

    def test_numbered_classes_are_not_drifter(self):
        for slug in ("c1", "c2", "c3", "c4", "c5", "c6"):
            with self.subTest(slug=slug):
                self.assertFalse(WormholeClass.objects.get(slug=slug).is_drifter)

    def test_wormhole_space_categories(self):
        for slug in ("c1", "c13", "thera", "sentinel"):
            with self.subTest(slug=slug):
                self.assertTrue(WormholeClass.objects.get(slug=slug).is_wormhole_space)
        for slug in ("hs", "ls", "ns", "pochven"):
            with self.subTest(slug=slug):
                self.assertFalse(WormholeClass.objects.get(slug=slug).is_wormhole_space)


class WormholeTypeQuerySetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("wormholes_loaddata")

    def test_static_capable_excludes_wandering_only_types(self):
        codes = set(WormholeType.objects.static_capable().values_list("code", flat=True))
        self.assertIn("N062", codes)
        self.assertNotIn("A009", codes)

    def test_drifter_related_includes_both_directions(self):
        codes = set(WormholeType.objects.drifter_related().values_list("code", flat=True))
        self.assertIn("N062", codes)  # spawns in Drifter space
        self.assertIn("B735", codes)  # leads into Drifter space from k-space
        self.assertNotIn("A009", codes)

    def test_leading_to_class_by_slug(self):
        codes = set(WormholeType.objects.leading_to_class("thera").values_list("code", flat=True))
        self.assertIn("F135", codes)
        self.assertNotIn("A009", codes)  # A009 spawns in Thera but leads to c13, not thera


class WormholeSystemQuerySetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.j111613 = create_solar_system(31002318, "J111613", wormhole_class_id_raw=2)
        cls.thera = create_solar_system(31000005, "Thera", wormhole_class_id_raw=12)
        # 31001361: a real J-space system id from wormholes/data/wormhole_systems.json.
        # Its wormhole_class_id_raw is set here purely for this test - WormholeSystem's
        # class comes from eve_sde, not from our fixture, so this id just needs to exist
        # as a key in wormhole_systems.json for a WormholeSystem row to be created for it.
        cls.sentinel_system = create_solar_system(31001361, "J112747", wormhole_class_id_raw=14)
        call_command("wormholes_loaddata")

    def test_in_class_by_slug_and_id(self):
        self.assertEqual(WormholeSystem.objects.in_class("c2").count(), 1)
        self.assertEqual(WormholeSystem.objects.in_class(2).count(), 1)

    def test_drifter_systems_filters_to_drifter_classes_only(self):
        drifter_systems = WormholeSystem.objects.drifter_systems()
        self.assertEqual(list(drifter_systems.values_list("pk", flat=True)), [self.sentinel_system.pk])

    def test_with_effect(self):
        matches = WormholeSystem.objects.with_effect("Cataclysmic Variable")
        self.assertEqual(list(matches.values_list("pk", flat=True)), [self.j111613.pk])

    def test_with_static(self):
        matches = WormholeSystem.objects.with_static("E175")
        self.assertEqual(list(matches.values_list("pk", flat=True)), [self.j111613.pk])


class ShatteredConstellationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        region = Region.objects.create(id=10000030, name="Heimatar")
        # A real shattered-frigate-hole constellation id, from wormholes/data/shattered_constellations.json.
        cls.shattered_constellation = Constellation.objects.create(id=21000334, name="Shattered", region=region)
        cls.ordinary_constellation = Constellation.objects.create(id=21099999, name="Ordinary", region=region)
        cls.in_shattered = create_solar_system(
            31001677, "J113551", wormhole_class_id_raw=4, constellation=cls.shattered_constellation
        )
        cls.not_shattered = create_solar_system(
            31002318, "J111613", wormhole_class_id_raw=2, constellation=cls.ordinary_constellation
        )
        call_command("wormholes_loaddata")

    def test_shattered_constellation_is_seeded_from_bundled_data(self):
        self.assertTrue(ShatteredConstellation.objects.filter(pk=21000334).exists())
        self.assertFalse(ShatteredConstellation.objects.filter(pk=21099999).exists())

    def test_wormhole_system_in_shattered_constellation_is_flagged(self):
        system = WormholeSystem.objects.get(pk=self.in_shattered.pk)
        self.assertTrue(system.is_shattered)

    def test_wormhole_system_outside_shattered_constellation_is_not_flagged(self):
        system = WormholeSystem.objects.get(pk=self.not_shattered.pk)
        self.assertFalse(system.is_shattered)

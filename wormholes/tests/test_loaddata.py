from eve_sde.models import Constellation, Region
from django.core.management import call_command
from django.test import TestCase

from wormholes.models import Effect, WormholeClass, WormholeSystem, WormholeType
from wormholes.tests.utils import create_solar_system


class LoadDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.j111613 = create_solar_system(31002318, "J111613", wormhole_class_id_raw=2)
        cls.thera = create_solar_system(31000005, "Thera", wormhole_class_id_raw=12)
        # A real shattered-frigate-hole constellation id, from wormholes/data/shattered_constellations.json.
        shattered_constellation = Constellation.objects.create(
            id=21000334, name="Shattered", region=Region.objects.first()
        )
        cls.j113551 = create_solar_system(
            31001677, "J113551", wormhole_class_id_raw=4, constellation=shattered_constellation
        )
        cls.jita = create_solar_system(30000142, "Jita", wormhole_class_id_raw=None, security_status=0.9)
        call_command("wormholes_loaddata")

    def test_reference_tables_are_fully_loaded(self):
        self.assertEqual(WormholeClass.objects.count(), 28)
        self.assertEqual(WormholeType.objects.count(), 100)
        self.assertEqual(Effect.objects.count(), 11)

    def test_known_system_gets_its_real_statics_effect_and_class(self):
        system = WormholeSystem.objects.get(pk=self.j111613.pk)
        self.assertEqual(sorted(s.code for s in system.statics.all()), ["E175"])
        self.assertEqual(system.effect.name, "Cataclysmic Variable")
        self.assertEqual(system.wormhole_class.slug, "c2")

    def test_thera_has_three_statics(self):
        system = WormholeSystem.objects.get(pk=self.thera.pk)
        self.assertEqual(sorted(s.code for s in system.statics.all()), ["E587", "Q063", "V898"])

    def test_non_wormhole_system_has_no_wormhole_system_row(self):
        self.assertFalse(WormholeSystem.objects.filter(pk=self.jita.pk).exists())

    def test_rerunning_the_command_is_idempotent(self):
        call_command("wormholes_loaddata")
        self.assertEqual(WormholeClass.objects.count(), 28)
        system = WormholeSystem.objects.get(pk=self.j111613.pk)
        self.assertEqual(sorted(s.code for s in system.statics.all()), ["E175"])

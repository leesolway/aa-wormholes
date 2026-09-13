"""Load the bundled wormhole reference data (see wormholes/data/) into the database.

Safe to re-run: every row is upserted by its natural key. Solar systems not
yet present in eve_sde (e.g. the SDE hasn't been synced yet) are skipped with
a warning rather than failing the whole run.
"""

import json
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from wormholes.models import (
    Effect,
    EffectModifier,
    ShatteredConstellation,
    WormholeClass,
    WormholeSystem,
    WormholeType,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _load(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


class Command(BaseCommand):
    help = "Load bundled EVE wormhole reference data (classes, types, systems, effects)."

    @transaction.atomic
    def handle(self, *args, **options):
        self._load_classes()
        self._load_effects()
        self._load_types()
        self._load_shattered_constellations()
        self._load_systems()

    def _load_classes(self):
        count = 0
        for row in _load("wormhole_classes.json"):
            WormholeClass.objects.update_or_create(
                class_id=row["class_id"],
                defaults={
                    "slug": row["slug"],
                    "short_name": row["short_name"],
                    "title": row["title"],
                    "short_title": row["short_title"],
                    "effect_power": row["effect_power"],
                    "category": row["category"],
                },
            )
            count += 1
        self.stdout.write(f"wormhole classes: {count}")

    def _load_effects(self):
        count = 0
        for row in _load("effects.json"):
            effect, _created = Effect.objects.update_or_create(name=row["name"])
            for modifier in row["modifiers"]:
                EffectModifier.objects.update_or_create(
                    effect=effect,
                    name=modifier["name"],
                    defaults={
                        "is_positive": modifier["is_positive"],
                        "magnitude_by_class": modifier["magnitude_by_class"],
                    },
                )
            count += 1
        self.stdout.write(f"effects: {count}")

    def _load_types(self):
        class_by_slug = {c.slug: c for c in WormholeClass.objects.all()}
        count = 0
        for row in _load("wormhole_types.json"):
            lifetime = Decimal(row["lifetime_hours"]) if row["lifetime_hours"] is not None else None
            wormhole_type, _created = WormholeType.objects.update_or_create(
                code=row["code"],
                defaults={
                    "lifetime_hours": lifetime,
                    "total_mass": row["total_mass"],
                    "max_jump_mass": row["max_jump_mass"],
                    "mass_regeneration": row["mass_regeneration"],
                    "is_static_capable": row["is_static_capable"],
                    "can_be_wandering": row["can_be_wandering"],
                    "is_reverse_signature": row["is_reverse_signature"],
                    "spawns_in_shattered_system": row["spawns_in_shattered_system"],
                    "spawns_at_jovian_observatory": row["spawns_at_jovian_observatory"],
                },
            )
            wormhole_type.spawns_in.set(class_by_slug[s] for s in row["spawns_in"])
            wormhole_type.leads_to.set(class_by_slug[s] for s in row["leads_to"])
            count += 1
        self.stdout.write(f"wormhole types: {count}")

    def _load_shattered_constellations(self):
        from eve_sde.models import Constellation

        count = 0
        skipped = 0
        for constellation_id in _load("shattered_constellations.json"):
            try:
                constellation = Constellation.objects.get(pk=constellation_id)
            except Constellation.DoesNotExist:
                skipped += 1
                continue
            ShatteredConstellation.objects.update_or_create(constellation=constellation)
            count += 1
        self.stdout.write(f"shattered constellations: {count} (skipped {skipped} not yet in eve_sde)")

    def _load_systems(self):
        from eve_sde.models import SolarSystem

        class_by_id = {c.class_id: c for c in WormholeClass.objects.all()}
        type_by_code = {t.code: t for t in WormholeType.objects.all()}
        effect_by_name = {e.name: e for e in Effect.objects.all()}

        count = 0
        skipped = 0
        for row in _load("wormhole_systems.json"):
            try:
                solar_system = SolarSystem.objects.get(pk=row["solar_system_id"])
            except SolarSystem.DoesNotExist:
                skipped += 1
                continue

            wormhole_class = class_by_id.get(solar_system.wormhole_class_id_raw)
            wormhole_system, _created = WormholeSystem.objects.update_or_create(
                solar_system=solar_system,
                defaults={
                    "wormhole_class": wormhole_class,
                    "effect": effect_by_name.get(row["effect"]) if row["effect"] else None,
                },
            )
            wormhole_system.statics.set(type_by_code[c] for c in row["statics"])
            wormhole_system.wandering_types.set(type_by_code[c] for c in row["wandering_types"])
            count += 1

        self.stdout.write(f"wormhole systems: {count} (skipped {skipped} not yet in eve_sde)")

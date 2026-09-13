"""Data migration: seed WormholeClass, Effect, EffectModifier and WormholeType
from the bundled JSON files in wormholes/data/.

WormholeSystem and ShatteredConstellation are intentionally excluded — they
require eve_sde SolarSystem / Constellation rows that won't exist at migration
time.  Run ``manage.py wormholes_loaddata`` after the SDE has been synced to
populate those tables.
"""

import json
from decimal import Decimal
from pathlib import Path

from django.db import migrations

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def _seed_classes(apps, schema_editor):
    WormholeClass = apps.get_model("wormholes", "WormholeClass")
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


def _seed_effects(apps, schema_editor):
    Effect = apps.get_model("wormholes", "Effect")
    EffectModifier = apps.get_model("wormholes", "EffectModifier")
    for row in _load("effects.json"):
        effect, _ = Effect.objects.update_or_create(name=row["name"])
        for modifier in row["modifiers"]:
            EffectModifier.objects.update_or_create(
                effect=effect,
                name=modifier["name"],
                defaults={
                    "is_positive": modifier["is_positive"],
                    "magnitude_by_class": modifier["magnitude_by_class"],
                },
            )


def _seed_types(apps, schema_editor):
    WormholeType = apps.get_model("wormholes", "WormholeType")
    WormholeClass = apps.get_model("wormholes", "WormholeClass")
    class_by_slug = {c.slug: c for c in WormholeClass.objects.all()}
    for row in _load("wormhole_types.json"):
        lifetime = Decimal(row["lifetime_hours"]) if row["lifetime_hours"] is not None else None
        wt, _ = WormholeType.objects.update_or_create(
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
        wt.spawns_in.set(class_by_slug[s] for s in row["spawns_in"])
        wt.leads_to.set(class_by_slug[s] for s in row["leads_to"])


class Migration(migrations.Migration):
    dependencies = [
        ("wormholes", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(_seed_classes, migrations.RunPython.noop),
        migrations.RunPython(_seed_effects, migrations.RunPython.noop),
        migrations.RunPython(_seed_types, migrations.RunPython.noop),
    ]

"""Add color field to Effect; backfill from the effects.json data."""

import json
from pathlib import Path

from django.db import migrations, models

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "effects.json"


def _seed_colors(apps, schema_editor):
    with open(DATA_FILE, encoding="utf-8") as f:
        rows = json.load(f)
    color_map = {row["name"]: row.get("color", "") for row in rows}
    Effect = apps.get_model("wormholes", "Effect")
    for effect in Effect.objects.all():
        color = color_map.get(effect.name, "")
        if color:
            effect.color = color
            effect.save(update_fields=["color"])


class Migration(migrations.Migration):
    dependencies = [
        ("wormholes", "0003_wormholesystem_wormhole_class"),
    ]

    operations = [
        migrations.AddField(
            model_name="effect",
            name="color",
            field=models.CharField(
                blank=True,
                default="#6c757d",
                help_text="Hex colour used to represent this effect in the UI.",
                max_length=20,
            ),
        ),
        migrations.RunPython(_seed_colors, migrations.RunPython.noop),
    ]

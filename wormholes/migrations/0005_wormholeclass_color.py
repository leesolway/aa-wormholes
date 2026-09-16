"""Add color field to WormholeClass; backfill from the wormhole_classes.json data."""

import json
from pathlib import Path

from django.db import migrations, models

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "wormhole_classes.json"


def _seed_colors(apps, schema_editor):
    with open(DATA_FILE, encoding="utf-8") as f:
        rows = json.load(f)
    color_map = {row["class_id"]: row.get("color", "") for row in rows}
    WormholeClass = apps.get_model("wormholes", "WormholeClass")
    for wh_class in WormholeClass.objects.all():
        color = color_map.get(wh_class.class_id, "")
        if color:
            wh_class.color = color
            wh_class.save(update_fields=["color"])


class Migration(migrations.Migration):
    dependencies = [
        ("wormholes", "0004_effect_color"),
    ]

    operations = [
        migrations.AddField(
            model_name="wormholeclass",
            name="color",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Hex colour used to represent this class in the UI.",
                max_length=20,
            ),
        ),
        migrations.RunPython(_seed_colors, migrations.RunPython.noop),
    ]

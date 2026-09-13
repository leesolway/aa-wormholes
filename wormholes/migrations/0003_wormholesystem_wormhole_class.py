"""Add WormholeSystem.wormhole_class FK; drop Pochven-only effect_power and invasion_status."""

from django.db import migrations, models
import django.db.models.deletion


def _backfill_wormhole_class(apps, schema_editor):
    WormholeSystem = apps.get_model("wormholes", "WormholeSystem")
    WormholeClass = apps.get_model("wormholes", "WormholeClass")
    class_by_id = {c.class_id: c for c in WormholeClass.objects.all()}
    for system in WormholeSystem.objects.select_related("solar_system").all():
        class_id = system.solar_system.wormhole_class_id_raw
        wc = class_by_id.get(class_id)
        if wc is not None:
            system.wormhole_class = wc
            system.save(update_fields=["wormhole_class"])


class Migration(migrations.Migration):
    dependencies = [
        ("eve_sde", "0001_initial"),
        ("wormholes", "0002_seed_reference_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="wormholesystem",
            name="wormhole_class",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="systems",
                to="wormholes.wormholeclass",
            ),
        ),
        migrations.RunPython(_backfill_wormhole_class, migrations.RunPython.noop),
        migrations.RemoveField(model_name="wormholesystem", name="effect_power"),
        migrations.RemoveField(model_name="wormholesystem", name="invasion_status"),
    ]

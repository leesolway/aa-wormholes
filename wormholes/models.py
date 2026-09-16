"""Static reference data for EVE Online wormhole space (Anoikis, Thera, Drifter
space, Pochven) - classes, connection types, per-system statics and effects.

Reference data is sourced (MIT licensed) from the Wanderer map tool
(https://github.com/wanderer-industries/wanderer) and loaded via the
``wormholes_loaddata`` management command; see wormholes/data/.
"""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from wormholes.managers import WormholeSystemQuerySet, WormholeTypeQuerySet


class WormholeClass(models.Model):
    """A system classification from EVE's wormholeClassID (SDE mapSolarSystems /
    mapConstellations / mapRegions), covering C1-C6, Thera, C13 shattered
    frigate holes, the five Drifter classes (C14-C18), Pochven, Abyssal
    Deadspace and ordinary K-space.
    """

    class Category(models.TextChoices):
        NUMBERED = "numbered", _("Numbered (C1-C6)")
        SHATTERED_FRIGATE = "shattered_frigate", _("Shattered frigate hole (C13)")
        DRIFTER = "drifter", _("Drifter space (C14-C18)")
        THERA = "thera", _("Thera")
        ABYSSAL = "abyssal", _("Abyssal Deadspace")
        KNOWN_SPACE = "known_space", _("High/Low/Null-sec")
        POCHVEN = "pochven", _("Pochven")
        PIRATE = "pirate", _("Pirate space (Zarzakh)")
        REVERSE = "reverse", _("Reverse signature marker (K162)")
        CCP = "ccp", _("CCP-reserved / test system")

    class_id = models.IntegerField(
        primary_key=True,
        help_text=_("EVE SDE wormholeClassID, matches eve_sde.SolarSystem.wormhole_class_id_raw."),
    )
    slug = models.SlugField(max_length=20, unique=True)
    short_name = models.CharField(max_length=10)
    title = models.CharField(max_length=100)
    short_title = models.CharField(max_length=30)
    effect_power = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text=_("1-6 index into an Effect's per-strength modifier list for systems of this class."),
    )
    category = models.CharField(max_length=20, choices=Category.choices)

    class Meta:
        ordering = ["class_id"]
        verbose_name = _("wormhole class")
        verbose_name_plural = _("wormhole classes")

    def __str__(self):
        return self.title

    @property
    def is_drifter(self) -> bool:
        return self.category == self.Category.DRIFTER

    @property
    def is_wormhole_space(self) -> bool:
        """True for any system reached only through a wormhole (Anoikis, Thera, Drifter space)."""
        return self.category in (
            self.Category.NUMBERED,
            self.Category.SHATTERED_FRIGATE,
            self.Category.DRIFTER,
            self.Category.THERA,
        )


class Effect(models.Model):
    """A system environmental effect (Pulsar, Magnetar, Black Hole, ..., or one
    of the Pochven Stellar Observatory effects).
    """

    name = models.CharField(max_length=64, primary_key=True)
    color = models.CharField(
        max_length=20,
        blank=True,
        default="#6c757d",
        help_text=_("Hex colour used to represent this effect in the UI."),
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class EffectModifier(models.Model):
    """One bonus/penalty an Effect applies, at each of the six effect-power strengths."""

    effect = models.ForeignKey(Effect, on_delete=models.CASCADE, related_name="modifiers")
    name = models.CharField(max_length=64)
    is_positive = models.BooleanField()
    magnitude_by_class = models.JSONField(
        help_text=_("Strength text (e.g. '+30%') indexed by effect_power - 1."),
    )

    class Meta:
        ordering = ["effect", "name"]
        constraints = [
            models.UniqueConstraint(fields=["effect", "name"], name="unique_effect_modifier_name"),
        ]

    def __str__(self):
        return f"{self.effect_id}: {self.name}"

    def magnitude_for(self, effect_power: int) -> str | None:
        if not effect_power or effect_power < 1 or effect_power > len(self.magnitude_by_class):
            return None
        return self.magnitude_by_class[effect_power - 1]


class WormholeType(models.Model):
    """A wormhole connection type identified by its in-game code (e.g. K162, N062)."""

    code = models.CharField(max_length=8, primary_key=True)
    lifetime_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    total_mass = models.BigIntegerField(null=True, blank=True)
    max_jump_mass = models.BigIntegerField(null=True, blank=True)
    mass_regeneration = models.BigIntegerField(null=True, blank=True)
    is_static_capable = models.BooleanField(
        default=False, help_text=_("Can this type appear as a system's permanent static.")
    )
    can_be_wandering = models.BooleanField(
        default=False, help_text=_("Can this type appear as a random (non-static) signature.")
    )
    is_reverse_signature = models.BooleanField(
        default=False,
        help_text=_("K162: the generic signature seen on the far side of any wormhole."),
    )
    spawns_in_shattered_system = models.BooleanField(default=False)
    spawns_at_jovian_observatory = models.BooleanField(default=False)
    spawns_in = models.ManyToManyField(
        WormholeClass, related_name="wormhole_types_spawning_here", blank=True
    )
    leads_to = models.ManyToManyField(
        WormholeClass, related_name="wormhole_types_leading_here", blank=True
    )

    objects = WormholeTypeQuerySet.as_manager()

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code

    @property
    def leads_to_drifter_space(self) -> bool:
        return self.leads_to.filter(category=WormholeClass.Category.DRIFTER).exists()

    @property
    def spawns_in_drifter_space(self) -> bool:
        return self.spawns_in.filter(category=WormholeClass.Category.DRIFTER).exists()

    @property
    def is_drifter_related(self) -> bool:
        """True if this code identifies a Drifter wormhole - either a static/wandering
        connection found inside Drifter space, or a K-space hole known to lead into it.
        """
        return self.spawns_in_drifter_space or self.leads_to_drifter_space


class ShatteredConstellation(models.Model):
    """A constellation containing only frigate-sized "shattered" wormhole systems."""

    constellation = models.OneToOneField(
        "eve_sde.Constellation", on_delete=models.CASCADE, primary_key=True
    )

    def __str__(self):
        return str(self.constellation)


class WormholeSystem(models.Model):
    """Per-solar-system wormhole data: its class, statics, possible wandering
    connections and environmental effect.
    """

    solar_system = models.OneToOneField(
        "eve_sde.SolarSystem", on_delete=models.CASCADE, primary_key=True, related_name="wormhole_info"
    )
    wormhole_class = models.ForeignKey(
        WormholeClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="systems",
    )
    statics = models.ManyToManyField(
        WormholeType, related_name="static_in_systems", blank=True
    )
    wandering_types = models.ManyToManyField(
        WormholeType, related_name="wandering_in_systems", blank=True
    )
    effect = models.ForeignKey(
        Effect, on_delete=models.SET_NULL, null=True, blank=True, related_name="systems"
    )

    objects = WormholeSystemQuerySet.as_manager()

    class Meta:
        ordering = ["solar_system__name"]
        verbose_name = _("wormhole system")
        verbose_name_plural = _("wormhole systems")

    def __str__(self):
        return self.solar_system.name

    @property
    def is_drifter_system(self) -> bool:
        return bool(self.wormhole_class and self.wormhole_class.is_drifter)

    @property
    def is_shattered(self) -> bool:
        return ShatteredConstellation.objects.filter(
            pk=self.solar_system.constellation_id
        ).exists()

"""Custom querysets for filtering wormhole reference data."""

from django.db import models


class WormholeTypeQuerySet(models.QuerySet):
    def static_capable(self):
        return self.filter(is_static_capable=True)

    def wandering(self):
        return self.filter(can_be_wandering=True)

    def drifter_related(self):
        """Wormhole codes that either spawn inside Drifter space or are known
        K-space entrances into it (e.g. B735, C414, R259, S877, V928).
        """
        return self.filter(
            models.Q(spawns_in__category="drifter") | models.Q(leads_to__category="drifter")
        ).distinct()

    def leading_to_class(self, slug_or_id):
        field = "leads_to__class_id" if isinstance(slug_or_id, int) else "leads_to__slug"
        return self.filter(**{field: slug_or_id}).distinct()

    def spawning_in_class(self, slug_or_id):
        field = "spawns_in__class_id" if isinstance(slug_or_id, int) else "spawns_in__slug"
        return self.filter(**{field: slug_or_id}).distinct()


class WormholeSystemQuerySet(models.QuerySet):
    def in_class(self, slug_or_id):
        if isinstance(slug_or_id, int):
            return self.filter(wormhole_class_id=slug_or_id)
        return self.filter(wormhole_class__slug=slug_or_id)

    def drifter_systems(self):
        return self.filter(wormhole_class__category="drifter")

    def with_effect(self, effect_name: str):
        return self.filter(effect__name=effect_name)

    def with_static(self, code: str):
        return self.filter(statics__code=code)

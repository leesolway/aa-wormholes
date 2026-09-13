"""Small helper functions for identifying wormholes and the space they connect.

Intended as the entry point for other apps (e.g. aa-wanderer) that need to
answer "what is this wormhole / this system" without reaching into the model
layer directly.
"""

from __future__ import annotations

from wormholes.models import WormholeClass, WormholeSystem, WormholeType

DRIFTER_CLASS_SLUGS = {"sentinel", "barbican", "vidette", "conflux", "redoubt"}


def identify_wormhole_code(code: str) -> WormholeType | None:
    """Look up a wormhole type by its in-game code (e.g. "K162", "N062").

    Case-insensitive; returns None for unrecognized codes.
    """
    if not code:
        return None
    return WormholeType.objects.filter(code__iexact=code.strip()).first()


def is_drifter_wormhole_code(code: str) -> bool:
    """True if the given code identifies a Drifter wormhole: either a
    connection found inside Drifter space, or a known K-space entrance to it.
    """
    wormhole_type = identify_wormhole_code(code)
    return bool(wormhole_type and wormhole_type.is_drifter_related)


def wormhole_class_for_solar_system(solar_system) -> WormholeClass | None:
    """Resolve the WormholeClass of an eve_sde.SolarSystem instance."""
    class_id = getattr(solar_system, "wormhole_class_id_raw", None)
    if class_id is None:
        return None
    return WormholeClass.objects.filter(pk=class_id).first()


def wormhole_system_info(solar_system) -> WormholeSystem | None:
    """Fetch the WormholeSystem row (statics, effect, ...) for a solar system, if any."""
    return WormholeSystem.objects.filter(pk=solar_system.pk).first()

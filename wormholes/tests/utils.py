"""Helpers for creating the minimal eve_sde fixtures wormholes tests need."""

from __future__ import annotations

from eve_sde.models import Constellation, Region, SolarSystem

_next_id = [21000000]


def create_solar_system(
    solar_system_id: int,
    name: str,
    wormhole_class_id_raw: int | None,
    constellation: Constellation | None = None,
    security_status: float = -0.99,
) -> SolarSystem:
    if constellation is None:
        constellation = create_constellation()
    return SolarSystem.objects.create(
        id=solar_system_id,
        name=name,
        constellation=constellation,
        wormhole_class_id_raw=wormhole_class_id_raw,
        security_status=security_status,
    )


def create_constellation(region: Region | None = None) -> Constellation:
    if region is None:
        region = Region.objects.first() or Region.objects.create(id=10000030, name="Heimatar")
    _next_id[0] += 1
    return Constellation.objects.create(id=_next_id[0], name=f"Constellation {_next_id[0]}", region=region)

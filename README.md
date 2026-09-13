# AA Wormholes

Static EVE Online wormhole reference data for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth):
wormhole classes (C1-C6, C13 shattered frigate holes, the five Drifter
classes C14-C18, Thera, Pochven), wormhole connection types (K162, N062,
...), per-solar-system statics, and system environmental effects (Pulsar,
Magnetar, Black Hole, Wolf-Rayet Star, Cataclysmic Variable, Red Giant, and
the Pochven Stellar Observatory effects).

This is a backend/data app: models + Django admin for browsing the data,
and a small `wormholes.services` API for other apps to query it. It has no
end-user pages of its own.

Solar systems are matched against
[`django-eveonline-sde`](https://github.com/Solar-Helix-Independent-Transport/django-eveonline-sde)'s
`eve_sde.SolarSystem` - a system's wormhole class is read directly from
`solar_system.wormhole_class_id_raw` rather than duplicated in this app.

## Data source

The reference data in `wormholes/data/` (wormhole classes, connection types,
per-system statics, effect modifiers) is adapted from the MIT-licensed
[Wanderer](https://github.com/wanderer-industries/wanderer) map tool's
`priv/repo/data/*.json`. See `LICENSE` for attribution.

## Installation

1. Add `"wormholes"` to `INSTALLED_APPS` (after `"eve_sde"`).
2. Run migrations: `python manage.py migrate wormholes`.
3. Load the reference data: `python manage.py wormholes_loaddata`.

Re-run `wormholes_loaddata` any time - it's idempotent, and safe to run
before the SDE has been fully synced (solar systems it doesn't recognize
yet are skipped and picked up on the next run).

## Models

- `WormholeClass` - one row per EVE `wormholeClassID` (C1-C6, Thera, C13,
  the five Drifter classes, Pochven, Abyssal, K-space, ...), with a
  `category` field and `is_drifter` / `is_wormhole_space` helpers.
- `WormholeType` - a connection type identified by its code (e.g. `K162`,
  `N062`), with mass/lifetime limits, which classes it can spawn in
  (`spawns_in`), which classes it leads to (`leads_to`), and an
  `is_drifter_related` property.
- `WormholeSystem` - per-system statics, possible wandering connections,
  and environmental effect. Keyed 1:1 on `eve_sde.SolarSystem`.
- `Effect` / `EffectModifier` - system environmental effects and their
  per-class-strength modifiers.
- `ShatteredConstellation` - the handful of constellations containing only
  frigate-sized "shattered" wormhole systems.

## Identifying Drifter wormholes

A wormhole is "Drifter-related" either because it's a connection found
inside Drifter space (Sentinel/Barbican/Vidette/Conflux/Redoubt) or because
it's a known K-space entrance into it:

```python
from wormholes.services import is_drifter_wormhole_code

is_drifter_wormhole_code("N062")  # True - static inside Drifter space, leads to a C5
is_drifter_wormhole_code("B735")  # True - k-space wandering hole leading into Barbican
is_drifter_wormhole_code("A009")  # False - an ordinary wandering hole
```

See `wormholes/services.py` for the rest of the lookup helpers
(`identify_wormhole_code`, `wormhole_class_for_solar_system`,
`wormhole_system_info`).

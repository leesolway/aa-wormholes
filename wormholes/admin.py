"""Admin site.

All models here are static reference data populated by the
``wormholes_loaddata`` management command, so the admin is read-only browsing
rather than a data-entry surface - re-running the command would overwrite any
manual edits anyway.
"""

from django.contrib import admin

from wormholes.models import (
    Effect,
    EffectModifier,
    ShatteredConstellation,
    WormholeClass,
    WormholeSystem,
    WormholeType,
)


class ReadOnlyAdminMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm(f"{self.model._meta.app_label}.view_{self.model._meta.model_name}")


@admin.register(WormholeClass)
class WormholeClassAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["class_id", "short_title", "title", "category", "effect_power"]
    list_filter = ["category"]
    search_fields = ["slug", "short_name", "title", "short_title"]


@admin.register(WormholeType)
class WormholeTypeAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = [
        "code",
        "lifetime_hours",
        "total_mass",
        "max_jump_mass",
        "is_static_capable",
        "can_be_wandering",
        "is_reverse_signature",
    ]
    list_filter = ["is_static_capable", "can_be_wandering", "is_reverse_signature", "spawns_in", "leads_to"]
    search_fields = ["code"]


class EffectModifierInline(admin.TabularInline):
    model = EffectModifier
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Effect)
class EffectAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    inlines = [EffectModifierInline]


@admin.register(ShatteredConstellation)
class ShatteredConstellationAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["constellation"]
    search_fields = ["constellation__name"]


@admin.register(WormholeSystem)
class WormholeSystemAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["solar_system", "wormhole_class", "effect"]
    list_filter = ["wormhole_class", "effect"]
    search_fields = ["solar_system__name", "statics__code", "wandering_types__code"]

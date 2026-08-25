from django.contrib import admin, messages
from django.utils.translation import ngettext

from .models import (
    Asset,
    CompositeIndicator,
    MetricSnapshot,
    WatchlistEntry,
)
from .services.calculations import compute_shin_indicator


@admin.register(CompositeIndicator)
class CompositeIndicatorAdmin(admin.ModelAdmin):
    list_display = ("name", "formula_code", "updated_at")
    search_fields = ("name",)


class MetricSnapshotInline(admin.TabularInline):
    model = MetricSnapshot
    extra = 0
    ordering = ("-timestamp",)
    readonly_fields = ("date",)
    exclude = ("shin_indicator", "source")


@admin.register(MetricSnapshot)
class MetricSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "asset", "timestamp", "p_l", "p_vp", "dy", "margem_liquida",
    )
    list_filter = ("asset",)
    search_fields = ("asset__symbol",)
    readonly_fields = ("date",)
    exclude = ("shin_indicator", "source")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "asset_type", "is_active")
    list_filter = ("is_active", "asset_type")
    search_fields = ("symbol", "name")
    inlines = [MetricSnapshotInline]
    actions = ["recalculate_selected_shin_indicator"]

    def recalculate_selected_shin_indicator(self, request, queryset):
        computed_count = 0
        for asset in queryset:
            value = compute_shin_indicator(asset, persist=True)
            if value is not None:
                computed_count += 1

        self.message_user(
            request,
            ngettext(
                "%d indicator value recalculated.",
                "%d indicator values recalculated.",
                computed_count,
            )
            % computed_count,
            messages.SUCCESS,
        )

    recalculate_selected_shin_indicator.short_description = "Recalculate SHIN indicator for selected assets"


@admin.register(WatchlistEntry)
class WatchlistEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "asset", "added_at")
    list_filter = ("user",)

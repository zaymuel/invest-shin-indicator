from django.contrib import admin, messages
from django.utils.translation import ngettext

from .models import (
    Asset,
    CompositeIndicator,
    Metric,
    MetricHistory,
    WatchlistEntry,
)
from .services.calculations import compute_derived_metrics


@admin.register(CompositeIndicator)
class CompositeIndicatorAdmin(admin.ModelAdmin):
    list_display = ("name", "formula_code", "updated_at")
    search_fields = ("name",)


class MetricHistoryInline(admin.TabularInline):
    model = MetricHistory
    extra = 0
    ordering = ("-timestamp",)


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ("asset", "name", "key", "unit", "kind", "is_active", "updated_at")
    list_filter = ("is_active", "kind", "asset")
    search_fields = ("asset__symbol", "name", "key")
    readonly_fields = ("key", "unit", "kind")
    inlines = [MetricHistoryInline]
    actions = ["recalculate_selected_derived"]

    def recalculate_selected_derived(self, request, queryset):
        derived_qs = queryset.filter(kind="derived", asset__isnull=False)
        computed_count = 0
        for asset in Asset.objects.filter(id__in=derived_qs.values_list("asset_id", flat=True).distinct()):
            computed = compute_derived_metrics(
                derived_keys=list(derived_qs.filter(asset=asset).values_list("key", flat=True)),
                persist=True,
                asset=asset,
            )
            computed_count += sum(1 for value in computed.values() if value is not None)

        self.message_user(
            request,
            ngettext(
                "%d derived metric recalculated.",
                "%d derived metrics recalculated.",
                computed_count,
            )
            % computed_count,
            messages.SUCCESS,
        )

    recalculate_selected_derived.short_description = "Recalculate selected derived metrics"


@admin.register(MetricHistory)
class MetricHistoryAdmin(admin.ModelAdmin):
    list_display = ("metric", "value", "timestamp", "source")
    list_filter = ("metric",)
    search_fields = ("metric__name", "source")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "asset_type", "is_active")
    list_filter = ("is_active", "asset_type")
    search_fields = ("symbol", "name")


@admin.register(WatchlistEntry)
class WatchlistEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "asset", "added_at")
    list_filter = ("user",)

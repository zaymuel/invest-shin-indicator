from django.contrib import admin, messages
from django.utils.translation import ngettext

from .models import (
    Asset,
    CompositeIndicator,
    Metric,
    MetricFormula,
    MetricHistory,
    WatchlistEntry,
)
from .services.calculations import compute_derived_metrics


@admin.register(CompositeIndicator)
class CompositeIndicatorAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at")
    search_fields = ("name",)


class MetricHistoryInline(admin.TabularInline):
    model = MetricHistory
    extra = 0
    ordering = ("-timestamp",)


class MetricFormulaInline(admin.StackedInline):
    model = MetricFormula
    extra = 0
    fk_name = "metric"


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ("name", "composite", "key", "kind", "is_active", "updated_at")
    list_filter = ("is_active", "composite", "kind")
    search_fields = ("name", "key")
    inlines = [MetricFormulaInline, MetricHistoryInline]
    actions = ["recalculate_selected_derived"]

    def recalculate_selected_derived(self, request, queryset):
        # if user selected specific derived metrics, compute only those; otherwise compute all
        derived_qs = queryset.filter(kind="derived")
        if not derived_qs.exists():
            # nothing selected: calculate all derived
            computed = compute_derived_metrics(persist=True)
        else:
            keys = list(derived_qs.values_list("key", flat=True))
            computed = compute_derived_metrics(derived_keys=keys, persist=True)

        n = sum(1 for v in computed.values() if v is not None)
        self.message_user(request, ngettext(
            '%d derived metric recalculated.',
            '%d derived metrics recalculated.',
            n,
        ) % n, messages.SUCCESS)

    recalculate_selected_derived.short_description = "Recalculate selected derived metrics"


@admin.register(MetricFormula)
class MetricFormulaAdmin(admin.ModelAdmin):
    list_display = ("metric", "formula_code", "is_active", "updated_at")
    list_filter = ("formula_code", "is_active")
    search_fields = ("metric__name", "metric__key", "formula_code")


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

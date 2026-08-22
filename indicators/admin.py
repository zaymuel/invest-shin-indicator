from django.contrib import admin

from .models import Asset, CompositeIndicator, Metric, MetricHistory, WatchlistEntry


@admin.register(CompositeIndicator)
class CompositeIndicatorAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at")
    search_fields = ("name",)


class MetricHistoryInline(admin.TabularInline):
    model = MetricHistory
    extra = 0
    ordering = ("-timestamp",)


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ("name", "composite", "key", "is_active", "updated_at")
    list_filter = ("is_active", "composite")
    search_fields = ("name", "key")
    inlines = [MetricHistoryInline]


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

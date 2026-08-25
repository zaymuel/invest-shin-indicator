from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .models import (
    Asset,
    CompositeIndicator,
    MetricSnapshot,
    WatchlistEntry,
)


class HomeView(TemplateView):
    template_name = "indicators/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        first_indicator = CompositeIndicator.objects.first()
        context["first_indicator"] = first_indicator

        if not user.is_authenticated:
            context["total_assets_count"] = Asset.objects.filter(
                is_active=True).count()
            return context

        entries = (
            WatchlistEntry.objects.filter(user=user)
            .select_related("asset")
            .order_by("asset__symbol")
        )

        watched_asset_ids = [entry.asset_id for entry in entries]
        latest_snapshot = MetricSnapshot.objects.filter(
            asset=OuterRef("pk")
        ).order_by("-timestamp")

        assets_with_snapshots = (
            Asset.objects.filter(id__in=watched_asset_ids, is_active=True)
            .annotate(latest_snapshot_id=Subquery(latest_snapshot.values("pk")[:1]))
        )

        snapshot_ids = [
            a.latest_snapshot_id for a in assets_with_snapshots if a.latest_snapshot_id
        ]
        snapshots_by_id = {
            s.id: s
            for s in MetricSnapshot.objects.filter(id__in=snapshot_ids)
        }

        entry_map = {entry.asset_id: entry.id for entry in entries}
        asset_info = {}
        for asset in assets_with_snapshots:
            snapshot = snapshots_by_id.get(asset.latest_snapshot_id)
            asset_info[asset.id] = {
                "asset": asset,
                "snapshot": snapshot,
                "entry_id": entry_map.get(asset.id),
                "shin_indicator": snapshot.shin_indicator if snapshot else None,
            }

        grouped_assets = []
        for type_code, type_label in Asset.ASSET_TYPE_CHOICES:
            type_items = [
                item for item in asset_info.values()
                if item["asset"].asset_type == type_code
            ]
            if type_items:
                grouped_assets.append({
                    "type_code": type_code,
                    "type_label": type_label,
                    "items": type_items,
                    "count": len(type_items),
                })

        context["grouped_assets"] = grouped_assets
        context["total_watched"] = len(asset_info)
        return context


class CompositeIndicatorListView(ListView):
    model = CompositeIndicator
    template_name = "indicators/indicator_list.html"
    context_object_name = "indicators"


class CompositeIndicatorDetailView(DetailView):
    model = CompositeIndicator
    template_name = "indicators/indicator_detail.html"
    context_object_name = "indicator"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        metric_fields = MetricSnapshot.METRIC_FIELDS
        metric_labels = [MetricSnapshot.METRIC_LABELS[field]
                         for field in metric_fields]

        latest_snapshot = MetricSnapshot.objects.filter(
            asset=OuterRef("pk")
        ).order_by("-timestamp")
        assets = Asset.objects.filter(is_active=True).order_by("symbol").annotate(
            latest_snapshot_id=Subquery(latest_snapshot.values("pk")[:1])
        )

        snapshot_ids = [
            asset.latest_snapshot_id for asset in assets if asset.latest_snapshot_id
        ]
        snapshots_by_id = {
            snapshot.id: snapshot
            for snapshot in MetricSnapshot.objects.filter(id__in=snapshot_ids)
        }

        rows = []
        for asset in assets:
            snapshot = snapshots_by_id.get(asset.latest_snapshot_id)
            rows.append({
                "asset": asset,
                "metric_values": [
                    getattr(snapshot, field) if snapshot else None
                    for field in metric_fields
                ],
                "indicator_value": snapshot.shin_indicator if snapshot else None,
            })

        context["metric_labels"] = metric_labels
        context["rows"] = rows
        return context


class AssetListView(ListView):
    model = Asset
    template_name = "indicators/asset_list.html"
    context_object_name = "assets"

    def get_queryset(self):
        latest_snapshot = MetricSnapshot.objects.filter(
            asset=OuterRef("pk")
        ).order_by("-timestamp")
        return (
            Asset.objects.filter(is_active=True)
            .annotate(latest_snapshot_id=Subquery(latest_snapshot.values("pk")[:1]))
            .order_by("symbol")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assets = context["assets"]
        snapshot_ids = [
            a.latest_snapshot_id for a in assets if a.latest_snapshot_id]
        snapshots_by_id = {
            s.id: s for s in MetricSnapshot.objects.filter(id__in=snapshot_ids)
        }

        watched_asset_ids = set()
        if self.request.user.is_authenticated:
            watched_asset_ids = set(
                WatchlistEntry.objects.filter(user=self.request.user).values_list(
                    "asset_id", flat=True
                )
            )

        asset_rows = []
        for asset in assets:
            snapshot = snapshots_by_id.get(asset.latest_snapshot_id)
            asset_rows.append({
                "asset": asset,
                "snapshot": snapshot,
                "shin_indicator": snapshot.shin_indicator if snapshot else None,
                "is_watched": asset.id in watched_asset_ids,
            })

        context["asset_rows"] = asset_rows
        context["first_indicator"] = CompositeIndicator.objects.first()
        return context


class AssetDetailView(DetailView):
    model = Asset
    template_name = "indicators/asset_detail.html"
    context_object_name = "asset"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.object

        snapshots = asset.metric_snapshots.order_by("-timestamp")
        latest_snapshot = snapshots.first()
        history = list(snapshots[:50])

        is_watched = False
        watchlist_entry = None
        if self.request.user.is_authenticated:
            watchlist_entry = WatchlistEntry.objects.filter(
                user=self.request.user, asset=asset
            ).first()
            is_watched = watchlist_entry is not None

        metric_fields = MetricSnapshot.METRIC_FIELDS
        metric_labels = MetricSnapshot.METRIC_LABELS

        latest_metrics = []
        if latest_snapshot:
            for field in metric_fields:
                val = getattr(latest_snapshot, field)
                if val is not None:
                    latest_metrics.append({
                        "field": field,
                        "label": metric_labels.get(field, field),
                        "value": val,
                    })

        context["latest_snapshot"] = latest_snapshot
        context["latest_metrics"] = latest_metrics
        context["history"] = history
        context["metric_fields"] = metric_fields
        context["metric_labels"] = metric_labels
        context["is_watched"] = is_watched
        context["watchlist_entry"] = watchlist_entry
        context["first_indicator"] = CompositeIndicator.objects.first()
        return context


class WatchlistListView(LoginRequiredMixin, ListView):
    model = WatchlistEntry
    template_name = "indicators/watchlist_list.html"
    context_object_name = "entries"
    login_url = reverse_lazy("login")

    def get_queryset(self):
        return (
            WatchlistEntry.objects.filter(user=self.request.user)
            .select_related("asset")
            .order_by("-added_at")
        )


class WatchlistAddView(LoginRequiredMixin, View):
    login_url = reverse_lazy("login")

    def post(self, request, *args, **kwargs):
        asset_id = request.POST.get("asset_id")
        asset = get_object_or_404(Asset, id=asset_id, is_active=True)
        entry, created = WatchlistEntry.objects.get_or_create(
            user=request.user, asset=asset
        )
        if created:
            messages.success(
                request, f"{asset.symbol} added to your watchlist.")
        else:
            messages.info(
                request, f"{asset.symbol} is already in your watchlist.")

        next_url = request.POST.get("next") or request.META.get(
            "HTTP_REFERER") or reverse_lazy("home")
        return redirect(next_url)


class WatchlistRemoveView(LoginRequiredMixin, View):
    login_url = reverse_lazy("login")

    def post(self, request, *args, **kwargs):
        entry = get_object_or_404(
            WatchlistEntry, id=kwargs.get("pk"), user=request.user)
        asset_symbol = entry.asset.symbol
        entry.delete()
        messages.info(request, f"{asset_symbol} removed from your watchlist.")

        next_url = request.POST.get("next") or request.META.get(
            "HTTP_REFERER") or reverse_lazy("home")
        return redirect(next_url)

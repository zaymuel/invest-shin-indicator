from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView

from .models import Asset, CompositeIndicator, Metric, MetricHistory, WatchlistEntry
from .services.calculations import compute_derived_metrics


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
        latest_history = MetricHistory.objects.filter(metric=OuterRef("pk")).order_by(
            "-timestamp"
        )
        metrics = (
            Metric.objects.filter(composite=self.object, is_active=True)
            .annotate(
                latest_value=Subquery(latest_history.values("value")[:1]),
                latest_timestamp=Subquery(
                    latest_history.values("timestamp")[:1]),
            )
            .order_by("name")
        )
        recent_history = (
            MetricHistory.objects.filter(metric__composite=self.object)
            .select_related("metric")
            .order_by("-timestamp")[:50]
        )

        available_metric_keys = [metric.key for metric in metrics]
        derived_metrics = compute_derived_metrics(
            derived_keys=available_metric_keys,
            persist=False,
        )

        context["metrics"] = metrics
        context["recent_history"] = recent_history
        context["derived_metrics"] = derived_metrics
        return context


class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = "indicators/asset_list.html"
    context_object_name = "assets"
    login_url = reverse_lazy("login")

    def get_queryset(self):
        return Asset.objects.filter(is_active=True).order_by("symbol")


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
        return redirect("watchlist")


class WatchlistRemoveView(LoginRequiredMixin, View):
    login_url = reverse_lazy("login")

    def post(self, request, *args, **kwargs):
        entry = get_object_or_404(
            WatchlistEntry, id=kwargs.get("pk"), user=request.user)
        asset_symbol = entry.asset.symbol
        entry.delete()
        messages.info(request, f"{asset_symbol} removed from your watchlist.")
        return redirect("watchlist")

from django.urls import path

from .views import (
    AssetDetailView,
    AssetListView,
    CompositeIndicatorDetailView,
    CompositeIndicatorListView,
    HomeView,
    WatchlistAddView,
    WatchlistListView,
    WatchlistRemoveView,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("indicators/", CompositeIndicatorListView.as_view(), name="indicator-list"),
    path("indicators/<int:pk>/", CompositeIndicatorDetailView.as_view(),
         name="indicator-detail"),
    path("assets/", AssetListView.as_view(), name="asset-list"),
    path("assets/<int:pk>/", AssetDetailView.as_view(), name="asset-detail"),
    path("watchlist/", WatchlistListView.as_view(), name="watchlist"),
    path("watchlist/add/", WatchlistAddView.as_view(), name="watchlist-add"),
    path("watchlist/remove/<int:pk>/",
         WatchlistRemoveView.as_view(), name="watchlist-remove"),
]

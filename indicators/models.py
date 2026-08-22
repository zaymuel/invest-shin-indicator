from django.conf import settings
from django.db import models
from django.utils import timezone


class CompositeIndicator(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name="name")
    description = models.TextField(blank=True, verbose_name="description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updated at")

    class Meta:
        verbose_name = "Composite indicator"
        verbose_name_plural = "Composite indicators"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Metric(models.Model):
    KIND_RAW = "raw"
    KIND_DERIVED = "derived"

    KIND_CHOICES = [
        (KIND_RAW, "Raw"),
        (KIND_DERIVED, "Derived"),
    ]

    composite = models.ForeignKey(
        CompositeIndicator,
        related_name="metrics",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="composite indicator",
    )
    asset = models.ForeignKey(
        "Asset",
        related_name="metrics",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="asset",
    )
    name = models.CharField(max_length=120, verbose_name="name")
    key = models.SlugField(max_length=60, verbose_name="key")
    unit = models.CharField(max_length=40, blank=True, verbose_name="unit")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=KIND_RAW, verbose_name="kind")
    is_active = models.BooleanField(default=True, verbose_name="active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updated at")

    class Meta:
        verbose_name = "Metric"
        verbose_name_plural = "Metrics"
        unique_together = (("composite", "key"), ("asset", "key"))
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def latest_history(self):
        return self.history.order_by("-timestamp").first()


class MetricFormula(models.Model):
    FORMULA_SHIN_V1 = "shin_v1"

    FORMULA_CHOICES = [
        (FORMULA_SHIN_V1, "SHIN indicator (v1)"),
    ]

    metric = models.OneToOneField(
        Metric,
        related_name="formula",
        on_delete=models.CASCADE,
        verbose_name="metric",
    )
    formula_code = models.CharField(
        max_length=40,
        choices=FORMULA_CHOICES,
        verbose_name="formula code",
    )
    expression = models.TextField(verbose_name="expression")
    operands = models.JSONField(default=dict, blank=True, verbose_name="operands")
    is_active = models.BooleanField(default=True, verbose_name="active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updated at")

    class Meta:
        verbose_name = "Metric formula"
        verbose_name_plural = "Metric formulas"
        ordering = ["metric__name"]

    def __str__(self) -> str:
        return f"{self.metric.key} ({self.formula_code})"


class MetricHistory(models.Model):
    metric = models.ForeignKey(
        Metric,
        related_name="history",
        on_delete=models.CASCADE,
        verbose_name="metric",
    )
    value = models.DecimalField(max_digits=20, decimal_places=6, verbose_name="value")
    timestamp = models.DateTimeField(
        default=timezone.now, db_index=True, verbose_name="timestamp"
    )
    source = models.CharField(max_length=255, blank=True, verbose_name="source")

    class Meta:
        verbose_name = "Metric history"
        verbose_name_plural = "Metric history"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.metric.name} @ {self.timestamp:%Y-%m-%d %H:%M:%S}"


class Asset(models.Model):
    TYPE_REIT = "reit"
    TYPE_FII = "fii"
    TYPE_STOCK = "stock"
    TYPE_ACAO = "acao"

    ASSET_TYPE_CHOICES = [
        (TYPE_REIT, "REIT"),
        (TYPE_FII, "FII"),
        (TYPE_STOCK, "Stock"),
        (TYPE_ACAO, "Ação"),
    ]

    symbol = models.CharField(max_length=20, unique=True, verbose_name="symbol")
    name = models.CharField(max_length=120, blank=True, verbose_name="name")
    asset_type = models.CharField(
        max_length=20,
        choices=ASSET_TYPE_CHOICES,
        default=TYPE_STOCK,
        verbose_name="asset type",
    )
    is_active = models.BooleanField(default=True, verbose_name="active")

    class Meta:
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
        ordering = ["symbol"]

    def __str__(self) -> str:
        return self.symbol


class WatchlistEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="watchlist_entries",
        on_delete=models.CASCADE,
        verbose_name="user",
    )
    asset = models.ForeignKey(
        Asset,
        related_name="watchlisted_by",
        on_delete=models.CASCADE,
        verbose_name="asset",
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="added at")

    class Meta:
        verbose_name = "Watchlist entry"
        verbose_name_plural = "Watchlist entries"
        unique_together = ("user", "asset")
        ordering = ["-added_at"]

    def __str__(self) -> str:
        return f"{self.user} - {self.asset}"

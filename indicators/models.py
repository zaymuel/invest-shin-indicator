from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class CompositeIndicator(models.Model):
    FORMULA_SHIN_V1 = "shin_v1"

    FORMULA_CHOICES = [
        (FORMULA_SHIN_V1, "SHIN indicator (v1)"),
    ]

    SHIN_EXPRESSION = "=LOG10(MAX(0.001, (1+([@[DY (%)]]/4)) * MAX(0.01, [@[Marg líq (%)]]) * MAX(0.01, [@[CAGR receitas]]) * MAX(0.01, [@[CAGR lucros]]) / (IF([@[P/L]]<=0, 1000, [@[P/L]]) * IF([@[P/VP]]<=0, 1000, [@[P/VP]]))))"
    SHIN_OPERANDS = {
        "dy_key": "dy",
        "margem_liquida_key": "margem_liquida",
        "receitas_cagr_key": "receitas_cagr5",
        "lucros_cagr_key": "lucros_cagr5",
        "p_l_key": "p_l",
        "p_vp_key": "p_vp",
    }

    name = models.CharField(max_length=120, unique=True, verbose_name="name")
    description = models.TextField(blank=True, verbose_name="description")
    formula_code = models.CharField(
        max_length=40,
        choices=FORMULA_CHOICES,
        blank=True,
        null=True,
        verbose_name="formula code",
    )
    expression = models.TextField(blank=True, verbose_name="expression")
    operands = models.JSONField(default=dict, blank=True, verbose_name="operands")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updated at")

    class Meta:
        verbose_name = "Composite indicator"
        verbose_name_plural = "Composite indicators"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get_or_create_shin_definition(cls):
        composite, _ = cls.objects.get_or_create(
            name="SHIN Indicator",
            defaults={
                "description": "Composite indicator formula for SHIN score.",
                "formula_code": cls.FORMULA_SHIN_V1,
                "expression": cls.SHIN_EXPRESSION,
                "operands": cls.SHIN_OPERANDS,
            },
        )
        return composite


class Metric(models.Model):
    KIND_RAW = "raw"
    KIND_DERIVED = "derived"

    KIND_CHOICES = [
        (KIND_RAW, "Raw"),
        (KIND_DERIVED, "Derived"),
    ]

    METRIC_P_L = "p_l"
    METRIC_P_VP = "p_vp"
    METRIC_DY = "dy"
    METRIC_MARGEM_LIQUIDA = "margem_liquida"
    METRIC_RECEITAS_CAGR3 = "receitas_cagr3"
    METRIC_RECEITAS_CAGR5 = "receitas_cagr5"
    METRIC_LUCROS_CAGR3 = "lucros_cagr3"
    METRIC_LUCROS_CAGR5 = "lucros_cagr5"
    METRIC_SHIN_INDICATOR = "shin_indicator"

    METRIC_DEFINITIONS = {
        METRIC_P_L: {"label": "P/L", "unit": "", "kind": KIND_RAW},
        METRIC_P_VP: {"label": "P/VP", "unit": "", "kind": KIND_RAW},
        METRIC_DY: {"label": "DY (%)", "unit": "%", "kind": KIND_RAW},
        METRIC_MARGEM_LIQUIDA: {
            "label": "Margem Líquida (%)",
            "unit": "%",
            "kind": KIND_RAW,
        },
        METRIC_RECEITAS_CAGR3: {
            "label": "CAGR Receitas 3a (%)",
            "unit": "%",
            "kind": KIND_RAW,
        },
        METRIC_RECEITAS_CAGR5: {
            "label": "CAGR Receitas 5a (%)",
            "unit": "%",
            "kind": KIND_RAW,
        },
        METRIC_LUCROS_CAGR3: {
            "label": "CAGR Lucros 3a (%)",
            "unit": "%",
            "kind": KIND_RAW,
        },
        METRIC_LUCROS_CAGR5: {
            "label": "CAGR Lucros 5a (%)",
            "unit": "%",
            "kind": KIND_RAW,
        },
        METRIC_SHIN_INDICATOR: {
            "label": "SHIN Indicator",
            "unit": "log10",
            "kind": KIND_DERIVED,
        },
    }

    METRIC_NAME_CHOICES = [
        (metric_key, metric_data["label"])
        for metric_key, metric_data in METRIC_DEFINITIONS.items()
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
    name = models.CharField(
        max_length=120,
        choices=METRIC_NAME_CHOICES,
        verbose_name="metric name",
    )
    key = models.SlugField(max_length=60, verbose_name="key", editable=False)
    unit = models.CharField(max_length=40, blank=True, verbose_name="unit", editable=False)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=KIND_RAW, verbose_name="kind")
    is_active = models.BooleanField(default=True, verbose_name="active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="updated at")

    class Meta:
        verbose_name = "Metric"
        verbose_name_plural = "Metrics"
        unique_together = (("asset", "key"),)
        ordering = ["name"]

    def __str__(self) -> str:
        return self.get_name_display()

    def latest_history(self):
        return self.history.order_by("-timestamp").first()

    def save(self, *args, **kwargs):
        definition = self.METRIC_DEFINITIONS.get(self.name)
        if definition is None:
            raise ValueError(f"Unsupported metric name: {self.name}")

        self.key = self.name
        self.unit = definition["unit"]
        self.kind = definition["kind"]

        if self.kind == self.KIND_DERIVED and not self.composite:
            self.composite = CompositeIndicator.get_or_create_shin_definition()

        super().save(*args, **kwargs)


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
        return f"{self.metric.get_name_display()} @ {self.timestamp:%Y-%m-%d %H:%M:%S}"


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

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.ensure_default_metrics()

    def ensure_default_metrics(self):
        composite = CompositeIndicator.get_or_create_shin_definition()
        with transaction.atomic():
            for metric_name, metric_definition in Metric.METRIC_DEFINITIONS.items():
                defaults = {
                    "name": metric_name,
                    "is_active": True,
                }
                if metric_definition["kind"] == Metric.KIND_DERIVED:
                    defaults["composite"] = composite

                metric, created = Metric.objects.get_or_create(
                    asset=self,
                    key=metric_name,
                    defaults=defaults,
                )
                if not created:
                    updates = []
                    if metric.name != metric_name:
                        metric.name = metric_name
                        updates.append("name")
                    if metric_definition["kind"] == Metric.KIND_DERIVED and metric.composite_id != composite.id:
                        metric.composite = composite
                        updates.append("composite")
                    if updates:
                        metric.save(update_fields=updates)


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

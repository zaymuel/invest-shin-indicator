from django.conf import settings
from django.db import models
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
    operands = models.JSONField(
        default=dict, blank=True, verbose_name="operands")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="created at")
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


class MetricSnapshot(models.Model):
    """One row per (asset, date): every metric scraped for that asset at that time, plus the derived indicator."""

    METRIC_P_L = "p_l"
    METRIC_P_VP = "p_vp"
    METRIC_DY = "dy"
    METRIC_MARGEM_LIQUIDA = "margem_liquida"
    METRIC_RECEITAS_CAGR3 = "receitas_cagr3"
    METRIC_RECEITAS_CAGR5 = "receitas_cagr5"
    METRIC_LUCROS_CAGR3 = "lucros_cagr3"
    METRIC_LUCROS_CAGR5 = "lucros_cagr5"
    METRIC_FFO_CAGR3 = "ffo_cagr3"
    METRIC_FFO_CAGR5 = "ffo_cagr5"
    METRIC_CAIXA = "caixa"
    METRIC_DY_CAGR3 = "dy_cagr3"
    METRIC_DY_CAGR5 = "dy_cagr5"
    METRIC_VALOR_CAGR3 = "valor_cagr3"
    METRIC_VALOR_CAGR5 = "valor_cagr5"

    # Common to every asset type.
    METRIC_FIELDS = (
        METRIC_P_L,
        METRIC_P_VP,
        METRIC_DY,
        METRIC_MARGEM_LIQUIDA,
        # Ações growth (net income / revenue based).
        METRIC_RECEITAS_CAGR3,
        METRIC_RECEITAS_CAGR5,
        METRIC_LUCROS_CAGR3,
        METRIC_LUCROS_CAGR5,
        # REIT growth (FFO based).
        METRIC_FFO_CAGR3,
        METRIC_FFO_CAGR5,
        # FIIs specific metrics.
        METRIC_CAIXA,
        METRIC_DY_CAGR3,
        METRIC_DY_CAGR5,
        METRIC_VALOR_CAGR3,
        METRIC_VALOR_CAGR5,
    )

    METRIC_LABELS = {
        METRIC_P_L: "P/L",
        METRIC_P_VP: "P/VP",
        METRIC_DY: "DY (%)",
        METRIC_MARGEM_LIQUIDA: "Margem Líquida (%)",
        METRIC_RECEITAS_CAGR3: "CAGR Receitas 3a (%)",
        METRIC_RECEITAS_CAGR5: "CAGR Receitas 5a (%)",
        METRIC_LUCROS_CAGR3: "CAGR Lucros 3a (%)",
        METRIC_LUCROS_CAGR5: "CAGR Lucros 5a (%)",
        METRIC_FFO_CAGR3: "CAGR FFO 3a (%)",
        METRIC_FFO_CAGR5: "CAGR FFO 5a (%)",
        METRIC_CAIXA: "Caixa (%)",
        METRIC_DY_CAGR3: "CAGR DY 3a (%)",
        METRIC_DY_CAGR5: "CAGR DY 5a (%)",
        METRIC_VALOR_CAGR3: "CAGR Valor 3a (%)",
        METRIC_VALOR_CAGR5: "CAGR Valor 5a (%)",
    }

    asset = models.ForeignKey(
        "Asset",
        related_name="metric_snapshots",
        on_delete=models.CASCADE,
        verbose_name="asset",
    )
    timestamp = models.DateTimeField(
        default=timezone.now, db_index=True, verbose_name="timestamp")
    date = models.DateField(editable=False, db_index=True, verbose_name="date")
    source = models.CharField(
        max_length=255, blank=True, verbose_name="source")

    p_l = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="P/L")
    p_vp = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="P/VP")
    dy = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="DY (%)")
    margem_liquida = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name="Margem Líquida (%)")
    receitas_cagr3 = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name="CAGR Receitas 3a (%)")
    receitas_cagr5 = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name="CAGR Receitas 5a (%)")
    lucros_cagr3 = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name="CAGR Lucros 3a (%)")
    lucros_cagr5 = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name="CAGR Lucros 5a (%)")
    ffo_cagr3 = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name="CAGR FFO 3a (%)")
    ffo_cagr5 = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name="CAGR FFO 5a (%)")
    caixa = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name="Caixa (%)")
    dy_cagr3 = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name="CAGR DY 3a (%)")
    dy_cagr5 = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name="CAGR DY 5a (%)")
    valor_cagr3 = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name="CAGR Valor 3a (%)")
    valor_cagr5 = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True,
        verbose_name="CAGR Valor 5a (%)")

    # Derived: which formula applies depends on the asset's type (e.g. FIIs vs Ações/Stocks/REITs).
    shin_indicator = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True,
        editable=False, verbose_name="SHIN Indicator")

    class Meta:
        verbose_name = "Metric snapshot"
        verbose_name_plural = "Metric snapshots"
        unique_together = (("asset", "date"),)
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["asset", "-timestamp"],
                         name="asset_snapshot_ts_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.asset.symbol} @ {self.timestamp:%Y-%m-%d %H:%M:%S}"

    def save(self, *args, **kwargs):
        if self.timestamp is None:
            self.timestamp = timezone.now()
        self.date = (
            timezone.localtime(self.timestamp).date()
            if timezone.is_aware(self.timestamp)
            else self.timestamp.date()
        )
        if self.shin_indicator is None:
            from .services.calculations import calculate_snapshot_shin_score
            self.shin_indicator = calculate_snapshot_shin_score(self)
        super().save(*args, **kwargs)


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

    symbol = models.CharField(
        max_length=20, unique=True, verbose_name="symbol")
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
            CompositeIndicator.get_or_create_shin_definition()


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

# Implementation Plan: Metric Model Restructure (Wide Snapshot)

## 1. Motivation

Today, capturing "everything we know about an asset at a point in time" requires two models:

- `Metric` — a catalog row per `(asset, metric key)` (e.g. one row for `WEGE3`'s `p_l`, another for `WEGE3`'s `dy`, etc.), carrying `kind`/`unit`/`is_active`/`key`.
- `MetricHistory` — one time-series row per `Metric`, holding the actual scraped value + timestamp.

Pain points with this shape:

- Reading "the current state of an asset" means joining N `Metric` rows to their latest `MetricHistory` row each (mitigated today with subqueries in `views.py`, but still awkward).
- Writing "the current state of an asset" from one scrape run means N separate `MetricHistory.objects.create()` calls, each with its own timestamp instead of one atomic snapshot.
- The `Metric` catalog (`kind`, `unit`, `is_active`, `key`) is identical across every asset of the same shape — it doesn't vary per asset, so replicating a full catalog row per asset is pure overhead.
- `Asset.ensure_default_metrics()` has to pre-create 8 `Metric` rows for every new asset just so there's somewhere to attach history later.

## 2. New design: one wide, timestamped row per scrape

Collapse `Metric` (catalog) + `MetricHistory` (time series) into a single model, `MetricSnapshot`, with every possible metric hardcoded as its own nullable column. One row = one `Asset` + one point in time + every metric value captured during that scrape (nulls where the asset's type doesn't have that metric, or the scraper couldn't find it).

```python
class MetricSnapshot(models.Model):
    METRIC_FIELDS = (
        "p_l",
        "p_vp",
        "dy",
        "margem_liquida",
        "receitas_cagr3",
        "receitas_cagr5",
        "lucros_cagr3",
        "lucros_cagr5",
    )

    asset = models.ForeignKey(
        "Asset",
        related_name="metric_snapshots",
        on_delete=models.CASCADE,
        verbose_name="asset",
    )
    timestamp = models.DateTimeField(
        default=timezone.now, db_index=True, verbose_name="timestamp")
    source = models.CharField(max_length=255, blank=True, verbose_name="source")

    p_l = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True, verbose_name="P/L")
    p_vp = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True, verbose_name="P/VP")
    dy = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True, verbose_name="DY (%)")
    margem_liquida = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True,
        verbose_name="Margem Líquida (%)")
    receitas_cagr3 = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True,
        verbose_name="CAGR Receitas 3a (%)")
    receitas_cagr5 = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True,
        verbose_name="CAGR Receitas 5a (%)")
    lucros_cagr3 = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True,
        verbose_name="CAGR Lucros 3a (%)")
    lucros_cagr5 = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True,
        verbose_name="CAGR Lucros 5a (%)")

    class Meta:
        verbose_name = "Metric snapshot"
        verbose_name_plural = "Metric snapshots"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["asset", "-timestamp"],
                         name="asset_snapshot_ts_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.asset.symbol} @ {self.timestamp:%Y-%m-%d %H:%M:%S}"
```

`METRIC_FIELDS` (plus a parallel `METRIC_LABELS` dict built from each field's `verbose_name`) becomes the single source of truth other code iterates over, replacing today's `Metric.METRIC_DEFINITIONS`.

### What gets deleted
- `Metric` model entirely (catalog concept: `kind`, `unit`, `is_active`, `key`, `composite` FK, `METRIC_DEFINITIONS`/`METRIC_NAME_CHOICES`).
- `MetricHistory` model entirely.
- `Asset.ensure_default_metrics()` — nothing needs pre-seeding anymore; a `MetricSnapshot` is simply created whenever new data arrives.

### What's unchanged
- `CompositeIndicator` / `CompositeIndicatorValue` — the computed SHIN score is still a derived, independently-timestamped value, so it stays a separate time series keyed by `(composite, asset, timestamp)`.
- `WatchlistEntry` — no change.

## 3. Dependent code changes

### `indicators/services/calculations.py`
- `_collect_latest_raw_metric_values(asset)` shrinks to a single query:
  ```python
  latest = MetricSnapshot.objects.filter(asset=asset).order_by("-timestamp").first()
  ```
  then read `getattr(latest, field)` per `MetricSnapshot.METRIC_FIELDS` instead of assembling a dict from N `MetricHistory` rows.
- `compute_derived_metrics()` drops the leftover `derived_keys`/`"shin_indicator"` compatibility branch — that was already dead cruft tied to the old catalog's derived-metric row.

### `indicators/views.py`
- `CompositeIndicatorDetailView.get_context_data()` gets simpler: one annotated queryset (`Asset.objects.filter(is_active=True)` + a subquery per `MetricSnapshot` field, or a `Prefetch` of each asset's latest snapshot) instead of the current two-pass `defaultdict` assembly across `Metric` catalog rows.
- Table columns are driven directly by `MetricSnapshot.METRIC_FIELDS` / labels.

### `indicators/admin.py`
- Remove `MetricAdmin`, `MetricHistoryAdmin`, `MetricHistoryInline`.
- Add `MetricSnapshotAdmin` (`list_display` = asset, timestamp, source, plus all metric fields; `list_filter` = asset) and/or a `MetricSnapshotInline` on `AssetAdmin`.
- `recalculate_selected_derived` admin action moves to `AssetAdmin` (or `MetricSnapshotAdmin`), operating on the assets behind the selected rows.

### `scraper/management/commands/run_scraper.py`
- Instead of looking up/creating a `Metric` row per metric key and writing one `MetricHistory` row per key, the command collects `{field_name: value}` for all metrics found on that asset's single page load, then makes **one** call per asset:
  ```python
  MetricSnapshot.objects.create(asset=asset, timestamp=timestamp, source=source_type, **collected_values)
  ```
  This slots naturally into the asset-type-driven `SCRAPER_SOURCES` structure already in place — no further change needed there.

### Templates
- `indicator_detail.html` needs no structural change — it already just renders `rows` / `metric_labels` from context.

## 4. Data / migration approach

Per your preference, this plan only covers `models.py` and dependent code — no migration files are written here. You'll run `makemigrations` yourself once satisfied with the shape.

Practically, this restructure means dropping `indicators_metric` and `indicators_metrichistory` and creating `indicators_metricsnapshot` — there's no reasonable automatic data migration between a long/EAV shape and a wide shape, so (as you already anticipated) this is a good fit for wiping the disposable test DB and applying one fresh, squashed migration.

## 5. Open questions before implementation

1. **Naming** — keep calling the new model `Metric` (reusing the name) or introduce `MetricSnapshot` (recommended, avoids confusion with the old catalog concept)?
2. **Derived value placement** — keep the computed SHIN score in `CompositeIndicatorValue` as today (recommended — it's derived, versionable per `formula_code`, and independently timestamped), or add a `shin_indicator` column directly onto `MetricSnapshot`?
3. **Uniqueness** — is "one row per scrape run, whenever that happens" fine, or do you want a constraint like one snapshot per `(asset, date)`?

Once you confirm naming/placement/uniqueness, I'll implement the model + dependent code changes described above (still leaving migrations to you).

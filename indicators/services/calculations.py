import math
from decimal import Decimal, InvalidOperation
from django.utils import timezone

from ..models import CompositeIndicator, Metric, MetricHistory
from django.db import transaction


def safe_decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _max_decimal(threshold: str, value):
    decimal_value = safe_decimal(value)
    if decimal_value is None:
        return None
    return max(Decimal(threshold), decimal_value)


def _get_operand(formula, latest_values: dict, operand_name: str, default_key: str):
    operand_key = formula.operands.get(operand_name, default_key)
    return safe_decimal(latest_values.get(operand_key))


def _evaluate_shin_v1(formula: CompositeIndicator, latest_values: dict):
    """
    LOG10(
      MAX(0.001,
        (1 + (DY/4))
        * MAX(0.01, MargemLiquida)
        * MAX(0.01, CAGRReceitas)
        * MAX(0.01, CAGRlucros)
        / (IF(P_L<=0,1000,P_L) * IF(P_VP<=0,1000,P_VP))
      )
    )
    """
    dy = _get_operand(formula, latest_values, "dy_key", "dy")
    margem_liquida = _max_decimal(
        "0.01",
        _get_operand(formula, latest_values,
                     "margem_liquida_key", "margem_liquida"),
    )
    receitas_cagr = _max_decimal(
        "0.01",
        _get_operand(formula, latest_values,
                     "receitas_cagr_key", "receitas_cagr5"),
    )
    lucros_cagr = _max_decimal(
        "0.01",
        _get_operand(formula, latest_values,
                     "lucros_cagr_key", "lucros_cagr5"),
    )
    p_l = _get_operand(formula, latest_values, "p_l_key", "p_l")
    p_vp = _get_operand(formula, latest_values, "p_vp_key", "p_vp")

    if None in (dy, margem_liquida, receitas_cagr, lucros_cagr, p_l, p_vp):
        return None

    p_l_safe = p_l if p_l > 0 else Decimal("1000")
    p_vp_safe = p_vp if p_vp > 0 else Decimal("1000")
    denominator = p_l_safe * p_vp_safe
    if denominator <= 0:
        denominator = Decimal("0.001")

    numerator = (
        (Decimal("1") + (dy / Decimal("4")))
        * margem_liquida
        * receitas_cagr
        * lucros_cagr
    )
    base = max(Decimal("0.001"), numerator / denominator)
    return Decimal(str(math.log10(float(base))))


def evaluate_formula(formula: CompositeIndicator, latest_values: dict):
    if formula.formula_code == CompositeIndicator.FORMULA_SHIN_V1:
        return _evaluate_shin_v1(formula, latest_values)
    return None


def _collect_latest_raw_metric_values(asset=None):
    raw_metrics = Metric.objects.filter(kind="raw", is_active=True)
    if asset is not None:
        raw_metrics = raw_metrics.filter(asset=asset)
    latest_values = {}
    for m in raw_metrics:
        mh = MetricHistory.objects.filter(
            metric=m).order_by("-timestamp").first()
        if mh:
            latest_values[m.key] = mh.value
    return latest_values


def compute_derived_metrics(derived_keys=None, persist=False, source_label="calculated", asset=None):
    latest_values = _collect_latest_raw_metric_values(asset=asset)
    derived_qs = Metric.objects.filter(
        kind="derived", is_active=True).select_related("composite")
    if asset is not None:
        derived_qs = derived_qs.filter(asset=asset)
    if derived_keys:
        derived_qs = derived_qs.filter(key__in=list(derived_keys))

    results = {}
    now = timezone.now()
    create_items = []
    for dm in derived_qs:
        composite = dm.composite
        if composite is None or not composite.formula_code:
            results[dm.key] = None
            continue
        value = evaluate_formula(composite, latest_values)
        results[dm.key] = value
        if persist and value is not None:
            create_items.append(
                MetricHistory(
                    metric=dm,
                    value=value,
                    timestamp=now,
                    source=source_label,
                )
            )
    if create_items:
        with transaction.atomic():
            MetricHistory.objects.bulk_create(create_items)
    return results

import math
from decimal import Decimal, InvalidOperation

from ..models import CompositeIndicator, MetricSnapshot


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
    # TODO: the formula/operands should eventually vary by asset type (e.g. REITs use FFO
    # instead of net income/revenue CAGR). Only SHIN v1 is implemented today, for all types.
    if formula.formula_code == CompositeIndicator.FORMULA_SHIN_V1:
        return _evaluate_shin_v1(formula, latest_values)
    return None


def compute_shin_indicator(asset, persist=False):
    """Compute the SHIN indicator from an asset's latest MetricSnapshot, optionally persisting it onto that row."""
    snapshot = MetricSnapshot.objects.filter(
        asset=asset).order_by("-timestamp").first()
    if snapshot is None:
        return None

    formula = CompositeIndicator.get_or_create_shin_definition()
    latest_values = {
        field: getattr(snapshot, field) for field in MetricSnapshot.METRIC_FIELDS
    }
    value = evaluate_formula(formula, latest_values)

    if persist and value is not None:
        snapshot.shin_indicator = value
        snapshot.save(update_fields=["shin_indicator"])

    return value

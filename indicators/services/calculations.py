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


def _evaluate_shin_acao(formula: CompositeIndicator, latest_values: dict):
    """
    Evaluates for Ações / Stocks / REITs:
    =LOG10(
        MAX(0.001, 
            (1+([@[DY (%)]]/4)) 
            * MAX(0.01, [@[Marg líq (%)]]) 
            * MAX(0.01, [@[CAGR receitas 3a]]) 
            * MAX(0.01, [@[CAGR receitas 5a]]) 
            * MAX(0.01, [@[CAGR lucros 3a]]) 
            * MAX(0.01, [@[CAGR lucros 5a]]) 
            / (
                IF(
                    [@[P/L]]<=0, 1000, [@[P/L]]
                ) * IF(
                    [@[P/VP]]<=0, 1000, [@[P/VP]]
                )
            )
        )
    )
    """
    dy = _get_operand(formula, latest_values, "dy_key", "dy")
    margem_liquida = _get_operand(
        formula, latest_values, "margem_liquida_key", "margem_liquida"
    )

    receitas_cagr3 = safe_decimal(latest_values.get("receitas_cagr3"))
    receitas_cagr5 = _get_operand(
        formula, latest_values, "receitas_cagr_key", "receitas_cagr5"
    )
    lucros_cagr3 = safe_decimal(latest_values.get("lucros_cagr3"))
    lucros_cagr5 = _get_operand(
        formula, latest_values, "lucros_cagr_key", "lucros_cagr5"
    )

    # Fallback to FFO CAGR for REITs
    ffo_cagr3 = safe_decimal(latest_values.get("ffo_cagr3"))
    ffo_cagr5 = safe_decimal(latest_values.get("ffo_cagr5"))

    p_l = _get_operand(formula, latest_values, "p_l_key", "p_l")
    p_vp = _get_operand(formula, latest_values, "p_vp_key", "p_vp")

    present = [
        v
        for v in (
            dy,
            margem_liquida,
            receitas_cagr3,
            receitas_cagr5,
            lucros_cagr3,
            lucros_cagr5,
            ffo_cagr3,
            ffo_cagr5,
            p_l,
            p_vp,
        )
        if v is not None
    ]
    if not present:
        return None

    dy_factor = (
        (Decimal("1") + (dy / Decimal("4"))) if dy is not None else Decimal("1")
    )
    margem_factor = (
        max(Decimal("0.01"), margem_liquida)
        if margem_liquida is not None
        else Decimal("1")
    )

    # TODO: review the logic for using FFO CAGR as a fallback for REITs. It might be better to handle this in a more explicit way, rather than relying on the presence of FFO values.
    rec3 = receitas_cagr3 if receitas_cagr3 is not None else ffo_cagr3
    rec5 = receitas_cagr5 if receitas_cagr5 is not None else ffo_cagr5
    luc3 = lucros_cagr3 if lucros_cagr3 is not None else ffo_cagr3
    luc5 = lucros_cagr5 if lucros_cagr5 is not None else ffo_cagr5

    rec3_factor = max(
        Decimal("0.01"), rec3) if rec3 is not None else Decimal("1")
    rec5_factor = max(
        Decimal("0.01"), rec5) if rec5 is not None else Decimal("1")
    luc3_factor = max(
        Decimal("0.01"), luc3) if luc3 is not None else Decimal("1")
    luc5_factor = max(
        Decimal("0.01"), luc5) if luc5 is not None else Decimal("1")

    numerator = (
        dy_factor
        * margem_factor
        * rec3_factor
        * rec5_factor
        * luc3_factor
        * luc5_factor
    )

    p_l_factor = (
        (p_l if p_l > 0 else Decimal("1000")) if p_l is not None else Decimal("1")
    )
    p_vp_factor = (
        (p_vp if p_vp > 0 else Decimal("1000"))
        if p_vp is not None
        else Decimal("1")
    )

    denominator = p_l_factor * p_vp_factor
    if denominator <= 0:
        denominator = Decimal("0.001")

    base = max(Decimal("0.001"), numerator / denominator)
    return Decimal(str(round(math.log10(float(base)), 6)))


def _evaluate_shin_fii(formula: CompositeIndicator, latest_values: dict):
    """
    Evaluates for FIIs:
    =LOG10(
        MAX(0.001, 
            (1+([@[DY (%)]]/6)) 
            * [@[Caixa (%)]] 
            * MAX(0.01,[@[DY CAGR3]]) 
            * MAX(0.01, [@[DY CAGR5]]) 
            * MAX(0.01, [@[valor CAGR3]]) 
            * MAX(0.01, [@[valor CAGR5]]) 
            / ([@[P/VP]])
        )
    )
    """
    dy = _get_operand(formula, latest_values, "dy_key", "dy")
    caixa = safe_decimal(latest_values.get("caixa"))
    dy_cagr3 = safe_decimal(latest_values.get("dy_cagr3"))
    dy_cagr5 = safe_decimal(latest_values.get("dy_cagr5"))
    valor_cagr3 = safe_decimal(latest_values.get("valor_cagr3"))
    valor_cagr5 = safe_decimal(latest_values.get("valor_cagr5"))
    p_vp = _get_operand(formula, latest_values, "p_vp_key", "p_vp")

    present = [
        v
        for v in (dy, caixa, dy_cagr3, dy_cagr5, valor_cagr3, valor_cagr5, p_vp)
        if v is not None
    ]
    if not present:
        return None

    dy_factor = (
        (Decimal("1") + (dy / Decimal("6"))) if dy is not None else Decimal("1")
    )
    caixa_factor = caixa if caixa is not None else Decimal("1")
    dy3_factor = (
        max(Decimal("0.01"), dy_cagr3) if dy_cagr3 is not None else Decimal("1")
    )
    dy5_factor = (
        max(Decimal("0.01"), dy_cagr5) if dy_cagr5 is not None else Decimal("1")
    )
    val3_factor = (
        max(Decimal("0.01"), valor_cagr3)
        if valor_cagr3 is not None
        else Decimal("1")
    )
    val5_factor = (
        max(Decimal("0.01"), valor_cagr5)
        if valor_cagr5 is not None
        else Decimal("1")
    )

    numerator = (
        dy_factor
        * caixa_factor
        * dy3_factor
        * dy5_factor
        * val3_factor
        * val5_factor
    )

    p_vp_factor = (
        (p_vp if p_vp > 0 else Decimal("1000"))
        if p_vp is not None
        else Decimal("1")
    )
    denominator = max(Decimal("0.001"), p_vp_factor)

    base = max(Decimal("0.001"), numerator / denominator)
    return Decimal(str(round(math.log10(float(base)), 6)))


def evaluate_formula(formula: CompositeIndicator, latest_values: dict, asset_type: str = None):
    if formula.formula_code == CompositeIndicator.FORMULA_SHIN_V1:
        if asset_type == "fii":
            return _evaluate_shin_fii(formula, latest_values)
        return _evaluate_shin_acao(formula, latest_values)
    return None


def calculate_snapshot_shin_score(snapshot):
    """Calculate the SHIN score directly for a given MetricSnapshot instance."""
    if snapshot is None:
        return None

    formula = CompositeIndicator.get_or_create_shin_definition()
    latest_values = {
        field: getattr(snapshot, field) for field in MetricSnapshot.METRIC_FIELDS
    }
    asset_type = snapshot.asset.asset_type if snapshot.asset else None
    return evaluate_formula(formula, latest_values, asset_type=asset_type)


def compute_shin_indicator(asset, persist=False):
    """Compute the SHIN indicator from an asset's latest MetricSnapshot, optionally persisting it onto that row."""
    snapshot = MetricSnapshot.objects.filter(
        asset=asset).order_by("-timestamp").first()
    if snapshot is None:
        return None

    value = calculate_snapshot_shin_score(snapshot)

    if persist and value is not None:
        snapshot.shin_indicator = value
        snapshot.save(update_fields=["shin_indicator"])

    return value

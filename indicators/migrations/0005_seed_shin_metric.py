from django.db import migrations


def forwards(apps, schema_editor):
    Metric = apps.get_model("indicators", "Metric")
    MetricFormula = apps.get_model("indicators", "MetricFormula")
    CompositeIndicator = apps.get_model("indicators", "CompositeIndicator")

    # Ensure a composite indicator exists to attach the derived metric to
    composite, _ = CompositeIndicator.objects.get_or_create(
        name="SHIN Composite",
        defaults={"description": "Composite for SHIN indicator metrics"},
    )

    # Create or update the derived metric
    metric, created = Metric.objects.update_or_create(
        key="shin_indicator",
        defaults={
            "composite_id": composite.id,
            "name": "SHIN Indicator",
            "unit": "",
            "kind": "derived",
            "is_active": True,
        },
    )

    # Expression text (stored for documentation)
    expression_text = "=LOG10(MAX(0.001, (1+([@[DY (%)]]/4)) * MAX(0.01, [@[Marg líq (%)]]) * MAX(0.01, [@[CAGR receitas]]) * MAX(0.01, [@[CAGR lucros]]) / (IF([@[P/L]]<=0, 1000, [@[P/L]]) * IF([@[P/VP]]<=0, 1000, [@[P/VP]]))))"

    operands = {
        "dy_key": "dy",
        "margem_liquida_key": "margem_liquida",
        "receitas_cagr_key": "receitas_cagr5",
        "lucros_cagr_key": "lucros_cagr5",
        "p_l_key": "p_l",
        "p_vp_key": "p_vp",
    }

    # Create or update the formula
    MetricFormula.objects.update_or_create(
        metric_id=metric.id,
        defaults={
            "formula_code": "shin_v1",
            "expression": expression_text,
            "operands": operands,
            "is_active": True,
        },
    )


def backwards(apps, schema_editor):
    Metric = apps.get_model("indicators", "Metric")
    MetricFormula = apps.get_model("indicators", "MetricFormula")

    try:
        metric = Metric.objects.get(key="shin_indicator")
    except Metric.DoesNotExist:
        return

    # Remove the formula if present
    MetricFormula.objects.filter(metric_id=metric.id).delete()
    # Remove the metric
    metric.delete()


class Migration(migrations.Migration):

    dependencies = [("indicators", "0004_metric_kind_metricformula")]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

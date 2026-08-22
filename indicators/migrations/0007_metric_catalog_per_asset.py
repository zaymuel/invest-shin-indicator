from django.db import migrations


METRIC_DEFINITIONS = {
    "p_l": {"label": "P/L", "unit": "", "kind": "raw"},
    "p_vp": {"label": "P/VP", "unit": "", "kind": "raw"},
    "dy": {"label": "DY (%)", "unit": "%", "kind": "raw"},
    "margem_liquida": {"label": "Margem Líquida (%)", "unit": "%", "kind": "raw"},
    "receitas_cagr5": {"label": "CAGR Receitas 5a (%)", "unit": "%", "kind": "raw"},
    "lucros_cagr5": {"label": "CAGR Lucros 5a (%)", "unit": "%", "kind": "raw"},
    "shin_indicator": {"label": "SHIN Indicator", "unit": "log10", "kind": "derived"},
}

SHIN_EXPRESSION = "=LOG10(MAX(0.001, (1+([@[DY (%)]]/4)) * MAX(0.01, [@[Marg líq (%)]]) * MAX(0.01, [@[CAGR receitas]]) * MAX(0.01, [@[CAGR lucros]]) / (IF([@[P/L]]<=0, 1000, [@[P/L]]) * IF([@[P/VP]]<=0, 1000, [@[P/VP]]))))"
SHIN_OPERANDS = {
    "dy_key": "dy",
    "margem_liquida_key": "margem_liquida",
    "receitas_cagr_key": "receitas_cagr5",
    "lucros_cagr_key": "lucros_cagr5",
    "p_l_key": "p_l",
    "p_vp_key": "p_vp",
}


def forwards(apps, schema_editor):
    CompositeIndicator = apps.get_model("indicators", "CompositeIndicator")
    Metric = apps.get_model("indicators", "Metric")
    Asset = apps.get_model("indicators", "Asset")

    composite, _ = CompositeIndicator.objects.get_or_create(
        name="SHIN Indicator",
        defaults={
            "description": "Composite indicator formula for SHIN score.",
            "formula_code": "shin_v1",
            "expression": SHIN_EXPRESSION,
            "operands": SHIN_OPERANDS,
        },
    )

    for asset in Asset.objects.all():
        for metric_key, metric_data in METRIC_DEFINITIONS.items():
            defaults = {
                "name": metric_key,
                "unit": metric_data["unit"],
                "kind": metric_data["kind"],
                "is_active": True,
                "composite": composite if metric_data["kind"] == "derived" else None,
            }
            metric, created = Metric.objects.get_or_create(
                asset=asset,
                key=metric_key,
                defaults=defaults,
            )
            if not created:
                metric.name = metric_key
                metric.unit = metric_data["unit"]
                metric.kind = metric_data["kind"]
                metric.composite = composite if metric_data["kind"] == "derived" else None
                metric.save(update_fields=["name", "unit", "kind", "composite"])


def backwards(apps, schema_editor):
    Metric = apps.get_model("indicators", "Metric")
    Asset = apps.get_model("indicators", "Asset")

    metric_keys = list(METRIC_DEFINITIONS.keys())
    for asset in Asset.objects.all():
        Metric.objects.filter(asset=asset, key__in=metric_keys).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("indicators", "0006_alter_metric_unique_together_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="metric",
            unique_together={("asset", "key")},
        ),
        migrations.RunPython(forwards, backwards),
    ]

from unittest.mock import patch
from django.test import TestCase

from indicators.models import CompositeIndicator
from indicators.services.calculations import evaluate_formula


class IndicatorsSmokeTests(TestCase):
    def test_indicator_app_loaded(self):
        self.assertTrue(True)


class EvaluateFormulaTests(TestCase):
    @patch("indicators.services.calculations._evaluate_shin_fii")
    @patch("indicators.services.calculations._evaluate_shin_acao")
    def test_evaluate_formula_routing(self, mock_evaluate_acao, mock_evaluate_fii):
        formula = CompositeIndicator(formula_code=CompositeIndicator.FORMULA_SHIN_V1)
        latest_values = {"some": "data"}

        # Test FII routing
        mock_evaluate_fii.return_value = 1.23
        result_fii = evaluate_formula(formula, latest_values, asset_type="fii")
        self.assertEqual(result_fii, 1.23)
        mock_evaluate_fii.assert_called_once_with(formula, latest_values)
        mock_evaluate_acao.assert_not_called()

        # Reset mocks
        mock_evaluate_fii.reset_mock()
        mock_evaluate_acao.reset_mock()

        # Test Acao routing
        mock_evaluate_acao.return_value = 4.56
        result_acao = evaluate_formula(formula, latest_values, asset_type="acao")
        self.assertEqual(result_acao, 4.56)
        mock_evaluate_acao.assert_called_once_with(formula, latest_values)
        mock_evaluate_fii.assert_not_called()

        # Reset mocks
        mock_evaluate_fii.reset_mock()
        mock_evaluate_acao.reset_mock()

        # Test fallback / default routing
        mock_evaluate_acao.return_value = 7.89
        result_default = evaluate_formula(formula, latest_values)
        self.assertEqual(result_default, 7.89)
        mock_evaluate_acao.assert_called_once_with(formula, latest_values)
        mock_evaluate_fii.assert_not_called()

        # Test unknown formula code
        unknown_formula = CompositeIndicator(formula_code="unknown_code")
        result_unknown = evaluate_formula(
            unknown_formula, latest_values, asset_type="acao"
        )
        self.assertIsNone(result_unknown)

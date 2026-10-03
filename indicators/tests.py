from decimal import Decimal
from django.test import TestCase

from indicators.services.calculations import safe_decimal


class IndicatorsSmokeTests(TestCase):
    def test_indicator_app_loaded(self):
        self.assertTrue(True)


class SafeDecimalTests(TestCase):
    def test_valid_inputs(self):
        self.assertEqual(safe_decimal("1.23"), Decimal("1.23"))
        self.assertEqual(safe_decimal(1.23), Decimal("1.23"))
        self.assertEqual(safe_decimal(42), Decimal("42"))

    def test_none_input(self):
        self.assertIsNone(safe_decimal(None))

    def test_invalid_inputs(self):
        self.assertIsNone(safe_decimal("invalid"))
        self.assertIsNone(safe_decimal(""))
        self.assertIsNone(safe_decimal("1.2.3"))

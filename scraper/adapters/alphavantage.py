from decimal import Decimal
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class AlphaVantageAdapter:
    KEY_MAP = {
        'p_l': 'TrailingPE',
        'p_vp': 'PriceToBookRatio',
        'dy': 'DividendYield',
        'margem_liquida': 'ProfitMargin',
    }

    @staticmethod
    def scrape_overview(json_data):
        results = {}
        for app_key, site_key in AlphaVantageAdapter.KEY_MAP.items():
            val = json_data.get(site_key)
            if val and val != "None":
                try:
                    d_val = Decimal(val)
                    if app_key == 'dy' or app_key == 'margem_liquida':
                         d_val = d_val * Decimal('100')
                    results[app_key] = d_val
                except Exception as e:
                    logger.warning(f"Could not parse decimal from {val} for {site_key}: {e}")

        # Alpha Vantage overview also provides 52WeekHigh and 52WeekLow which we can use
        # to approximate the current year's high/low
        current_year = timezone.now().year
        high_str = json_data.get("52WeekHigh")
        low_str = json_data.get("52WeekLow")

        yearly_perf_data = {"year": current_year}
        if high_str and high_str != "None":
            try: yearly_perf_data["high"] = Decimal(high_str)
            except: pass
        if low_str and low_str != "None":
            try: yearly_perf_data["low"] = Decimal(low_str)
            except: pass

        return results, yearly_perf_data

    @staticmethod
    def scrape_earnings(json_data):
        results = []
        annual_earnings = json_data.get("annualEarnings", [])
        for earning in annual_earnings:
            date_str = earning.get("fiscalDateEnding")
            eps_str = earning.get("reportedEPS")
            if date_str and eps_str and eps_str != "None":
                try:
                    year = int(date_str.split("-")[0])
                    eps = Decimal(eps_str)
                    results.append({"year": year, "eps": eps})
                except Exception as e:
                    logger.warning(f"Could not parse year/eps from {date_str}/{eps_str}: {e}")
        return results

import re
from decimal import Decimal
import logging
import lxml.html

logger = logging.getLogger(__name__)

class YahooFinanceAdapter:
    KEY_MAP = {
        'p_l': 'trailingPE',
        'p_vp': 'priceToBook',
        'dy': 'dividendYield',
        'margem_liquida': 'profitMargins',
    }

    @staticmethod
    def scrape(html_content):
        results = {}
        tree = lxml.html.fromstring(html_content)
        scripts = tree.xpath('//script/text()')

        for script in scripts:
            for app_key, site_key in YahooFinanceAdapter.KEY_MAP.items():
                if app_key in results: continue
                if site_key in script:
                    pattern = site_key + r'\\?\"\s*:\s*\{[^\}]*?\\?\"raw\\?\"\s*:\s*([\-\d\.]+)'
                    match = re.search(pattern, script)
                    if match:
                        try:
                            val = Decimal(match.group(1))
                            if app_key == 'dy' or app_key == 'margem_liquida':
                                val = val * Decimal('100')
                            results[app_key] = val
                        except Exception as e:
                            logger.warning(f"Could not parse decimal from {match.group(1)} for {site_key}: {e}")

            if 'p_l' not in results and 'forwardPE' in script:
                 pattern = r'forwardPE\\?\"\s*:\s*\{[^\}]*?\\?\"raw\\?\"\s*:\s*([\-\d\.]+)'
                 match = re.search(pattern, script)
                 if match:
                     try:
                         val = Decimal(match.group(1))
                         results['p_l'] = val
                     except Exception as e:
                         pass
        return results

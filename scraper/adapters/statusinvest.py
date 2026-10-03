import re
from decimal import Decimal
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def parse_decimal(value_str):
    if not value_str:
        return None
    cleaned = re.sub(r'[^\d,\-]', '', value_str)
    if not cleaned:
        return None
    cleaned = cleaned.replace(',', '.')
    try:
        return Decimal(cleaned)
    except Exception as e:
        logger.warning(f"Could not parse decimal from {value_str}: {e}")
        return None

class StatusInvestAdapter:
    KEY_MAP = {
        'p_l': 'p_l',
        'p_vp': 'p_vp',
        'dy': 'dy',
        'margem_liquida': 'margemliquida',
        'receitas_cagr5': 'receitas_cagr5',
        'lucros_cagr5': 'lucros_cagr5',
        'dy_cagr3': 'dy_cagr3',
        'dy_cagr5': 'dy_cagr5',
        'valor_cagr3': 'valor_cagr3',
        'valor_cagr5': 'valor_cagr5',
        'caixa': 'caixa',
    }

    @staticmethod
    def scrape(html_content):
        soup = BeautifulSoup(html_content, 'lxml')
        results = {}
        for app_key, site_key in StatusInvestAdapter.KEY_MAP.items():
            elem = soup.find(attrs={'data-key': site_key})
            if elem:
                parent = elem.find_parent('div', class_='item') or elem.find_parent('div', class_='w-100') or elem.find_parent('div')
                if parent:
                    val_el = parent.find(class_=lambda x: x and 'value' in x)
                    if val_el:
                        parsed_val = parse_decimal(val_el.text.strip())
                        if parsed_val is not None:
                            results[app_key] = parsed_val
        return results

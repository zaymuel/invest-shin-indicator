import logging
import requests
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from indicators.models import Asset, MetricSnapshot, YearlyAssetPerformance
from scraper.adapters.statusinvest import StatusInvestAdapter
from scraper.adapters.yahoofinance import YahooFinanceAdapter
from scraper.adapters.alphavantage import AlphaVantageAdapter

logger = logging.getLogger(__name__)

def get_html_with_selenium(url):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        time.sleep(3) # Wait for JS to load
        html = driver.page_source
        driver.quit()
        return html
    except Exception as e:
        logger.error(f"Selenium failed: {e}")
        return None

class Command(BaseCommand):
    help = "Scrape latest data for active assets and save to MetricSnapshot and YearlyAssetPerformance."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting scraper...")

        assets = Asset.objects.filter(is_active=True)
        if not assets.exists():
            self.stdout.write("No active assets found to scrape.")
            return

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        for asset in assets:
            self.stdout.write(f"Scraping data for {asset.symbol} ({asset.get_asset_type_display()})")

            source_config = getattr(settings, 'SCRAPER_SOURCES', {}).get(asset.asset_type)
            if not source_config:
                self.stdout.write(self.style.WARNING(f"No source configuration found for asset type {asset.asset_type}. Skipping."))
                continue

            source_type = source_config.get("source_type")
            metrics = {}
            timestamp = timezone.now()

            try:
                if source_type == "statusinvest":
                    url = source_config["url_template"].format(symbol=asset.symbol.lower())
                    self.stdout.write(f"Fetching {url} with Selenium")
                    html_content = get_html_with_selenium(url)
                    if html_content:
                        metrics = StatusInvestAdapter.scrape(html_content)
                    else:
                        self.stdout.write(self.style.ERROR(f"Failed to fetch {url}"))

                elif source_type == "yahoo":
                    url = source_config["url_template"].format(symbol=asset.symbol.upper())
                    self.stdout.write(f"Fetching {url}")
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    metrics = YahooFinanceAdapter.scrape(response.text)

                elif source_type == "alphavantage":
                    api_key = getattr(settings, 'ALPHAVANTAGE_API_KEY', 'demo')

                    # Overview
                    overview_url = source_config["overview_url"].format(symbol=asset.symbol.upper(), api_key=api_key)
                    self.stdout.write(f"Fetching {overview_url}")
                    overview_resp = requests.get(overview_url, timeout=10).json()
                    metrics, yearly_perf_data = AlphaVantageAdapter.scrape_overview(overview_resp)

                    # Store high/low for current year
                    if 'high' in yearly_perf_data or 'low' in yearly_perf_data:
                        YearlyAssetPerformance.objects.update_or_create(
                            asset=asset,
                            year=yearly_perf_data['year'],
                            defaults={k: v for k, v in yearly_perf_data.items() if k != 'year'}
                        )

                    # Earnings
                    earnings_url = source_config["earnings_url"].format(symbol=asset.symbol.upper(), api_key=api_key)
                    self.stdout.write(f"Fetching {earnings_url}")
                    earnings_resp = requests.get(earnings_url, timeout=10).json()
                    yearly_earnings = AlphaVantageAdapter.scrape_earnings(earnings_resp)

                    for ye in yearly_earnings:
                        YearlyAssetPerformance.objects.update_or_create(
                            asset=asset,
                            year=ye['year'],
                            defaults={'eps': ye['eps']}
                        )

                else:
                    self.stdout.write(self.style.WARNING(f"Unknown source type: {source_type}"))
                    continue

                if metrics:
                    # Create or update snapshot for today
                    today = timezone.localtime(timestamp).date() if timezone.is_aware(timestamp) else timestamp.date()
                    MetricSnapshot.objects.update_or_create(
                        asset=asset,
                        date=today,
                        defaults=dict(timestamp=timestamp, source=source_type, **metrics)
                    )
                    self.stdout.write(self.style.SUCCESS(f"Successfully finished scraping {asset.symbol}."))
                else:
                    self.stdout.write(self.style.WARNING(f"No metrics found for {asset.symbol}."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error scraping {asset.symbol}: {e}"))
                logger.error(f"Error scraping {asset.symbol}", exc_info=True)

        self.stdout.write("Scraper completed.")

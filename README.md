# Shin Investment Indicator

A Django-based web application and Selenium web scraper designed to track, calculate, and manage a composite investing indicator ("Shin Indicator"). 

This project provides a platform where users can register, view the current market indicator scores, and manage a personalized watchlist of their preferred assets. Core indicator data is strictly managed by administrators, ensuring data integrity.

## Features

- **Selenium Web Scraper**: Automatically fetches financial metrics from external sources using headless browser automation.
- **Composite Indicator Engine**: Calculates a proprietary score based on various fundamental metrics.
- **User Authentication**: Secure registration and login for users to save and track their favorite stocks.
- **Personalized Watchlists**: Registered users can maintain and view personal watchlists.
- **Admin Management**: Dedicated administrative views to oversee scraped data, without allowing regular user modification.

## Technology Stack

- **Backend**: Django 5.2
- **Database**: SQLite (Local Development) / MySQL (Production)
- **Scraper**: Python, Selenium WebDriver
- **Frontend**: Standard Django Templates, HTML/CSS

## Getting Started

### Prerequisites
- Python 3.10+
- [Google Chrome](https://www.google.com/chrome/) and [ChromeDriver](https://chromedriver.chromium.org/downloads) (for Selenium)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/zaymuel/invest-shin-indicator.git
cd invest-shin-indicator
```

### 2. Create and Activate a Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Note: Ensure you have Selenium and Django installed. A `requirements.txt` will be provided as development progresses.)*

### 4. Database Setup & Configurations
The project uses `invest.local_settings` by default for local development, which utilizes a local `db.sqlite3` database to prevent exposing production credentials.

Run migrations to set up your local database:
```bash
python manage.py migrate
```

### 5. Create a Superuser (Admin)
To manage the core indicator data, you'll need an admin account:
```bash
python manage.py createsuperuser
```

### 6. Run the local server
```bash
python manage.py runserver
```
Access the application at `http://127.0.0.1:8000/` and the admin panel at `http://127.0.0.1:8000/admin/`.

## Running the Scraper
The web scraper is decoupled from the main web views and runs via a Django management command.

1. Define scraping sources per asset type in your settings (local settings example):
```python
SCRAPER_SOURCES = {
    "stock": {
        "source_type": "yahoo",
        "url_template": "https://finance.yahoo.com/quote/{symbol}",
        "metrics": {
            "p_l": "trailingPE",
            "p_vp": "priceToBook",
            "dy": "dividendYield",
            "margem_liquida": "profitMargins",
        },
    },
    "reit": {
        "source_type": "yahoo",
        "url_template": "https://finance.yahoo.com/quote/{symbol}",
        "metrics": {
            "p_l": "trailingPE",
            "p_vp": "priceToBook",
            "dy": "dividendYield",
            "margem_liquida": "profitMargins",
        },
    },
    "acao": {
        "source_type": "statusinvest",
        "url_template": "https://statusinvest.com.br/acoes/{symbol}",
        "metrics": {
            "p_l": "p_l",
            "p_vp": "p_vp",
            "dy": "dy",
            "margem_liquida": "margemliquida",
            "receitas_cagr5": "receitas_cagr5",
            "lucros_cagr5": "lucros_cagr5",
        },
    },
    "fii": {
        "source_type": "statusinvest",
        "url_template": "https://statusinvest.com.br/fundos-imobiliarios/{symbol}",
        "metrics": {
            "p_l": "p_l",
            "p_vp": "p_vp",
            "dy": "dy",
            "margem_liquida": "margemliquida",
            "receitas_cagr5": "receitas_cagr5",
            "lucros_cagr5": "lucros_cagr5",
        },
    },
}
```

Each key must match one of `Asset.ASSET_TYPE_CHOICES` (`stock`, `reit`, `acao`, `fii`). The scraper visits `url_template` once per active asset of that type (with `{symbol}` filled in from `Asset.symbol`) and extracts every metric listed in `metrics` from that single page load.

`source_type` supports:
- `selector` / `css` for regular DOM selectors (the `metrics` values are CSS selectors)
- `statusinvest` / `yahoo` / `json` for embedded JSON/data-attribute extraction (the `metrics` values are the remote JSON/data keys)


2. Run the scraper:
```bash
python manage.py run_scraper
```

## Security & Open Source Warning
- **DO NOT commit sensitive information** (Secret Keys, Database Passwords, API Keys, etc.) to this repository.
- Production configurations should exclusively be handled inside `invest/production_settings.py` or `.env` files (which are ignored by `.gitignore`).
- Ensure `invest_secret_key.txt` and `sql_invest.cnf` are referenced from a safe OS-level directory in production.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### How to configure your exact formula

The formula metadata now lives directly on the `CompositeIndicator`, not in a separate `MetricFormula` model.

To register the SHIN indicator formula in the project:

1. Create or edit a `CompositeIndicator` record:
   - name: `SHIN Indicator`
   - formula_code: `shin_v1`
   - expression: store the literal formula for documentation and auditing
   - operands: map the formula inputs to actual metric keys

2. Example formula definition:

```text
=LOG10(MAX(0.001, (1+([@[DY (%)]]/4)) * MAX(0.01, [@[Marg líq (%)]]) * MAX(0.01, [@[CAGR receitas]]) * MAX(0.01, [@[CAGR lucros]]) / (IF([@[P/L]]<=0, 1000, [@[P/L]]) * IF([@[P/VP]]<=0, 1000, [@[P/VP]]))))
```

3. Example operands JSON:

```json
{
  "dy_key": "dy",
  "margem_liquida_key": "margem_liquida",
  "receitas_cagr_key": "receitas_cagr5",
  "lucros_cagr_key": "lucros_cagr5",
  "p_l_key": "p_l",
  "p_vp_key": "p_vp"
}
```

4. How to compute:
   - `compute_shin_indicator(asset=some_asset, persist=False)` computes the score in memory for views.
   - `compute_shin_indicator(asset=some_asset, persist=True)` updates `shin_indicator` on the asset's latest existing `MetricSnapshot`; if no snapshot exists, it returns `None` without creating one.

```python
from indicators.services.calculations import compute_shin_indicator

compute_shin_indicator(asset=some_asset, persist=True)
```

Notes
- The formula logic is stored on the `CompositeIndicator`, keeping the model simpler and aligned with the fact that the formula defines the indicator itself.
- If you change metric keys referenced in `operands`, update the JSON mapping accordingly.


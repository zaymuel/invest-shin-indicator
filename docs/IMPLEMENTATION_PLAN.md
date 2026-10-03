# Implementation Plan: Invest Shin Indicator

## 1. Project Context

This is a Django 5.2 application for scraping and tracking investing indicators. The project conceptually consists of two main parts:

1. **Selenium Web Scraper**: Fetches investing indicators and financial metrics from external sources.
2. **Django Web Application**: Stores, manages, and displays these indicators, offering custom watchlist functionality for registered users.

## 2. Core Requirements & Architecture

- **Backend Stack**: Django 5.2, Python 3.13.11.
- **Database**: SQLite (local development in `invest.local_settings`), MySQL (production in `invest.production_settings`).
- **Scraper Stack**: Python + Selenium WebDriver (headless browsing).
- **User Access & Permissions**:
  - Regular users can register, log in, view indicators, and manage a personal "Watchlist".
  - Regular users CANNOT add, edit, or delete the base indicator data or scrape rules.
  - Admin users manage the core indicator data and historical metrics via the Django Admin panel.
- **Data Model Focus**:
  - The application revolves around a single MVP composite "Shin Indicator" made of various metrics.
  - **Historical Tracking**: For every metric composing the indicator, historical values (time-series data) are recorded.
  - **Timestamps**: Every metric value must have a precise recorded timestamp of when it was scraped.
- **Production Paradigm**:
  - 12-Factor App methodology heavily relies on environment variables (`DJANGO_SECRET_KEY`, `DJANGO_DB_CONF`, etc.) so no credentials are functionally hardcoded into the open-source repository.

## 3. Code Conventions & Rules

- **Django Views**: Prefer generic Class-Based Views (CBVs) over Function-Based Views (FBVs). Keep business logic decoupled from views where possible.
- **Django Templates**: Use standard Django template syntax, avoiding complex logical processing in templates.
- **Models**: Always define `__str__` methods and `verbose_name` attributes. Ensure historical time-series data relies on standard Django `DateTimeField` implementations.
- **Scraper Architecture**: Keep scraper logic completely separate from Django views/models. Place them in a dedicated module (e.g., inside a `management/commands/` path or a dedicated `scraper/` module) so they can be run via CLI or Cron without interfering with the web request cycle.
- **Security**: Never commit real API keys, secret keys, or passwords. Follow the strict placeholder and local-only standards currently configured.

## 4. indicators PER CLASS

FIIs e ações:
- DY (%)
- P/L 
- P/VP 
- Marg líq (%) 
- CAGR receitas 3 e 5 anos
- CAGR lucros 3 e 5 anos

stocks:
- DY (%)
- PE Ratio (TTM) / Trailing P/E (P/L)
- P/VP (Price / Book) (P/VP)
- Profit Margin (%) (Marg líq)

reits:
- DY (%)
- PE Ratio (TTM) / Trailing P/E (P/L)
- P/VP (Price / Book) (P/VP)
- Profit Margin (%) (Marg líq)
- FFO Growth

---

## 4. Step-by-Step Implementation Strategy

### Phase 1: Core App setup & Authentication

- Initialize the primary Django application (e.g., `core` or `users`).
- Implement a Custom User Model (extending `AbstractUser`) and update `AUTH_USER_MODEL` in settings to establish the foundation for the "Watchlist" capability.
- Configure registration/login templating and URL routing.

### Phase 2: Domain Data Modeling (Indicators & Metrics)

- Create models for the main `CompositeIndicator`.
- Create a `MetricSnapshot` model to store all metrics captured for an asset in a single wide row per date, accompanied by a precise `timestamp = models.DateTimeField(default=timezone.now)`.
- Establish the `Watchlist` model linking the `CustomUser` to their preferred assets or indicators.
- Register all new models in the Django Admin for admin-only management.

### Phase 3: Selenium Scraper Development

- Create a dedicated `scraper` module.
- Set up a headless Selenium WebDriver script capable of visiting the target data sources.
- Implement robust exception handling, implicit/explicit wait structures, and user-agent spoofing if necessary.
- Build logic to parse the DOM, extract the metric values, and use Django's ORM to update or create the `MetricSnapshot` row for each `(asset, date)`.

### Phase 4: Business Logic & Django Views

- Implement `ListView` and `DetailView` for the web app to display the latest composite indicator and its historical trends.
- Implement views specifically for the User Watchlist (Add to watchlist, Remove from watchlist, List user's watchlist).
- Implement necessary permission checks (e.g., `LoginRequiredMixin`) to restrict watchlist access to authenticated users.

### Phase 5: UI & Templates

- Develop base HTML layer with a navigation bar (allowing login/logout and admin access for superusers).
- Render tables or simple charts for the historical indicator data.
- Ensure the user interface accurately represents the read-only nature of the indicators for standard users.

### Phase 6: Automation & Final Polish

- Convert the scraper script into a custom Django Management Command (e.g., `python manage.py run_scraper`).
- Document how to schedule the scraper on a production server (e.g., using `crontab`).
- Finalize testing, ensure the GitHub Action CI passes for all test cases.
- Apply finishing touches to the `README.md`.

---

## 6. Warnings

Please take note of the following critical warnings regarding the architecture and implementation of this project:

- The most important rule is that you should never run Selenium directly inside your Django views. PythonAnywhere explicitly warns against launching Selenium during a web request cycle. Selenium and headless browsers take a significant amount of time to initialize and scrape data. If your button click triggers Selenium directly, it will block your web worker. This causes your website to freeze for you and any other visitors, ultimately resulting in a request timeout error.  Instead, the proper architecture requires a background task system. When you click the button on your website, your Django view should immediately save a task or a flag to your database and return a quick response to the user, perhaps telling them the scrape has started.Separately, you will need a background worker script running independently of your web app. This script constantly checks the database for new tasks. When it finds one, it initializes the Selenium webdriver, scrapes the target website, updates the indexes in your database, and marks the task as complete.

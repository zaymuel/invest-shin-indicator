# Project Context
This is a Django 5.2 application for scraping and tracking investing indicators. The project conceptually consists of two main parts:
1. A Selenium web scraper to fetch investing indicators from external sources.
2. A Django web application to store, manage, and display these indicators.

# Core Requirements & Architecture
- **Backend Engine:** Django 5.2, using SQLite for local development (`invest.local_settings`) and MySQL for production (`invest.production_settings`).
- **Scraper Engine:** Python + Selenium. Use headless browsing, precise explicit waits, and handle exceptions cleanly.
- **User Access & Permissions:**
  - The app includes user authentication (registration and login) for all users.
  - Regular users can view indicators and manage a personal **watchlist** of their preferred stocks/assets.
  - Regular users CANNOT add, edit, or delete the base indicator data.
  - Only admins can manage (create/update/delete) core indicator data via the Django Admin panel.
- **Data Model Focus:** Initially, the app centers around a single composite indicator made up of various financial metrics.
  - **Historical Tracking:** For any metric composing the indicator, models must record historical values (time-series data) to track evolution over time.
  - **Timestamps:** Every recorded metric value must include a timestamp indicating exactly when it was scraped.

# Code Conventions & Rules
- **Django Views:** Prefer Class-Based Views (CBV) over Function-Based Views (FBV). Let generic CBVs do the heavy lifting for list and detail views.
- **Django Templates:** Use standard Django template syntax. Keep business logic out of templates.
- **Models:** Always define `__str__` methods. Ensure verbose_names are set for clarity.
- **Architecture:** Keep scraper logic decoupled from Django views. Place scrapers in a dedicated module/app (e.g., `scraper/`), triggered via Django management commands or background tasks.
- **Security & Config:** 
  - Never hardcode sensitive credentials. Follow `invest.local_settings` overrides as configured.
  - THIS IS A PUBLIC OPEN SOURCE REPOSITORY. ABSOLUTELY NEVER generate, suggest, or hardcode real passwords, real API keys, or real secret keys. Always use environment variables, placeholder text (e.g., `<YOUR_API_KEY>`), or local ignored files.

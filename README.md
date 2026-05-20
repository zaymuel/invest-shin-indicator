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
To initiate a scraping task and update the database with fresh metrics, run:
```bash
python manage.py run_scraper
```
*(Note: This command will be fully available once Phase 4 of project implementation is complete.)*

## Security & Open Source Warning
- **DO NOT commit sensitive information** (Secret Keys, Database Passwords, API Keys, etc.) to this repository.
- Production configurations should exclusively be handled inside `invest/production_settings.py` or `.env` files (which are ignored by `.gitignore`).
- Ensure `invest_secret_key.txt` and `sql_invest.cnf` are referenced from a safe OS-level directory in production.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

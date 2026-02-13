#!/usr/bin/env bash
# Render build script — installs core deps first, then optional native packages
set -e

echo "=== Installing core Python packages ==="
pip install --upgrade pip

# Install all core packages (pure Python — always works)
pip install \
  Flask==3.1.2 \
  flask-cors==6.0.2 \
  gunicorn==25.0.3 \
  requests==2.32.5 \
  beautifulsoup4==4.14.3 \
  fake-useragent==2.2.0 \
  lxml==6.0.2 \
  pandas==2.3.3 \
  openpyxl==3.1.5 \
  APScheduler==3.11.2 \
  python-dateutil==2.9.0.post0 \
  cloudscraper==1.2.71 \
  html5lib==1.1 \
  markdownify==0.13.1 \
  regex==2024.11.6 \
  numpy==1.26.3 \
  Jinja2==3.1.6 \
  urllib3==2.6.3 \
  certifi==2026.1.4 \
  pytz==2025.2 \
  tzdata==2025.3 \
  Werkzeug==3.1.5 \
  typing_extensions==4.15.0

echo "=== Installing optional native packages (may fail on some platforms) ==="

# curl_cffi — needed for anti-bot bypass, has native C deps
pip install curl_cffi==0.14.0 || echo "⚠️  curl_cffi failed to install (optional — scrapers will use requests fallback)"

# python-jobspy — depends on curl_cffi and other native libs
pip install python-jobspy==1.1.82 || echo "⚠️  python-jobspy failed to install (optional — JobSpy scrapers disabled)"

# tls-client — native TLS fingerprinting (not used in current scrapers)
pip install tls-client==1.0.1 || echo "⚠️  tls-client failed to install (optional)"

# selenium + chromedriver — NOT available on Render (no browser)
# pip install selenium undetected-chromedriver  # Skipped — no browser on Render

echo "=== Build complete ==="

# 🚀 Quick Start Guide

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

If you encounter any issues, install packages individually:

```bash
pip install Flask Flask-CORS requests beautifulsoup4 pandas openpyxl fake-useragent cloudscraper
```

### 2. (Optional) Install Browser Automation Tools

For sites that require JavaScript rendering (like LinkedIn):

```bash
# Install Playwright
pip install playwright
playwright install chromium

# OR Install Selenium
pip install selenium
# Download ChromeDriver from https://chromedriver.chromium.org/
```

### 3. Configuration

Copy `.env.example` to `.env` and add your API keys (optional):

```bash
cp .env.example .env
```

Edit `config.json` to customize:
- Job sites to scrape
- Default search parameters
- Scraping delays and timeouts

## Running the Application

### Start the server:

```bash
python app.py
```

The application will start at: **http://localhost:5000**

## Usage

1. **Open your browser** and navigate to http://localhost:5000

2. **Enter search criteria:**
   - Job Title (e.g., "Software Engineer")
   - Location (e.g., "United States")
   - Check "Remote Only" if you want remote jobs

3. **Select job sites** to scrape (Indeed, RemoteOK, WeWorkRemotely, etc.)

4. **Click "Start Scraping"** and watch jobs appear in real-time!

5. **Export results:**
   - Click "Export CSV" or "Export Excel" to download your job list

## Features

✅ **Real-time updates** - Jobs appear as they're found  
✅ **Multiple sources** - Scrapes 10+ job sites  
✅ **Smart filtering** - Filter by remote, location, salary  
✅ **Export options** - Download as CSV or Excel  
✅ **Live search** - Search through results instantly  

## Troubleshooting

### Issue: "Module not found" errors
**Solution:** Install missing packages:
```bash
pip install [package-name]
```

### Issue: No jobs found from Indeed/Glassdoor
**Solution:** These sites have anti-scraping measures. Try:
- Using a VPN or proxy
- Increasing delays in config.json
- Using official APIs (Indeed has a free API)

### Issue: Browser automation needed
**Solution:** Some sites require headless browsers:
```bash
pip install playwright
playwright install
```

## Adding New Job Sites

To add a new job site:

1. Create a new scraper in `scrapers/` folder:

```python
from .base_scraper import BaseScraper

class NewSiteScraper(BaseScraper):
    def scrape(self, job_title, location, remote=False):
        # Your scraping logic
        jobs = []
        # ... scrape jobs ...
        return jobs
```

2. Register it in `app.py`:

```python
from scrapers.newsite_scraper import NewSiteScraper

SCRAPERS = {
    'newsite': NewSiteScraper,
    # ... existing scrapers
}
```

3. Add it to `config.json`:

```json
{
  "name": "NewSite",
  "enabled": true,
  "url": "https://newsite.com"
}
```

## API Optional (for better results)

Some sites offer official APIs:

### Indeed API
- Sign up at: https://www.indeed.com/publisher
- Free tier: 100 API calls/day
- Add your Publisher ID to `.env`

### Adzuna API
- Sign up at: https://developer.adzuna.com/
- Free tier: 500 calls/month
- Add app ID and API key to `.env`

## Best Practices

1. **Respect robots.txt** - Always check site's scraping policy
2. **Use delays** - Don't hammer servers (2-5 seconds between requests)
3. **Use APIs when available** - More reliable and legal
4. **Rotate user agents** - Avoid detection (handled automatically)
5. **Handle errors gracefully** - Sites change, scrapers break

## Legal Notice

⚠️ **Important:** Web scraping may violate Terms of Service of some websites. This tool is for **educational purposes** only. Always:

- Check the website's Terms of Service
- Respect robots.txt files
- Use official APIs when available
- Don't overload servers with requests
- Consider the ethical implications

## Production Deployment

To deploy this in production:

1. **Use a production WSGI server:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **Add authentication** to protect your instance

3. **Set up a database** (PostgreSQL, MongoDB) instead of in-memory storage

4. **Use task queues** (Celery + Redis) for better scalability

5. **Deploy to cloud:**
   - Heroku: Easy deployment
   - AWS EC2: More control
   - DigitalOcean: Simple VPS
   - Railway.app: Modern deployment

## Support

Having issues? Check:
- Python version (3.8+ required)
- All dependencies installed
- Port 5000 is available
- Firewall not blocking requests

---

**Happy Job Hunting! 🎯**

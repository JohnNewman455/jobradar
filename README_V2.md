# 🎯 JobRadar v2 - Professional Job Scraping Tool

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.0-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-Production-brightgreen.svg" alt="Status">
</p>

## 🚀 What's New in v2

**JobRadar v2** is a complete redesign with a modern, professional interface inspired by industry-leading job aggregators. Now with **16+ job sites** and real-time scraping!

### ✨ Key Features

- 🎨 **Modern Dark/Light UI** - Toggle between themes
- 🔄 **Real-Time Updates** - Watch jobs appear live as they're found
- 🌐 **16+ Job Sites** - Indeed, Google Jobs, LinkedIn*, Glassdoor, Dice, ZipRecruiter, and more
- 🇨🇦 **Canada-Focused** - Special support for Canadian job sites (Talent.com, Jooble CA, WorkPolice)
- ⚙️ **Toggle Controls** - Easy source management with checkboxes
- ➕ **Custom Sources** - Add your own job sites
- 📊 **Live Progress** - See scraping progress for each site
- 📥 **Export Options** - Download as CSV, Excel, or JSON
- 🔍 **Advanced Filtering** - Search, sort, and filter results
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

## 🎯 Supported Job Sites

### Global Sites
- ✅ **Indeed** - #1 job site worldwide
- ✅ **Google Jobs** - Google's job search aggregator
- ✅ **Dice.com** - Tech jobs (has API!)
- ✅ **Glassdoor** - Jobs + company reviews
- ✅ **ZipRecruiter** - US & Canada jobs
- 🔒 **LinkedIn** - Requires authentication

### Canada-Specific
- ✅ **Talent.com** - Canadian job aggregator
- ✅ **Jooble Canada** - Multi-source aggregator
- ✅ **SimplyHired CA** - Canadian jobs
- ✅ **Workopolis** - Canadian career site

### Remote-Focused
- ✅ **RemoteOK** - Remote jobs (has API!)
- ✅ **WeWorkRemotely** - Curated remote jobs
- ✅ **RemoteRocketship** - Remote developer jobs
- ✅ **Remote.co** - Remote positions
- ✅ **Wellfound** - Startup jobs (formerly AngelList)

### ServiceNow-Specific
- ✅ **ServiceNow Careers** - Official company jobs
- 🔨 **NowTribe** - ServiceNow community jobs (coming soon)
- 🔨 **ServiceNow Community** - User-posted roles (coming soon)

*Some sites require API keys or authentication

## ⚡ Quick Start (60 seconds!)

### Option 1: Automated Setup (Recommended)

**macOS/Linux:**
```bash
cd "/Users/user/Desktop/JOB tool"
./quickstart.sh
```

**Windows:**
```batch
cd "C:\Users\...\JOB tool"
quickstart.bat
```

That's it! The script will:
1. ✅ Create virtual environment
2. ✅ Install dependencies
3. ✅ Start the server
4. ✅ Open at http://localhost:5000

### Option 2: Manual Setup

```bash
# Install dependencies
pip install Flask Flask-CORS requests beautifulsoup4 pandas openpyxl fake-useragent cloudscraper

# Run the application
python app.py
```

## 📖 How to Use

### 1. Launch the Dashboard
Open http://localhost:5000 in your browser

### 2. Configure Search
- **Job Title**: e.g., "ServiceNow Developer"
- **Location**: e.g., "Canada" or "United States"
- **Remote Only**: Toggle on for remote jobs only

### 3. Select Sources
- ✅ Check boxes to select which sites to scrape
- Click "Select All" or "Deselect All" for quick selection
- Add custom sources with the "+ Add Source" button

### 4. Start Scraping
- Click **"Start Scan"**
- Watch jobs appear in real-time!
- Progress bars show status for each site
- Jobs display immediately as they're found

### 5. Review & Export
- Search through results
- Sort by date, salary, or company
- Export to CSV, Excel, or JSON

## 🎨 UI Features

### Modern Dashboard
- **Dark/Light Mode** - Toggle in sidebar
- **Sidebar Navigation** - Easy access to features
- **Stats Bar** - Live metrics (jobs found, sources, remote count)
- **Dual Panel Layout** - Sources on left, results on right

### Source Management
- **Toggle Switches** - Easy on/off for each source
- **Status Indicators** - See which sources are scanning
- **Progress Bars** - Real-time scraping progress
- **Custom Sources** - Add your own job sites

### Job Cards
- **Company & Title** - Clear job information
- **Metadata** - Location, salary, job type, posted date
- **Remote Badge** - Highlighted for remote positions
- **Source Badge** - Color-coded by site
- **Apply Button** - Direct link to job posting

## 📊 Export Formats

### CSV Export
- Optimized for Excel and Google Sheets
- All job fields included
- Compatible with most data tools

### Excel Export
- Formatted spreadsheet with auto-column sizing
- Professional layout
- Ready for analysis

### JSON Export
- Structured data for developers
- Perfect for integrations
- Full job details preserved

## 🔧 Configuration

### Adding Custom Job Sites

1. Click "+ Add Source" in the dashboard
2. Enter name and URL
3. Source appears in your list
4. Select and start scraping!

### API Keys (Optional)

Some sites work better with official APIs:

**Indeed API:**
- Sign up: https://www.indeed.com/publisher
- Add to `.env`: `INDEED_PUBLISHER_ID=your_key`

**Dice API:**
- Free tier available
- Automatic usage if configured

### Advanced Configuration

Edit `config.json`:
```json
{
  "scraping": {
    "delay_between_requests": 2,  // Seconds between requests
    "timeout": 30,                 // Request timeout
    "max_retries": 3,             // Retry failed requests
    "use_proxy": false            // Enable proxy support
  }
}
```

## 🛠️ Extending the Tool

### Adding a New Job Site Scraper

1. Create `scrapers/yoursite_scraper.py`:

```python
from .base_scraper import BaseScraper

class YourSiteScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://yoursite.com"
    
    def scrape(self, job_title, location, remote=False):
        jobs = []
        # Your scraping logic here
        return jobs
```

2. Register in `app.py`:

```python
from scrapers.yoursite_scraper import YourSiteScraper

SCRAPERS = {
    'yoursite': YourSiteScraper,
    # ... existing scrapers
}
```

3. Add to source list in `app.py` under `get_available_sites()`

## 📈 Performance

- **Speed**: Scrapes 16+ sites in parallel
- **Results**: 50+ jobs per site (configurable)
- **Real-time**: Jobs appear within seconds
- **Efficient**: Smart caching and duplicate detection

## ⚠️ Legal & Ethical Usage

### Important Notes

✅ **Allowed:**
- Personal job searching 
- Educational purposes
- Using official HTTP APIs
- Respecting robots.txt
- Reasonable request rates

❌ **Not Allowed:**
- Commercial resale of data
- Violating Terms of Service
- Overloading servers
- Ignoring rate limits

### Recommendations

1. **Use Official APIs** when available (Indeed, Dice, RemoteOK)
2. **Respect delays** - Don't hammer servers
3. **Check robots.txt** for each site
4. **Read Terms of Service** before scraping
5. **Consider this tool educational** - not for commercial use

## 🐛 Troubleshooting

### No jobs found from certain sites?
→ Some sites (LinkedIn, Glassdoor) have anti-scraping measures. Use their official APIs or set up browser automation.

### Import errors?
→ Run: `pip install -r requirements.txt`

### Port 5000 already in use?
→ Change port in `app.py`: `app.run(port=5001)`

### Jobs appear slowly?
→ Some sites are slower than others. Be patient or adjust timeout settings.

### Scraper breaks after site update?
→ Websites change their HTML frequently. Check GitHub for updates or fix the specific scraper.

## 🚀 Future Enhancements

Planned features:
- [ ] Email alerts for new jobs
- [ ] Save custom searches
- [ ] Job bookmarking system
- [ ] Salary trend analysis
- [ ] Company research integration
- [ ] Browser extension
- [ ] Mobile app
- [ ] Machine learning job matching

## 💡 Tips & Tricks

1. **Best Results**: Use specific job titles ("ServiceNow Developer" vs "Developer")
2. **Location**: Be specific ("Toronto, Canada" vs "Canada")
3. **Remote Filter**: Toggle on to focus on remote opportunities
4. **Multiple Searches**: Export results, then search again with different criteria
5. **Regular Updates**: Run daily to catch new postings
6. **Combine Sources**: Select both general (Indeed) and niche (RemoteOK) sites

## 📝 Project Structure

```
JOB tool/
├── app.py                          # Main Flask application
├── scrapers/                       # Job site scrapers
│   ├── base_scraper.py            # Base class
│   ├── indeed_scraper.py          # Indeed
│   ├── google_jobs_scraper.py     # Google Jobs
│   ├── dice_scraper.py            # Dice.com
│   ├── talent_com_scraper.py      # Talent.com
│   ├── jooble_scraper.py          # Jooble
│   ├── servicenow_careers_scraper.py
│   ├── wellfound_scraper.py
│   ├── simplyhired_ca_scraper.py
│   └── ... (more scrapers)
├── templates/                      # HTML templates
│   └── index_v2.html              # Main dashboard
├── static/                         # CSS & JavaScript
│   ├── style_v2.css               # Styles
│   └── app_v2.js                  # Frontend logic
├── utils/                          # Utilities
│   ├── job_storage.py             # Job storage
│   └── export_utils.py            # Export functions
├── config.json                     # Configuration
├── requirements.txt                # Dependencies
├── quickstart.sh                   # Quick setup (Mac/Linux)
└── quickstart.bat                  # Quick setup (Windows)
```

## 🤝 Contributing

Want to add a new job site or improve the tool?

1. Fork the repository
2. Create your feature branch
3. Add your scraper or enhancement
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - Feel free to use for personal projects!

## 🙋 Support

- 📖 Read: `QUICKSTART.md` for detailed setup
- 📊 Check: `PROJECT_OVERVIEW.md` for architecture
- 🐛 Issues: Report bugs via GitHub issues

---

<p align="center">
  <strong>Made with ❤️ for job seekers everywhere</strong><br>
  <em>Happy Job Hunting! 🎯</em>
</p>

## 🎉 Credits

Powered by:
- **Flask** - Web framework
- **BeautifulSoup** - HTML parsing
- **Pandas** - Data processing
- **Font Awesome** - Icons
- **Python** - Everything else!

---

**Version**: 2.0  
**Last Updated**: February 2026  
**Status**: ✅ Production Ready

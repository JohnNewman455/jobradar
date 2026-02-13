# Job Scraper Tool 🔍

A real-time job scraping tool that searches multiple job sites and displays results in a live dashboard.

## Features

✅ **Real-time scraping** - Click start and watch jobs appear live
✅ **Multiple job sites** - Indeed, RemoteOK, WeWorkRemotely, Glassdoor, and more
✅ **Custom filters** - Search by role, location, salary, remote options
✅ **Live updates** - Results appear as they're found
✅ **Export options** - Download results as CSV or Excel
✅ **Extensible** - Easy to add new job sites

## Supported Job Sites

- Indeed
- RemoteOK
- WeWorkRemotely  
- Glassdoor
- AngelList
- FlexJobs
- Remote.co
- Adzuna
- SimplyHired
- ZipRecruiter

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Then open http://localhost:5000 in your browser

## Usage

1. Enter your search criteria (job title, location, keywords)
2. Select which job sites to search
3. Click "Start Scraping"
4. Watch results appear in real-time
5. Export results when done

## Configuration

Edit `config.json` to:
- Add new job sites
- Configure scraping intervals
- Set API keys (for Indeed, Adzuna)

## Legal Notice

This tool is for educational purposes. Always respect websites' Terms of Service and robots.txt files. Consider using official APIs where available.

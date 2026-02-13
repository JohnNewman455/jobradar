# JobRadar v2 - Quick Start Guide

## 🚀 Starting the App

```bash
cd "/Users/user/Desktop/JOB tool"
source venv312/bin/activate
python3 app.py
```

Then open: **http://localhost:5001**

## ✨ New Features Guide

### 1. **Posted Date Display**
- Each job now shows: "2 days ago", "1 week ago", "Today", etc.
- Look in the job card metadata (clock icon ⏰)

### 2. **Advanced Sorting** (Top right dropdown)
- **Most Recent** - Shows newest jobs first
- **Highest Salary** - Best paying jobs first  
- **Remote First** - Remote → Hybrid → On-site
- **By Site** - Groups by source alphabetically
- **Company A-Z** - Alphabetical by company

### 3. **Collapsible Sources**
- Click **"Show Sources"** button to expand source list
- Reorder sources by dragging (scrapes in that order)
- Click **"Hide Sources"** to collapse and save space

### 4. **Work Type Display**
Every job shows one of:
- 🏠 **Remote** - Work from anywhere
- 🔄 **Hybrid** - Mix of remote and office
- 🏢 **On-site** - Office-based only

### 5. **Search Filter**
- Type in the search box (top right)
- Filters: titles, companies, locations, descriptions
- Works instantly as you type
- Count updates automatically

### 6. **Collapsible Progress Bar**
- Click the progress header to collapse/expand
- Saves screen space during scraping
- Still see status without hiding jobs

## 🎯 How to Use

### Basic Search
1. Enter job title (e.g., "ServiceNow Developer")
2. Enter location (e.g., "Canada")
3. Toggle "Remote Only" checkbox if needed
4. Click **"Show Sources"** to select which sites to scrape
5. Click **"Start Scan"**

### Advanced Search
1. **Reorder sources**: Drag sources to preferred order
2. **Select specific sources**: Uncheck ones you don't want
3. **Use filters during scraping**: Search and sort work in real-time

### Best Practices
- ✅ Select 5-10 sources for faster results
- ✅ Use "Remote First" sort to find remote jobs quickly
- ✅ Use "Highest Salary" to find best paying opportunities
- ✅ Search by keywords to narrow results
- ✅ Collapse progress bar once scraping starts to see jobs better

## 📊 Understanding Results

### Job Card Layout
```
┌─────────────────────────────────────┐
│ Title                    [SOURCE]   │
│ Company Name                        │
├─────────────────────────────────────┤
│ 📍 Location  ⏰ 2 days ago          │
│ 💼 Full-time  🏠 Remote             │
├─────────────────────────────────────┤
│ Job description preview...          │
├─────────────────────────────────────┤
│ 💰 $100k-$150k/year   [Apply Now]  │
└─────────────────────────────────────┘
```

### Stats Bar Shows
- **Jobs Found** - Total results
- **Sources** - Number of sites scanned
- **Remote** - Count of remote jobs
- **Scan Time** - How long it took

## 🔍 Working Sources (Best Results)

### Tier 1: Always Working ✅
- **Indeed** - JobSpy with anti-bot bypass
- **LinkedIn** - JobSpy with anti-bot bypass
- **Glassdoor** - JobSpy with anti-bot bypass
- **RemoteOK** - Official API
- **WeWorkRemotely** - Direct scraping
- **ServiceNow Careers** - Official career site
- **Nelson Frank** - #1 ServiceNow recruitment firm

### Tier 2: May Be Limited ⚠️
- ZipRecruiter, Google Jobs, Dice, etc.
- Use these as supplements

## 💡 Pro Tips

1. **For Best Results**: Select all Tier 1 sources
2. **For Speed**: Select 3-5 sources only
3. **For Remote Jobs**: Enable "Remote Only" + "Remote First" sort
4. **For High Salary**: Use "Highest Salary" sort
5. **Narrow Results**: Use search after scraping completes
6. **Export Data**: Click "Export" → Choose CSV/Excel/JSON

## 🐛 Troubleshooting

### No jobs found?
- ✅ Try broader job title (e.g., "Developer" instead of "Senior DevOps Engineer")
- ✅ Try different location or leave blank
- ✅ Disable "Remote Only" filter
- ✅ Select more sources

### Scraping stuck?
- ✅ Click "Stop" and restart
- ✅ Some sites may be slow (timeout after 30s)
- ✅ Check console log (bottom right icon)

### Jobs showing "N/A"?
- ✅ Some sites don't provide all fields
- ✅ Work type always shows (Remote/Hybrid/On-site)
- ✅ Posted date always shows (even if "Recently")

## 📥 Exporting Results

1. Click **"Export"** button
2. Choose format:
   - **CSV** - Excel/Sheets compatible
   - **Excel** - Formatted spreadsheet
   - **JSON** - For developers
3. File downloads automatically

## 🎨 Theme Toggle

Click the moon/sun icon in sidebar to switch between:
- 🌙 **Dark Mode** (default)
- ☀️ **Light Mode**

Theme preference is saved automatically.

## 📱 Console Log

Click terminal icon (bottom right) to:
- See real-time scraping progress
- Debug issues
- Copy logs
- Clear console

---

**Enjoy your enhanced job search! 🎉**

All 8 requested features have been implemented and tested.

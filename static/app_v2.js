// JobRadar v3 - Enhanced JavaScript

let eventSource = null;
let isScrapingActive = false;
let selectedSources = new Set();
let allSources = [];
let startTime = null;
let timerInterval = null;

// Pagination state
let currentPage = 1;
let jobsPerPage = 50;

// Dedup tracking
let dedupCount = 0;

// Applied Jobs tracking (persists in localStorage)
let appliedJobs = new Set();
try {
    const stored = JSON.parse(localStorage.getItem('appliedJobs') || '[]');
    appliedJobs = new Set(stored);
} catch(e) { appliedJobs = new Set(); }

function saveAppliedJobs() {
    localStorage.setItem('appliedJobs', JSON.stringify([...appliedJobs]));
    updateAppliedCount();
}

function markApplied(url) {
    appliedJobs.add(url);
    saveAppliedJobs();
    // Update all cards with this URL
    document.querySelectorAll('.job-card').forEach(card => {
        if (card.dataset.url === url) {
            card.classList.add('applied');
            const btn = card.querySelector('.apply-track-btn');
            if (btn) {
                btn.innerHTML = '<i class="fas fa-check-circle"></i> Applied';
                btn.classList.add('applied');
                btn.onclick = function(e) { e.stopPropagation(); toggleApplied(url); };
            }
        }
    });
    showNotification('Marked as Applied!', 'success');
}

function unmarkApplied(url) {
    appliedJobs.delete(url);
    saveAppliedJobs();
    document.querySelectorAll('.job-card').forEach(card => {
        if (card.dataset.url === url) {
            card.classList.remove('applied');
            const btn = card.querySelector('.apply-track-btn');
            if (btn) {
                btn.innerHTML = '<i class="fas fa-paper-plane"></i> Mark Applied';
                btn.classList.remove('applied');
                btn.onclick = function(e) { e.stopPropagation(); toggleApplied(url); };
            }
        }
    });
    showNotification('Unmarked as Applied', 'info');
}

function toggleApplied(url) {
    if (appliedJobs.has(url)) {
        unmarkApplied(url);
    } else {
        markApplied(url);
    }
}

function updateAppliedCount() {
    const el = document.getElementById('appliedCount');
    if (el) el.textContent = appliedJobs.size;
}

function filterApplied() {
    const filter = document.getElementById('filterByApplied');
    if (filter) {
        filter.value = 'applied';
        filterJobs();
    }
    // Switch to search tab
    switchTab('search');
}

// DOM Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const exportBtn = document.getElementById('exportBtn');
const themeToggle = document.getElementById('themeToggle');
const sourcesList = document.getElementById('sourcesList');
const resultsList = document.getElementById('resultsList');
const readyState = document.getElementById('readyState');
const progressSection = document.getElementById('progressSection');
const addSourceBtn = document.getElementById('addSourceBtn');
const addSourceModal = document.getElementById('addSourceModal');
const saveSourceBtn = document.getElementById('saveSourceBtn');
const cancelSourceBtn = document.getElementById('cancelSourceBtn');
const selectAllBtn = document.getElementById('selectAllBtn');
const deselectAllBtn = document.getElementById('deselectAllBtn');

// State for collapsible sections
let sourcesExpanded = false;
let progressExpanded = true;

// Saved jobs storage
let savedJobs = [];
let allScrapedJobs = []; // Keep track of all jobs for analytics

// Load saved data from localStorage
try {
    savedJobs = JSON.parse(localStorage.getItem('savedJobs') || '[]');
    const settings = JSON.parse(localStorage.getItem('appSettings') || '{}');
    applySettings(settings);
} catch (e) {
    console.error('Error loading saved data:', e);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadSources();
    initEventListeners();
    updateSavedJobsDisplay();
    initTabNavigation();
    updateAppliedCount();
});

// Event Listeners
function initEventListeners() {
    startBtn.addEventListener('click', startScraping);
    stopBtn.addEventListener('click', stopScraping);
    exportBtn.addEventListener('click', () => showModal('exportModal'));
    themeToggle.addEventListener('click', toggleTheme);
    if (addSourceBtn) addSourceBtn.addEventListener('click', () => toggleAddSourceForm(true));
    if (saveSourceBtn) saveSourceBtn.addEventListener('click', saveCustomSource);
    if (cancelSourceBtn) cancelSourceBtn.addEventListener('click', () => toggleAddSourceForm(false));
    selectAllBtn.addEventListener('click', selectAllSources);
    deselectAllBtn.addEventListener('click', deselectAllSources);
    
    // Export buttons
    document.getElementById('exportCSV').addEventListener('click', () => exportJobs('csv'));
    document.getElementById('exportExcel').addEventListener('click', () => exportJobs('excel'));
    document.getElementById('exportJSON').addEventListener('click', () => exportJobs('json'));
    document.getElementById('closeExportModal').addEventListener('click', () => hideModal('exportModal'));
    
    // Search and Sort
    document.getElementById('searchJobs').addEventListener('input', filterJobs);
    document.getElementById('sortBy').addEventListener('change', sortJobs);
    
    // Source filter
    const filterBySource = document.getElementById('filterBySource');
    if (filterBySource) filterBySource.addEventListener('change', filterJobs);
    
    // Score filter
    const filterByScore = document.getElementById('filterByScore');
    if (filterByScore) filterByScore.addEventListener('change', filterJobs);
    
    // Applied filter
    const filterByApplied = document.getElementById('filterByApplied');
    if (filterByApplied) filterByApplied.addEventListener('change', filterJobs);
    
    // Work type filter
    const filterByWorkType = document.getElementById('filterByWorkType');
    if (filterByWorkType) filterByWorkType.addEventListener('change', filterJobs);
}

// Load Sources from API
async function loadSources() {
    try {
        const response = await fetch('/api/sites');
        const data = await response.json();
        
        allSources = data.sites || [];
        
        // Auto-select all by default
        allSources.forEach(source => {
            if (source.enabled && !source.requires_api) {
                selectedSources.add(source.id);
            }
        });
        
        renderSources();
        updateSourceCount();
        
    } catch (error) {
        console.error('Error loading sources:', error);
    }
}

// Render Sources List
function renderSources() {
    sourcesList.innerHTML = '';
    
    allSources.forEach((source, index) => {
        const isSelected = selectedSources.has(source.id);
        const isDisabled = source.requires_api;
        
        const sourceItem = document.createElement('div');
        sourceItem.className = `source-item ${isSelected ? 'active' : ''}`;
        sourceItem.draggable = !isDisabled;
        sourceItem.dataset.sourceId = source.id;
        sourceItem.dataset.index = index;
        
        sourceItem.innerHTML = `
            <div class="drag-handle" title="Drag to reorder">
                <i class="fas fa-grip-vertical"></i>
            </div>
            <div class="source-info">
                <input type="checkbox" 
                       class="source-checkbox" 
                       id="source-${source.id}" 
                       ${isSelected ? 'checked' : ''}
                       ${isDisabled ? 'disabled' : ''}
                       data-source-id="${source.id}">
                <div class="source-details">
                    <span class="source-name">${source.name}</span>
                    <span class="source-country">${source.country || 'Global'}</span>
                </div>
            </div>
            <span class="source-status status-waiting" id="status-${source.id}">
                ${isDisabled ? '🔒 API' : '⏸️ Ready'}
            </span>
        `;
        
        // Drag events
        if (!isDisabled) {
            sourceItem.addEventListener('dragstart', handleDragStart);
            sourceItem.addEventListener('dragend', handleDragEnd);
            sourceItem.addEventListener('dragover', handleDragOver);
            sourceItem.addEventListener('drop', handleDrop);
            sourceItem.addEventListener('dragenter', handleDragEnter);
            sourceItem.addEventListener('dragleave', handleDragLeave);
        }
        
        sourceItem.querySelector('.source-checkbox').addEventListener('change', (e) => {
            toggleSource(source.id, e.target.checked);
        });
        
        sourcesList.appendChild(sourceItem);
    });
}

// Toggle Source Selection
function toggleSource(sourceId, isChecked) {
    if (isChecked) {
        selectedSources.add(sourceId);
    } else {
        selectedSources.delete(sourceId);
    }
    renderSources();
    updateSourceCount();
}

// Select/Deselect All
function selectAllSources() {
    allSources.forEach(source => {
        if (!source.requires_api) {
            selectedSources.add(source.id);
        }
    });
    renderSources();
    updateSourceCount();
}

function deselectAllSources() {
    selectedSources.clear();
    renderSources();
    updateSourceCount();
}

// Update Source Count
function updateSourceCount() {
    document.getElementById('sourceCount').textContent = `${selectedSources.size} selected`;
    document.getElementById('sourcesScanned').textContent = selectedSources.size;
}

// Toggle Add Source Form
function toggleAddSourceForm(show) {
    addSourceModal.style.display = show ? 'block' : 'none';
    if (!show) {
        document.getElementById('customSourceName').value = '';
        document.getElementById('customSourceUrl').value = '';
    }
}

// Save Custom Source
async function saveCustomSource() {
    const name = document.getElementById('customSourceName').value.trim();
    const url = document.getElementById('customSourceUrl').value.trim();
    
    if (!name || !url) {
        alert('Please provide both name and URL');
        return;
    }
    
    try {
        const response = await fetch('/api/sites/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, url})
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            allSources.push(data.site);
            selectedSources.add(data.site.id);
            renderSources();
            toggleAddSourceForm(false);
            showNotification('Source added successfully!', 'success');
        }
    } catch (error) {
        console.error('Error adding source:', error);
        showNotification('Failed to add source', 'error');
    }
}

// Start Scraping
async function startScraping() {
    if (selectedSources.size === 0) {
        showNotification('Please select at least one source', 'warning');
        return;
    }
    
    const jobTitle = document.getElementById('jobTitle').value.trim();
    const location = document.getElementById('location').value.trim();
    const remote = document.getElementById('remoteOnly').checked;
    
    if (!jobTitle) {
        showNotification('Please enter a job title', 'warning');
        return;
    }
    
    // Reset tracking
    lastLoggedSite = null;
    loggedSites.clear();
    
    logToConsole('info', `🚀 Starting scan for "${jobTitle}" in "${location}"`);
    logToConsole('info', `📋 Selected sources: ${Array.from(selectedSources).join(', ')}`);
    
    // Get sites in the order they appear in allSources (respects drag-drop order)
    const sitesInOrder = allSources
        .filter(source => selectedSources.has(source.id))
        .map(source => source.id);
    
    console.log('Scraping order:', sitesInOrder);
    
    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                job_title: jobTitle,
                location: location,
                remote: remote,
                sites: sitesInOrder
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            isScrapingActive = true;
            startBtn.disabled = true;
            stopBtn.disabled = false;
            
            // Hide ready state, show progress
            readyState.style.display = 'none';
            progressSection.style.display = 'block';
            resultsList.innerHTML = '';
            
            // Reset all counters and data
            allScrapedJobs = []; // Clear analytics data
            dedupCount = 0;
            currentPage = 1;
            document.getElementById('totalJobs').textContent = '0';
            document.getElementById('resultsCount').textContent = '(0)';
            document.getElementById('dedupCount').textContent = '0';
            updateAppliedCount();
            document.getElementById('scanTime').textContent = '0s';
            
            // Clear source filter if exists
            const sourceFilter = document.getElementById('filterBySource');
            if (sourceFilter) {
                sourceFilter.value = 'all';
            }
            
            // Clear previous progress bars
            const progressBars = document.getElementById('progressBars');
            if (progressBars) {
                progressBars.innerHTML = '';
            }
            
            // Start timer
            startTime = Date.now();
            timerInterval = setInterval(updateTimer, 1000);
            
            // Update source statuses to waiting
            selectedSources.forEach(sourceId => {
                updateSourceStatus(sourceId, 'waiting');
            });
            
            // Start listening for updates
            connectToEventStream();
            startStatusPolling();
            
            showNotification(`Scanning ${selectedSources.size} sources...`, 'info');
        } else {
            showNotification(data.error || 'Failed to start scraping', 'error');
        }
    } catch (error) {
        console.error('Error starting scraping:', error);
        showNotification('Failed to start scraping', 'error');
    }
}

// Stop Scraping
async function stopScraping() {
    try {
        // Set flags first to stop all processes
        isScrapingActive = false;
        
        // Close event source immediately
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        
        // Stop polling interval
        if (statusInterval) {
            clearInterval(statusInterval);
            statusInterval = null;
        }
        
        // Stop timer
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        
        // Send stop request to backend
        await fetch('/api/stop', {method: 'POST'});
        
        // Update UI
        startBtn.disabled = false;
        stopBtn.disabled = true;
        
        // Reset all statuses to waiting
        selectedSources.forEach(sourceId => {
            updateSourceStatus(sourceId, 'waiting');
        });
        
        // Clear progress section
        const progressSection = document.getElementById('progressSection');
        const progressBars = document.getElementById('progressBars');
        if (progressBars) {
            progressBars.innerHTML = '';
        }
        if (progressSection) {
            progressSection.style.display = 'none';
        }
        
        showNotification('Scraping stopped', 'info');
        logToConsole('info', '⏹️ Scraping stopped by user');
        
    } catch (error) {
        console.error('Error stopping scraping:', error);
        // Even if fetch fails, ensure UI is reset
        isScrapingActive = false;
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
}

// Connect to Event Stream (with polling fallback for production/gunicorn)
let _lastJobCount = 0;
function connectToEventStream() {
    // Try SSE first, but fall back to polling if it fails
    try {
        eventSource = new EventSource('/api/stream');
        let sseWorking = false;
        
        eventSource.onmessage = function(event) {
            sseWorking = true;
            const data = JSON.parse(event.data);
            
            if (data.status === 'complete') {
                eventSource.close();
                eventSource = null;
            } else {
                addJobToResults(data);
            }
        };
        
        eventSource.onerror = function(error) {
            console.warn('SSE unavailable, using polling fallback');
            eventSource.close();
            eventSource = null;
            // SSE failed — polling will handle job fetching via startStatusPolling
        };
    } catch (e) {
        console.warn('SSE not supported, using polling only');
    }
}

// Status Polling
let statusInterval = null;
let _pollJobsSeen = new Set(); // Track which job URLs we've already added to DOM

function startStatusPolling() {
    _lastJobCount = 0;
    _pollJobsSeen = new Set();
    
    statusInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            // Save scraper results for analytics
            if (data.scraper_results) {
                window._lastScraperResults = data.scraper_results;
            }
            
            document.getElementById('totalJobs').textContent = data.total_jobs || 0;
            
            // Update dedup count if provided
            if (data.duplicates_removed !== undefined) {
                document.getElementById('dedupCount').textContent = data.duplicates_removed;
            }
            
            // --- POLLING-BASED JOB FETCH (works even when SSE fails) ---
            const backendCount = data.total_jobs || 0;
            const domCards = resultsList.querySelectorAll('.job-card').length;
            if (backendCount > 0 && backendCount > domCards) {
                // Fetch new jobs from backend
                try {
                    const jobsResp = await fetch('/api/jobs?sort=recent');
                    const jobsData = await jobsResp.json();
                    if (jobsData.jobs) {
                        let added = 0;
                        jobsData.jobs.forEach(job => {
                            const key = job.url || (job.title + '|' + job.company);
                            if (!_pollJobsSeen.has(key)) {
                                _pollJobsSeen.add(key);
                                addJobToResults(job);
                                added++;
                            }
                        });
                        if (added > 0) {
                            logToConsole('info', `📥 +${added} new jobs (${_pollJobsSeen.size} total)`);
                        }
                    }
                } catch (fetchErr) {
                    // ignore individual fetch errors
                }
            }
            
            // Update individual site progress
            if (data.site_progress) {
                Object.entries(data.site_progress).forEach(([site, percent]) => {
                    updateProgress(site, percent);
                    
                    // Update source status based on progress
                    if (percent === 0) {
                        updateSourceStatus(site, 'waiting');
                    } else if (percent < 100) {
                        updateSourceStatus(site, 'scanning');
                    } else {
                        updateSourceStatus(site, 'done');
                    }
                });
            }
            
            // Log current scanning site
            if (data.current_site && data.current_site !== lastLoggedSite) {
                logToConsole('info', `🔍 Currently scanning: ${data.current_site}`);
                lastLoggedSite = data.current_site;
            }
            
            // Show completed sites
            if (data.sites_scraped) {
                Object.entries(data.sites_scraped).forEach(([site, count]) => {
                    if (!loggedSites.has(site) && count > 0) {
                        logToConsole('success', `✅ ${site}: ${count} jobs found`);
                        loggedSites.add(site);
                    } else if (!loggedSites.has(site) && data.site_progress && data.site_progress[site] === 100 && count === 0) {
                        logToConsole('info', `💭 ${site}: No jobs found`);
                        loggedSites.add(site);
                    }
                });
            }
            
            // Handle completion — only when we KNOW scraping has started
            if (!data.active && data.completed_sites > 0) {
                if (statusInterval) {
                    clearInterval(statusInterval);
                    statusInterval = null;
                    
                    // Close SSE if still open
                    if (eventSource) {
                        eventSource.close();
                        eventSource = null;
                    }
                    
                    // Stop timer
                    if (timerInterval) {
                        clearInterval(timerInterval);
                        timerInterval = null;
                    }
                    
                    // Disable buttons properly
                    isScrapingActive = false;
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                    
                    // Final job sync — ensure all jobs are in the DOM
                    try {
                        const jobsResp = await fetch('/api/jobs');
                        const jobsData = await jobsResp.json();
                        if (jobsData.jobs && jobsData.jobs.length > 0) {
                            let added = 0;
                            jobsData.jobs.forEach(job => {
                                const key = job.url || (job.title + '|' + job.company);
                                if (!_pollJobsSeen.has(key)) {
                                    _pollJobsSeen.add(key);
                                    addJobToResults(job);
                                    added++;
                                }
                            });
                            if (added > 0) {
                                logToConsole('info', `📥 Final sync: +${added} jobs`);
                            }
                            document.getElementById('totalJobs').textContent = jobsData.jobs.length;
                            const visibleCards = Array.from(resultsList.querySelectorAll('.job-card')).filter(c => c.style.display !== 'none');
                            document.getElementById('resultsCount').textContent = `(${visibleCards.length})`;
                        }
                    } catch (syncErr) {
                        console.error('Final sync error:', syncErr);
                    }
                    
                    const finalCount = resultsList.querySelectorAll('.job-card').length;
                    logToConsole('success', `✅ Scan complete! ${finalCount} jobs found`);
                    showNotification(`Scan complete! ${finalCount} jobs found`, 'success');
                    
                    // Reset tracking
                    lastLoggedSite = null;
                    loggedSites.clear();
                }
            }
        } catch (error) {
            console.error('Error fetching status:', error);
        }
    }, 2000); // Poll every 2 seconds (was 1s, reduce server load)
}

// Track logged sites to avoid duplicates
let lastLoggedSite = null;
let loggedSites = new Set();

// Add Job to Results
function addJobToResults(job) {
    const jobCard = createJobCard(job);
    resultsList.insertBefore(jobCard, resultsList.firstChild);
    
    // Store for analytics
    allScrapedJobs.push(job);
    
    // Update total count
    const allCards = resultsList.querySelectorAll('.job-card');
    const totalCount = allCards.length;
    document.getElementById('totalJobs').textContent = totalCount;
    
    // Update visible count (respecting filters)
    const visibleCards = Array.from(allCards).filter(card => card.style.display !== 'none');
    document.getElementById('resultsCount').textContent = `(${visibleCards.length})`;
    
    // Update source filter dropdown options
    updateSourceFilterOptions();
}

// Create Job Card
function createJobCard(job, isSaved = false) {
    const card = document.createElement('div');
    const jobUrl = job.url || '';
    const isApplied = appliedJobs.has(jobUrl);
    card.className = `job-card${isApplied ? ' applied' : ''}`;
    card.dataset.source = (job.source || 'unknown').toLowerCase();
    card.dataset.posted = job.posted_timestamp || 0;
    card.dataset.salary = job.salary_numeric || 0;
    card.dataset.worktype = job.work_type || 'On-site';
    card.dataset.matchscore = job.match_score || 0;
    card.dataset.url = jobUrl;
    
    const sourceColor = getSourceColor(job.source);
    
    // Use cleaned description from backend
    const description = job.description_preview || job.description || 'No description available';
    
    // Format date — NEVER show "Scraped: timestamp"
    let postedDate = 'Recently';
    if (job.posted_date && job.posted_date !== 'Recently' && job.posted_date !== 'N/A' && job.posted_date !== '') {
        postedDate = job.posted_date;
    } else if (job.date_posted && job.date_posted !== 'Recently' && job.date_posted !== 'N/A' && job.date_posted !== '') {
        postedDate = job.date_posted;
    }
    
    const workType = job.work_type || 'On-site';
    
    // Work type icon
    const workTypeIcons = { 'Remote': '🏠', 'Hybrid': '🔄', 'On-site': '🏢' };
    
    // Match score badge
    const matchScore = parseInt(job.match_score) || 0;
    let scoreClass = 'score-low';
    if (matchScore >= 80) scoreClass = 'score-excellent';
    else if (matchScore >= 50) scoreClass = 'score-good';
    
    const matchBadge = `
        <div class="match-score-badge ${scoreClass}" title="Resume Match Score: ${matchScore}%">
            ${matchScore}
            <small>match</small>
        </div>
    `;
    
    // Bookmark button
    const isSavedJob = savedJobs.some(j => j.url === jobUrl);
    const bookmarkClass = isSavedJob ? 'fas' : 'far';
    const bookmarkAction = isSaved ? 
        `onclick="unsaveJob('${escapeHtml(jobUrl)}'); event.stopPropagation();"` : 
        `onclick="saveJob(${JSON.stringify(job).replace(/"/g, '&quot;')}); event.stopPropagation();"`;
    
    // Applied button
    const appliedBtnClass = isApplied ? 'apply-track-btn applied' : 'apply-track-btn';
    const appliedBtnText = isApplied ? '<i class="fas fa-check-circle"></i> Applied' : '<i class="fas fa-paper-plane"></i> Mark Applied';

    // Applied indicator
    const appliedBadge = isApplied ? '<span class="applied-badge"><i class="fas fa-check-circle"></i> Applied</span>' : '';

    // Ghost job badge
    let ghostBadge = '';
    if (job.is_ghost) {
        const cls = job.ghost_score >= 60 ? '' : ' low-risk';
        ghostBadge = `<span class="ghost-badge${cls}"><i class="fas fa-ghost"></i> Ghost ${job.ghost_score}%</span>`;
    }

    card.innerHTML = `
        <div class="job-card-header">
            <div style="flex:1;">
                <div class="job-title">${escapeHtml(job.title)} ${appliedBadge} ${ghostBadge}</div>
                <div class="job-company">${escapeHtml(job.company)}</div>
            </div>
            <div class="job-header-actions">
                ${matchBadge}
                <button class="bookmark-btn" ${bookmarkAction} title="Save job">
                    <i class="${bookmarkClass} fa-bookmark"></i>
                </button>
                <span class="job-source-badge" style="background: ${sourceColor}; color: white;">
                    ${escapeHtml(job.source || 'Unknown')}
                </span>
            </div>
        </div>
        
        <div class="job-meta">
            <div>
                <i class="fas fa-map-marker-alt"></i>
                <span>${escapeHtml(job.location)}</span>
            </div>
            <div>
                <i class="fas fa-calendar-alt"></i>
                <span>${escapeHtml(postedDate)}</span>
            </div>
            <div>
                <i class="fas fa-briefcase"></i>
                <span>${escapeHtml(job.job_type || 'Full-time')}</span>
            </div>
            <div>
                <span>${workTypeIcons[workType] || '🏢'}</span>
                <span>${escapeHtml(workType)}</span>
            </div>
        </div>
        
        <div class="job-description">
            ${escapeHtml(description)}
        </div>
        
        <div class="job-footer">
            <div class="job-salary">
                <i class="fas fa-dollar-sign"></i>
                ${escapeHtml(job.salary || 'Not specified')}
            </div>
            <div class="job-footer-actions">
                <button class="${appliedBtnClass}" onclick="toggleApplied('${escapeHtml(jobUrl)}'); event.stopPropagation();" title="Toggle application status">
                    ${appliedBtnText}
                </button>
                <a href="${escapeHtml(jobUrl)}" target="_blank" class="job-apply-btn" onclick="event.stopPropagation();">
                    Apply Now <i class="fas fa-external-link-alt"></i>
                </a>
            </div>
        </div>
    `;
    
    return card;
}

// Update Source Status
function updateSourceStatus(sourceId, status) {
    const statusElem = document.getElementById(`status-${sourceId}`);
    if (!statusElem) return;
    
    statusElem.className = `source-status status-${status}`;
    
    const statusText = {
        'waiting': '⏸️ Ready',
        'scanning': '🔄 Scanning...',
        'done': '✅ Done'
    };
    
    statusElem.textContent = statusText[status] || status;
}

// Update Progress
function updateProgress(sourceId, percent) {
    const progressBars = document.getElementById('progressBars');
    let progressItem = document.getElementById(`progress-${sourceId}`);
    
    if (!progressItem) {
        progressItem = document.createElement('div');
        progressItem.id = `progress-${sourceId}`;
        progressItem.className = 'progress-item';
        progressItem.innerHTML = `
            <div class="progress-header">
                <span>${sourceId}</span>
                <span class="progress-percent">${percent}%</span>
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: ${percent}%"></div>
            </div>
        `;
        progressBars.appendChild(progressItem);
    } else {
        progressItem.querySelector('.progress-percent').textContent = `${percent}%`;
        progressItem.querySelector('.progress-bar').style.width = `${percent}%`;
    }
}

// Update Timer
function updateTimer() {
    if (!startTime) return;
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    document.getElementById('scanTime').textContent = `${elapsed}s`;
}

// Export Jobs
async function exportJobs(format) {
    try {
        const response = await fetch(`/api/export/${format}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const ext = format === 'csv' ? 'csv' : format === 'excel' ? 'xlsx' : 'json';
            a.download = `jobradar_${Date.now()}.${ext}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            hideModal('exportModal');
            showNotification('Jobs exported successfully!', 'success');
        } else {
            showNotification('Export failed', 'error');
        }
    } catch (error) {
        console.error('Error exporting:', error);
        showNotification('Export failed', 'error');
    }
}

// Filter Jobs
function filterJobs() {
    const query = document.getElementById('searchJobs').value.toLowerCase();
    const sourceFilter = (document.getElementById('filterBySource')?.value || 'all').toLowerCase();
    const scoreFilter = parseInt(document.getElementById('filterByScore')?.value || '0') || 0;
    const appliedFilter = document.getElementById('filterByApplied')?.value || 'all';
    const workTypeFilter = document.getElementById('filterByWorkType')?.value || 'all';
    const jobCards = resultsList.querySelectorAll('.job-card');
    
    let visibleCount = 0;
    jobCards.forEach(card => {
        const text = card.textContent.toLowerCase();
        const cardSource = (card.dataset.source || '').toLowerCase();
        const cardScore = parseFloat(card.dataset.matchscore) || 0;
        const cardUrl = card.dataset.url || '';
        const cardWorkType = card.dataset.worktype || 'On-site';
        const isCardApplied = appliedJobs.has(cardUrl);
        
        // Check all filters
        const matchesSearch = !query || text.includes(query);
        const matchesSource = sourceFilter === 'all' || cardSource === sourceFilter;
        const matchesScore = scoreFilter === 0 || cardScore >= scoreFilter;
        const matchesApplied = appliedFilter === 'all' || 
            (appliedFilter === 'applied' && isCardApplied) ||
            (appliedFilter === 'not-applied' && !isCardApplied);
        const matchesWorkType = workTypeFilter === 'all' || cardWorkType === workTypeFilter;
        
        if (matchesSearch && matchesSource && matchesScore && matchesApplied && matchesWorkType) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    // Update results count
    const totalCount = jobCards.length;
    if (visibleCount === totalCount) {
        document.getElementById('resultsCount').textContent = `(${totalCount})`;
    } else {
        document.getElementById('resultsCount').textContent = `(${visibleCount}/${totalCount})`;
    }
}

// Sort Jobs
function sortJobs() {
    const sortBy = document.getElementById('sortBy').value;
    const jobCardsArray = Array.from(resultsList.querySelectorAll('.job-card'));
    
    jobCardsArray.sort((a, b) => {
        if (sortBy === 'match' || sortBy === 'score') {
            // Sort by match score (highest first)
            const scoreA = parseFloat(a.dataset.matchscore) || 0;
            const scoreB = parseFloat(b.dataset.matchscore) || 0;
            return scoreB - scoreA;
        } else if (sortBy === 'salary') {
            // Sort by salary (highest first)
            const salaryA = parseFloat(a.dataset.salary) || 0;
            const salaryB = parseFloat(b.dataset.salary) || 0;
            return salaryB - salaryA;
        } else if (sortBy === 'recent') {
            // Sort by posted date (most recent first)
            const dateA = parseFloat(a.dataset.posted) || 0;
            const dateB = parseFloat(b.dataset.posted) || 0;
            return dateB - dateA;
        } else if (sortBy === 'company') {
            // Sort by company name A-Z
            const companyA = a.querySelector('.job-company').textContent;
            const companyB = b.querySelector('.job-company').textContent;
            return companyA.localeCompare(companyB);
        } else if (sortBy === 'remote') {
            // Remote first, then Hybrid, then On-site
            const typeA = a.dataset.worktype || 'On-site';
            const typeB = b.dataset.worktype || 'On-site';
            const order = {'Remote': 0, 'Hybrid': 1, 'On-site': 2};
            return (order[typeA] || 2) - (order[typeB] || 2);
        } else if (sortBy === 'site') {
            // Sort by source site A-Z
            const siteA = a.dataset.source || '';
            const siteB = b.dataset.source || '';
            return siteA.localeCompare(siteB);
        }
        return 0;
    });
    
    // Re-append in sorted order
    resultsList.innerHTML = '';
    jobCardsArray.forEach(card => resultsList.appendChild(card));
}

// Helper: Extract salary from text
function extractSalary(text) {
    const match = text.match(/\$(\d{1,3}(?:,\d{3})*)/);
    return match ? parseInt(match[1].replace(/,/g, '')) : 0;
}

// Helper: Extract date from text (returns ms timestamp for sorting)
function extractDate(text) {
    if (!text || text === 'N/A' || text === 'Unknown') return 0;
    if (text.includes('Today') || text.includes('Just')) return Date.now();
    if (text.includes('Yesterday')) return Date.now() - 86400000;
    
    const daysMatch = text.match(/(\d+) days? ago/);
    if (daysMatch) {
        return Date.now() - (parseInt(daysMatch[1]) * 86400000);
    }
    
    const weeksMatch = text.match(/(\d+) weeks? ago/);
    if (weeksMatch) {
        return Date.now() - (parseInt(weeksMatch[1]) * 7 * 86400000);
    }
    
    const monthsMatch = text.match(/(\d+) months? ago/);
    if (monthsMatch) {
        return Date.now() - (parseInt(monthsMatch[1]) * 30 * 86400000);
    }
    
    // Parse actual date strings like "Feb 12, 2026", "February 12, 2026", "2026-02-12"
    const parsed = Date.parse(text);
    if (!isNaN(parsed)) return parsed;
    
    return 0; // Unknown date
}

// Theme Toggle
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const icon = themeToggle.querySelector('i');
    const text = themeToggle.querySelector('span');
    
    if (newTheme === 'light') {
        icon.className = 'fas fa-sun';
        text.textContent = 'Light Mode';
    } else {
        icon.className = 'fas fa-moon';
        text.textContent = 'Dark Mode';
    }
}

// Load saved theme
const savedTheme = localStorage.getItem('theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);

// Modal Functions
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: var(--bg-card);
        border-left: 4px solid ${type === 'success' ? 'var(--accent-success)' : type === 'error' ? 'var(--accent-danger)' : 'var(--accent-primary)'};
        border-radius: 8px;
        box-shadow: var(--shadow-lg);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Drag and Drop Handlers
let draggedElement = null;

function handleDragStart(e) {
    draggedElement = e.currentTarget;
    e.currentTarget.style.opacity = '0.4';
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', e.currentTarget.innerHTML);
}

function handleDragEnd(e) {
    e.currentTarget.style.opacity = '1';
    
    // Remove all drag-over classes
    document.querySelectorAll('.source-item').forEach(item => {
        item.classList.remove('drag-over');
    });
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    e.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDragEnter(e) {
    if (e.currentTarget !== draggedElement) {
        e.currentTarget.classList.add('drag-over');
    }
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('drag-over');
}

function handleDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation();
    }
    
    e.currentTarget.classList.remove('drag-over');
    
    if (draggedElement !== e.currentTarget) {
        const fromIndex = parseInt(draggedElement.dataset.index);
        const toIndex = parseInt(e.currentTarget.dataset.index);
        
        // Reorder the sources array
        const movedSource = allSources.splice(fromIndex, 1)[0];
        allSources.splice(toIndex, 0, movedSource);
        
        // Re-render
        renderSources();
        showNotification('Sources reordered. Will scrape in new order.', 'success');
    }
    
    return false;
}

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function getSourceColor(source) {
    const colors = {
        'indeed': '#2164f3',
        'google': '#4285f4',
        'linkedin': '#0077b5',
        'glassdoor': '#0caa41',
        'dice': '#ff6b35',
        'ziprecruiter': '#1c71d8',
        'talent': '#8b5cf6',
        'jooble': '#f59e0b',
        'remoteok': '#ff4742',
        'weworkremotely': '#5469d4',
        'wellfound': '#000000',
        'servicenow': '#62d84e',
        'simplyhired': '#a358df',
        'simplyhired_ca': '#a358df',
        'jobrapido': '#e8590c',
        'workopolis': '#0ea5e9',
        'adzuna': '#10b981',
        'builtin': '#0d9488',
        'usajobs': '#1d4ed8',
        'remoterocketship': '#7c3aed',
        'serper': '#64748b'
    };
    return colors[(source || '').toLowerCase()] || '#64748b';
}

// =====================================
// CONSOLE LOG SYSTEM
// =====================================

let consoleOpen = false;

function toggleConsole() {
    const panel = document.getElementById('consolePanel');
    consoleOpen = !consoleOpen;
    
    if (consoleOpen) {
        panel.classList.add('active');
        logToConsole('info', 'Console opened');
    } else {
        panel.classList.remove('active');
    }
}

function logToConsole(type, message) {
    const consoleContent = document.getElementById('consoleContent');
    if (!consoleContent) return;
    
    const timestamp = new Date().toLocaleTimeString();
    
    const logLine = document.createElement('div');
    logLine.className = `console-line ${type}`;
    logLine.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${message}`;
    
    consoleContent.appendChild(logLine);
    
    // Auto-scroll to bottom
    consoleContent.scrollTop = consoleContent.scrollHeight;
    
    // Limit to 200 lines
    while (consoleContent.children.length > 200) {
        consoleContent.removeChild(consoleContent.firstChild);
    }
}

function clearConsole() {
    const consoleContent = document.getElementById('consoleContent');
    if (consoleContent) {
        consoleContent.innerHTML = '';
        logToConsole('info', 'Console cleared');
    }
}

function copyConsole() {
    const consoleContent = document.getElementById('consoleContent');
    const text = Array.from(consoleContent.children)
        .map(line => line.textContent)
        .join('\n');
    
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Console logs copied to clipboard!', 'success');
    }).catch(err => {
        showNotification('Failed to copy logs', 'error');
    });
}

// =====================================
// COLLAPSIBLE SECTIONS
// =====================================

function toggleSourcesDropdown() {
    sourcesExpanded = !sourcesExpanded;
    const sourcesList = document.getElementById('sourcesList');
    const toggleIcon = document.getElementById('sourcesToggleIcon');
    const toggleText = document.getElementById('sourcesToggleText');
    
    if (sourcesExpanded) {
        sourcesList.style.display = 'block';
        toggleIcon.className = 'fas fa-chevron-up';
        toggleText.textContent = 'Hide Sources';
    } else {
        sourcesList.style.display = 'none';
        toggleIcon.className = 'fas fa-chevron-down';
        toggleText.textContent = 'Show Sources';
    }
}

function toggleProgressSection() {
    progressExpanded = !progressExpanded;
    const progressContent = document.getElementById('progressContent');
    const collapseBtn = document.getElementById('progressCollapseBtn');
    
    if (progressExpanded) {
        progressContent.style.display = 'block';
        collapseBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';
    } else {
        progressContent.style.display = 'none';
        collapseBtn.innerHTML = '<i class="fas fa-chevron-down"></i>';
    }
}

// Update source filter dropdown with available sources
function updateSourceFilterOptions() {
    const filterBySource = document.getElementById('filterBySource');
    if (!filterBySource) return;
    
    const jobCards = resultsList.querySelectorAll('.job-card');
    const sources = new Set();
    
    jobCards.forEach(card => {
        const source = card.dataset.source;
        if (source && source !== 'unknown') {
            sources.add(source.toLowerCase());
        }
    });
    
    // Keep current selection
    const currentValue = filterBySource.value;
    
    // Rebuild options
    filterBySource.innerHTML = '<option value="all">All Sources</option>';
    
    Array.from(sources).sort().forEach(source => {
        const option = document.createElement('option');
        option.value = source;
        option.textContent = source.toUpperCase();
        filterBySource.appendChild(option);
    });
    
    console.log('Updated source filter options:', Array.from(sources));
    
    // Restore selection if still valid
    if (currentValue && Array.from(sources).includes(currentValue.toLowerCase())) {
        filterBySource.value = currentValue;
    }
}

// =====================================
// TAB NAVIGATION
// =====================================

function initTabNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = item.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tabName) {
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.dataset.tab === tabName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // Hide all tabs
    document.getElementById('searchTab').style.display = 'none';
    document.getElementById('savedTab').style.display = 'none';
    if (document.getElementById('resumeTab')) document.getElementById('resumeTab').style.display = 'none';
    if (document.getElementById('optimizerTab')) document.getElementById('optimizerTab').style.display = 'none';
    document.getElementById('analyticsTab').style.display = 'none';
    document.getElementById('settingsTab').style.display = 'none';
    
    // Show selected tab
    switch(tabName) {
        case 'search':
            document.getElementById('searchTab').style.display = 'grid';
            break;
        case 'saved':
            document.getElementById('savedTab').style.display = 'block';
            updateSavedJobsDisplay();
            break;
        case 'resume':
            document.getElementById('resumeTab').style.display = 'block';
            loadResume();
            renderMatchedJobs();
            break;
        case 'optimizer':
            document.getElementById('optimizerTab').style.display = 'block';
            loadOptimizerResume();
            break;
        case 'analytics':
            document.getElementById('analyticsTab').style.display = 'block';
            updateAnalytics();
            break;
        case 'settings':
            document.getElementById('settingsTab').style.display = 'block';
            loadSettingsValues();
            loadScheduleConfig();
            break;
    }
}

// =====================================
// SAVED JOBS FUNCTIONALITY
// =====================================

function saveJob(job) {
    // Check if already saved
    if (savedJobs.some(j => j.url === job.url)) {
        showNotification('Job already saved!', 'info');
        return;
    }
    
    savedJobs.push(job);
    localStorage.setItem('savedJobs', JSON.stringify(savedJobs));
    showNotification('Job saved!', 'success');
    updateSavedJobsDisplay();
}

function unsaveJob(jobUrl) {
    savedJobs = savedJobs.filter(j => j.url !== jobUrl);
    localStorage.setItem('savedJobs', JSON.stringify(savedJobs));
    updateSavedJobsDisplay();
    showNotification('Job removed', 'info');
}

function updateSavedJobsDisplay() {
    const savedJobsList = document.getElementById('savedJobsList');
    const savedCount = document.getElementById('savedCount');
    
    if (!savedJobsList) return;
    
    savedCount.textContent = `(${savedJobs.length})`;
    
    if (savedJobs.length === 0) {
        savedJobsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-bookmark fa-3x"></i>
                <h3>No saved jobs yet</h3>
                <p>Click the bookmark icon on any job to save it for later</p>
            </div>
        `;
        return;
    }
    
    savedJobsList.innerHTML = '';
    savedJobs.forEach(job => {
        const card = createJobCard(job, true);
        savedJobsList.appendChild(card);
    });
}

function clearSavedJobs() {
    if (confirm('Are you sure you want to clear all saved jobs?')) {
        savedJobs = [];
        localStorage.setItem('savedJobs', JSON.stringify(savedJobs));
        updateSavedJobsDisplay();
        showNotification('Saved jobs cleared', 'success');
    }
}

// =====================================
// ANALYTICS FUNCTIONALITY (ENHANCED)
// =====================================

function updateAnalytics() {
    // Load jobs if not already loaded
    if (allScrapedJobs.length === 0) {
        const jobCards = document.querySelectorAll('#resultsList .job-card');
        allScrapedJobs = Array.from(jobCards).map(card => ({
            title: card.querySelector('.job-title')?.textContent || '',
            company: card.querySelector('.job-company')?.textContent || '',
            location: card.querySelector('.job-meta')?.textContent || '',
            source: card.dataset.source || 'Unknown',
            work_type: card.dataset.worktype || 'On-site',
            salary_numeric: parseFloat(card.dataset.salary) || 0,
            match_score: parseFloat(card.dataset.matchscore) || 0,
            url: card.dataset.url || ''
        }));
    }
    
    const jobs = allScrapedJobs;
    
    // Quick stats
    document.getElementById('analyticsTotal').textContent = jobs.length;
    document.getElementById('analyticsApplied').textContent = appliedJobs.size;
    document.getElementById('analyticsRemote').textContent = jobs.filter(j => (j.work_type || '').toLowerCase() === 'remote').length;
    
    // Average score
    const scores = jobs.filter(j => (j.match_score || 0) > 0).map(j => j.match_score);
    const avgScore = scores.length > 0 ? Math.round(scores.reduce((a,b) => a+b, 0) / scores.length) : '--';
    document.getElementById('analyticsAvgScore').textContent = avgScore;
    document.getElementById('analyticsUpdated').textContent = `Updated: ${new Date().toLocaleTimeString()}`;
    
    if (jobs.length === 0) return;
    
    // Match Score Distribution
    const scoreRanges = {'80-100 (Excellent)': 0, '50-79 (Good)': 0, '1-49 (Low)': 0, '0 (No Score)': 0};
    jobs.forEach(j => {
        const s = j.match_score || 0;
        if (s >= 80) scoreRanges['80-100 (Excellent)']++;
        else if (s >= 50) scoreRanges['50-79 (Good)']++;
        else if (s >= 1) scoreRanges['1-49 (Low)']++;
        else scoreRanges['0 (No Score)']++;
    });
    const scoreColors = {'80-100 (Excellent)': '#10b981', '50-79 (Good)': '#f59e0b', '1-49 (Low)': '#ef4444', '0 (No Score)': '#64748b'};
    const scoreFilterValues = {'80-100 (Excellent)': '80', '50-79 (Good)': '50', '1-49 (Low)': '1', '0 (No Score)': '0'};
    const maxScoreCount = Math.max(...Object.values(scoreRanges));
    document.getElementById('scoreDistChart').innerHTML = Object.entries(scoreRanges).map(([range, count]) => `
        <div class="chart-bar clickable-bar" onclick="filterByScoreRange('${scoreFilterValues[range]}')" title="Click to filter jobs by this score range" style="cursor:pointer;">
            <span class="chart-label">${range}</span>
            <div class="chart-bar-fill" style="width: ${maxScoreCount > 0 ? (count / maxScoreCount) * 100 : 0}%; background: ${scoreColors[range]}">
                <span class="chart-value">${count}</span>
            </div>
        </div>
    `).join('');
    
    // Top Companies
    const companyCounts = {};
    jobs.forEach(job => {
        const company = job.company || 'Unknown';
        companyCounts[company] = (companyCounts[company] || 0) + 1;
    });
    const topCompanies = Object.entries(companyCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
    document.getElementById('topCompanies').innerHTML = topCompanies.map(([company, count]) => `
        <div class="chart-bar">
            <span class="chart-label">${escapeHtml(company)}</span>
            <div class="chart-bar-fill" style="width: ${(count / topCompanies[0][1]) * 100}%">
                <span class="chart-value">${count}</span>
            </div>
        </div>
    `).join('');
    
    // Salary Distribution
    const salaries = jobs.filter(j => j.salary_numeric > 0).map(j => j.salary_numeric);
    if (salaries.length > 0) {
        const avgSalary = salaries.reduce((a, b) => a + b, 0) / salaries.length;
        document.getElementById('salaryChart').innerHTML = `
            <div class="salary-stats">
                <div class="salary-stat"><span class="label">Average</span><span class="value">$${Math.round(avgSalary).toLocaleString()}</span></div>
                <div class="salary-stat"><span class="label">Min</span><span class="value">$${Math.round(Math.min(...salaries)).toLocaleString()}</span></div>
                <div class="salary-stat"><span class="label">Max</span><span class="value">$${Math.round(Math.max(...salaries)).toLocaleString()}</span></div>
                <div class="salary-stat"><span class="label">Jobs w/ Salary</span><span class="value">${salaries.length}</span></div>
            </div>
        `;
    }
    
    // Work Type Chart
    const workTypes = {};
    jobs.forEach(job => { workTypes[job.work_type || 'On-site'] = (workTypes[job.work_type || 'On-site'] || 0) + 1; });
    drawPieChart('workTypeCanvas', workTypes);
    
    // Source Chart
    const sources = {};
    jobs.forEach(job => { const s = (job.source || 'Unknown').toUpperCase(); sources[s] = (sources[s] || 0) + 1; });
    drawPieChart('sourceCanvas', sources);
    
    // Source table — show ALL scrapers (including 0-result ones)
    const sourceTableDiv = document.getElementById('sourceTable');
    if (sourceTableDiv) {
        const sortedSources = Object.entries(sources).sort((a, b) => b[1] - a[1]);
        const total = Object.values(sources).reduce((a, b) => a + b, 0);
        let tableHTML = `<div class="source-breakdown"><table class="analytics-table">
            <thead><tr><th>Source</th><th>Jobs</th><th>%</th><th>Status</th></tr></thead><tbody>`;
        sortedSources.forEach(([source, count]) => {
            tableHTML += `<tr><td><strong>${escapeHtml(source)}</strong></td><td>${count}</td><td>${((count/total)*100).toFixed(1)}%</td><td><span class="source-status-ok">✅ Active</span></td></tr>`;
        });
        // Show 0-result scrapers from status data
        if (window._lastScraperResults) {
            Object.entries(window._lastScraperResults).forEach(([site, info]) => {
                const siteUpper = site.toUpperCase();
                if (!sources[siteUpper] && !sources[site]) {
                    const statusLabel = {
                        'zero': '⚠️ 0 jobs found',
                        'filtered': '🔍 All filtered out',
                        'error': '❌ Error',
                        'needs_api': '🔑 Needs API key',
                        'pending': '⏳ Pending',
                    }[info.status] || info.status;
                    tableHTML += `<tr style="opacity:0.7;"><td>${escapeHtml(siteUpper)}</td><td>0</td><td>0%</td><td>${statusLabel}</td></tr>`;
                }
            });
        }
        tableHTML += `</tbody><tfoot><tr><td><strong>Total</strong></td><td><strong>${total}</strong></td><td><strong>100%</strong></td><td></td></tr></tfoot></table></div>`;
        sourceTableDiv.innerHTML = tableHTML;
    }
    
    // Top Locations
    const locationCounts = {};
    jobs.forEach(job => {
        const loc = (job.location || 'Unknown').split(',')[0].trim();
        if (loc) locationCounts[loc] = (locationCounts[loc] || 0) + 1;
    });
    const topLocations = Object.entries(locationCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const topLocDiv = document.getElementById('topLocations');
    if (topLocDiv && topLocations.length > 0) {
        topLocDiv.innerHTML = topLocations.map(([loc, count]) => `
            <div class="chart-bar">
                <span class="chart-label">${escapeHtml(loc)}</span>
                <div class="chart-bar-fill" style="width: ${(count / topLocations[0][1]) * 100}%">
                    <span class="chart-value">${count}</span>
                </div>
            </div>
        `).join('');
    }
}

function drawPieChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    canvas.width = 300;
    canvas.height = 300;
    
    const total = Object.values(data).reduce((a, b) => a + b, 0);
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
    
    let currentAngle = -Math.PI / 2;
    
    Object.entries(data).forEach(([label, value], index) => {
        const sliceAngle = (value / total) * 2 * Math.PI;
        
        ctx.beginPath();
        ctx.fillStyle = colors[index % colors.length];
        ctx.moveTo(150, 150);
        ctx.arc(150, 150, 120, currentAngle, currentAngle + sliceAngle);
        ctx.closePath();
        ctx.fill();
        
        currentAngle += sliceAngle;
    });
    
    // Legend
    const legend = canvas.parentElement;
    let legendHTML = '<div class="chart-legend">';
    Object.entries(data).forEach(([label, value], index) => {
        const percentage = ((value / total) * 100).toFixed(1);
        legendHTML += `
            <div class="legend-item">
                <span class="legend-color" style="background: ${colors[index % colors.length]}"></span>
                <span>${escapeHtml(label)}: ${value} (${percentage}%)</span>
            </div>
        `;
    });
    legendHTML += '</div>';
    
    // Add legend if not exists
    if (!legend.querySelector('.chart-legend')) {
        legend.insertAdjacentHTML('beforeend', legendHTML);
    }
}

// =====================================
// SETTINGS FUNCTIONALITY
// =====================================

function loadSettingsValues() {
    const settings = JSON.parse(localStorage.getItem('appSettings') || '{}');
    
    const djtEl = document.getElementById('defaultJobTitle');
    const dlEl = document.getElementById('defaultLocation');
    const droEl = document.getElementById('defaultRemoteOnly');
    const jppEl = document.getElementById('jobsPerPage');
    
    if (djtEl) djtEl.value = settings.defaultJobTitle || '';
    if (dlEl) dlEl.value = settings.defaultLocation || '';
    if (droEl) droEl.checked = settings.defaultRemoteOnly || false;
    if (jppEl) jppEl.value = settings.jobsPerPage || '50';
}

function saveSettings() {
    const settings = {
        defaultJobTitle: (document.getElementById('defaultJobTitle') || {}).value || '',
        defaultLocation: (document.getElementById('defaultLocation') || {}).value || '',
        defaultRemoteOnly: (document.getElementById('defaultRemoteOnly') || {}).checked || false,
        jobsPerPage: (document.getElementById('jobsPerPage') || {}).value || '50'
    };
    
    localStorage.setItem('appSettings', JSON.stringify(settings));
    applySettings(settings);
    showNotification('Settings saved!', 'success');
}

function applySettings(settings) {
    // Apply default values to search form
    if (settings.defaultJobTitle) {
        document.getElementById('jobTitle').value = settings.defaultJobTitle;
    }
    if (settings.defaultLocation) {
        document.getElementById('location').value = settings.defaultLocation;
    }
    if (settings.defaultRemoteOnly) {
        document.getElementById('remoteOnly').checked = settings.defaultRemoteOnly;
    }
}

function clearAllData() {
    if (confirm('This will clear all saved jobs and settings. Continue?')) {
        localStorage.clear();
        savedJobs = [];
        showNotification('All data cleared!', 'success');
        updateSavedJobsDisplay();
        loadSettingsValues();
    }
}

// =====================================
// RESUME MATCHER FUNCTIONALITY
// =====================================

async function loadResume() {
    try {
        const response = await fetch('/api/resume');
        const data = await response.json();
        if (data.resume_text) {
            const el = document.getElementById('resumeText');
            if (el) el.value = data.resume_text;
        }
    } catch (e) {
        console.error('Error loading resume:', e);
    }
}

async function saveResume() {
    const text = (document.getElementById('resumeText') || {}).value || '';
    if (!text.trim()) {
        showNotification('Please paste your resume first', 'warning');
        return;
    }
    try {
        const response = await fetch('/api/resume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume_text: text })
        });
        const data = await response.json();
        if (data.status === 'success') {
            showNotification('Resume saved! Scores will update on next scan.', 'success');
            // Auto re-score if we have jobs
            if (allScrapedJobs.length > 0) {
                rescoreJobs();
            }
        }
    } catch (e) {
        console.error('Error saving resume:', e);
        showNotification('Failed to save resume', 'error');
    }
}

// =====================================
// RE-SCORE JOBS WITH CURRENT RESUME
// =====================================

async function rescoreJobs() {
    try {
        showNotification('Re-scoring jobs...', 'info');
        const response = await fetch('/api/rescore', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'success') {
            // Reload jobs to get updated scores
            const jobsResp = await fetch('/api/jobs?sort=match_score');
            const jobsData = await jobsResp.json();
            
            // Update allScrapedJobs and re-render
            allScrapedJobs = jobsData.jobs || [];
            
            // Re-render results
            resultsList.innerHTML = '';
            allScrapedJobs.forEach(job => {
                const card = createJobCard(job);
                resultsList.appendChild(card);
            });
            
            // Update matched jobs tab
            renderMatchedJobs();
            
            showNotification(`Re-scored ${data.rescored} jobs with updated resume!`, 'success');
        } else {
            showNotification(data.error || 'Failed to re-score', 'error');
        }
    } catch(e) {
        console.error('Error re-scoring:', e);
        showNotification('Failed to re-score jobs', 'error');
    }
}

// =====================================
// MATCHED JOBS IN RESUME TAB
// =====================================

function renderMatchedJobs() {
    const container = document.getElementById('matchedJobsList');
    const countEl = document.getElementById('matchedJobsCount');
    const threshold = parseInt(document.getElementById('matchThreshold')?.value || '50');
    const sourceFilter = (document.getElementById('matchFilterSource')?.value || 'all').toLowerCase();
    const workTypeFilter = document.getElementById('matchFilterWorkType')?.value || 'all';
    const appliedFilter = document.getElementById('matchFilterApplied')?.value || 'all';
    
    if (!container) return;
    
    // Get matched jobs above threshold, sorted by score
    let matched = allScrapedJobs
        .filter(j => (j.match_score || 0) >= threshold)
        .sort((a, b) => (b.match_score || 0) - (a.match_score || 0));
    
    // Apply additional filters
    if (sourceFilter !== 'all') {
        matched = matched.filter(j => (j.source || '').toLowerCase() === sourceFilter);
    }
    if (workTypeFilter !== 'all') {
        matched = matched.filter(j => (j.work_type || 'On-site') === workTypeFilter);
    }
    if (appliedFilter !== 'all') {
        if (appliedFilter === 'applied') {
            matched = matched.filter(j => appliedJobs.has(j.url || ''));
        } else {
            matched = matched.filter(j => !appliedJobs.has(j.url || ''));
        }
    }
    
    if (countEl) countEl.textContent = `(${matched.length})`;
    
    // Populate source filter dropdown
    const srcDropdown = document.getElementById('matchFilterSource');
    if (srcDropdown && srcDropdown.options.length <= 1) {
        const sources = [...new Set(allScrapedJobs.map(j => j.source || 'Unknown'))].sort();
        sources.forEach(src => {
            const opt = document.createElement('option');
            opt.value = src.toLowerCase();
            opt.textContent = src;
            srcDropdown.appendChild(opt);
        });
    }
    
    if (matched.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-bullseye fa-3x"></i>
                <h3>No matched jobs${threshold > 0 ? ' above ' + threshold + '%' : ''}</h3>
                <p>Save your resume and run a scan. Top matches will appear here.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    matched.forEach(job => {
        const card = createJobCard(job);
        container.appendChild(card);
    });
}

// =====================================
// DUPES VIEWER
// =====================================

async function showDupesModal() {
    showModal('dupesModal');
    const container = document.getElementById('dupesListContainer');
    container.innerHTML = '<p class="text-muted">Loading duplicates...</p>';
    
    try {
        const response = await fetch('/api/dupes');
        const data = await response.json();
        
        if (!data.dupes || data.dupes.length === 0) {
            container.innerHTML = '<p class="text-muted">No duplicates found yet. Run a scan first.</p>';
            return;
        }
        
        let html = `<p class="text-muted">${data.count} duplicates removed (${data.total_removed} total detections)</p>`;
        html += '<div class="dupes-table">';
        html += '<div class="dupe-header"><span>Job Title</span><span>Company</span><span>Source</span><span>Reason</span></div>';
        
        data.dupes.forEach(dupe => {
            html += `
                <div class="dupe-row">
                    <span class="dupe-title">${escapeHtml(dupe.title || 'Unknown')}</span>
                    <span>${escapeHtml(dupe.company || 'Unknown')}</span>
                    <span class="dupe-source">${escapeHtml(dupe.source || '?')}</span>
                    <span class="dupe-reason">${escapeHtml(dupe.reason || '')}</span>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    } catch(e) {
        container.innerHTML = '<p class="text-muted">Failed to load duplicates</p>';
    }
}

// =====================================
// PAGINATION
// =====================================

function changePage(delta) {
    const allCards = Array.from(resultsList.querySelectorAll('.job-card'));
    const perPage = parseInt(document.getElementById('jobsPerPage')?.value || '50');
    if (perPage <= 0) return; // Show All
    const totalPages = Math.ceil(allCards.length / perPage);
    currentPage = Math.max(1, Math.min(currentPage + delta, totalPages));
    applyPagination();
}

function applyPagination() {
    const allCards = Array.from(resultsList.querySelectorAll('.job-card'));
    const perPage = parseInt(document.getElementById('jobsPerPage')?.value || '50');
    const paginationBar = document.getElementById('pagination');
    
    if (perPage <= 0 || allCards.length <= perPage) {
        // Show all
        allCards.forEach(c => c.style.display = '');
        if (paginationBar) paginationBar.style.display = 'none';
        return;
    }
    
    const totalPages = Math.ceil(allCards.length / perPage);
    currentPage = Math.max(1, Math.min(currentPage, totalPages));
    const start = (currentPage - 1) * perPage;
    const end = start + perPage;
    
    allCards.forEach((card, i) => {
        card.style.display = (i >= start && i < end) ? '' : 'none';
    });
    
    if (paginationBar) {
        paginationBar.style.display = 'flex';
        document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages}`;
        document.getElementById('prevPageBtn').disabled = currentPage <= 1;
        document.getElementById('nextPageBtn').disabled = currentPage >= totalPages;
    }
}

// =====================================
// APPLIED JOBS MODAL
// =====================================

function showAppliedModal() {
    showModal('appliedModal');
    const container = document.getElementById('appliedListContainer');
    const countEl = document.getElementById('appliedModalCount');
    
    if (countEl) countEl.textContent = appliedJobs.size;
    
    if (appliedJobs.size === 0) {
        container.innerHTML = '<p class="text-muted">No jobs marked as applied yet.</p>';
        return;
    }
    
    // Find applied jobs from allScrapedJobs
    const applied = allScrapedJobs.filter(j => appliedJobs.has(j.url || ''));
    
    if (applied.length === 0) {
        // Jobs not in memory — show URLs
        let html = '<div class="dupes-table">';
        html += '<div class="dupe-header"><span>Applied Job URL</span><span>Action</span></div>';
        appliedJobs.forEach(url => {
            html += `
                <div class="dupe-row">
                    <span class="dupe-title"><a href="${escapeHtml(url)}" target="_blank">${escapeHtml(url.substring(0, 80))}...</a></span>
                    <span><button class="btn-sm btn-danger" onclick="toggleApplied('${escapeHtml(url)}'); showAppliedModal();">Remove</button></span>
                </div>`;
        });
        html += '</div>';
        container.innerHTML = html;
        return;
    }
    
    let html = '<div class="dupes-table">';
    html += '<div class="dupe-header"><span>Job Title</span><span>Company</span><span>Score</span><span>Action</span></div>';
    
    applied.forEach(job => {
        const score = job.match_score || 0;
        const scoreClass = score >= 80 ? 'score-excellent' : score >= 50 ? 'score-good' : 'score-low';
        html += `
            <div class="dupe-row">
                <span class="dupe-title"><a href="${escapeHtml(job.url || '#')}" target="_blank">${escapeHtml(job.title || 'Unknown')}</a></span>
                <span>${escapeHtml(job.company || 'Unknown')}</span>
                <span><span class="match-pill ${scoreClass}">${score}%</span></span>
                <span><button class="btn-sm btn-danger" onclick="toggleApplied('${escapeHtml(job.url || '')}'); showAppliedModal();">Remove</button></span>
            </div>`;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// =====================================
// CLICKABLE ANALYTICS — SCORE RANGE FILTER
// =====================================

function filterByScoreRange(minScore) {
    // Switch to search tab and set the score filter
    switchTab('search');
    const scoreFilter = document.getElementById('filterByScore');
    if (scoreFilter) {
        scoreFilter.value = minScore;
        filterJobs();
    }
}

// =====================================
// RESUME OPTIMIZER
// =====================================

function loadOptimizerResume() {
    // Auto-fill from saved resume if optimizer box is empty
    const optimizerBox = document.getElementById('optimizerResume');
    const resumeBox = document.getElementById('resumeText');
    if (optimizerBox && !optimizerBox.value && resumeBox && resumeBox.value) {
        optimizerBox.value = resumeBox.value;
    }
}

async function runOptimizer() {
    const resume = (document.getElementById('optimizerResume')?.value || '').trim();
    const jd = (document.getElementById('optimizerJD')?.value || '').trim();
    
    if (!resume || !jd) {
        showNotification('Please paste both your resume and job description', 'warning');
        return;
    }
    
    showNotification('Analyzing resume...', 'info');
    
    try {
        const response = await fetch('/api/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume_text: resume, job_description: jd })
        });
        const data = await response.json();
        
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }
        
        renderOptimizerResults(data);
        document.getElementById('optimizerResults').style.display = 'block';
        document.getElementById('optimizerResults').scrollIntoView({ behavior: 'smooth' });
        showNotification('Optimization complete!', 'success');
    } catch(e) {
        console.error('Optimizer error:', e);
        showNotification('Optimization failed', 'error');
    }
}

function renderOptimizerResults(data) {
    // ATS & Match Scores
    const atsScore = data.ats_score || 0;
    const matchScore = data.match_score || 0;
    
    document.getElementById('atsScoreVal').textContent = atsScore + '%';
    document.getElementById('matchScoreVal').textContent = matchScore + '%';
    
    const atsRing = document.getElementById('atsScoreRing');
    const matchRing = document.getElementById('matchScoreRing');
    atsRing.className = 'opt-score-ring ' + (atsScore >= 70 ? 'ring-excellent' : atsScore >= 40 ? 'ring-good' : 'ring-low');
    matchRing.className = 'opt-score-ring ' + (matchScore >= 70 ? 'ring-excellent' : matchScore >= 40 ? 'ring-good' : 'ring-low');
    
    document.getElementById('matchedCount').textContent = data.total_matched || 0;
    document.getElementById('missingCount').textContent = (data.missing_skills || []).length;
    
    // === Section Scores (NEW in v2) ===
    const sectionScoresEl = document.getElementById('sectionScoresGrid');
    const secScores = data.suggestions?.section_scores || {};
    if (sectionScoresEl && Object.keys(secScores).length) {
        const labelMap = {hard_skills:'Hard Skills',soft_skills:'Soft Skills',experience:'Experience',formatting:'Formatting',summary:'Summary'};
        let html = '';
        Object.entries(secScores).forEach(([key, score]) => {
            const s = typeof score === 'object' ? score.score : score;
            const lbl = labelMap[key] || key.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
            const cls = s >= 70 ? 'excellent' : s >= 40 ? 'good' : 'low';
            html += `<div class="section-score-item">
                <div class="section-score-bar-bg"><div class="section-score-bar-fill ${cls}" style="width:${s}%"></div></div>
                <span class="section-score-label">${escapeHtml(lbl)}<span class="section-score-val ${cls}">${s}%</span></span>
            </div>`;
        });
        sectionScoresEl.innerHTML = html;
    }
    
    // Matched Skills Tags
    const matchedEl = document.getElementById('matchedSkillsList');
    matchedEl.innerHTML = (data.matched_skills || []).map(s =>
        `<span class="skill-tag skill-matched">${escapeHtml(s)}</span>`
    ).join('') || '<span class="text-muted">None</span>';
    
    // Missing Skills Tags
    const missingEl = document.getElementById('missingSkillsList');
    missingEl.innerHTML = (data.missing_skills || []).map(s =>
        `<span class="skill-tag skill-missing">${escapeHtml(s)}</span>`
    ).join('') || '<span class="text-muted">None — great coverage!</span>';
    
    // === Professional Summary (v2: has current_assessment + options) ===
    const summaryEl = document.getElementById('summaryOptions');
    const summaryData = data.suggestions?.professional_summary || {};
    let summaryHTML = '';
    // Assessment
    if (summaryData.current_assessment) {
        summaryHTML += '<div class="summary-assessment">';
        summaryData.current_assessment.forEach(item => {
            summaryHTML += `<p class="assessment-item">${escapeHtml(item)}</p>`;
        });
        summaryHTML += '</div>';
    }
    // Options
    (summaryData.options || []).forEach(opt => {
        summaryHTML += `<div class="summary-option ${opt.recommended ? 'recommended' : ''}">
            <div class="summary-label">${escapeHtml(opt.label)} ${opt.recommended ? '<span class="rec-badge">Recommended</span>' : ''}</div>
            <div class="summary-text">${escapeHtml(opt.text)}</div>
            ${(opt.tips || []).map(t => `<div class="opt-tip"><i class="fas fa-lightbulb"></i> ${escapeHtml(t)}</div>`).join('')}
            <button class="btn-sm" onclick="navigator.clipboard.writeText(this.closest('.summary-option').querySelector('.summary-text').textContent); showNotification('Copied!', 'success');">
                <i class="fas fa-copy"></i> Copy
            </button>
        </div>`;
    });
    summaryEl.innerHTML = summaryHTML;
    
    // === Hard Skills (v2: categories with copy-paste section) ===
    const techEl = document.getElementById('techSkillsSection');
    const hardSkills = data.suggestions?.hard_skills || {};
    let techHTML = '';
    if (hardSkills.copy_paste_section) {
        techHTML += `<div class="copy-paste-block"><pre>${escapeHtml(hardSkills.copy_paste_section)}</pre>
        <button class="btn-sm" onclick="navigator.clipboard.writeText(this.previousElementSibling.textContent); showNotification('Copied!', 'success');"><i class="fas fa-copy"></i> Copy Skills Section</button></div>`;
    }
    Object.entries(hardSkills.categories || {}).forEach(([category, skills]) => {
        techHTML += `<div class="tech-category"><h4>${escapeHtml(category)}</h4><div class="skill-tags">`;
        skills.forEach(s => {
            const cls = s.status === 'matched' ? 'skill-matched' : (s.priority === 'high' ? 'skill-missing' : 'skill-nice');
            const skillName = s.skill || s.name || '';
            const label = s.status === 'missing' ? `ADD: ${skillName}` : `✓ ${skillName}`;
            techHTML += `<span class="skill-tag ${cls}" title="${s.action || ''}">${escapeHtml(label)}</span>`;
        });
        techHTML += '</div></div>';
    });
    techEl.innerHTML = techHTML || '<p class="text-muted">No technical skills analysis available</p>';
    
    // === Work Experience (v2: dict with rewrites/keyword_bullets/metrics_coaching OR array) ===
    const tipsEl = document.getElementById('experienceTips');
    const rawExp = data.suggestions?.work_experience || {};
    // Normalize: if dict {rewrites, keyword_bullets, metrics_coaching}, convert to array for rendering
    let expTips = [];
    if (Array.isArray(rawExp)) {
        expTips = rawExp;
    } else if (typeof rawExp === 'object') {
        // Convert rewrites to tip cards
        (rawExp.rewrites || []).forEach(r => {
            expTips.push({
                skill: r.skill || 'Resume Bullet',
                action: 'Rewrite generic bullet with quantified impact',
                priority: r.priority || 'high',
                before: r.before,
                after: r.after,
                new_bullet: r.after || '',
            });
        });
        // Add keyword bullets as a single group
        if ((rawExp.keyword_bullets || []).length) {
            expTips.push({
                skill: 'Power Keyword Bullets',
                action: 'Add these quantified bullets to your Experience section',
                priority: 'high',
                keyword_bullets: rawExp.keyword_bullets.map(b => typeof b === 'string' ? {keyword: 'Add', suggestion: b} : b),
            });
        }
        // Add metrics coaching as a single group
        if ((rawExp.metrics_coaching || []).length) {
            expTips.push({
                skill: 'Metrics & Impact Coaching',
                action: 'Replace weak verbs and add quantifiable metrics',
                priority: 'medium',
                examples: rawExp.metrics_coaching,
            });
        }
    }
    let tipsHTML = '';
    expTips.forEach(tip => {
        if (tip.keyword_bullets) {
            // Power keywords group
            tipsHTML += `<div class="experience-tip ${tip.priority}">
                <div class="tip-skill"><i class="fas fa-key"></i> ${escapeHtml(tip.skill)}</div>
                <div class="tip-action">${escapeHtml(tip.action)}</div>
                <div class="kw-bullets">`;
            tip.keyword_bullets.forEach(kb => {
                tipsHTML += `<div class="kw-bullet"><strong>${escapeHtml(kb.keyword)}:</strong> ${escapeHtml(kb.suggestion)}</div>`;
            });
            tipsHTML += '</div></div>';
        } else if (tip.examples) {
            // Metrics coaching
            tipsHTML += `<div class="experience-tip ${tip.priority}">
                <div class="tip-skill"><i class="fas fa-chart-line"></i> ${escapeHtml(tip.skill)}</div>
                <div class="tip-action">${escapeHtml(tip.action)}</div>
                <div class="metric-examples">`;
            tip.examples.forEach(ex => {
                tipsHTML += `<div class="metric-example">${escapeHtml(ex)}</div>`;
            });
            tipsHTML += '</div></div>';
        } else {
            // Standard skill tip with before/after
            tipsHTML += `<div class="experience-tip ${tip.priority}">
                <div class="tip-skill"><span class="priority-badge ${tip.priority}">${tip.priority}</span> ${escapeHtml(tip.skill)}</div>
                <div class="tip-action">${escapeHtml(tip.action)}</div>`;
            if (tip.before) {
                tipsHTML += `<div class="before-after">
                    <div class="before"><strong>Before:</strong> ${escapeHtml(tip.before)}</div>
                    <div class="after"><strong>After:</strong> ${escapeHtml(tip.after)}</div>
                </div>`;
            }
            tipsHTML += `<div class="tip-bullet">${escapeHtml(tip.new_bullet)}</div>
                <button class="btn-sm" onclick="navigator.clipboard.writeText('${escapeHtml(tip.new_bullet).replace(/'/g, "\\'")}'); showNotification('Copied!', 'success');"><i class="fas fa-copy"></i> Copy</button>
            </div>`;
        }
    });
    tipsEl.innerHTML = tipsHTML || '<p class="text-muted">No specific experience tips</p>';
    
    // === Keyword Density (NEW in v2) ===
    const densityEl = document.getElementById('keywordDensity');
    if (densityEl) {
        const density = data.suggestions?.keyword_density || [];
        let densityHTML = '<div class="density-table">';
        densityHTML += '<div class="density-header"><span>Keyword</span><span>In JD</span><span>In Resume</span><span>Status</span></div>';
        density.forEach(row => {
            const cls = row.status === 'ok' ? 'density-ok' : 'density-missing';
            const jdCount = row.jd_count ?? row.in_jd ?? 0;
            const rCount = row.resume_count ?? row.in_resume ?? 0;
            densityHTML += `<div class="density-row ${cls}">
                <span class="density-kw">${escapeHtml(row.keyword)}</span>
                <span>${jdCount}x</span>
                <span>${rCount}x</span>
                <span class="density-rec">${escapeHtml(row.recommendation || '')}</span>
            </div>`;
        });
        densityHTML += '</div>';
        densityEl.innerHTML = densityHTML;
    }
    
    // === Formatting Tips (NEW in v2) ===
    const fmtEl = document.getElementById('formattingTips');
    if (fmtEl) {
        const fmtTips = data.suggestions?.formatting_tips || data.suggestions?.formatting || [];
        let fmtHTML = '';
        fmtTips.forEach(tip => {
            const sev = tip.severity || (tip.passed ? 'pass' : 'medium');
            const icon = sev === 'pass' ? 'fa-check-circle' : sev === 'high' ? 'fa-exclamation-triangle' : 'fa-info-circle';
            const cls = sev === 'pass' ? 'fmt-pass' : sev === 'high' ? 'fmt-high' : 'fmt-medium';
            const label = tip.check || tip.issue || '';
            fmtHTML += `<div class="fmt-tip ${cls}">
                <i class="fas ${icon}"></i>
                <div class="fmt-fix">
                    <strong>${escapeHtml(label)}</strong>
                    ${tip.fix ? `<p style="margin:4px 0 0;"><i class="fas fa-wrench"></i> ${escapeHtml(tip.fix)}</p>` : ''}
                </div>
            </div>`;
        });
        fmtEl.innerHTML = fmtHTML;
    }
    
    // === Soft Skills (NEW in v2) ===
    const softEl = document.getElementById('softSkillsSection');
    if (softEl) {
        const softData = data.suggestions?.soft_skills || {};
        let softHTML = '';
        // Handle dict format: {matched, critical_missing, nice_to_have}
        if (softData.matched || softData.critical_missing || softData.nice_to_have) {
            if (softData.matched && softData.matched.length) {
                softHTML += `<div class="highlight-group reinforce"><h4><i class="fas fa-check" style="color:#10b981;"></i> Found in Your Resume</h4><div class="skill-tags" style="margin-bottom:8px;">`;
                softData.matched.forEach(m => { softHTML += `<span class="skill-tag skill-matched">${escapeHtml(m.keyword || m)}</span>`; });
                softHTML += '</div></div>';
            }
            if (softData.critical_missing && softData.critical_missing.length) {
                softHTML += `<div class="highlight-group critical_gap"><h4><i class="fas fa-exclamation-circle" style="color:#ef4444;"></i> Missing — Add These</h4><div class="skill-tags" style="margin-bottom:8px;">`;
                softData.critical_missing.forEach(m => { softHTML += `<span class="skill-tag skill-missing">${escapeHtml(m.keyword || m)}</span>`; });
                softHTML += '</div>';
                softData.critical_missing.forEach(m => {
                    if (m.how_to_add) softHTML += `<div class="kw-bullet"><i class="fas fa-arrow-right"></i> <strong>${escapeHtml(m.keyword)}:</strong> ${escapeHtml(m.how_to_add)}</div>`;
                });
                softHTML += '</div>';
            }
            if (softData.nice_to_have && softData.nice_to_have.length) {
                softHTML += `<div class="highlight-group nice_to_have"><h4><i class="fas fa-plus-circle" style="color:#f59e0b;"></i> Nice to Have</h4><div class="skill-tags">`;
                softData.nice_to_have.forEach(k => { softHTML += `<span class="skill-tag skill-nice">${escapeHtml(k)}</span>`; });
                softHTML += '</div></div>';
            }
        } else if (Array.isArray(softData)) {
            // Legacy array format
            softData.forEach(item => {
                const borderCls = item.type === 'matched' ? 'reinforce' : item.type === 'critical_missing' ? 'critical_gap' : 'nice_to_have';
                softHTML += `<div class="highlight-group ${borderCls}"><h4>${escapeHtml(item.title)}</h4>
                    <div class="skill-tags">${(item.keywords||[]).map(kw => `<span class="skill-tag">${escapeHtml(kw)}</span>`).join('')}</div></div>`;
            });
        }
        softEl.innerHTML = softHTML || '<p class="text-muted">No soft skill gaps detected</p>';
    }
}

// =====================================
// SCHEDULER / EMAIL
// =====================================

function autoFillEmail() {
    // Auto-fill recipient with sender if empty
    const sender = document.getElementById('senderEmail').value;
    const recipient = document.getElementById('recipientEmail');
    if (recipient && !recipient.value && sender) {
        recipient.value = sender;
    }
}

async function loadScheduleConfig() {
    try {
        const response = await fetch('/api/schedule');
        const config = await response.json();
        
        document.getElementById('scheduleEnabled').checked = config.enabled || false;
        document.getElementById('scheduleTime').value = config.schedule_time || '08:00';
        document.getElementById('scheduleFrequency').value = config.frequency || 'daily';
        document.getElementById('scheduleKeywords').value = (config.keywords || []).join(', ');
        
        const email = config.email || {};
        document.getElementById('senderEmail').value = email.sender || email.username || '';
        document.getElementById('recipientEmail').value = email.to || '';
        if (email.app_password) {
            document.getElementById('appPassword').value = email.app_password;
        } else if (email.password) {
            document.getElementById('appPassword').value = email.password;
        }
        document.getElementById('scheduleFormat').value = config.format || 'html';

        // Show status
        const statusEl = document.getElementById('scheduleStatus');
        if (statusEl) {
            if (config.running) {
                statusEl.innerHTML = '<span style="color:#22c55e;">● Scheduler is ACTIVE</span>';
                if (config.last_run) statusEl.innerHTML += ` — Last run: ${new Date(config.last_run).toLocaleString()}`;
            } else if (config.enabled) {
                statusEl.innerHTML = '<span style="color:#eab308;">● Scheduled but not running yet</span>';
            } else {
                statusEl.innerHTML = '<span style="color:#64748b;">○ Scheduler is off</span>';
            }
        }
    } catch(e) {
        console.error('Error loading schedule config:', e);
    }
}

async function saveSchedule() {
    const keywords = document.getElementById('scheduleKeywords').value
        .split(',').map(k => k.trim()).filter(k => k);
    
    const sender = document.getElementById('senderEmail').value;
    const recipient = document.getElementById('recipientEmail').value || sender;
    const appPw = document.getElementById('appPassword').value;

    const emailConfig = {
        enabled: true,
        to: recipient,
        sender: sender,
        app_password: (appPw && appPw !== '••••••••') ? appPw : '••••••••',
    };
    
    const config = {
        enabled: document.getElementById('scheduleEnabled').checked,
        schedule_time: document.getElementById('scheduleTime').value,
        frequency: document.getElementById('scheduleFrequency').value,
        keywords: keywords,
        email: emailConfig,
        format: document.getElementById('scheduleFormat').value,
    };
    
    try {
        const response = await fetch('/api/schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const data = await response.json();
        showNotification('Schedule saved' + (data.enabled ? ' & activated!' : '!'), 'success');
        loadScheduleConfig(); // Refresh status
    } catch(e) {
        showNotification('Failed to save schedule', 'error');
    }
}

async function testScheduleEmail() {
    await saveSchedule();
    
    const sender = document.getElementById('senderEmail').value;
    const appPw = document.getElementById('appPassword').value;
    if (!sender) {
        showNotification('Enter your Gmail address first', 'error');
        return;
    }
    if (!appPw || appPw === '••••••••') {
        showNotification('Enter your Gmail App Password (16 characters from Google Security)', 'error');
        return;
    }

    showNotification('Sending test email...', 'info');
    try {
        const response = await fetch('/api/schedule/test', { method: 'POST', headers: {'Content-Type':'application/json'}, body: '{}' });
        const data = await response.json();
        if (data.status === 'sent') {
            showNotification(data.message || '✅ Email sent! Check your inbox.', 'success');
        } else {
            showNotification(data.error || 'Email failed. Check your App Password.', 'error');
        }
    } catch(e) {
        showNotification('Test failed: ' + e.message, 'error');
    }
}

async function runScheduleNow() {
    showNotification('Running scrape + email now...', 'info');
    try {
        const response = await fetch('/api/schedule/run', { method: 'POST', headers: {'Content-Type':'application/json'}, body: '{}' });
        const data = await response.json();
        if (data.jobs_found > 0) {
            showNotification(`Found ${data.jobs_found} jobs! ${data.email_sent ? 'Email sent!' : 'Report saved.'}`, 'success');
        } else {
            showNotification('Scrape complete but no jobs matched filters.', 'info');
        }
    } catch(e) {
        showNotification('Run failed: ' + e.message, 'error');
    }
}

/* ===================================== */
/* AI CONTENT GENERATOR                   */
/* ===================================== */

async function generateCoverLetter() {
    const resume = document.getElementById('resumeText')?.value || document.getElementById('optimizerResume')?.value || '';
    const jd = document.getElementById('optimizerJD')?.value || '';
    if (!resume || !jd) { showNotification('Paste your resume (Resume tab) and a job description (Optimizer tab) first', 'error'); return; }
    showNotification('Generating cover letter...', 'info');
    try {
        const res = await fetch('/api/generate/cover-letter', {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({resume_text: resume, job_description: jd})
        });
        const data = await res.json();
        showGeneratorOutput(data.cover_letter);
    } catch(e) { showNotification('Generation failed', 'error'); }
}

async function generateColdMessage() {
    const resume = document.getElementById('resumeText')?.value || document.getElementById('optimizerResume')?.value || '';
    const jd = document.getElementById('optimizerJD')?.value || '';
    if (!jd) { showNotification('Paste a job description in the Optimizer tab first', 'error'); return; }
    showNotification('Generating cold message...', 'info');
    try {
        const res = await fetch('/api/generate/cold-message', {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({resume_text: resume, job_description: jd})
        });
        const data = await res.json();
        showGeneratorOutput(data.message);
    } catch(e) { showNotification('Generation failed', 'error'); }
}

async function generateThankYou() {
    const jd = document.getElementById('optimizerJD')?.value || '';
    if (!jd) { showNotification('Paste a job description in the Optimizer tab first', 'error'); return; }
    showNotification('Generating thank-you email...', 'info');
    try {
        const res = await fetch('/api/generate/thank-you', {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({job_description: jd, interviewer_name: 'Hiring Manager'})
        });
        const data = await res.json();
        showGeneratorOutput(data.email);
    } catch(e) { showNotification('Generation failed', 'error'); }
}

function showGeneratorOutput(text) {
    const box = document.getElementById('generatorOutput');
    const pre = document.getElementById('generatorText');
    if (box && pre) {
        pre.textContent = text;
        box.style.display = 'block';
        box.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }
}

/* ===================================== */
/* MARKET INTELLIGENCE                    */
/* ===================================== */

async function loadMarketIntelligence() {
    const container = document.getElementById('marketIntelContent');
    if (!container) return;
    container.innerHTML = '<p class="text-muted">Loading market data...</p>';
    try {
        const [pulse, skills, sources] = await Promise.all([
            fetch('/api/analytics/market-pulse').then(r => r.json()),
            fetch('/api/analytics/skills').then(r => r.json()),
            fetch('/api/analytics/sources').then(r => r.json())
        ]);
        let html = '';
        // Salary stats
        if (pulse.salary && pulse.salary.stats) {
            const s = pulse.salary.stats;
            html += `<div class="market-card"><h4><i class="fas fa-dollar-sign"></i> Salary Insights</h4>`;
            html += `<p>Average: <strong>$${Math.round(s.average_usd).toLocaleString()}</strong> | Median: <strong>$${Math.round(s.median_usd).toLocaleString()}</strong></p>`;
            html += `<p>Range: $${Math.round(s.p25_usd).toLocaleString()} – $${Math.round(s.p75_usd).toLocaleString()} (25th–75th percentile)</p></div>`;
        }
        // Top skills demand
        if (skills.skills && skills.skills.length) {
            html += `<div class="market-card"><h4><i class="fas fa-fire"></i> Top In-Demand Skills</h4>`;
            const topSkills = skills.skills.slice(0, 12);
            const maxCount = topSkills[0]?.count || 1;
            topSkills.forEach(sk => {
                const pct = Math.round((sk.count / maxCount) * 100);
                html += `<div class="skill-heat-bar"><span style="width:100px;">${sk.skill}</span><div class="bar-bg"><div class="bar-fill" style="width:${pct}%;"></div></div><span>${sk.count}</span></div>`;
            });
            html += `</div>`;
        }
        // Source quality
        if (sources.sources && sources.sources.length) {
            html += `<div class="market-card"><h4><i class="fas fa-chart-bar"></i> Source Quality</h4>`;
            sources.sources.forEach(src => {
                html += `<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;"><span class="source-grade ${src.grade}">${src.grade}</span><span style="flex:1;">${src.source}</span><span class="text-muted">${src.count} jobs</span></div>`;
            });
            html += `</div>`;
        }
        container.innerHTML = html || '<p class="text-muted">Run a search first to generate market intelligence.</p>';
    } catch(e) {
        container.innerHTML = '<p class="text-muted">Failed to load market data.</p>';
    }
}

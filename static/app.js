// Job Scraper Tool - Frontend JavaScript

let eventSource = null;
let isScrapingActive = false;

// DOM Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const exportCsvBtn = document.getElementById('exportCsvBtn');
const exportExcelBtn = document.getElementById('exportExcelBtn');
const jobsList = document.getElementById('jobsList');
const statusText = document.getElementById('statusText');
const jobCount = document.getElementById('jobCount');
const siteStats = document.getElementById('siteStats');
const searchFilter = document.getElementById('searchFilter');

// Event Listeners
startBtn.addEventListener('click', startScraping);
stopBtn.addEventListener('click', stopScraping);
exportCsvBtn.addEventListener('click', () => exportJobs('csv'));
exportExcelBtn.addEventListener('click', () => exportJobs('excel'));
searchFilter.addEventListener('input', filterJobs);

// Start Scraping
async function startScraping() {
    const jobTitle = document.getElementById('jobTitle').value;
    const location = document.getElementById('location').value;
    const remote = document.getElementById('remoteOnly').checked;
    
    // Get selected sites
    const siteCheckboxes = document.querySelectorAll('#siteCheckboxes input:checked');
    const sites = Array.from(siteCheckboxes).map(cb => cb.value);
    
    if (sites.length === 0) {
        alert('Please select at least one job site');
        return;
    }
    
    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                job_title: jobTitle,
                location: location,
                remote: remote,
                sites: sites
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            isScrapingActive = true;
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusText.textContent = 'Scraping...';
            statusText.style.color = '#10b981';
            
            // Clear previous results
            jobsList.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin fa-3x"></i><h3>Searching for jobs...</h3><p>This may take a minute</p></div>';
            
            // Start listening for real-time updates
            connectToEventStream();
            
            // Also poll for status updates
            startStatusPolling();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error starting scraping:', error);
        alert('Failed to start scraping');
    }
}

// Stop Scraping
async function stopScraping() {
    try {
        const response = await fetch('/api/stop', {
            method: 'POST'
        });
        
        if (response.ok) {
            isScrapingActive = false;
            startBtn.disabled = false;
            stopBtn.disabled = true;
            statusText.textContent = 'Stopped';
            statusText.style.color = '#ef4444';
            
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
        }
    } catch (error) {
        console.error('Error stopping scraping:', error);
    }
}

// Connect to Server-Sent Events stream
function connectToEventStream() {
    eventSource = new EventSource('/api/stream');
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.status === 'complete') {
            isScrapingActive = false;
            startBtn.disabled = false;
            stopBtn.disabled = true;
            statusText.textContent = 'Complete!';
            statusText.style.color = '#10b981';
            eventSource.close();
            eventSource = null;
        } else {
            addJobToList(data);
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('EventSource error:', error);
        eventSource.close();
        eventSource = null;
        
        // Fallback to polling
        pollForJobs();
    };
}

// Fallback: Poll for jobs
let pollInterval = null;
function pollForJobs() {
    if (pollInterval) return;
    
    pollInterval = setInterval(async () => {
        if (!isScrapingActive) {
            clearInterval(pollInterval);
            pollInterval = null;
            return;
        }
        
        try {
            const response = await fetch('/api/jobs');
            const data = await response.json();
            
            // Update job list
            if (data.jobs && data.jobs.length > 0) {
                displayJobs(data.jobs);
            }
        } catch (error) {
            console.error('Error polling jobs:', error);
        }
    }, 2000);
}

// Status Polling
let statusInterval = null;
function startStatusPolling() {
    statusInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            jobCount.textContent = data.total_jobs;
            
            // Update site stats
            if (data.sites_scraped) {
                const statsHtml = Object.entries(data.sites_scraped)
                    .map(([site, count]) => `${site}: ${count}`)
                    .join(' | ');
                siteStats.textContent = statsHtml;
            }
            
            if (!data.active) {
                clearInterval(statusInterval);
                statusInterval = null;
                isScrapingActive = false;
                startBtn.disabled = false;
                stopBtn.disabled = true;
                statusText.textContent = 'Complete!';
            }
        } catch (error) {
            console.error('Error fetching status:', error);
        }
    }, 1000);
}

// Add job to list (for real-time updates)
function addJobToList(job) {
    // Remove empty state if present
    const emptyState = jobsList.querySelector('.empty-state');
    if (emptyState) {
        jobsList.innerHTML = '';
    }
    
    const jobCard = createJobCard(job);
    jobsList.insertBefore(jobCard, jobsList.firstChild);
    
    // Update counter
    const currentCount = parseInt(jobCount.textContent) || 0;
    jobCount.textContent = currentCount + 1;
}

// Display all jobs
function displayJobs(jobs) {
    jobsList.innerHTML = '';
    
    if (jobs.length === 0) {
        jobsList.innerHTML = '<div class="empty-state"><i class="fas fa-inbox fa-3x"></i><h3>No jobs found</h3><p>Try adjusting your search criteria</p></div>';
        return;
    }
    
    jobs.forEach(job => {
        const jobCard = createJobCard(job);
        jobsList.appendChild(jobCard);
    });
    
    jobCount.textContent = jobs.length;
}

// Create job card element
function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';
    
    const sourceColor = getSourceColor(job.source);
    
    card.innerHTML = `
        <div class="job-header">
            <div>
                <div class="job-title">${escapeHtml(job.title)}</div>
                <div class="job-company">${escapeHtml(job.company)}</div>
            </div>
            <span class="job-source" style="background: ${sourceColor}; color: white;">
                ${escapeHtml(job.source || 'Unknown')}
            </span>
        </div>
        
        <div class="job-details">
            <div>
                <i class="fas fa-map-marker-alt"></i>
                <span>${escapeHtml(job.location)}</span>
            </div>
            <div>
                <i class="fas fa-clock"></i>
                <span>${escapeHtml(job.posted_date)}</span>
            </div>
            <div>
                <i class="fas fa-briefcase"></i>
                <span>${escapeHtml(job.job_type || 'Full-time')}</span>
            </div>
            ${job.remote ? '<span class="badge badge-remote"><i class="fas fa-home"></i> Remote</span>' : ''}
        </div>
        
        <div class="job-description">
            ${truncateText(escapeHtml(job.description), 200)}
        </div>
        
        <div class="job-footer">
            <div class="job-salary">
                <i class="fas fa-dollar-sign"></i>
                ${escapeHtml(job.salary || 'Not specified')}
            </div>
            <a href="${escapeHtml(job.url)}" target="_blank" class="job-link">
                View Job <i class="fas fa-external-link-alt"></i>
            </a>
        </div>
    `;
    
    return card;
}

// Export jobs
async function exportJobs(format) {
    try {
        const response = await fetch(`/api/export/${format}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `jobs_${Date.now()}.${format === 'csv' ? 'csv' : 'xlsx'}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Error exporting jobs');
        }
    } catch (error) {
        console.error('Error exporting:', error);
        alert('Failed to export jobs');
    }
}

// Filter jobs by search query
function filterJobs() {
    const query = searchFilter.value.toLowerCase();
    const jobCards = jobsList.querySelectorAll('.job-card');
    
    jobCards.forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(query) ? 'block' : 'none';
    });
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
        'remoteok': '#ff4742',
        'weworkremotely': '#5469d4',
        'glassdoor': '#0caa41',
        'linkedin': '#0077b5'
    };
    return colors[source] || '#64748b';
}

// Load available sites on page load
async function loadAvailableSites() {
    try {
        const response = await fetch('/api/sites');
        const data = await response.json();
        
        // Update site checkboxes
        // (Already hardcoded in HTML, but could be dynamic)
    } catch (error) {
        console.error('Error loading sites:', error);
    }
}

// Initialize
loadAvailableSites();

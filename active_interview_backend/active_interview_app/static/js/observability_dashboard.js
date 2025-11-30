/**
 * Observability Dashboard JavaScript
 * Handles chart rendering, data fetching, auto-refresh, and export functionality
 *
 * Related to Issues #14, #15 (Observability Dashboard)
 */

// Get CSS theme variables for charts
const styles = getComputedStyle(document.documentElement);
const textPrimaryColor = styles.getPropertyValue('--text-primary').trim();
const primaryColor = styles.getPropertyValue('--primary').trim();
const primaryLightColor = styles.getPropertyValue('--primary-light').trim();
const accentColor = styles.getPropertyValue('--accent').trim();
const successColor = styles.getPropertyValue('--success').trim();
const errorColor = styles.getPropertyValue('--error').trim();
const warningColor = styles.getPropertyValue('--warning').trim();

// Configure Chart.js defaults
Chart.defaults.color = textPrimaryColor;
Chart.defaults.borderColor = styles.getPropertyValue('--border').trim();

// Global state
let currentTimeRange = '24h';
let autoRefreshInterval = null;
let charts = {
    rps: null,
    latency: null,
    errors: null,
    costs: null
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    setupEventListeners();
    loadAllMetrics();
});

/**
 * Initialize all Chart.js charts
 */
function initializeCharts() {
    // RPS Chart
    const ctxRPS = document.getElementById('chartRPS').getContext('2d');
    charts.rps = new Chart(ctxRPS, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'RPS',
                data: [],
                borderColor: primaryColor,
                backgroundColor: primaryLightColor + '33',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Requests/Second'
                    },
                    beginAtZero: true
                }
            }
        }
    });

    // Latency Chart
    const ctxLatency = document.getElementById('chartLatency').getContext('2d');
    charts.latency = new Chart(ctxLatency, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'p50',
                    data: [],
                    borderColor: accentColor,
                    backgroundColor: accentColor + '33',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'p95',
                    data: [],
                    borderColor: warningColor,
                    backgroundColor: warningColor + '33',
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Latency (ms)'
                    },
                    beginAtZero: true
                }
            }
        }
    });

    // Error Rate Chart
    const ctxErrors = document.getElementById('chartErrors').getContext('2d');
    charts.errors = new Chart(ctxErrors, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Error Rate %',
                data: [],
                borderColor: errorColor,
                backgroundColor: errorColor + '33',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `Error Rate: ${context.parsed.y.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Error Rate (%)'
                    },
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    // Provider Costs Chart
    const ctxCosts = document.getElementById('chartCosts').getContext('2d');
    charts.costs = new Chart(ctxCosts, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Total Cost ($)',
                data: [],
                backgroundColor: successColor,
                borderColor: successColor,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `Cost: $${context.parsed.y.toFixed(4)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Cost (USD)'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Time range selector
    document.querySelectorAll('input[name="timeRange"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            currentTimeRange = e.target.value;
            loadAllMetrics();
        });
    });

    // Refresh button
    document.getElementById('btnRefresh').addEventListener('click', () => {
        loadAllMetrics();
    });

    // Auto-refresh button
    document.getElementById('btnAutoRefresh').addEventListener('click', toggleAutoRefresh);

    // Export button
    document.getElementById('btnExport').addEventListener('click', exportMetrics);

    // Share button
    document.getElementById('btnShare').addEventListener('click', showShareModal);

    // Copy URL button
    document.getElementById('btnCopyUrl').addEventListener('click', copyShareUrl);

    // Configure Cap button (Issue #12)
    document.getElementById('btnConfigureCap').addEventListener('click', showConfigureCapModal);

    // Save Cap button
    document.getElementById('btnSaveCap').addEventListener('click', saveSpendingCap);
}

/**
 * Load all metrics from APIs
 */
async function loadAllMetrics() {
    try {
        await Promise.all([
            loadRPSMetrics(),
            loadLatencyMetrics(),
            loadErrorMetrics(),
            loadCostMetrics(),
            loadSpendingData()  // Issue #11: Monthly Spending Tracker
        ]);

        updateLastUpdatedTime();
    } catch (error) {
        console.error('Error loading metrics:', error);
        alert('Failed to load metrics. Please try again.');
    }
}

/**
 * Load RPS metrics
 */
async function loadRPSMetrics() {
    const response = await fetch(`/admin/observability/api/metrics/rps/?time_range=${currentTimeRange}`);
    const data = await response.json();

    const labels = data.data.map(d => formatTimestamp(d.timestamp));
    const values = data.data.map(d => d.value);

    charts.rps.data.labels = labels;
    charts.rps.data.datasets[0].data = values;
    charts.rps.update();

    // Update summary stat
    const avgRPS = values.length > 0 ? (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2) : '0.00';
    document.getElementById('statAvgRPS').textContent = avgRPS;
}

/**
 * Load latency metrics
 */
async function loadLatencyMetrics() {
    const response = await fetch(`/admin/observability/api/metrics/latency/?time_range=${currentTimeRange}`);
    const data = await response.json();

    const labels = data.data.map(d => formatTimestamp(d.timestamp));
    const p50Values = data.data.map(d => d.p50);
    const p95Values = data.data.map(d => d.p95);

    charts.latency.data.labels = labels;
    charts.latency.data.datasets[0].data = p50Values;
    charts.latency.data.datasets[1].data = p95Values;
    charts.latency.update();

    // Update summary stat
    const avgP95 = p95Values.length > 0 ? (p95Values.reduce((a, b) => a + b, 0) / p95Values.length).toFixed(2) : '0.00';
    document.getElementById('statP95Latency').textContent = avgP95;
}

/**
 * Load error rate metrics
 */
async function loadErrorMetrics() {
    const response = await fetch(`/admin/observability/api/metrics/errors/?time_range=${currentTimeRange}`);
    const data = await response.json();

    const labels = data.data.map(d => formatTimestamp(d.timestamp));
    const values = data.data.map(d => d.error_rate);

    charts.errors.data.labels = labels;
    charts.errors.data.datasets[0].data = values;
    charts.errors.update();

    // Update summary stat
    const avgErrorRate = values.length > 0 ? (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2) : '0.00';
    document.getElementById('statErrorRate').textContent = avgErrorRate + '%';
}

/**
 * Load cost metrics
 */
async function loadCostMetrics() {
    const response = await fetch(`/admin/observability/api/metrics/costs/?time_range=${currentTimeRange}`);
    const data = await response.json();

    const labels = data.data.map(d => d.date);
    const values = data.data.map(d => d.total_cost);

    charts.costs.data.labels = labels;
    charts.costs.data.datasets[0].data = values;
    charts.costs.update();

    // Update summary stat
    const totalCost = values.reduce((a, b) => a + b, 0).toFixed(2);
    document.getElementById('statTotalCost').textContent = '$' + totalCost;
}

/**
 * Toggle auto-refresh
 */
function toggleAutoRefresh() {
    const btn = document.getElementById('btnAutoRefresh');

    if (autoRefreshInterval) {
        // Stop auto-refresh
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        btn.innerHTML = '<i class="fas fa-play"></i> Auto-refresh';
        btn.classList.remove('active');
    } else {
        // Start auto-refresh (every 30 seconds)
        autoRefreshInterval = setInterval(loadAllMetrics, 30000);
        btn.innerHTML = '<i class="fas fa-pause"></i> Auto-refresh';
        btn.classList.add('active');
    }
}

/**
 * Export metrics to CSV
 */
function exportMetrics() {
    const metrics = 'rps,latency,errors,costs';
    const url = `/admin/observability/api/export/?time_range=${currentTimeRange}&metrics=${metrics}`;

    // Trigger download
    window.location.href = url;
}

/**
 * Show share modal
 */
function showShareModal() {
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('time_range', currentTimeRange);

    document.getElementById('shareUrl').value = currentUrl.toString();

    const modal = new bootstrap.Modal(document.getElementById('shareModal'));
    modal.show();
}

/**
 * Copy share URL to clipboard
 */
function copyShareUrl() {
    const input = document.getElementById('shareUrl');
    input.select();
    document.execCommand('copy');

    // Visual feedback
    const btn = document.getElementById('btnCopyUrl');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
    setTimeout(() => {
        btn.innerHTML = originalText;
    }, 2000);
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffHours = (now - date) / (1000 * 60 * 60);

    if (currentTimeRange === '1h') {
        // Show HH:MM for 1 hour range
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } else if (currentTimeRange === '24h') {
        // Show HH:MM for 24 hour range
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } else {
        // Show MM/DD HH:MM for longer ranges
        return date.toLocaleString('en-US', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

/**
 * Update last updated time
 */
function updateLastUpdatedTime() {
    const now = new Date();
    document.getElementById('lastUpdated').textContent = now.toLocaleTimeString();
}

/**
 * Load monthly spending data (Issue #11: Track Monthly Spending)
 */
async function loadSpendingData() {
    try {
        const response = await fetch('/admin/observability/api/spending/current/');
        if (!response.ok) {
            throw new Error('Failed to fetch spending data');
        }
        const data = await response.json();

        // Update month display
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const monthLabel = `${monthNames[data.month - 1]} ${data.year}`;
        document.getElementById('spendingMonth').textContent = monthLabel;

        // Update cost breakdown
        document.getElementById('llmCost').textContent = data.llm_cost.toFixed(2);
        document.getElementById('llmRequests').textContent = data.llm_requests.toLocaleString();
        document.getElementById('ttsCost').textContent = data.tts_cost.toFixed(2);
        document.getElementById('ttsRequests').textContent = data.tts_requests.toLocaleString();
        document.getElementById('otherCost').textContent = data.other_cost.toFixed(2);
        document.getElementById('totalCost').textContent = data.total_cost.toFixed(2);
        document.getElementById('totalRequests').textContent = data.total_requests.toLocaleString();

        // Update spending progress bar and cap info
        const capStatus = data.cap_status;
        if (capStatus.has_cap) {
            const percentage = Math.min(capStatus.percentage, 100);
            const progressBar = document.getElementById('spendingProgress');

            // Update progress bar
            progressBar.style.width = percentage + '%';
            progressBar.setAttribute('aria-valuenow', percentage);
            document.getElementById('spendingPercentage').textContent = percentage.toFixed(1) + '%';

            // Set progress bar color based on alert level
            progressBar.className = 'progress-bar';
            if (capStatus.alert_level === 'danger' || capStatus.is_over_cap) {
                progressBar.classList.add('bg-danger');
            } else if (capStatus.alert_level === 'critical') {
                progressBar.classList.add('bg-warning');
            } else if (capStatus.alert_level === 'warning') {
                progressBar.classList.add('bg-warning');
            } else if (capStatus.alert_level === 'caution') {
                progressBar.classList.add('bg-info');
            } else {
                progressBar.classList.add('bg-success');
            }

            // Update cap and remaining amounts
            document.getElementById('spendingCurrent').textContent = capStatus.spent.toFixed(2);
            document.getElementById('spendingCap').textContent = capStatus.cap_amount.toFixed(2);
            document.getElementById('spendingRemaining').textContent = capStatus.remaining.toFixed(2);

            // Add warning message if over cap
            if (capStatus.is_over_cap) {
                progressBar.style.width = '100%';
                document.getElementById('spendingPercentage').textContent = 'OVER CAP (' + capStatus.percentage.toFixed(1) + '%)';
            }
        } else {
            // No cap set
            document.getElementById('spendingCurrent').textContent = data.total_cost.toFixed(2);
            document.getElementById('spendingCap').textContent = 'Not Set';
            document.getElementById('spendingRemaining').textContent = 'N/A';
            document.getElementById('spendingProgress').style.width = '0%';
            document.getElementById('spendingPercentage').textContent = 'No cap configured';
        }

        // Update last updated time for spending
        const lastUpdated = new Date(data.last_updated);
        document.getElementById('spendingLastUpdated').textContent = lastUpdated.toLocaleString();

    } catch (error) {
        console.error('Error loading spending data:', error);
        // Don't show alert for spending data failures - just log it
        document.getElementById('spendingMonth').textContent = 'Error';
        document.getElementById('spendingCurrent').textContent = '--';
    }
}

/**
 * Show Configure Spending Cap Modal (Issue #12)
 */
function showConfigureCapModal() {
    // Clear previous messages
    document.getElementById('capErrorMessage').classList.add('d-none');
    document.getElementById('capSuccessMessage').classList.add('d-none');

    // Populate current cap information
    const currentCap = document.getElementById('spendingCap').textContent;
    const currentSpending = document.getElementById('spendingCurrent').textContent;
    const currentStatus = document.getElementById('spendingProgress').classList.contains('bg-danger') ? 'Over Cap' :
                         document.getElementById('spendingProgress').classList.contains('bg-warning') ? 'Warning' :
                         document.getElementById('spendingProgress').classList.contains('bg-success') ? 'OK' : 'Unknown';

    document.getElementById('currentCapAmount').textContent = currentCap;
    document.getElementById('currentSpending').textContent = currentSpending;
    document.getElementById('currentStatus').textContent = currentStatus;

    // Set placeholder to current cap if exists
    if (currentCap !== '--' && currentCap !== 'Not Set') {
        document.getElementById('capAmountInput').value = currentCap;
    }

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('configureCapModal'));
    modal.show();
}

/**
 * Save Spending Cap (Issue #12)
 */
async function saveSpendingCap() {
    const capAmountInput = document.getElementById('capAmountInput');
    const errorDiv = document.getElementById('capErrorMessage');
    const successDiv = document.getElementById('capSuccessMessage');
    const saveBtn = document.getElementById('btnSaveCap');

    // Clear previous messages
    errorDiv.classList.add('d-none');
    successDiv.classList.add('d-none');

    // Validate input
    const capAmount = parseFloat(capAmountInput.value);

    if (isNaN(capAmount) || capAmount <= 0) {
        errorDiv.textContent = 'Please enter a valid positive number';
        errorDiv.classList.remove('d-none');
        return;
    }

    // Disable save button while processing
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         getCookie('csrftoken');

        // Make API request
        const response = await fetch('/admin/observability/api/spending/update-cap/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                cap_amount: capAmount
            })
        });

        const data = await response.json();

        if (data.success) {
            // Show success message
            successDiv.textContent = data.message;
            successDiv.classList.remove('d-none');

            // Refresh spending data
            await loadSpendingData();

            // Close modal after 2 seconds
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('configureCapModal'));
                modal.hide();
            }, 2000);
        } else {
            // Show error message
            errorDiv.textContent = data.error || 'Failed to update spending cap';
            errorDiv.classList.remove('d-none');
        }
    } catch (error) {
        console.error('Error saving spending cap:', error);
        errorDiv.textContent = 'An error occurred while saving the cap. Please try again.';
        errorDiv.classList.remove('d-none');
    } finally {
        // Re-enable save button
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Cap';
    }
}

/**
 * Get CSRF token from cookie
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

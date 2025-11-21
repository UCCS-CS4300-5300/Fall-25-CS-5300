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
            loadCostMetrics()
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

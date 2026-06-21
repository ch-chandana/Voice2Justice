document.addEventListener("DOMContentLoaded", () => {
    
    // API Endpoints
    const ENDPOINTS = {
        stats: '/api/dashboard/stats',
        categories: '/api/dashboard/categories',
        trends: '/api/dashboard/trends',
        recent: '/api/dashboard/recent'
    };

    // Global Chart Configuration defaults
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.color = "#6c757d";

    // Reusable fetch function with error handling
    async function fetchData(url) {
        try {
            const response = await fetch(url);
            const data = await response.json();
            if (data.status === 'success') {
                return data.data;
            } else {
                console.error(`API Error (${url}):`, data.message);
                return null;
            }
        } catch (error) {
            console.error(`Network Error (${url}):`, error);
            return null;
        }
    }

    function removeLoading(id) {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    }

    function createEmptyState(containerId, message) {
        const container = document.getElementById(containerId);
        container.innerHTML = `<div class="empty-state"><i class="fa-solid fa-box-open fa-2x mb-2"></i><br>${message}</div>`;
    }

    // 1. Load Stats
    async function loadStats() {
        const data = await fetchData(ENDPOINTS.stats);
        const container = document.getElementById('stats-container');
        document.getElementById('stats-loading').style.display = 'none';

        if (!data) {
            container.innerHTML = '<div class="col-12 text-danger text-center">Failed to load statistics.</div>';
            return;
        }

        container.innerHTML = `
            <div class="col-md-4">
                <div class="card bg-primary text-white h-100 p-4">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-uppercase mb-1 opacity-75">Total Complaints</h6>
                            <h2 class="display-5 fw-bold mb-0">${data.total}</h2>
                        </div>
                        <i class="fa-solid fa-file-lines stat-icon"></i>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-warning text-dark h-100 p-4">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-uppercase mb-1 opacity-75">Open Complaints</h6>
                            <h2 class="display-5 fw-bold mb-0">${data.open}</h2>
                        </div>
                        <i class="fa-solid fa-folder-open stat-icon"></i>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-success text-white h-100 p-4">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-uppercase mb-1 opacity-75">Closed Complaints</h6>
                            <h2 class="display-5 fw-bold mb-0">${data.closed}</h2>
                        </div>
                        <i class="fa-solid fa-check-circle stat-icon"></i>
                    </div>
                </div>
            </div>
        `;
    }

    // 2. Load Trends & Status Distribution
    async function loadTrends() {
        const data = await fetchData(ENDPOINTS.trends);
        removeLoading('trends-loading');
        removeLoading('status-loading');

        if (!data) return;

        // Render Trends Line Chart
        const trends = data.monthly_trends;
        if (trends.length === 0) {
            createEmptyState('trendsChart', 'No trend data available');
        } else {
            const ctxTrends = document.getElementById('trendsChart').getContext('2d');
            new Chart(ctxTrends, {
                type: 'line',
                data: {
                    labels: trends.map(t => t.month),
                    datasets: [{
                        label: 'Complaints',
                        data: trends.map(t => t.count),
                        borderColor: '#4f46e5',
                        backgroundColor: 'rgba(79, 70, 229, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
                }
            });
        }

        // Render Status Bar Chart
        const statusData = data.status_distribution;
        if (statusData.length === 0) {
            createEmptyState('statusChart', 'No status data available');
        } else {
            const ctxStatus = document.getElementById('statusChart').getContext('2d');
            new Chart(ctxStatus, {
                type: 'bar',
                data: {
                    labels: statusData.map(s => s.status),
                    datasets: [{
                        label: 'Count',
                        data: statusData.map(s => s.count),
                        backgroundColor: [
                            'rgba(255, 193, 7, 0.8)', // Warning
                            'rgba(13, 202, 240, 0.8)', // Info
                            'rgba(25, 135, 84, 0.8)', // Success
                            'rgba(220, 53, 69, 0.8)', // Danger
                            'rgba(108, 117, 125, 0.8)' // Secondary
                        ],
                        borderWidth: 0,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
                }
            });
        }
    }

    // 3. Load Categories
    async function loadCategories() {
        const data = await fetchData(ENDPOINTS.categories);
        removeLoading('categories-loading');

        if (!data || data.length === 0) {
            createEmptyState('categoriesChart', 'No category data available');
            return;
        }

        const ctxCat = document.getElementById('categoriesChart').getContext('2d');
        new Chart(ctxCat, {
            type: 'doughnut',
            data: {
                labels: data.map(c => c.category),
                datasets: [{
                    data: data.map(c => c.count),
                    backgroundColor: [
                        '#4f46e5', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                },
                cutout: '70%'
            }
        });
    }

    // 4. Load Recent Complaints Table
    async function loadRecent() {
        const data = await fetchData(ENDPOINTS.recent);
        removeLoading('recent-loading');

        const tbody = document.getElementById('recent-table-body');
        
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No recent complaints found.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(comp => {
            // Determine badge color based on status
            let badgeClass = 'bg-secondary';
            if (['Resolved', 'Closed'].includes(comp.status)) badgeClass = 'bg-success';
            if (['Received', 'Under Review'].includes(comp.status)) badgeClass = 'bg-warning text-dark';
            if (['In Progress', 'Investigating'].includes(comp.status)) badgeClass = 'bg-info text-dark';
            if (comp.status === 'Rejected') badgeClass = 'bg-danger';

            // Format date
            const dateStr = new Date(comp.created_at).toLocaleDateString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric'
            });

            return `
                <tr>
                    <td><span class="font-monospace text-muted">${comp.complaint_number || '#' + comp.id}</span></td>
                    <td class="fw-medium">${comp.user_name || 'Anonymous'}</td>
                    <td>${comp.category || 'N/A'}</td>
                    <td><span class="badge ${badgeClass}">${comp.status}</span></td>
                    <td class="text-muted small">${dateStr}</td>
                    <td>
                        <a href="/report/${comp.id}/pdf" target="_blank"
                           class="btn btn-sm btn-outline-primary" title="Download PDF Report"
                           style="font-size:.75rem;padding:.25rem .5rem;">
                            <i class="fa-solid fa-file-pdf me-1"></i>PDF
                        </a>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // Execute loaders
    loadStats();
    loadTrends();
    loadCategories();
    loadRecent();
});

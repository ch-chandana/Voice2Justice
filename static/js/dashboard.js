/**
 * Voice2Justice — Admin Dashboard JavaScript
 * ===========================================
 * Fetches and renders:
 *   1. Top-level stats (Total / Open / Closed)
 *   2. Fraud & verification intelligence stats
 *   3. Monthly trends chart
 *   4. Status distribution chart
 *   5. Top categories doughnut chart
 *   6. Fraud status doughnut chart
 *   7. Review status doughnut chart
 *   8. Recent complaints table with fraud/verification/review columns
 *   9. Admin review actions (Mark Genuine / Mark Fake)
 */
document.addEventListener("DOMContentLoaded", () => {

    // ── API Endpoints ────────────────────────────────────────────────────
    const ENDPOINTS = {
        stats: '/api/dashboard/stats',
        categories: '/api/dashboard/categories',
        trends: '/api/dashboard/trends',
        recent: '/api/dashboard/recent',
        fraudStats: '/api/dashboard/fraud-stats',
        adminReview: '/api/admin/review'
    };

    // ── Global Chart Defaults ────────────────────────────────────────────
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.color = "#6c757d";

    // ── Helpers ──────────────────────────────────────────────────────────
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
        if (container) {
            container.innerHTML = `<div class="empty-state"><i class="fa-solid fa-box-open fa-2x mb-2"></i><br>${message}</div>`;
        }
    }

    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const id = 'toast-' + Date.now();
        const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
        const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle';
        
        container.insertAdjacentHTML('beforeend', `
            <div id="${id}" class="toast align-items-center text-white ${bgClass} border-0 show" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fa-solid ${icon} me-1"></i> ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `);

        setTimeout(() => {
            const toast = document.getElementById(id);
            if (toast) toast.remove();
        }, 4000);
    }

    // ── 1. Load Stats ────────────────────────────────────────────────────
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
                <div class="card stat-card bg-primary text-white h-100 p-4">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-uppercase mb-1 opacity-75 small">Total Complaints</h6>
                            <h2 class="display-5 fw-bold mb-0">${data.total}</h2>
                        </div>
                        <i class="fa-solid fa-file-lines stat-icon"></i>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card stat-card bg-warning text-dark h-100 p-4">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-uppercase mb-1 opacity-75 small">Open Complaints</h6>
                            <h2 class="display-5 fw-bold mb-0">${data.open}</h2>
                        </div>
                        <i class="fa-solid fa-folder-open stat-icon"></i>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card stat-card bg-success text-white h-100 p-4">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="text-uppercase mb-1 opacity-75 small">Closed Complaints</h6>
                            <h2 class="display-5 fw-bold mb-0">${data.closed}</h2>
                        </div>
                        <i class="fa-solid fa-check-circle stat-icon"></i>
                    </div>
                </div>
            </div>
        `;
    }

    // ── 2. Load Fraud & Verification Stats ───────────────────────────────
    async function loadFraudStats() {
        const data = await fetchData(ENDPOINTS.fraudStats);
        const container = document.getElementById('fraud-stats-container');
        document.getElementById('fraud-stats-loading').style.display = 'none';

        if (!data) {
            container.innerHTML = '<div class="col-12 text-danger text-center small">Failed to load fraud stats.</div>';
            return;
        }

        container.innerHTML = `
            <div class="col-6 col-lg-3">
                <div class="card stat-card h-100 p-3" style="border-left: 4px solid #10b981;">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-muted small fw-bold text-uppercase">Clean</div>
                            <h3 class="fw-bold mb-0 text-success">${data.clean}</h3>
                        </div>
                        <i class="fa-solid fa-shield-check text-success" style="font-size:1.5rem;opacity:0.6;"></i>
                    </div>
                </div>
            </div>
            <div class="col-6 col-lg-3">
                <div class="card stat-card h-100 p-3" style="border-left: 4px solid #f59e0b;">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-muted small fw-bold text-uppercase">Review Required</div>
                            <h3 class="fw-bold mb-0 text-warning">${data.review_required}</h3>
                        </div>
                        <i class="fa-solid fa-eye text-warning" style="font-size:1.5rem;opacity:0.6;"></i>
                    </div>
                </div>
            </div>
            <div class="col-6 col-lg-3">
                <div class="card stat-card h-100 p-3" style="border-left: 4px solid #ef4444;">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-muted small fw-bold text-uppercase">Suspicious</div>
                            <h3 class="fw-bold mb-0 text-danger">${data.suspicious}</h3>
                        </div>
                        <i class="fa-solid fa-triangle-exclamation text-danger" style="font-size:1.5rem;opacity:0.6;"></i>
                    </div>
                </div>
            </div>
            <div class="col-6 col-lg-3">
                <div class="card stat-card h-100 p-3" style="border-left: 4px solid #3b82f6;">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-muted small fw-bold text-uppercase">Verified Users</div>
                            <h3 class="fw-bold mb-0" style="color:#3b82f6;">${data.verified}</h3>
                        </div>
                        <i class="fa-solid fa-user-check" style="font-size:1.5rem;opacity:0.6;color:#3b82f6;"></i>
                    </div>
                </div>
            </div>
            <div class="col-6 col-lg-3 mt-2">
                <div class="card stat-card h-100 p-3" style="border-left: 4px solid #94a3b8;">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-muted small fw-bold text-uppercase">Unverified</div>
                            <h3 class="fw-bold mb-0 text-secondary">${data.unverified}</h3>
                        </div>
                        <i class="fa-solid fa-user-xmark text-secondary" style="font-size:1.5rem;opacity:0.6;"></i>
                    </div>
                </div>
            </div>
            <div class="col-6 col-lg-3 mt-2">
                <div class="card stat-card h-100 p-3" style="border-left: 4px solid #f59e0b;">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-muted small fw-bold text-uppercase">Pending Review</div>
                            <h3 class="fw-bold mb-0 text-warning">${data.pending_review}</h3>
                        </div>
                        <i class="fa-solid fa-hourglass-half text-warning" style="font-size:1.5rem;opacity:0.6;"></i>
                    </div>
                </div>
            </div>
            <div class="col-6 col-lg-3 mt-2">
                <div class="card stat-card h-100 p-3" style="border-left: 4px solid #10b981;">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-muted small fw-bold text-uppercase">Confirmed Genuine</div>
                            <h3 class="fw-bold mb-0 text-success">${data.genuine}</h3>
                        </div>
                        <i class="fa-solid fa-circle-check text-success" style="font-size:1.5rem;opacity:0.6;"></i>
                    </div>
                </div>
            </div>
            <div class="col-6 col-lg-3 mt-2">
                <div class="card stat-card h-100 p-3" style="border-left: 4px solid #ef4444;">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-muted small fw-bold text-uppercase">Confirmed Fake</div>
                            <h3 class="fw-bold mb-0 text-danger">${data.fake}</h3>
                        </div>
                        <i class="fa-solid fa-ban text-danger" style="font-size:1.5rem;opacity:0.6;"></i>
                    </div>
                </div>
            </div>
        `;

        // Render Fraud Status Chart
        renderFraudChart(data);
        // Render Review Status Chart
        renderReviewChart(data);
    }

    // ── Fraud Status Doughnut Chart ──────────────────────────────────────
    function renderFraudChart(data) {
        removeLoading('fraud-chart-loading');
        const total = data.clean + data.review_required + data.suspicious;
        if (total === 0) {
            createEmptyState('fraudChart', 'No fraud data yet');
            return;
        }
        const ctx = document.getElementById('fraudChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Clean', 'Review Required', 'Suspicious'],
                datasets: [{
                    data: [data.clean, data.review_required, data.suspicious],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { font: { size: 11 } } } },
                cutout: '65%'
            }
        });
    }

    // ── Review Status Doughnut Chart ─────────────────────────────────────
    function renderReviewChart(data) {
        removeLoading('review-chart-loading');
        const total = data.pending_review + data.genuine + data.fake;
        if (total === 0) {
            createEmptyState('reviewChart', 'No review data yet');
            return;
        }
        const ctx = document.getElementById('reviewChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Pending', 'Genuine', 'Fake'],
                datasets: [{
                    data: [data.pending_review, data.genuine, data.fake],
                    backgroundColor: ['#94a3b8', '#10b981', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { font: { size: 11 } } } },
                cutout: '65%'
            }
        });
    }

    // ── 3. Load Trends & Status Distribution ─────────────────────────────
    async function loadTrends() {
        const data = await fetchData(ENDPOINTS.trends);
        removeLoading('trends-loading');
        removeLoading('status-loading');

        if (!data) return;

        // Monthly Trends Line Chart
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
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(79, 70, 229, 0.08)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#2563eb',
                        pointRadius: 4
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

        // Status Bar Chart
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
                            'rgba(255, 193, 7, 0.8)',
                            'rgba(13, 202, 240, 0.8)',
                            'rgba(25, 135, 84, 0.8)',
                            'rgba(220, 53, 69, 0.8)',
                            'rgba(108, 117, 125, 0.8)'
                        ],
                        borderWidth: 0,
                        borderRadius: 6
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

    // ── 4. Load Categories ───────────────────────────────────────────────
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
                    backgroundColor: ['#2563eb', '#60a5fa', '#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { font: { size: 11 } } } },
                cutout: '70%'
            }
        });
    }

    // ── 5. Load Recent Complaints (Enhanced with Fraud + Review) ─────────
    async function loadRecent() {
        const data = await fetchData(ENDPOINTS.recent);
        removeLoading('recent-loading');

        const tbody = document.getElementById('recent-table-body');

        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" class="text-center text-muted py-4">No complaints found.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(comp => {
            // Status badge
            let statusBadge = 'badge-soft-secondary';
            if (['Resolved', 'Closed'].includes(comp.status)) statusBadge = 'badge-soft-success';
            if (['Received', 'Under Review'].includes(comp.status)) statusBadge = 'badge-soft-warning';
            if (['In Progress', 'Investigating'].includes(comp.status)) statusBadge = 'badge-soft-info';
            if (comp.status === 'Rejected') statusBadge = 'badge-soft-danger';

            // Fraud score color
            const score = comp.fraud_score || 0;
            let scoreColor = '#10b981';
            if (score >= 0.7) scoreColor = '#ef4444';
            else if (score >= 0.4) scoreColor = '#f59e0b';

            // Fraud status badge
            let fraudBadge = 'badge-soft-success';
            if (comp.fraud_status === 'Review Required') fraudBadge = 'badge-soft-warning';
            if (comp.fraud_status === 'Suspicious') fraudBadge = 'badge-soft-danger';

            // Verification badge
            let verifyBadge = comp.verification_status === 'Verified'
                ? '<span class="badge badge-soft-primary badge-fraud"><i class="fa-solid fa-user-check me-1"></i>Verified</span>'
                : '<span class="badge badge-soft-secondary badge-fraud"><i class="fa-solid fa-user-xmark me-1"></i>Unverified</span>';

            // Review status badge
            let reviewBadge = '';
            const rs = comp.review_status || 'Pending';
            if (rs === 'Genuine') {
                reviewBadge = '<span class="badge badge-soft-success badge-review"><i class="fa-solid fa-check me-1"></i>Genuine</span>';
            } else if (rs === 'Fake') {
                reviewBadge = '<span class="badge badge-soft-danger badge-review"><i class="fa-solid fa-xmark me-1"></i>Fake</span>';
            } else {
                reviewBadge = '<span class="badge badge-soft-secondary badge-review"><i class="fa-solid fa-hourglass-half me-1"></i>Pending</span>';
            }

            // Date
            const dateStr = new Date(comp.created_at).toLocaleDateString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric'
            });

            // Admin action buttons
            const adminActions = `
                <div class="d-flex gap-1" data-complaint-id="${comp.id}">
                    <button class="btn btn-review btn-genuine" onclick="adminReview(${comp.id}, 'Genuine', this)" title="Mark as Genuine">
                        <i class="fa-solid fa-check"></i> Genuine
                    </button>
                    <button class="btn btn-review btn-fake" onclick="adminReview(${comp.id}, 'Fake', this)" title="Mark as Fake">
                        <i class="fa-solid fa-xmark"></i> Fake
                    </button>
                    <button class="btn btn-review btn-pending" onclick="adminReview(${comp.id}, 'Pending', this)" title="Reset to Pending">
                        <i class="fa-solid fa-rotate-left"></i>
                    </button>
                </div>
            `;

            return `
                <tr>
                    <td><span class="font-monospace text-muted small">${comp.complaint_number || '#' + comp.id}</span></td>
                    <td class="fw-medium small">${comp.display_name || 'Anonymous'}</td>
                    <td class="small text-muted">${comp.display_email || 'Unknown'}</td>
                    <td><span class="badge bg-light text-dark border">${comp.user_type || 'Legacy'}</span></td>
                    <td class="small">${comp.category || 'N/A'}</td>
                    <td><span class="badge ${statusBadge}" style="font-size:.68rem;">${comp.status}</span></td>
                    <td>
                        <span class="fw-bold small" style="color:${scoreColor};">${score.toFixed(2)}</span>
                    </td>
                    <td><span class="badge ${fraudBadge} badge-fraud">${comp.fraud_status || 'Clean'}</span></td>
                    <td>${verifyBadge}</td>
                    <td>${reviewBadge}</td>
                    <td class="text-muted" style="font-size:.72rem;">${dateStr}</td>
                    <td>${adminActions}</td>
                    <td>
                        <a href="/report/${comp.id}/pdf" target="_blank"
                           class="btn btn-sm btn-outline-primary" title="Download PDF"
                           style="font-size:.68rem;padding:.2rem .4rem;">
                            <i class="fa-solid fa-file-pdf"></i>
                        </a>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // ── Admin Review Action (Global) ─────────────────────────────────────
    window.adminReview = async function(complaintId, reviewStatus, btn) {
        // Disable all buttons in this row during request
        const row = btn.closest('[data-complaint-id]');
        const buttons = row.querySelectorAll('button');
        buttons.forEach(b => b.disabled = true);

        try {
            const response = await fetch(ENDPOINTS.adminReview, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    complaint_id: complaintId,
                    review_status: reviewStatus
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                showToast(`Complaint #${complaintId} marked as ${reviewStatus}`, 'success');
                // Reload the table to reflect changes
                await loadRecent();
                // Also refresh fraud stats
                await loadFraudStats();
            } else {
                showToast(result.message || 'Failed to update', 'error');
                buttons.forEach(b => b.disabled = false);
            }
        } catch (error) {
            console.error('Admin review error:', error);
            showToast('Network error. Please try again.', 'error');
            buttons.forEach(b => b.disabled = false);
        }
    };

    // ── Execute All Loaders ──────────────────────────────────────────────
    loadStats();
    loadFraudStats();
    loadTrends();
    loadCategories();
    loadRecent();
});

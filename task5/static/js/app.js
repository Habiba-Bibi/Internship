/**
 * SkillBridge AI - Interactive Frontend Controller
 * Chart.js Visualizations, REST API Orchestration, and Interactive Diagnostics.
 */

// Global State
const state = {
    overview: null,
    clusters: null,
    interns: [],
    jobs: [],
    courses: {},
    activeTab: 'overview',
    charts: {}
};

// Color Palette for Clusters (8 distinct vibrant hues)
const CLUSTER_COLORS = [
    { bg: 'rgba(239, 68, 68, 0.75)', border: '#EF4444', name: 'Cybersecurity' },
    { bg: 'rgba(245, 158, 11, 0.75)', border: '#F59E0B', name: 'BI & Analytics' },
    { bg: 'rgba(16, 185, 129, 0.75)', border: '#10B981', name: 'Mobile App Dev' },
    { bg: 'rgba(6, 182, 212, 0.75)', border: '#06B6D4', name: 'Data Engineering' },
    { bg: 'rgba(99, 102, 241, 0.75)', border: '#6366F1', name: 'AI & Machine Learning' },
    { bg: 'rgba(139, 92, 246, 0.75)', border: '#8B5CF6', name: 'Cloud & DevOps' },
    { bg: 'rgba(236, 72, 153, 0.75)', border: '#EC4899', name: 'Embedded & IoT' },
    { bg: 'rgba(59, 130, 246, 0.75)', border: '#3B82F6', name: 'Full Stack Web' }
];

// Presets for the Live Simulator
const SIM_PRESETS = {
    ai: {
        role: "Machine Learning Engineer",
        skills: "Python, scikit-learn, Pandas, NumPy, Data Analysis, SQL, Git, Problem Solving",
        bio: "B.S. in Data Science student with project experience in customer churn prediction and exploratory data analysis."
    },
    web: {
        role: "Full Stack Developer",
        skills: "JavaScript, HTML5, CSS3, React, Git, REST APIs, Problem Solving",
        bio: "Frontend focused computer science candidate with experience building responsive web apps in React."
    },
    cloud: {
        role: "DevOps Engineer",
        skills: "Linux, Bash Scripting, Docker, Git, Networking Basics, Cloud Computing",
        bio: "Systems enthusiast with Linux server administration and basic containerization project experience."
    },
    sec: {
        role: "Cybersecurity Analyst",
        skills: "Linux, Python, Network Security, TCP/IP, Wireshark, Firewalls",
        bio: "Information security student with coursework in ethical hacking, packet inspection, and network defense."
    }
};

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initNavigation();
    initEventListeners();
    loadInitialData();
});

function initTheme() {
    const savedTheme = localStorage.getItem('skillbridge_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeToggleText(savedTheme);

    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('skillbridge_theme', next);
            updateThemeToggleText(next);
            updateAllChartsTheme();
        });
    }
}

function updateThemeToggleText(theme) {
    const txt = document.getElementById('theme-text');
    if (txt) {
        txt.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
    }
}

function initNavigation() {
    const navButtons = document.querySelectorAll('.nav-item');
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
}

function switchTab(tabId) {
    state.activeTab = tabId;

    // Update active nav button
    document.querySelectorAll('.nav-item').forEach(b => {
        b.classList.toggle('active', b.getAttribute('data-tab') === tabId);
    });

    // Update tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `pane-${tabId}`);
    });

    // Lazy load tab data if needed
    if (tabId === 'clusters' && !state.clusters) {
        fetchClusters();
    } else if (tabId === 'interns' && state.interns.length === 0) {
        fetchInterns();
    } else if (tabId === 'jobs' && state.jobs.length === 0) {
        fetchJobs();
    } else if (tabId === 'catalog' && Object.keys(state.courses).length === 0) {
        fetchCourses();
    }

    // Trigger Chart resize
    setTimeout(() => {
        Object.values(state.charts).forEach(c => {
            if (c && typeof c.resize === 'function') c.resize();
        });
    }, 100);
}

function initEventListeners() {
    // Intern search and filter
    const internSearch = document.getElementById('intern-search-input');
    const internDomain = document.getElementById('intern-domain-filter');
    if (internSearch) internSearch.addEventListener('input', debounce(fetchInterns, 300));
    if (internDomain) internDomain.addEventListener('change', fetchInterns);

    // Job search and filter
    const jobSearch = document.getElementById('job-search-input');
    const jobDomain = document.getElementById('job-domain-filter');
    if (jobSearch) jobSearch.addEventListener('input', debounce(fetchJobs, 300));
    if (jobDomain) jobDomain.addEventListener('change', fetchJobs);

    // Catalog search
    const catSearch = document.getElementById('catalog-search-input');
    if (catSearch) catSearch.addEventListener('input', filterCoursesCatalog);
}

function debounce(fn, delay) {
    let timer = null;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

// ============================================================================
// DATA FETCHING & RENDERING
// ============================================================================
async function loadInitialData() {
    await fetchOverview();
    // Pre-fetch clusters for fast exploration
    fetchClusters();
}

async function fetchOverview() {
    try {
        const res = await fetch('/api/overview');
        const json = await res.json();
        if (json.status === 'success') {
            state.overview = json.data;
            renderOverviewKPIs(json.data.summary_metrics);
            renderDemandSupplyChart(json.data.skill_gap_comparison);
            renderDomainDistChart(json.data.domain_stats);
            renderSkillGapTable(json.data.skill_gap_comparison);
        }
    } catch (err) {
        console.error('Error fetching overview:', err);
        showToast('Failed to load market overview', 'error');
    }
}

function renderOverviewKPIs(metrics) {
    if (!metrics) return;
    document.getElementById('kpi-avg-readiness').textContent = `${metrics.average_readiness_score}%`;
    document.getElementById('kpi-high-gap').textContent = metrics.highest_gap_skill;
    document.getElementById('kpi-clusters').textContent = `${metrics.total_clusters} Archetypes`;
}

function renderDemandSupplyChart(comparison) {
    const ctx = document.getElementById('chart-demand-supply');
    if (!ctx) return;

    const labels = comparison.map(c => c.skill);
    const demandData = comparison.map(c => c.industry_demand_pct);
    const supplyData = comparison.map(c => c.intern_supply_pct);

    if (state.charts.demandSupply) {
        state.charts.demandSupply.destroy();
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#94A3B8' : '#475569';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)';

    state.charts.demandSupply = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Industry Demand (%)',
                    data: demandData,
                    backgroundColor: 'rgba(99, 102, 241, 0.85)',
                    borderColor: '#6366F1',
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    label: 'Intern Candidate Supply (%)',
                    data: supplyData,
                    backgroundColor: 'rgba(6, 182, 212, 0.85)',
                    borderColor: '#06B6D4',
                    borderWidth: 1,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                x: {
                    ticks: { color: textColor, font: { family: 'Inter', size: 11 } },
                    grid: { display: false }
                },
                y: {
                    ticks: { color: textColor, callback: v => `${v}%` },
                    grid: { color: gridColor }
                }
            },
            plugins: {
                legend: {
                    labels: { color: textColor, font: { family: 'Inter', weight: 600 } }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.dataset.label}: ${ctx.raw}%`
                    }
                }
            }
        }
    });
}

function renderDomainDistChart(domainStats) {
    const ctx = document.getElementById('chart-domain-dist');
    if (!ctx) return;

    const labels = domainStats.map(d => d.domain);
    const jobCounts = domainStats.map(d => d.job_count);

    if (state.charts.domainDist) {
        state.charts.domainDist.destroy();
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#94A3B8' : '#475569';

    state.charts.domainDist = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: jobCounts,
                backgroundColor: [
                    '#6366F1', '#8B5CF6', '#EC4899', '#F43F5E',
                    '#F59E0B', '#10B981', '#06B6D4', '#3B82F6'
                ],
                borderWidth: isDark ? 2 : 1,
                borderColor: isDark ? '#111827' : '#FFFFFF'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: textColor, font: { family: 'Inter', size: 11 }, boxWidth: 12 }
                }
            }
        }
    });
}

function renderSkillGapTable(comparison) {
    const tbody = document.getElementById('tbody-skill-gaps');
    if (!tbody) return;

    tbody.innerHTML = comparison.map(item => {
        let statusBadge = '';
        if (item.status === 'High Deficit') {
            statusBadge = `<span class="badge badge-danger"><i class="fa-solid fa-triangle-exclamation"></i> High Deficit (${item.gap_pct}%)</span>`;
        } else if (item.status === 'Moderate Deficit') {
            statusBadge = `<span class="badge badge-warning"><i class="fa-solid fa-arrow-down"></i> Deficit (${item.gap_pct}%)</span>`;
        } else {
            statusBadge = `<span class="badge badge-success"><i class="fa-solid fa-check"></i> Balanced/Surplus</span>`;
        }

        const actionText = item.gap_pct > 0 
            ? `Integrate ${item.skill} module into sprint roadmap`
            : `Maintain current elective training level`;

        return `
            <tr>
                <td><strong>${item.skill}</strong></td>
                <td><span class="badge badge-primary">${item.industry_demand_pct}%</span></td>
                <td><span class="badge badge-accent">${item.intern_supply_pct}%</span></td>
                <td><strong class="${item.gap_pct > 0 ? 'text-danger' : 'text-success'}">${item.gap_pct > 0 ? '+' : ''}${item.gap_pct}%</strong></td>
                <td>${statusBadge}</td>
                <td><small style="color: var(--text-secondary)">${actionText}</small></td>
            </tr>
        `;
    }).join('');
}

// ============================================================================
// TAB 2: CLUSTERS & 2D PCA PROJECTION
// ============================================================================
async function fetchClusters() {
    try {
        const res = await fetch('/api/clusters');
        const json = await res.json();
        if (json.status === 'success') {
            state.clusters = json.data;
            renderClusterScatterPlot(json.data);
            renderClusterCards(json.data.clusters);
        }
    } catch (err) {
        console.error('Error fetching clusters:', err);
        showToast('Failed to load cluster data', 'error');
    }
}

function renderClusterScatterPlot(data) {
    const ctx = document.getElementById('chart-pca-clusters');
    if (!ctx) return;

    if (state.charts.pcaScatter) {
        state.charts.pcaScatter.destroy();
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#94A3B8' : '#475569';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)';

    // Group jobs by cluster
    const datasets = [];
    Object.keys(data.clusters).forEach(cId => {
        const idInt = parseInt(cId);
        const col = CLUSTER_COLORS[idInt % CLUSTER_COLORS.length];
        const profile = data.clusters[cId];

        // Jobs dataset
        const clusterJobs = data.jobs_scatter.filter(j => j.cluster_id === idInt);
        datasets.push({
            label: `Cluster ${cId}: ${profile.dominant_domain} (Jobs)`,
            data: clusterJobs.map(j => ({ x: j.x, y: j.y, title: j.title, company: j.company, domain: j.domain, type: 'Job' })),
            backgroundColor: col.bg,
            borderColor: col.border,
            pointRadius: 4.5,
            pointHoverRadius: 7,
            pointStyle: 'circle'
        });

        // Interns dataset
        const clusterInterns = data.interns_scatter.filter(i => i.cluster_id === idInt);
        datasets.push({
            label: `Cluster ${cId}: ${profile.dominant_domain} (Interns)`,
            data: clusterInterns.map(i => ({ x: i.x, y: i.y, name: i.name, role: i.role, domain: i.domain, type: 'Intern' })),
            backgroundColor: col.border,
            borderColor: '#FFFFFF',
            borderWidth: 1,
            pointRadius: 5.5,
            pointHoverRadius: 8,
            pointStyle: 'rectRot'
        });
    });

    state.charts.pcaScatter = new Chart(ctx, {
        type: 'scatter',
        data: { datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Principal Component 1 (PCA X)', color: textColor },
                    ticks: { color: textColor },
                    grid: { color: gridColor }
                },
                y: {
                    title: { display: true, text: 'Principal Component 2 (PCA Y)', color: textColor },
                    ticks: { color: textColor },
                    grid: { color: gridColor }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: textColor,
                        boxWidth: 10,
                        font: { size: 10 },
                        filter: item => item.text.includes('(Jobs)') // simplify legend
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const raw = context.raw;
                            if (raw.type === 'Job') {
                                return `[Job] ${raw.title} @ ${raw.company} (${raw.domain})`;
                            } else {
                                return `[Intern] ${raw.name} - Target: ${raw.role}`;
                            }
                        }
                    }
                }
            }
        }
    });
}

function renderClusterCards(clusters) {
    const container = document.getElementById('cluster-cards-container');
    if (!container) return;

    container.innerHTML = Object.values(clusters).map(c => {
        const topSkillsKeys = Object.keys(c.top_demanded_skills).slice(0, 5);
        const col = CLUSTER_COLORS[c.cluster_id % CLUSTER_COLORS.length];

        return `
            <div class="cluster-card glass-card" style="border-left: 4px solid ${col.border}">
                <div class="cluster-header">
                    <div>
                        <div class="badge badge-primary">Cluster ${c.cluster_id}</div>
                        <h4 class="cluster-title" style="margin-top: 6px;">${c.cluster_name}</h4>
                    </div>
                </div>
                
                <div>
                    <small style="color: var(--text-muted); text-transform: uppercase; font-size: 10px; font-weight: 700;">Top TF-IDF Keywords</small>
                    <div class="cluster-keywords" style="margin-top: 4px;">
                        ${c.top_terms.slice(0, 6).map(t => `<span class="skill-tag">${t}</span>`).join('')}
                    </div>
                </div>

                <div>
                    <small style="color: var(--text-muted); text-transform: uppercase; font-size: 10px; font-weight: 700;">Core Required Skills</small>
                    <div class="cluster-keywords" style="margin-top: 4px;">
                        ${topSkillsKeys.map(s => `<span class="skill-tag matched">${s}</span>`).join('')}
                    </div>
                </div>

                <div class="cluster-meta-row">
                    <span><i class="fa-solid fa-briefcase"></i> ${c.job_count} Jobs</span>
                    <span><i class="fa-solid fa-user-graduate"></i> ${c.intern_count} Interns</span>
                    <span><i class="fa-solid fa-bullseye"></i> ${c.dominant_domain}</span>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================================================
// TAB 3: INTERN TALENT DIRECTORY
// ============================================================================
async function fetchInterns() {
    try {
        const search = document.getElementById('intern-search-input')?.value || '';
        const domain = document.getElementById('intern-domain-filter')?.value || '';

        const url = `/api/interns?search=${encodeURIComponent(search)}&domain=${encodeURIComponent(domain)}`;
        const res = await fetch(url);
        const json = await res.json();
        if (json.status === 'success') {
            state.interns = json.data;
            renderInternsTable(json.data);
        }
    } catch (err) {
        console.error('Error fetching interns:', err);
        showToast('Failed to load interns directory', 'error');
    }
}

function renderInternsTable(interns) {
    const tbody = document.getElementById('tbody-interns');
    if (!tbody) return;

    if (interns.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--text-muted);">No intern records found matching your filters.</td></tr>`;
        return;
    }

    tbody.innerHTML = interns.slice(0, 100).map(intern => `
        <tr>
            <td><code>${intern.intern_id}</code></td>
            <td>
                <strong>${intern.name}</strong>
                <div style="font-size: 11px; color: var(--text-muted)">${intern.email}</div>
            </td>
            <td>
                <div>${intern.university}</div>
                <div style="font-size: 11px; color: var(--text-secondary)">${intern.degree}</div>
            </td>
            <td>
                <span class="badge badge-primary">${intern.target_role}</span>
            </td>
            <td>
                <div style="max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    ${intern.skills.slice(0, 4).map(s => `<span class="skill-tag">${s}</span>`).join('')}
                    ${intern.skills.length > 4 ? `<span class="badge badge-accent">+${intern.skills.length - 4}</span>` : ''}
                </div>
            </td>
            <td>
                <span class="badge badge-accent"><i class="fa-solid fa-shapes"></i> ${intern.cluster_name}</span>
            </td>
            <td>
                <button class="btn-secondary" onclick="openInternModal('${intern.intern_id}')">
                    <i class="fa-solid fa-chart-radar"></i> Analyze Gaps
                </button>
            </td>
        </tr>
    `).join('');
}

// ============================================================================
// INTERN MODAL & GAP ROADMAP
// ============================================================================
async function openInternModal(internId) {
    try {
        const res = await fetch(`/api/intern/${internId}`);
        const json = await res.json();
        if (json.status !== 'success') {
            showToast('Failed to retrieve intern details', 'error');
            return;
        }

        const data = json.data;
        const gap = data.gap_analysis;
        const tp = gap.training_plan;

        document.getElementById('modal-intern-name').textContent = `${data.name} (${data.intern_id})`;
        document.getElementById('modal-intern-meta').innerHTML = `
            <span class="badge badge-primary"><i class="fa-solid fa-graduation-cap"></i> ${data.university}</span>
            <span class="badge badge-accent"><i class="fa-solid fa-briefcase"></i> Target: ${data.target_role}</span>
            <span class="badge badge-success"><i class="fa-solid fa-bullseye"></i> Readiness: ${gap.readiness_score}%</span>
            <span class="badge badge-warning"><i class="fa-solid fa-shapes"></i> ${data.cluster_name}</span>
        `;

        const modalBody = document.getElementById('modal-intern-content');
        modalBody.innerHTML = `
            <!-- Top Match & Radar Section -->
            <div class="grid-2-col" style="margin-bottom: 24px;">
                <div>
                    <h4 style="margin-bottom: 12px; font-family: var(--font-heading);">Competency Spider / Radar Comparison</h4>
                    <div style="position: relative; height: 280px;">
                        <canvas id="chart-modal-radar"></canvas>
                    </div>
                </div>

                <div style="display: flex; flex-direction: column; gap: 16px;">
                    <div style="background: var(--bg-tertiary); padding: 16px; border-radius: var(--radius-md);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 600;">Overall Match Readiness</span>
                            <span class="kpi-value gradient-text" style="font-size: 24px;">${gap.readiness_score}%</span>
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
                            Required Skills Match: ${gap.match_ratio} | Semantic Similarity: ${gap.cosine_similarity}
                        </div>
                    </div>

                    <div>
                        <small style="color: var(--accent-emerald); font-weight: 700; text-transform: uppercase; font-size: 11px;">[+] Matched Skills (${gap.matched_skills.length})</small>
                        <div style="margin-top: 4px;">
                            ${gap.matched_skills.length > 0 ? gap.matched_skills.map(s => `<span class="skill-tag matched"><i class="fa-solid fa-check"></i> ${s}</span>`).join('') : '<span style="color: var(--text-muted); font-size: 12px;">No exact matches</span>'}
                        </div>
                    </div>

                    <div>
                        <small style="color: var(--accent-rose); font-weight: 700; text-transform: uppercase; font-size: 11px;">[-] Missing Critical Skills (${gap.missing_critical_skills.length})</small>
                        <div style="margin-top: 4px;">
                            ${gap.missing_critical_skills.length > 0 ? gap.missing_critical_skills.map(s => `<span class="skill-tag missing"><i class="fa-solid fa-xmark"></i> ${s}</span>`).join('') : '<span style="color: var(--accent-emerald); font-size: 12px;">No critical gaps!</span>'}
                        </div>
                    </div>

                    ${gap.missing_preferred_skills.length > 0 ? `
                        <div>
                            <small style="color: var(--accent-amber); font-weight: 700; text-transform: uppercase; font-size: 11px;">[*] Preferred Bonus Skills (${gap.missing_preferred_skills.length})</small>
                            <div style="margin-top: 4px;">
                                ${gap.missing_preferred_skills.map(s => `<span class="skill-tag preferred">${s}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>

            <!-- 12-Week Training Curriculum -->
            <div style="border-top: 1px solid var(--border-color); padding-top: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div>
                        <h3 style="font-family: var(--font-heading); font-size: 18px;">Personalized 12-Week Upskilling Roadmap</h3>
                        <p style="font-size: 13px; color: var(--text-secondary);">Targeted learning modules designed to elevate readiness score by ${tp.expected_readiness_boost}.</p>
                    </div>
                    <span class="badge badge-success"><i class="fa-solid fa-clock"></i> ${tp.estimated_study_hours} Total Hours</span>
                </div>

                <div class="roadmap-timeline">
                    ${tp.phases.map((phase, idx) => `
                        <div class="phase-card phase-${idx + 1}">
                            <div class="phase-header">
                                <span class="phase-title">${phase.title}</span>
                                <span class="badge badge-primary">${phase.modules.length} Modules</span>
                            </div>
                            <p class="phase-desc">${phase.description}</p>
                            
                            <div class="module-list">
                                ${phase.modules.map(mod => `
                                    <div class="module-item">
                                        <div class="module-header">
                                            <span><strong>${mod.skill}</strong> - ${mod.course_title}</span>
                                            <span class="badge badge-accent">${mod.duration_weeks} Weeks</span>
                                        </div>
                                        <div class="module-sub">
                                            <span><i class="fa-solid fa-laptop-code"></i> Platform: <strong>${mod.platform}</strong></span> |
                                            <span><i class="fa-solid fa-diagram-project"></i> Project: <em>${mod.project}</em></span> |
                                            <span><i class="fa-solid fa-certificate"></i> Cert: ${mod.certification}</span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        document.getElementById('intern-modal').classList.add('active');

        // Render Radar Chart
        setTimeout(() => {
            renderModalRadarChart(data.radar_chart);
        }, 150);

    } catch (err) {
        console.error('Error opening intern modal:', err);
        showToast('Error opening intern modal', 'error');
    }
}

function renderModalRadarChart(radarData) {
    const ctx = document.getElementById('chart-modal-radar');
    if (!ctx) return;

    if (state.charts.modalRadar) {
        state.charts.modalRadar.destroy();
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#94A3B8' : '#475569';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)';

    state.charts.modalRadar = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: radarData.labels,
            datasets: [
                {
                    label: 'Intern Proficiency (0-5)',
                    data: radarData.intern_scores,
                    backgroundColor: 'rgba(99, 102, 241, 0.25)',
                    borderColor: '#6366F1',
                    pointBackgroundColor: '#6366F1',
                    borderWidth: 2
                },
                {
                    label: 'Industry Target Benchmark (4-5)',
                    data: radarData.benchmark_scores,
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    borderColor: '#10B981',
                    pointBackgroundColor: '#10B981',
                    borderWidth: 2,
                    borderDash: [4, 4]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    min: 0,
                    max: 5,
                    ticks: { stepSize: 1, display: false },
                    pointLabels: { color: textColor, font: { family: 'Inter', size: 11, weight: 600 } },
                    grid: { color: gridColor },
                    angleLines: { color: gridColor }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: textColor, font: { size: 11 } }
                }
            }
        }
    });
}

function closeInternModal() {
    document.getElementById('intern-modal').classList.remove('active');
}

function closeModalOnBackdrop(e) {
    if (e.target.id === 'intern-modal') {
        closeInternModal();
    }
}

// ============================================================================
// TAB 4: INDUSTRY JOBS DATABASE
// ============================================================================
async function fetchJobs() {
    try {
        const search = document.getElementById('job-search-input')?.value || '';
        const domain = document.getElementById('job-domain-filter')?.value || '';

        const url = `/api/jobs?search=${encodeURIComponent(search)}&domain=${encodeURIComponent(domain)}`;
        const res = await fetch(url);
        const json = await res.json();
        if (json.status === 'success') {
            state.jobs = json.data;
            renderJobsTable(json.data);
        }
    } catch (err) {
        console.error('Error fetching jobs:', err);
        showToast('Failed to load industry jobs', 'error');
    }
}

function renderJobsTable(jobs) {
    const tbody = document.getElementById('tbody-jobs');
    if (!tbody) return;

    if (jobs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--text-muted);">No job postings found matching your filters.</td></tr>`;
        return;
    }

    tbody.innerHTML = jobs.slice(0, 100).map(job => `
        <tr>
            <td><code>${job.job_id}</code></td>
            <td>
                <strong>${job.job_title}</strong>
                <div style="font-size: 11px; color: var(--text-secondary)">${job.domain}</div>
            </td>
            <td>
                <div>${job.company}</div>
                <div style="font-size: 11px; color: var(--text-muted)">${job.sector}</div>
            </td>
            <td><small><i class="fa-solid fa-location-dot"></i> ${job.location}</small></td>
            <td><span class="badge badge-accent">${job.experience_level}</span></td>
            <td>
                <div style="max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    ${job.required_skills.slice(0, 4).map(s => `<span class="skill-tag matched">${s}</span>`).join('')}
                    ${job.required_skills.length > 4 ? `<span class="badge badge-primary">+${job.required_skills.length - 4}</span>` : ''}
                </div>
            </td>
            <td><strong style="color: var(--accent-emerald); font-size: 12px;">${job.salary_range}</strong></td>
        </tr>
    `).join('');
}

// ============================================================================
// TAB 5: LIVE RESUME / SKILL GAP SIMULATOR
// ============================================================================
function applyPreset(presetKey) {
    const preset = SIM_PRESETS[presetKey];
    if (!preset) return;

    document.getElementById('sim-target-role').value = preset.role;
    document.getElementById('sim-skills-input').value = preset.skills;
    document.getElementById('sim-bio-input').value = preset.bio;
    showToast(`Loaded ${preset.role} preset!`, 'success');
}

async function runCustomAnalysis() {
    const skills = document.getElementById('sim-skills-input').value.trim();
    const role = document.getElementById('sim-target-role').value;
    const bio = document.getElementById('sim-bio-input').value.trim();

    if (!skills && !bio) {
        showToast('Please provide your skills or resume summary', 'error');
        return;
    }

    const btn = document.getElementById('btn-run-sim');
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Analyzing with NLP & K-Means...`;

    try {
        const res = await fetch('/api/analyze-custom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ skills, target_role: role, bio })
        });

        const json = await res.json();
        if (json.status !== 'success') {
            showToast(json.message || 'Analysis failed', 'error');
            return;
        }

        renderSimulatorResults(json.data);
        showToast('Skill gap analysis completed!', 'success');

    } catch (err) {
        console.error('Error running custom analysis:', err);
        showToast('Error executing NLP analysis', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-microchip"></i> Run NLP Skill Gap Analysis`;
    }
}

function renderSimulatorResults(data) {
    const placeholder = document.getElementById('simulator-results-placeholder');
    const container = document.getElementById('simulator-results-content');
    placeholder.classList.add('hidden');
    container.classList.remove('hidden');

    const gap = data.gap_analysis;
    const tp = gap.training_plan;

    container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;">
            <div>
                <span class="badge badge-accent"><i class="fa-solid fa-shapes"></i> ${data.cluster_name}</span>
                <h3 style="font-family: var(--font-heading); font-size: 22px; margin-top: 6px;">Evaluation against: ${data.target_role}</h3>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Match Score</div>
                <div class="kpi-value gradient-text" style="font-size: 28px;">${gap.readiness_score}%</div>
            </div>
        </div>

        <div class="grid-2-col" style="margin-bottom: 20px;">
            <div>
                <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 8px;">Competency Radar vs Benchmark</h4>
                <div style="position: relative; height: 240px;">
                    <canvas id="chart-sim-radar"></canvas>
                </div>
            </div>

            <div style="display: flex; flex-direction: column; gap: 12px;">
                <div>
                    <small style="color: var(--accent-emerald); font-weight: 700; text-transform: uppercase; font-size: 11px;">[+] Confirmed Competencies (${gap.matched_skills.length})</small>
                    <div style="margin-top: 4px;">
                        ${gap.matched_skills.length > 0 ? gap.matched_skills.map(s => `<span class="skill-tag matched"><i class="fa-solid fa-check"></i> ${s}</span>`).join('') : '<span style="color: var(--text-muted); font-size: 12px;">No direct matches found</span>'}
                    </div>
                </div>

                <div>
                    <small style="color: var(--accent-rose); font-weight: 700; text-transform: uppercase; font-size: 11px;">[-] Critical Missing Gaps (${gap.missing_critical_skills.length})</small>
                    <div style="margin-top: 4px;">
                        ${gap.missing_critical_skills.length > 0 ? gap.missing_critical_skills.map(s => `<span class="skill-tag missing"><i class="fa-solid fa-xmark"></i> ${s}</span>`).join('') : '<span style="color: var(--accent-emerald); font-size: 12px;">No critical gaps!</span>'}
                    </div>
                </div>

                <div>
                    <small style="color: var(--accent-amber); font-weight: 700; text-transform: uppercase; font-size: 11px;">[*] Preferred Skills to Excel (${gap.missing_preferred_skills.length})</small>
                    <div style="margin-top: 4px;">
                        ${gap.missing_preferred_skills.map(s => `<span class="skill-tag preferred">${s}</span>`).join('')}
                    </div>
                </div>
            </div>
        </div>

        <!-- Generated Roadmap -->
        <div style="border-top: 1px solid var(--border-color); padding-top: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h4 style="font-family: var(--font-heading); font-size: 16px;">Custom 12-Week Upskilling Roadmap</h4>
                <span class="badge badge-success">${tp.expected_readiness_boost} Expected Boost</span>
            </div>

            <div class="roadmap-timeline">
                ${tp.phases.map((phase, idx) => `
                    <div class="phase-card phase-${idx + 1}">
                        <div class="phase-header">
                            <span class="phase-title">${phase.title}</span>
                            <span class="badge badge-primary">${phase.modules.length} Modules</span>
                        </div>
                        <div class="module-list">
                            ${phase.modules.map(mod => `
                                <div class="module-item">
                                    <div class="module-header">
                                        <span><strong>${mod.skill}</strong> - ${mod.course_title}</span>
                                        <span class="badge badge-accent">${mod.duration_weeks} wks</span>
                                    </div>
                                    <div class="module-sub">
                                        <span><i class="fa-solid fa-laptop-code"></i> ${mod.platform}</span> |
                                        <span><i class="fa-solid fa-diagram-project"></i> Project: <em>${mod.project}</em></span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    // Render Sim Radar
    setTimeout(() => {
        renderSimRadarChart(data.radar_chart);
    }, 150);
}

function renderSimRadarChart(radarData) {
    const ctx = document.getElementById('chart-sim-radar');
    if (!ctx) return;

    if (state.charts.simRadar) {
        state.charts.simRadar.destroy();
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#94A3B8' : '#475569';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)';

    state.charts.simRadar = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: radarData.labels,
            datasets: [
                {
                    label: 'Your Current Level',
                    data: radarData.intern_scores,
                    backgroundColor: 'rgba(99, 102, 241, 0.3)',
                    borderColor: '#6366F1',
                    borderWidth: 2
                },
                {
                    label: 'Target Requirement',
                    data: radarData.benchmark_scores,
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    borderColor: '#10B981',
                    borderWidth: 2,
                    borderDash: [4, 4]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    min: 0,
                    max: 5,
                    ticks: { stepSize: 1, display: false },
                    pointLabels: { color: textColor, font: { family: 'Inter', size: 10, weight: 600 } },
                    grid: { color: gridColor },
                    angleLines: { color: gridColor }
                }
            },
            plugins: {
                legend: { position: 'bottom', labels: { color: textColor, font: { size: 10 } } }
            }
        }
    });
}

// ============================================================================
// TAB 6: TRAINING CATALOG
// ============================================================================
async function fetchCourses() {
    try {
        const res = await fetch('/api/courses');
        const json = await res.json();
        if (json.status === 'success') {
            state.courses = json.data;
            renderCoursesCatalog(json.data);
        }
    } catch (err) {
        console.error('Error fetching courses:', err);
        showToast('Failed to load courses catalog', 'error');
    }
}

function renderCoursesCatalog(courses) {
    const container = document.getElementById('courses-grid-container');
    if (!container) return;

    const entries = Object.entries(courses);
    document.getElementById('catalog-count-badge').textContent = `${entries.length} Courses Available`;

    container.innerHTML = entries.map(([skillName, course]) => `
        <div class="course-card glass-card">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="badge badge-primary">${skillName}</span>
                    <span class="badge badge-accent">${course.duration_weeks} Weeks</span>
                </div>
                <div class="course-platform"><i class="fa-solid fa-graduation-cap"></i> ${course.platform}</div>
                <h3 class="course-title" style="margin-top: 6px;">${course.title}</h3>
            </div>

            <div class="course-project-box">
                <strong style="color: var(--text-primary);"><i class="fa-solid fa-laptop-code"></i> Capstone Project:</strong>
                <p style="margin-top: 4px; color: var(--text-secondary);">${course.project}</p>
            </div>

            <div class="course-cert">
                <i class="fa-solid fa-award"></i>
                <span>${course.certification}</span>
            </div>
        </div>
    `).join('');
}

function filterCoursesCatalog() {
    const q = document.getElementById('catalog-search-input')?.value.toLowerCase() || '';
    const filtered = {};

    Object.entries(state.courses).forEach(([skill, course]) => {
        const text = `${skill} ${course.title} ${course.platform} ${course.project} ${course.certification}`.toLowerCase();
        if (!q || text.includes(q)) {
            filtered[skill] = course;
        }
    });

    renderCoursesCatalog(filtered);
}

// ============================================================================
// UTILITIES: THEME & TOASTS
// ============================================================================
function updateAllChartsTheme() {
    if (state.overview) {
        renderDemandSupplyChart(state.overview.skill_gap_comparison);
        renderDomainDistChart(state.overview.domain_stats);
    }
    if (state.clusters) {
        renderClusterScatterPlot(state.clusters);
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-circle-xmark' : 'fa-circle-info');
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

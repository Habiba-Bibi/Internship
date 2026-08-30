/**
 * InternAI - Frontend Application Logic & State Management
 */

// Application State
const state = {
    candidates: [],
    jobs: [],
    questionBank: [],
    activeKit: null,
    activeScorecard: {
        ratings: {},
        overallNotes: "",
    },
    simState: {
        activeQuestionIndex: 0,
        flatQuestions: [],
        timerSeconds: 300,
        timerInterval: null,
        isTimerRunning: false,
    },
    settings: {
        provider: "mock",
        apiKey: "",
        endpoint: "http://localhost:11434",
        modelName: "",
        temperature: 0.7,
    },
};

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
    initTheme();
    initTabs();
    initSliders();
    initModals();
    initExportDropdown();
    initSettings();
    initSimulator();

    // Load Data
    await loadCandidates();
    await loadJobs();
    await loadQuestionBank();

    // Event Listeners for Dynamic Match Preview
    document.getElementById("candidateSelect").addEventListener("change", updateSkillGapPreview);
    document.getElementById("jobSelect").addEventListener("change", updateSkillGapPreview);
    document.getElementById("generateKitBtn").addEventListener("click", generateInterviewKit);
    document.getElementById("finalizeScorecardBtn").addEventListener("click", finalizeScorecard);
    document.getElementById("launchSimulatorBtn").addEventListener("click", startSimulatorMode);

    // Question Bank Search & Filters
    document.getElementById("bankSearchInput").addEventListener("input", filterQuestionBank);
    document.getElementById("bankCategoryFilter").addEventListener("change", filterQuestionBank);
    document.getElementById("bankDifficultyFilter").addEventListener("change", filterQuestionBank);

    if (window.lucide) {
        lucide.createIcons();
    }
});

// Toast Notifications
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem("internai_theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeIcon(savedTheme);

    document.getElementById("themeToggle").addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme");
        const next = current === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        localStorage.setItem("internai_theme", next);
        updateThemeIcon(next);
    });
}

function updateThemeIcon(theme) {
    const icon = document.getElementById("themeIcon");
    if (theme === "dark") {
        icon.setAttribute("data-lucide", "sun");
    } else {
        icon.setAttribute("data-lucide", "moon");
    }
    if (window.lucide) lucide.createIcons();
}

// Tab Navigation
function initTabs() {
    const navButtons = document.querySelectorAll(".nav-tab");
    navButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const target = btn.getAttribute("data-tab");
            switchTab(target);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll(".nav-tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));

    const btn = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
    const pane = document.getElementById(tabId);

    if (btn) btn.classList.add("active");
    if (pane) pane.classList.add("active");

    if (window.lucide) lucide.createIcons();
}

// Sliders Initialization
function initSliders() {
    const sliders = [
        { id: "numDeepDive", valId: "valDeepDive" },
        { id: "numTechnical", valId: "valTechnical" },
        { id: "numBehavioral", valId: "valBehavioral" },
        { id: "numScenario", valId: "valScenario" },
    ];

    sliders.forEach((s) => {
        const input = document.getElementById(s.id);
        const label = document.getElementById(s.valId);
        input.addEventListener("input", (e) => {
            label.textContent = e.target.value;
        });
    });
}

// Fetch Candidates
async function loadCandidates() {
    try {
        const res = await fetch("/api/candidates");
        if (res.ok) {
            state.candidates = await res.json();
            populateCandidateSelect();
            renderCandidatesList();
        }
    } catch (err) {
        console.error("Error loading candidates:", err);
    }
}

function populateCandidateSelect() {
    const select = document.getElementById("candidateSelect");
    select.innerHTML = '<option value="">-- Select an Intern Candidate Profile --</option>';
    state.candidates.forEach((cand) => {
        const opt = document.createElement("option");
        opt.value = cand.id;
        opt.textContent = `${cand.name} (${cand.target_role || "Intern"})`;
        select.appendChild(opt);
    });

    // Auto select first candidate
    if (state.candidates.length > 0) {
        select.value = state.candidates[0].id;
    }
}

// Fetch Jobs
async function loadJobs() {
    try {
        const res = await fetch("/api/jobs");
        if (res.ok) {
            state.jobs = await res.json();
            populateJobSelect();
            renderJobsList();
            updateSkillGapPreview();
        }
    } catch (err) {
        console.error("Error loading jobs:", err);
    }
}

function populateJobSelect() {
    const select = document.getElementById("jobSelect");
    select.innerHTML = '<option value="">-- Select an Intern Job Description --</option>';
    state.jobs.forEach((job) => {
        const opt = document.createElement("option");
        opt.value = job.id;
        opt.textContent = `${job.title} (${job.department || "Engineering"})`;
        select.appendChild(opt);
    });

    // Auto select first job matching candidate or first job
    if (state.jobs.length > 0) {
        select.value = state.jobs[0].id;
    }
}

// Dynamic Skill Gap Preview
async function updateSkillGapPreview() {
    const candId = document.getElementById("candidateSelect").value;
    const jobId = document.getElementById("jobSelect").value;

    if (!candId || !jobId) {
        document.getElementById("matchScoreVal").textContent = "--%";
        document.getElementById("matchScoreTitle").textContent = "Profile Alignment";
        document.getElementById("matchedSkillsTags").innerHTML = '<span class="tag-empty">Select candidate & job</span>';
        document.getElementById("missingSkillsTags").innerHTML = '<span class="tag-empty">None detected</span>';
        document.getElementById("bonusSkillsTags").innerHTML = '<span class="tag-empty">None</span>';
        return;
    }

    try {
        const res = await fetch("/api/match-analysis", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ candidate_id: candId, job_id: jobId }),
        });

        if (res.ok) {
            const analysis = await res.json();
            renderSkillGap(analysis);
        }
    } catch (err) {
        console.error("Match analysis error:", err);
    }
}

function renderSkillGap(analysis) {
    const scoreVal = analysis.match_score_percentage || 0;
    document.getElementById("matchScoreVal").textContent = `${scoreVal}%`;

    const circle = document.getElementById("scoreCircle");
    circle.style.background = `conic-gradient(var(--primary) ${scoreVal}%, rgba(255,255,255,0.08) ${scoreVal}%)`;

    const candName = state.candidates.find((c) => c.id === document.getElementById("candidateSelect").value)?.name || "Candidate";
    const jobTitle = state.jobs.find((j) => j.id === document.getElementById("jobSelect").value)?.title || "Role";

    document.getElementById("matchScoreTitle").textContent = `${candName} ➔ ${jobTitle}`;
    document.getElementById("matchScoreSubtitle").textContent = `Calculated compatibility based on coursework, project stack, and job requirements.`;

    // Matched skills tags
    const matchedContainer = document.getElementById("matchedSkillsTags");
    if (analysis.matched_skills && analysis.matched_skills.length > 0) {
        matchedContainer.innerHTML = analysis.matched_skills.map((s) => `<span class="tag-pill success">${s}</span>`).join("");
    } else {
        matchedContainer.innerHTML = '<span class="tag-empty">No direct matches found</span>';
    }

    // Missing skills tags
    const missingContainer = document.getElementById("missingSkillsTags");
    const allMissing = [...(analysis.missing_required_skills || []), ...(analysis.missing_preferred_skills || [])];
    if (allMissing.length > 0) {
        missingContainer.innerHTML = allMissing.map((s) => `<span class="tag-pill warning">${s}</span>`).join("");
    } else {
        missingContainer.innerHTML = '<span class="tag-empty">No significant gaps detected</span>';
    }

    // Bonus skills tags
    const bonusContainer = document.getElementById("bonusSkillsTags");
    if (analysis.candidate_unique_strengths && analysis.candidate_unique_strengths.length > 0) {
        bonusContainer.innerHTML = analysis.candidate_unique_strengths.map((s) => `<span class="tag-pill accent">${s}</span>`).join("");
    } else {
        bonusContainer.innerHTML = '<span class="tag-empty">None</span>';
    }

    if (window.lucide) lucide.createIcons();
}

// Generate Full Interview Kit
async function generateInterviewKit() {
    const candId = document.getElementById("candidateSelect").value;
    const jobId = document.getElementById("jobSelect").value;

    if (!candId || !jobId) {
        showToast("Please select both a candidate and a job description first.", "warning");
        return;
    }

    const genBtn = document.getElementById("generateKitBtn");
    const originalBtnText = genBtn.innerHTML;
    genBtn.innerHTML = `<i data-lucide="loader-2" class="spin"></i> <span>Synthesizing Tailored Interview Kit...</span>`;
    genBtn.disabled = true;
    if (window.lucide) lucide.createIcons();

    const payload = {
        candidate_id: candId,
        job_id: jobId,
        num_resume_deep_dive: parseInt(document.getElementById("numDeepDive").value),
        num_technical: parseInt(document.getElementById("numTechnical").value),
        num_behavioral: parseInt(document.getElementById("numBehavioral").value),
        num_scenario: parseInt(document.getElementById("numScenario").value),
        difficulty: document.getElementById("difficultySelect").value,
        llm_provider: document.getElementById("llmProviderSelect").value,
        api_key: state.settings.apiKey,
        model_name: state.settings.modelName,
        temperature: state.settings.temperature,
    };

    try {
        const res = await fetch("/api/generate-kit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (res.ok) {
            const kit = await res.json();
            state.activeKit = kit;
            state.activeScorecard.ratings = {};
            renderInterviewKit(kit);
            switchTab("kit-tab");
            showToast(`✨ Generated ${kit.questions.length} questions for ${kit.candidate_name}!`, "success");
        } else {
            const err = await res.json();
            showToast(`Generation failed: ${err.detail || "Unknown error"}`, "danger");
        }
    } catch (err) {
        console.error("Error generating kit:", err);
        showToast("Server connection error during kit generation.", "danger");
    } finally {
        genBtn.innerHTML = originalBtnText;
        genBtn.disabled = false;
        if (window.lucide) lucide.createIcons();
    }
}

// Render Interview Kit
function renderInterviewKit(kit) {
    // Header info
    document.getElementById("kitRoleBadge").textContent = kit.job_title;
    document.getElementById("kitTimeBadge").innerHTML = `<i data-lucide="clock"></i> ${kit.total_duration_mins} Mins Total`;
    document.getElementById("kitMatchBadge").innerHTML = `<i data-lucide="check-check"></i> ${kit.skill_analysis.match_score_percentage}% Skill Fit`;
    document.getElementById("kitCandidateName").textContent = `${kit.candidate_name} - Interview Kit`;
    document.getElementById("kitMetaDesc").textContent = `Calibrated for ${kit.target_level} level. Target focus areas: ${kit.skill_analysis.recommended_focus_areas.slice(0, 2).join("; ")}`;
    document.getElementById("kitCountBadge").textContent = kit.questions.length;

    // Sections & Questions List
    const listContainer = document.getElementById("kitQuestionsList");
    listContainer.innerHTML = "";

    kit.sections.forEach((sec, sIdx) => {
        const secAccordion = document.createElement("div");
        secAccordion.className = "section-accordion";

        const questionsHtml = sec.questions.map((q, qIdx) => renderQuestionCard(q, sIdx + 1, qIdx + 1)).join("");

        secAccordion.innerHTML = `
            <div class="section-acc-header" onclick="this.parentElement.classList.toggle('collapsed')">
                <h3><i data-lucide="folder-check"></i> ${sec.title}</h3>
                <span class="sec-duration">${sec.duration_mins} mins (${sec.questions.length} Qs)</span>
            </div>
            <div class="section-acc-body">
                ${questionsHtml}
            </div>
        `;
        listContainer.appendChild(secAccordion);
    });

    updateScorecardSidebar();
    if (window.lucide) lucide.createIcons();
}

function renderQuestionCard(q, sNum, qNum) {
    const keyPtsHtml = (q.expected_key_points || []).map((pt, i) => `
        <li>
            <label>
                <input type="checkbox" id="chk_${q.id}_${i}">
                <span>${pt}</span>
            </label>
        </li>
    `).join("");

    const probesHtml = (q.follow_up_probes || []).map((pr) => `<li><em>${pr}</em></li>`).join("");

    return `
    <div class="question-item-card" id="card_${q.id}">
        <div class="q-top-row">
            <div class="q-badges-group">
                <span class="badge-cat">${q.category}</span>
                <span class="badge-diff">${q.difficulty}</span>
                <span class="badge-time-alloc">⏱️ ~${q.time_allocation_mins} mins</span>
                ${q.project_reference ? `<span class="badge-diff">Project: ${q.project_reference}</span>` : ""}
            </div>
            <button class="btn-reroll" onclick="rerollQuestion('${q.id}', '${q.category}', '${q.skills[0] || 'General'}', '${q.difficulty}')">
                <i data-lucide="refresh-cw"></i> Re-roll
            </button>
        </div>

        <h4 class="q-text">Q${sNum}.${qNum}: ${q.question}</h4>

        ${q.context ? `<div class="q-context-box"><strong>Context & Objective:</strong> ${q.context}</div>` : ""}

        <div class="q-grid-eval">
            <div class="q-eval-col">
                <h5>Key Points to Listen For:</h5>
                <ul>${keyPtsHtml}</ul>
            </div>
            <div class="q-eval-col">
                <h5>Follow-up Probing Questions:</h5>
                <ul>${probesHtml}</ul>
            </div>
        </div>

        <div class="rubric-container">
            <div class="rubric-item poor"><strong>🔴 Poor (1-2):</strong> ${q.rubric?.poor || "Fundamental misconceptions."}</div>
            <div class="rubric-item good"><strong>🟡 Good (3-4):</strong> ${q.rubric?.good || "Clear accurate answer."}</div>
            <div class="rubric-item excellent"><strong>🟢 Excellent (5):</strong> ${q.rubric?.excellent || "Exceptional depth."}</div>
        </div>

        <div class="q-scoring-footer">
            <div class="rating-stars-interactive" id="stars_${q.id}">
                <button class="star-btn" onclick="rateQuestion('${q.id}', 1)">1</button>
                <button class="star-btn" onclick="rateQuestion('${q.id}', 2)">2</button>
                <button class="star-btn" onclick="rateQuestion('${q.id}', 3)">3</button>
                <button class="star-btn" onclick="rateQuestion('${q.id}', 4)">4</button>
                <button class="star-btn" onclick="rateQuestion('${q.id}', 5)">5</button>
            </div>
            <input type="text" class="q-inline-note" id="note_${q.id}" placeholder="Quick candidate observation notes..." oninput="updateQuestionNote('${q.id}', this.value)">
        </div>
    </div>
    `;
}

// Rate Single Question
function rateQuestion(qId, score) {
    state.activeScorecard.ratings[qId] = {
        question_id: qId,
        score: score,
        notes: document.getElementById(`note_${qId}`)?.value || "",
    };

    // Update active class on star buttons
    const starContainer = document.getElementById(`stars_${qId}`);
    if (starContainer) {
        starContainer.querySelectorAll(".star-btn").forEach((btn, idx) => {
            if (idx + 1 === score) {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });
    }

    updateScorecardSidebar();
}

function updateQuestionNote(qId, note) {
    if (state.activeScorecard.ratings[qId]) {
        state.activeScorecard.ratings[qId].notes = note;
    }
}

// Re-roll / Regenerate Single Question
async function rerollQuestion(qId, category, skill, difficulty) {
    const card = document.getElementById(`card_${qId}`);
    if (!card) return;
    card.style.opacity = "0.5";

    try {
        const res = await fetch("/api/regenerate-question", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                category: category,
                domain: "Core Engineering",
                skill: skill,
                difficulty: difficulty,
                candidate_name: state.activeKit?.candidate_name || "Candidate",
                job_title: state.activeKit?.job_title || "Engineering Intern",
            }),
        });

        if (res.ok) {
            const newQ = await res.json();
            // Update in active kit
            if (state.activeKit) {
                for (let sec of state.activeKit.sections) {
                    const idx = sec.questions.findIndex((q) => q.id === qId);
                    if (idx !== -1) {
                        sec.questions[idx] = newQ;
                        break;
                    }
                }
                renderInterviewKit(state.activeKit);
                showToast("Question re-rolled with fresh context!", "success");
            }
        }
    } catch (err) {
        console.error("Error re-rolling question:", err);
        showToast("Failed to re-roll question.", "danger");
    } finally {
        card.style.opacity = "1";
    }
}

// Update Scorecard Sidebar
function updateScorecardSidebar() {
    const ratings = Object.values(state.activeScorecard.ratings);
    const totalQuestions = state.activeKit?.questions?.length || 0;
    const ratedCount = ratings.length;

    let avg = 0;
    if (ratedCount > 0) {
        const sum = ratings.reduce((acc, r) => acc + r.score, 0);
        avg = (sum / ratedCount).toFixed(1);
    }

    document.getElementById("liveAvgScore").textContent = avg;
    document.getElementById("evaluatedCount").textContent = `${ratedCount} / ${totalQuestions} Questions Rated`;

    const progressPct = totalQuestions > 0 ? (ratedCount / totalQuestions) * 100 : 0;
    document.getElementById("scorecardProgress").style.width = `${progressPct}%`;

    // Stars display
    const roundedStars = Math.round(avg);
    document.getElementById("liveScoreStars").textContent = "★".repeat(roundedStars) + "☆".repeat(5 - roundedStars);

    // Recommendation badge
    const badge = document.getElementById("liveRecBadge");
    if (ratedCount === 0) {
        badge.className = "recommendation-badge badge-neutral";
        badge.textContent = "Undecided";
    } else if (avg >= 4.5) {
        badge.className = "recommendation-badge badge-strong-hire";
        badge.textContent = "Strong Hire";
    } else if (avg >= 3.5) {
        badge.className = "recommendation-badge badge-hire";
        badge.textContent = "Hire";
    } else if (avg >= 2.8) {
        badge.className = "recommendation-badge badge-leaning";
        badge.textContent = "Leaning Hire";
    } else {
        badge.className = "recommendation-badge badge-no-hire";
        badge.textContent = "No Hire";
    }
}

// Finalize Scorecard
async function finalizeScorecard() {
    if (!state.activeKit) {
        showToast("Please generate an interview kit first.", "warning");
        return;
    }

    const ratings = Object.values(state.activeScorecard.ratings);
    if (ratings.length === 0) {
        showToast("Please rate at least one question before finalizing.", "warning");
        return;
    }

    const overallNotes = document.getElementById("overallNotes").value;

    const payload = {
        kit_id: state.activeKit.id,
        candidate_name: state.activeKit.candidate_name,
        job_title: state.activeKit.job_title,
        ratings: ratings,
        final_feedback: overallNotes,
    };

    try {
        const res = await fetch("/api/scorecard", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (res.ok) {
            const sc = await res.json();
            renderScorecardResultModal(sc);
        }
    } catch (err) {
        console.error("Error submitting scorecard:", err);
        showToast("Failed to finalize scorecard.", "danger");
    }
}

function renderScorecardResultModal(sc) {
    const body = document.getElementById("scorecardResultBody");
    body.innerHTML = `
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div style="font-size: 3rem; font-weight: 800; color: var(--primary);">${sc.overall_score} / 5.0</div>
            <div class="recommendation-badge ${sc.overall_score >= 3.5 ? 'badge-strong-hire' : 'badge-no-hire'}" style="font-size: 1rem; padding: 6px 20px;">
                ${sc.recommendation}
            </div>
            <h3 style="margin-top: 10px;">${sc.candidate_name} - ${sc.job_title}</h3>
            <p style="color: var(--text-muted); font-size: 0.88rem;">Evaluated on ${sc.date} | Questions Evaluated: ${sc.ratings.length}</p>
        </div>

        <div style="background: var(--bg-surface-elevated); padding: 14px; border-radius: 8px; margin-bottom: 1rem;">
            <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--text-faint); margin-bottom: 6px;">Interviewer Notes:</h4>
            <p style="font-size: 0.9rem;">${sc.final_feedback || "No general notes recorded."}</p>
        </div>

        <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--text-faint); margin-bottom: 8px;">Detailed Question Breakdown:</h4>
        <div style="display: flex; flex-direction: column; gap: 6px;">
            ${sc.ratings.map((r, i) => `
                <div style="display: flex; justify-content: space-between; padding: 8px; background: var(--bg-surface); border-radius: 6px; font-size: 0.85rem;">
                    <span><strong>Q${i+1} (${r.question_id}):</strong> ${r.notes || "No notes"}</span>
                    <span style="font-weight: 700; color: var(--primary);">Score: ${r.score} / 5</span>
                </div>
            `).join("")}
        </div>
    `;

    document.getElementById("scorecardResultModal").classList.add("active");
    if (window.lucide) lucide.createIcons();
}

// Export Dropdown
function initExportDropdown() {
    const menuBtn = document.getElementById("exportMenuBtn");
    const dropdown = document.getElementById("exportDropdown");

    menuBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        dropdown.classList.toggle("show");
    });

    document.addEventListener("click", () => {
        dropdown.classList.remove("show");
    });

    dropdown.querySelectorAll("button").forEach((btn) => {
        btn.addEventListener("click", () => {
            const format = btn.getAttribute("data-format");
            if (!state.activeKit) {
                showToast("Please generate an interview kit first.", "warning");
                return;
            }
            window.open(`/api/export/${state.activeKit.id}?format=${format}`, "_blank");
        });
    });
}

// Question Bank Explorer
async function loadQuestionBank() {
    try {
        const res = await fetch("/api/questions");
        if (res.ok) {
            state.questionBank = await res.json();
            renderQuestionBank(state.questionBank);
        }
    } catch (err) {
        console.error("Error loading question bank:", err);
    }
}

function renderQuestionBank(questions) {
    const grid = document.getElementById("bankQuestionsGrid");
    grid.innerHTML = "";

    if (questions.length === 0) {
        grid.innerHTML = `<div class="empty-state" style="grid-column: 1/-1;"><p>No questions match your filter criteria.</p></div>`;
        return;
    }

    questions.forEach((q) => {
        const card = document.createElement("div");
        card.className = "bank-card";
        card.innerHTML = `
            <div>
                <div class="bank-card-header">
                    <span class="badge-cat">${q.category}</span>
                    <span class="badge-diff">${q.difficulty}</span>
                </div>
                <h4>${q.question}</h4>
                <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 8px;">${q.context}</p>
                <div class="bank-card-skills">
                    ${(q.skills || []).map((s) => `<span class="tag-pill success">${s}</span>`).join("")}
                </div>
            </div>
            <div class="bank-card-footer">
                <span>⏱️ ~${q.time_allocation_mins}m</span>
                <span>Domain: ${q.domain}</span>
            </div>
        `;
        grid.appendChild(card);
    });

    if (window.lucide) lucide.createIcons();
}

function filterQuestionBank() {
    const query = document.getElementById("bankSearchInput").value.toLowerCase();
    const category = document.getElementById("bankCategoryFilter").value;
    const difficulty = document.getElementById("bankDifficultyFilter").value;

    let filtered = state.questionBank;

    if (category !== "all") {
        filtered = filtered.filter((q) => q.category.toLowerCase() === category.toLowerCase());
    }

    if (difficulty !== "all") {
        filtered = filtered.filter((q) => q.difficulty.toLowerCase() === difficulty.toLowerCase());
    }

    if (query) {
        filtered = filtered.filter(
            (q) =>
                q.question.toLowerCase().includes(query) ||
                q.context.toLowerCase().includes(query) ||
                q.domain.toLowerCase().includes(query) ||
                (q.skills || []).some((s) => s.toLowerCase().includes(query))
        );
    }

    renderQuestionBank(filtered);
}

// Candidate & Job Profiles Lists
function renderCandidatesList() {
    const list = document.getElementById("candidatesCardsList");
    list.innerHTML = "";
    state.candidates.forEach((cand) => {
        const card = document.createElement("div");
        card.className = "profile-card-item";
        card.innerHTML = `
            <h4>${cand.name}</h4>
            <p><strong>Target:</strong> ${cand.target_role || "Engineering Intern"} | <strong>Degree:</strong> ${cand.education?.degree || "CS"}</p>
            <div class="tags-container" style="margin-top: 6px;">
                ${(cand.skills?.languages || []).slice(0, 3).map((l) => `<span class="tag-pill success">${l}</span>`).join("")}
                ${(cand.skills?.frameworks || []).slice(0, 3).map((f) => `<span class="tag-pill accent">${f}</span>`).join("")}
            </div>
        `;
        list.appendChild(card);
    });
}

function renderJobsList() {
    const list = document.getElementById("jobsCardsList");
    list.innerHTML = "";
    state.jobs.forEach((job) => {
        const card = document.createElement("div");
        card.className = "profile-card-item";
        card.innerHTML = `
            <h4>${job.title}</h4>
            <p><strong>Department:</strong> ${job.department || "Core Product"} | <strong>Duration:</strong> ${job.duration || "12 Weeks"}</p>
            <div class="tags-container" style="margin-top: 6px;">
                ${(job.required_skills || []).slice(0, 4).map((r) => `<span class="tag-pill warning">${r.slice(0, 25)}</span>`).join("")}
            </div>
        `;
        list.appendChild(card);
    });
}

// Live Mock Simulator
function initSimulator() {
    document.getElementById("timerStartBtn").addEventListener("click", toggleTimer);
    document.getElementById("timerResetBtn").addEventListener("click", resetTimer);
    document.getElementById("simPrevBtn").addEventListener("click", () => navigateSimQuestion(-1));
    document.getElementById("simNextBtn").addEventListener("click", () => navigateSimQuestion(1));
    document.getElementById("exitSimBtn").addEventListener("click", () => switchTab("kit-tab"));

    // Simulator score buttons
    document.querySelectorAll(".sim-score-selector .score-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const score = parseInt(btn.getAttribute("data-score"));
            const curQ = state.simState.flatQuestions[state.simState.activeQuestionIndex];
            if (curQ) {
                rateQuestion(curQ.id, score);
                document.querySelectorAll(".sim-score-selector .score-btn").forEach((b) => b.classList.remove("active"));
                btn.classList.add("active");
            }
        });
    });
}

function startSimulatorMode() {
    if (!state.activeKit || !state.activeKit.questions || state.activeKit.questions.length === 0) {
        showToast("Please generate an interview kit first.", "warning");
        return;
    }

    state.simState.flatQuestions = state.activeKit.questions;
    state.simState.activeQuestionIndex = 0;
    document.getElementById("simCandidateName").textContent = `${state.activeKit.candidate_name}`;
    document.getElementById("simRoleLabel").textContent = `Role: ${state.activeKit.job_title}`;

    loadSimQuestion(0);
    resetTimer();
    switchTab("simulator-tab");
}

function loadSimQuestion(idx) {
    if (idx < 0 || idx >= state.simState.flatQuestions.length) return;
    state.simState.activeQuestionIndex = idx;
    const q = state.simState.flatQuestions[idx];

    document.getElementById("simCategoryBadge").textContent = q.category;
    document.getElementById("simDiffBadge").textContent = q.difficulty;
    document.getElementById("simIndexBadge").textContent = `Question ${idx + 1} of ${state.simState.flatQuestions.length}`;
    document.getElementById("simQuestionText").textContent = q.question;

    const kpList = document.getElementById("simKeyPointsList");
    kpList.innerHTML = (q.expected_key_points || []).map((pt) => `<li>${pt}</li>`).join("") || "<li>Evaluate core understanding and trade-offs.</li>";

    const prList = document.getElementById("simProbesList");
    prList.innerHTML = (q.follow_up_probes || []).map((pr) => `<li><em>${pr}</em></li>`).join("") || "<li>No specific follow-up probes.</li>";

    // Set existing rating if any
    const existingScore = state.activeScorecard.ratings[q.id]?.score;
    document.querySelectorAll(".sim-score-selector .score-btn").forEach((b) => {
        if (parseInt(b.getAttribute("data-score")) === existingScore) {
            b.classList.add("active");
        } else {
            b.classList.remove("active");
        }
    });

    // Scratchpad notes
    document.getElementById("simNotes").value = state.activeScorecard.ratings[q.id]?.notes || "";

    // Reset question timer to allocated time
    state.simState.timerSeconds = (q.time_allocation_mins || 5) * 60;
    updateTimerDisplay();
}

function navigateSimQuestion(direction) {
    // Save current notes
    const curQ = state.simState.flatQuestions[state.simState.activeQuestionIndex];
    if (curQ) {
        const notes = document.getElementById("simNotes").value;
        if (!state.activeScorecard.ratings[curQ.id]) {
            state.activeScorecard.ratings[curQ.id] = { question_id: curQ.id, score: 3, notes: notes };
        } else {
            state.activeScorecard.ratings[curQ.id].notes = notes;
        }
    }

    const nextIdx = state.simState.activeQuestionIndex + direction;
    if (nextIdx >= 0 && nextIdx < state.simState.flatQuestions.length) {
        loadSimQuestion(nextIdx);
    } else if (nextIdx >= state.simState.flatQuestions.length) {
        showToast("You have reached the end of the interview kit!", "success");
        finalizeScorecard();
    }
}

function toggleTimer() {
    if (state.simState.isTimerRunning) {
        clearInterval(state.simState.timerInterval);
        state.simState.isTimerRunning = false;
        document.getElementById("timerPlayIcon").setAttribute("data-lucide", "play");
    } else {
        state.simState.isTimerRunning = true;
        document.getElementById("timerPlayIcon").setAttribute("data-lucide", "pause");
        state.simState.timerInterval = setInterval(() => {
            if (state.simState.timerSeconds > 0) {
                state.simState.timerSeconds--;
                updateTimerDisplay();
            } else {
                clearInterval(state.simState.timerInterval);
                state.simState.isTimerRunning = false;
                document.getElementById("timerPlayIcon").setAttribute("data-lucide", "play");
                showToast("⏱️ Time allocated for this question has expired!", "warning");
            }
        }, 1000);
    }
    if (window.lucide) lucide.createIcons();
}

function resetTimer() {
    clearInterval(state.simState.timerInterval);
    state.simState.isTimerRunning = false;
    document.getElementById("timerPlayIcon").setAttribute("data-lucide", "play");
    const curQ = state.simState.flatQuestions[state.simState.activeQuestionIndex];
    state.simState.timerSeconds = (curQ?.time_allocation_mins || 5) * 60;
    updateTimerDisplay();
    if (window.lucide) lucide.createIcons();
}

function updateTimerDisplay() {
    const mins = Math.floor(state.simState.timerSeconds / 60);
    const secs = state.simState.timerSeconds % 60;
    document.getElementById("timerDisplay").textContent = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

// Modals
function initModals() {
    // Custom Candidate Modal
    document.getElementById("customCandBtn").addEventListener("click", () => {
        document.getElementById("customCandModal").classList.add("active");
    });
    document.getElementById("closeCandModal").addEventListener("click", () => {
        document.getElementById("customCandModal").classList.remove("active");
    });
    document.getElementById("cancelCandModal").addEventListener("click", () => {
        document.getElementById("customCandModal").classList.remove("active");
    });
    document.getElementById("saveCustomCandBtn").addEventListener("click", saveCustomCandidate);

    // Custom Job Modal
    document.getElementById("customJobBtn").addEventListener("click", () => {
        document.getElementById("customJobModal").classList.add("active");
    });
    document.getElementById("closeJobModal").addEventListener("click", () => {
        document.getElementById("customJobModal").classList.remove("active");
    });
    document.getElementById("cancelJobModal").addEventListener("click", () => {
        document.getElementById("customJobModal").classList.remove("active");
    });
    document.getElementById("saveCustomJobBtn").addEventListener("click", saveCustomJob);

    // Add Question Modal
    document.getElementById("addNewQuestionBtn").addEventListener("click", () => {
        document.getElementById("addQuestionModal").classList.add("active");
    });
    document.getElementById("closeQuestionModal").addEventListener("click", () => {
        document.getElementById("addQuestionModal").classList.remove("active");
    });
    document.getElementById("cancelQuestionModal").addEventListener("click", () => {
        document.getElementById("addQuestionModal").classList.remove("active");
    });
    document.getElementById("saveNewQuestionBtn").addEventListener("click", saveNewQuestion);

    // Scorecard Result Modal
    document.getElementById("closeScorecardModal").addEventListener("click", () => {
        document.getElementById("scorecardResultModal").classList.remove("active");
    });
    document.getElementById("closeScorecardSuccessBtn").addEventListener("click", () => {
        document.getElementById("scorecardResultModal").classList.remove("active");
    });
    document.getElementById("printScorecardBtn").addEventListener("click", () => {
        window.print();
    });
}

async function saveCustomCandidate() {
    const name = document.getElementById("customCandName").value.trim();
    const role = document.getElementById("customCandTargetRole").value.trim();
    const rawText = document.getElementById("customCandResumeText").value.trim();

    if (!name || !rawText) {
        showToast("Please enter candidate name and resume text.", "warning");
        return;
    }

    const payload = {
        name: name,
        target_role: role || "Engineering Intern",
        raw_resume_text: rawText,
    };

    try {
        const res = await fetch("/api/candidates", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (res.ok) {
            const cand = await res.json();
            state.candidates.push(cand);
            populateCandidateSelect();
            document.getElementById("candidateSelect").value = cand.id;
            updateSkillGapPreview();
            document.getElementById("customCandModal").classList.remove("active");
            showToast(`Candidate ${name} saved!`, "success");
        }
    } catch (err) {
        console.error("Error saving candidate:", err);
    }
}

async function saveCustomJob() {
    const title = document.getElementById("customJobTitle").value.trim();
    const dept = document.getElementById("customJobDept").value.trim();
    const rawText = document.getElementById("customJobText").value.trim();

    if (!title || !rawText) {
        showToast("Please enter job title and description text.", "warning");
        return;
    }

    const payload = {
        title: title,
        department: dept || "Engineering",
        raw_job_text: rawText,
    };

    try {
        const res = await fetch("/api/jobs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (res.ok) {
            const job = await res.json();
            state.jobs.push(job);
            populateJobSelect();
            document.getElementById("jobSelect").value = job.id;
            updateSkillGapPreview();
            document.getElementById("customJobModal").classList.remove("active");
            showToast(`Job ${title} saved!`, "success");
        }
    } catch (err) {
        console.error("Error saving job:", err);
    }
}

async function saveNewQuestion() {
    const cat = document.getElementById("newQCategory").value;
    const domain = document.getElementById("newQDomain").value.trim();
    const skills = document.getElementById("newQSkills").value.split(",").map((s) => s.trim()).filter(Boolean);
    const diff = document.getElementById("newQDifficulty").value;
    const text = document.getElementById("newQText").value.trim();
    const ctx = document.getElementById("newQContext").value.trim();

    if (!text) {
        showToast("Please enter the question text.", "warning");
        return;
    }

    const payload = {
        category: cat,
        domain: domain || "General Engineering",
        skills: skills,
        difficulty: diff,
        question: text,
        context: ctx,
    };

    try {
        const res = await fetch("/api/questions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (res.ok) {
            const q = await res.json();
            state.questionBank.unshift(q);
            renderQuestionBank(state.questionBank);
            document.getElementById("addQuestionModal").classList.remove("active");
            showToast("Question added to Question Bank!", "success");
        }
    } catch (err) {
        console.error("Error adding question:", err);
    }
}

// Settings
function initSettings() {
    const providerSelect = document.getElementById("settingsProvider");
    providerSelect.addEventListener("change", () => {
        const val = providerSelect.value;
        document.getElementById("apiKeyGroup").style.display = val === "openai" ? "block" : "none";
        document.getElementById("endpointGroup").style.display = val === "llama" ? "block" : "none";
    });

    document.getElementById("settingsTemp").addEventListener("input", (e) => {
        document.getElementById("tempVal").textContent = e.target.value;
    });

    document.getElementById("saveSettingsBtn").addEventListener("click", () => {
        state.settings.provider = document.getElementById("settingsProvider").value;
        state.settings.apiKey = document.getElementById("settingsApiKey").value;
        state.settings.endpoint = document.getElementById("settingsEndpoint").value;
        state.settings.modelName = document.getElementById("settingsModelName").value;
        state.settings.temperature = parseFloat(document.getElementById("settingsTemp").value);

        document.getElementById("llmProviderSelect").value = state.settings.provider;
        showToast("AI Configuration settings updated!", "success");
    });
}

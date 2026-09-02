const { useState, useEffect, useRef } = React;

// --- Helper Markdown Formatter ---
function renderFormattedMessage(text) {
  if (!text) return "";
  
  // Format code blocks
  let formatted = text.replace(/```([\s\S]*?)```/g, (match, code) => {
    return `<pre><code>${code.trim()}</code></pre>`;
  });

  // Format inline code
  formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Format bold text
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Format bullet points
  formatted = formatted.replace(/\n- /g, '<br/>• ');
  formatted = formatted.replace(/\n\d+\. /g, (match) => `<br/><b>${match.trim()}</b> `);

  // Convert newlines
  formatted = formatted.replace(/\n/g, '<br/>');

  return formatted;
}

// --- Main App Component ---
function App() {
  const [activeTab, setActiveTab] = useState("chat"); // 'chat', 'kb', 'tickets', 'analytics'
  const [internProfile, setInternProfile] = useState({
    name: "Alex Johnson (Intern)",
    id: "INT-2026-042",
    track: "AI & Fullstack Engineering",
    cohort: "Cohort Fall 2026"
  });

  // Chat State
  const [messages, setMessages] = useState([
    {
      id: "welcome-1",
      sender: "bot",
      text: "👋 Hello Alex! I'm **InternAI Assistant**, your 24/7 internship guide.\n\nI can help you with **task submission rules**, **GitHub workflows**, **deadline extensions**, **grading rubrics**, **certificates**, and **debugging technical errors** (like git push rejected, CORS, Docker, or dependency conflicts).\n\nHow can I help you today?",
      confidence: 1.0,
      confidence_percentage: 100,
      confidence_level: "HIGH",
      category: "Welcome",
      quick_chips: [
        "How do I submit weekly tasks?",
        "Git push rejected fix",
        "Deadline & grace period",
        "Certificate requirements",
        "FastAPI CORS error"
      ],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const chatBottomRef = useRef(null);

  // Escalation / New Ticket Modal State
  const [isTicketModalOpen, setIsTicketModalOpen] = useState(false);
  const [ticketDraft, setTicketDraft] = useState({
    title: "",
    category: "Weekly Tasks & Submissions",
    priority: "Medium",
    description: "",
    error_log: ""
  });

  // Knowledge Base State
  const [faqs, setFaqs] = useState([]);
  const [kbCategory, setKbCategory] = useState("All");
  const [kbSearch, setKbSearch] = useState("");
  const [expandedFaq, setExpandedFaq] = useState(null);

  // Tickets Desk State
  const [tickets, setTickets] = useState([]);
  const [ticketFilterStatus, setTicketFilterStatus] = useState("All");
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [replyText, setReplyText] = useState("");

  // Analytics State
  const [analytics, setAnalytics] = useState(null);

  // Load Data on Mount
  useEffect(() => {
    fetchFaqs();
    fetchTickets();
    fetchAnalytics();
  }, []);

  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  const fetchFaqs = async () => {
    try {
      const res = await fetch("/api/faqs");
      const data = await res.json();
      setFaqs(data.faqs || []);
    } catch (err) {
      console.error("Failed to load FAQs:", err);
    }
  };

  const fetchTickets = async () => {
    try {
      const res = await fetch("/api/tickets");
      const data = await res.json();
      setTickets(data.tickets || []);
    } catch (err) {
      console.error("Failed to load tickets:", err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await fetch("/api/analytics");
      const data = await res.json();
      setAnalytics(data);
    } catch (err) {
      console.error("Failed to load analytics:", err);
    }
  };

  // Handle Send Chat
  const handleSendMessage = async (textToSend) => {
    const query = textToSend || chatInput;
    if (!query.trim()) return;

    const userMsg = {
      id: "user-" + Date.now(),
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setIsTyping(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          intern_name: internProfile.name,
          intern_id: internProfile.id
        })
      });
      const data = await response.json();

      const botMsg = {
        id: "bot-" + Date.now(),
        sender: "bot",
        text: data.answer,
        confidence: data.confidence,
        confidence_percentage: data.confidence_percentage,
        confidence_level: data.confidence_level,
        category: data.category,
        matched_source: data.matched_source,
        related_items: data.related_items || [],
        escalate_needed: data.escalate_needed,
        suggested_ticket: data.suggested_ticket,
        quick_chips: data.quick_chips || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, botMsg]);
      fetchAnalytics(); // Refresh live analytics
    } catch (err) {
      const errorMsg = {
        id: "bot-err-" + Date.now(),
        sender: "bot",
        text: "⚠️ Connection error to AI Chat service. Please check your backend connection.",
        confidence: 0,
        confidence_level: "LOW",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  // Handle Ticket Escalation Click
  const handleOpenEscalationModal = (suggested) => {
    if (suggested) {
      setTicketDraft({
        title: suggested.title || "Internship Query Assistance",
        category: suggested.category || "Weekly Tasks & Submissions",
        priority: suggested.priority || "Medium",
        description: suggested.description || "",
        error_log: ""
      });
    } else {
      setTicketDraft({
        title: "",
        category: "Weekly Tasks & Submissions",
        priority: "Medium",
        description: "",
        error_log: ""
      });
    }
    setIsTicketModalOpen(true);
  };

  // Submit Ticket
  const handleSubmitTicket = async (e) => {
    e.preventDefault();
    if (!ticketDraft.title.trim() || !ticketDraft.description.trim()) {
      alert("Please fill in Title and Description.");
      return;
    }

    try {
      const res = await fetch("/api/tickets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...ticketDraft,
          intern_name: internProfile.name,
          tags: [ticketDraft.category.toLowerCase().replace(" ", "-"), "escalated-from-desk"]
        })
      });
      const data = await res.json();
      if (data.success) {
        setIsTicketModalOpen(false);
        fetchTickets();
        fetchAnalytics();
        
        // Add notification in chat
        setMessages((prev) => [
          ...prev,
          {
            id: "system-ticket-" + Date.now(),
            sender: "bot",
            text: `✅ **Support Ticket Created Successfully!**\n\nTicket Number: **${data.ticket.ticket_number}**\nCategory: *${data.ticket.category}*\nPriority: *${data.ticket.priority}*\n\nOur technical coordinator and mentors have been notified and will assist you shortly. You can track updates in the **Support Tickets** tab.`,
            confidence: 1.0,
            confidence_percentage: 100,
            confidence_level: "HIGH",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
      }
    } catch (err) {
      alert("Failed to create ticket. Please check backend connection.");
    }
  };

  // Handle Ticket Status Change
  const handleUpdateTicketStatus = async (ticketId, newStatus) => {
    try {
      const res = await fetch(`/api/tickets/${ticketId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      const data = await res.json();
      if (data.success) {
        fetchTickets();
        fetchAnalytics();
        if (selectedTicket) {
          setSelectedTicket({ ...selectedTicket, status: newStatus });
        }
      }
    } catch (err) {
      alert("Failed to update status.");
    }
  };

  // Submit Reply to Ticket
  const handleSendTicketReply = async () => {
    if (!replyText.trim() || !selectedTicket) return;
    try {
      const res = await fetch(`/api/tickets/${selectedTicket.id || selectedTicket.ticket_number}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          author: "Mentor / Coordinator",
          role: "Mentor",
          message: replyText
        })
      });
      const data = await res.json();
      if (data.success) {
        setReplyText("");
        setSelectedTicket(data.ticket);
        fetchTickets();
      }
    } catch (err) {
      alert("Could not post reply to ticket.");
    }
  };

  // Filter FAQs
  const filteredFaqs = faqs.filter((faq) => {
    const matchesCategory = kbCategory === "All" || faq.category === kbCategory;
    const matchesSearch =
      !kbSearch ||
      faq.question.toLowerCase().includes(kbSearch.toLowerCase()) ||
      faq.answer.toLowerCase().includes(kbSearch.toLowerCase()) ||
      (faq.keywords && faq.keywords.some((k) => k.toLowerCase().includes(kbSearch.toLowerCase())));
    return matchesCategory && matchesSearch;
  });

  // Filter Tickets
  const filteredTickets = tickets.filter((t) => {
    if (ticketFilterStatus === "All") return true;
    return t.status.toLowerCase() === ticketFilterStatus.toLowerCase();
  });

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="brand-section">
          <div className="brand-logo-glow">⚡</div>
          <div>
            <div className="brand-title">InternAI Desk</div>
            <div className="brand-subtitle">AI Assistant & Escalation</div>
          </div>
        </div>

        <nav className="nav-menu">
          <div
            className={`nav-item ${activeTab === "chat" ? "active" : ""}`}
            onClick={() => setActiveTab("chat")}
          >
            <span>💬</span>
            <span>Live AI Chat</span>
            <span className="nav-badge">Instant</span>
          </div>

          <div
            className={`nav-item ${activeTab === "kb" ? "active" : ""}`}
            onClick={() => setActiveTab("kb")}
          >
            <span>📚</span>
            <span>Knowledge Base</span>
            <span className="nav-badge">{faqs.length} FAQs</span>
          </div>

          <div
            className={`nav-item ${activeTab === "tickets" ? "active" : ""}`}
            onClick={() => setActiveTab("tickets")}
          >
            <span>🎫</span>
            <span>Support Tickets</span>
            <span className="nav-badge">{tickets.length}</span>
          </div>

          <div
            className={`nav-item ${activeTab === "analytics" ? "active" : ""}`}
            onClick={() => setActiveTab("analytics")}
          >
            <span>📊</span>
            <span>Coordinator Analytics</span>
          </div>
        </nav>

        {/* Intern Profile Card */}
        <div className="intern-profile-card">
          <div className="intern-avatar">AJ</div>
          <div className="intern-info">
            <div className="intern-name">{internProfile.name}</div>
            <div className="intern-id">{internProfile.id}</div>
          </div>
        </div>
      </aside>

      {/* Main Viewport */}
      <main className="main-viewport">
        {/* Topbar */}
        <header className="topbar">
          <div className="topbar-title-group">
            <h1>
              {activeTab === "chat" && "AI Internship Assistant"}
              {activeTab === "kb" && "Internship Knowledge Hub & FAQs"}
              {activeTab === "tickets" && "Technical Support & Escalation Desk"}
              {activeTab === "analytics" && "Coordinator Oversight & Model Analytics"}
            </h1>
          </div>
          <div className="topbar-actions">
            <div className="status-pill-online">
              <div className="status-dot"></div>
              <span>NLP Engine Active (v2.0)</span>
            </div>
            <button
              className="btn-primary-action"
              onClick={() => handleOpenEscalationModal(null)}
            >
              <span>+</span>
              <span>New Support Ticket</span>
            </button>
          </div>
        </header>

        {/* Content Body */}
        <div className="view-content">
          {/* TAB 1: LIVE AI CHAT */}
          {activeTab === "chat" && (
            <div className="chat-view-container">
              <div className="chat-main-card">
                <div className="chat-header">
                  <div className="chat-header-info">
                    <span style={{ fontSize: "1.2rem" }}>🤖</span>
                    <div>
                      <strong style={{ fontSize: "0.95rem" }}>InternAI Autonomous Agent</strong>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        Semantic Transformer matching + Automated Mentor Escalation
                      </div>
                    </div>
                  </div>
                  <div className="model-badge">Sub-10ms Semantic Vectorizer</div>
                </div>

                {/* Messages Area */}
                <div className="chat-messages-area">
                  {messages.map((m) => (
                    <div key={m.id} className={`message-row ${m.sender}`}>
                      <div className={`msg-avatar ${m.sender}`}>
                        {m.sender === "user" ? "AJ" : "⚡"}
                      </div>
                      <div className="msg-bubble">
                        {m.sender === "bot" && (
                          <div className="bot-meta-bar">
                            <span className={`conf-pill ${m.confidence_level || 'HIGH'}`}>
                              {m.confidence_percentage ? `${m.confidence_percentage}% Match` : "Verified Answer"} • {m.confidence_level || 'HIGH'}
                            </span>
                            {m.category && <span className="category-pill">{m.category}</span>}
                            <span style={{ marginLeft: "auto", fontSize: "0.72rem", color: "var(--text-dim)" }}>
                              {m.timestamp}
                            </span>
                          </div>
                        )}

                        <div
                          dangerouslySetInnerHTML={{
                            __html: renderFormattedMessage(m.text)
                          }}
                        />

                        {/* Matched Source Info */}
                        {m.matched_source && (
                          <div className="matched-source-card">
                            <div className="matched-source-title">
                              <span>📌</span>
                              <span>Matched Source: {m.matched_source.type} [{m.matched_source.id}]</span>
                            </div>
                            <div className="matched-source-desc">
                              "{m.matched_source.title}"
                            </div>
                          </div>
                        )}

                        {/* Auto-Escalation Prompt Card for Low Confidence */}
                        {m.escalate_needed && m.suggested_ticket && (
                          <div className="escalation-prompt-card">
                            <div className="escalation-header">
                              <span>🚨</span>
                              <span>Automated Mentor Escalation Ready</span>
                            </div>
                            <div style={{ fontSize: "0.84rem", color: "#cbd5e1" }}>
                              Our AI suggests escalating this topic to senior mentors for personalized help:
                            </div>
                            <div style={{ fontWeight: 600, fontSize: "0.88rem", color: "#fecdd3" }}>
                              {m.suggested_ticket.title}
                            </div>
                            <button
                              className="btn-escalate-now"
                              onClick={() => handleOpenEscalationModal(m.suggested_ticket)}
                            >
                              <span>🚀</span>
                              <span>Submit Escalation Ticket</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {isTyping && (
                    <div className="message-row bot">
                      <div className="msg-avatar bot">⚡</div>
                      <div className="msg-bubble" style={{ color: "var(--text-muted)", fontStyle: "italic" }}>
                        InternAI is querying semantic knowledge base...
                      </div>
                    </div>
                  )}

                  <div ref={chatBottomRef} />
                </div>

                {/* Quick Chips Bar */}
                <div className="quick-chips-wrapper">
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginRight: 6 }}>
                    Suggestions:
                  </span>
                  {[
                    "How do I submit weekly tasks?",
                    "Git push rejected fix",
                    "Deadline & grace period policy",
                    "Certificate criteria & passing marks",
                    "Fix ModuleNotFoundError: fastapi",
                    "Docker port already in use"
                  ].map((chip, idx) => (
                    <div
                      key={idx}
                      className="quick-chip"
                      onClick={() => handleSendMessage(chip)}
                    >
                      {chip}
                    </div>
                  ))}
                </div>

                {/* Input Bar */}
                <div className="chat-input-bar">
                  <input
                    type="text"
                    className="chat-input"
                    placeholder="Ask anything about weekly tasks, GitHub, deadlines, grading, certificates, or errors..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                  />
                  <button
                    className="btn-send"
                    onClick={() => handleSendMessage()}
                    title="Send message"
                  >
                    ➤
                  </button>
                </div>
              </div>

              {/* Chat Sidebar Information */}
              <div className="chat-side-panel">
                <div className="panel-card">
                  <div className="panel-card-title">
                    <span>💡</span>
                    <span>Quick Guidelines</span>
                  </div>
                  <ul style={{ fontSize: "0.82rem", color: "var(--text-muted)", paddingLeft: 18, lineHeight: 1.6 }}>
                    <li><strong>Deadlines:</strong> Every Sunday at 11:59 PM UTC (3h grace period).</li>
                    <li><strong>Branch Rules:</strong> <code>feature/task-X-name</code>. Never push to <code>main</code>.</li>
                    <li><strong>Demos:</strong> 2-3 min Loom video required with PR.</li>
                    <li><strong>Passing Score:</strong> 75% cumulative required for Certificate.</li>
                  </ul>
                </div>

                <div className="panel-card">
                  <div className="panel-card-title">
                    <span>🛠️</span>
                    <span>Direct Escalation</span>
                  </div>
                  <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: 12 }}>
                    Have a complex blocker or need a personalized extension? Open a direct ticket with our mentors.
                  </p>
                  <button
                    className="btn-primary-action"
                    style={{ width: "100%", justifyContent: "center" }}
                    onClick={() => handleOpenEscalationModal(null)}
                  >
                    Open Support Ticket
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: KNOWLEDGE BASE (FAQs) */}
          {activeTab === "kb" && (
            <div>
              <div className="kb-header-section">
                <div className="search-input-wrapper">
                  <span className="search-icon-pos">🔍</span>
                  <input
                    type="text"
                    className="search-input-large"
                    placeholder="Search FAQs by question, keywords, or error codes (e.g., git, deadlines, rubric, certificate, cors)..."
                    value={kbSearch}
                    onChange={(e) => setKbSearch(e.target.value)}
                  />
                </div>

                <div className="category-filter-bar">
                  {[
                    "All",
                    "Weekly Tasks & Submissions",
                    "GitHub & Version Control",
                    "Deadlines & Extensions",
                    "Grading & Evaluations",
                    "Certificates & Program Completion",
                    "Mentorship & Office Hours",
                    "Environment & Tooling"
                  ].map((cat) => (
                    <div
                      key={cat}
                      className={`cat-filter-chip ${kbCategory === cat ? "active" : ""}`}
                      onClick={() => setKbCategory(cat)}
                    >
                      {cat}
                    </div>
                  ))}
                </div>
              </div>

              <div className="faq-grid">
                {filteredFaqs.map((faq) => {
                  const isExpanded = expandedFaq === faq.id;
                  return (
                    <div
                      key={faq.id}
                      className="faq-card"
                      onClick={() => setExpandedFaq(isExpanded ? null : faq.id)}
                    >
                      <div className="faq-top-row">
                        <div className="faq-question-title">
                          <span style={{ color: "#818cf8" }}>{faq.id}</span>
                          <span>{faq.question}</span>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                          <span className="category-pill">{faq.category}</span>
                          <span style={{ fontSize: "1.2rem", color: "var(--text-muted)" }}>
                            {isExpanded ? "▲" : "▼"}
                          </span>
                        </div>
                      </div>

                      {isExpanded && (
                        <div className="faq-body-expanded">
                          <div
                            dangerouslySetInnerHTML={{
                              __html: renderFormattedMessage(faq.answer)
                            }}
                          />

                          {faq.suggested_actions && faq.suggested_actions.length > 0 && (
                            <div style={{ marginTop: 14 }}>
                              <strong style={{ fontSize: "0.82rem", color: "#a5b4fc" }}>
                                Recommended Actions:
                              </strong>
                              <ul style={{ fontSize: "0.82rem", color: "#94a3b8", paddingLeft: 18, marginTop: 4 }}>
                                {faq.suggested_actions.map((act, i) => (
                                  <li key={i}>{act}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {faq.keywords && (
                            <div className="tag-list">
                              {faq.keywords.map((kw, i) => (
                                <span key={i} className="tag-badge">#{kw}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}

                {filteredFaqs.length === 0 && (
                  <div style={{ textAlign: "center", padding: 48, color: "var(--text-muted)" }}>
                    No FAQs match your search criteria. Try a different search or ask in AI Chat.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: SUPPORT TICKETS DESK */}
          {activeTab === "tickets" && (
            <div>
              <div className="ticket-controls-bar">
                <div style={{ display: "flex", gap: 8 }}>
                  {["All", "Open", "In Progress", "Resolved", "Escalated"].map((st) => (
                    <button
                      key={st}
                      className={`cat-filter-chip ${ticketFilterStatus === st ? "active" : ""}`}
                      onClick={() => setTicketFilterStatus(st)}
                    >
                      {st}
                    </button>
                  ))}
                </div>
                <div style={{ fontSize: "0.88rem", color: "var(--text-muted)" }}>
                  Showing {filteredTickets.length} tickets
                </div>
              </div>

              <div className="tickets-table-container">
                {filteredTickets.map((t) => (
                  <div
                    key={t.id || t.ticket_number}
                    className="ticket-row"
                    onClick={() => setSelectedTicket(t)}
                  >
                    <div className="t-col-id">{t.ticket_number || t.id}</div>
                    <div className="t-col-title">
                      <div className="t-title-text">{t.title}</div>
                      <div className="t-meta-sub">
                        <span>👤 {t.intern_name || "Alex Johnson"}</span>
                        <span>📂 {t.category}</span>
                        <span>🕒 {t.created_at ? new Date(t.created_at).toLocaleDateString() : "Recent"}</span>
                      </div>
                    </div>
                    <div className="t-col-badge">
                      <span className={`priority-indicator priority-${t.priority || "Medium"}`}>
                        {t.priority || "Medium"}
                      </span>
                    </div>
                    <div className="t-col-badge">
                      <span className={`badge-status ${(t.status || "Open").replace(" ", "-")}`}>
                        {t.status || "Open"}
                      </span>
                    </div>
                  </div>
                ))}

                {filteredTickets.length === 0 && (
                  <div style={{ textAlign: "center", padding: 48, color: "var(--text-muted)" }}>
                    No tickets found for this status filter.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: COORDINATOR ANALYTICS */}
          {activeTab === "analytics" && analytics && (
            <div>
              {/* KPI Grid */}
              <div className="metrics-kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-label">Total Queries Handled</div>
                  <div className="kpi-value">{analytics.total_queries}</div>
                  <div className="kpi-trend">↑ 14% vs last week</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-label">Bot Auto-Resolution Rate</div>
                  <div className="kpi-value">{analytics.auto_resolved_rate}%</div>
                  <div className="kpi-trend" style={{ color: "#34d399" }}>★ Above SLA target (80%)</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-label">Avg Confidence Score</div>
                  <div className="kpi-value">{analytics.avg_confidence}%</div>
                  <div className="kpi-trend">High semantic precision</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-label">Active Support Tickets</div>
                  <div className="kpi-value">{analytics.active_tickets_count}</div>
                  <div className="kpi-trend" style={{ color: "#fbbf24" }}>● Requires mentor attention</div>
                </div>
              </div>

              {/* Charts Grid */}
              <div className="analytics-charts-grid">
                <div className="chart-card">
                  <div className="chart-header">
                    <strong style={{ fontSize: "1.05rem" }}>Query Distribution by Internship Category</strong>
                    <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>Live Cohort Data</span>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                    {Object.entries(analytics.category_distribution || {}).map(([cat, count], i) => {
                      const max = Math.max(...Object.values(analytics.category_distribution || {}), 1);
                      const pct = Math.round((count / max) * 100);
                      return (
                        <div key={i}>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: 4 }}>
                            <span>{cat}</span>
                            <span style={{ fontWeight: 600, color: "#818cf8" }}>{count} queries</span>
                          </div>
                          <div style={{ width: "100%", height: 8, background: "rgba(255,255,255,0.06)", borderRadius: 4, overflow: "hidden" }}>
                            <div style={{ width: `${pct}%`, height: "100%", background: "linear-gradient(90deg, #6366f1, #22d3ee)", borderRadius: 4 }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="chart-card">
                  <div className="chart-header">
                    <strong style={{ fontSize: "1.05rem" }}>Ticket Status Breakdown</strong>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 10 }}>
                    {Object.entries(analytics.status_distribution || {}).map(([st, cnt], idx) => (
                      <div key={idx} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", background: "rgba(255,255,255,0.03)", borderRadius: 8 }}>
                        <span className={`badge-status ${st.replace(" ", "-")}`}>{st}</span>
                        <strong style={{ fontSize: "1.1rem" }}>{cnt}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Escalated Queries Queue */}
              <div className="chart-card">
                <div className="chart-header">
                  <strong style={{ fontSize: "1.05rem" }}>Recent Escalation Queue (Low Confidence / Mentorship Needed)</strong>
                  <span className="badge-status Escalated">Auto-Escalated</span>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {analytics.escalated_queries && analytics.escalated_queries.map((q, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", background: "rgba(244,63,94,0.08)", border: "1px solid rgba(244,63,94,0.2)", borderRadius: 8 }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: "0.92rem", color: "#fecdd3" }}>"{q.query}"</div>
                        <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: 4 }}>
                          Intern: {q.intern_name} • Category: {q.category} • Confidence: {q.confidence_percentage}%
                        </div>
                      </div>
                      <button
                        className="btn-escalate-now"
                        style={{ padding: "6px 12px", fontSize: "0.78rem" }}
                        onClick={() => handleOpenEscalationModal({ title: `[Escalation] ${q.query}`, category: q.category, priority: "High", description: `Intern ${q.intern_name} queried: "${q.query}"` })}
                      >
                        Create Support Ticket
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* MODAL: CREATE SUPPORT TICKET */}
      {isTicketModalOpen && (
        <div className="modal-backdrop" onClick={() => setIsTicketModalOpen(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700 }}>Submit Support Ticket / Escalation</h2>
              <button
                style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "1.4rem", cursor: "pointer" }}
                onClick={() => setIsTicketModalOpen(false)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmitTicket}>
              <div className="form-group">
                <label className="form-label">Ticket Title / Summary</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g., [Git] Updates rejected on feature/task-3 push"
                  value={ticketDraft.title}
                  onChange={(e) => setTicketDraft({ ...ticketDraft, title: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <select
                    className="form-control"
                    value={ticketDraft.category}
                    onChange={(e) => setTicketDraft({ ...ticketDraft, category: e.target.value })}
                  >
                    <option>Weekly Tasks & Submissions</option>
                    <option>GitHub & Version Control</option>
                    <option>Deadlines & Extensions</option>
                    <option>Grading & Evaluations</option>
                    <option>Certificates & Program Completion</option>
                    <option>Environment & Dependencies</option>
                    <option>Backend & API</option>
                    <option>Frontend & UI</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Priority</label>
                  <select
                    className="form-control"
                    value={ticketDraft.priority}
                    onChange={(e) => setTicketDraft({ ...ticketDraft, priority: e.target.value })}
                  >
                    <option>Low</option>
                    <option>Medium</option>
                    <option>High</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Detailed Description</label>
                <textarea
                  className="form-control"
                  placeholder="Explain what you are trying to do, what happened, and any steps you tried..."
                  value={ticketDraft.description}
                  onChange={(e) => setTicketDraft({ ...ticketDraft, description: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Error Logs / Terminal Output (Optional)</label>
                <textarea
                  className="form-control"
                  style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.82rem" }}
                  placeholder="Paste stack traces or error logs here..."
                  value={ticketDraft.error_log}
                  onChange={(e) => setTicketDraft({ ...ticketDraft, error_log: e.target.value })}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 20 }}>
                <button
                  type="button"
                  className="quick-chip"
                  onClick={() => setIsTicketModalOpen(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary-action">
                  Submit Ticket
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: TICKET DETAILS & REPLY */}
      {selectedTicket && (
        <div className="modal-backdrop" onClick={() => setSelectedTicket(null)}>
          <div className="modal-dialog" style={{ maxWidth: 750 }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span className="t-col-id">{selectedTicket.ticket_number || selectedTicket.id}</span>
                <h2 style={{ fontSize: "1.15rem", fontWeight: 700, marginTop: 4 }}>
                  {selectedTicket.title}
                </h2>
              </div>
              <button
                style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "1.4rem", cursor: "pointer" }}
                onClick={() => setSelectedTicket(null)}
              >
                ✕
              </button>
            </div>

            <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
              <span className={`badge-status ${(selectedTicket.status || 'Open').replace(' ', '-')}`}>
                {selectedTicket.status || 'Open'}
              </span>
              <span className={`priority-indicator priority-${selectedTicket.priority || 'Medium'}`}>
                Priority: {selectedTicket.priority || 'Medium'}
              </span>
              <span className="category-pill">{selectedTicket.category}</span>
            </div>

            <div style={{ background: "rgba(255,255,255,0.03)", padding: 16, borderRadius: 8, marginBottom: 16 }}>
              <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: 6 }}>Description:</div>
              <div style={{ fontSize: "0.92rem", lineHeight: 1.6, whiteSpace: "pre-line" }}>
                {selectedTicket.description}
              </div>

              {selectedTicket.error_log && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: "0.82rem", color: "#f87171", marginBottom: 4 }}>Error Log:</div>
                  <pre style={{ margin: 0 }}><code>{selectedTicket.error_log}</code></pre>
                </div>
              )}

              {selectedTicket.root_cause && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: "0.82rem", color: "#fbbf24", marginBottom: 4 }}>Root Cause:</div>
                  <div style={{ fontSize: "0.88rem" }}>{selectedTicket.root_cause}</div>
                </div>
              )}

              {selectedTicket.solution_steps && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: "0.82rem", color: "#34d399", marginBottom: 4 }}>Solution Steps:</div>
                  <div
                    style={{ fontSize: "0.88rem" }}
                    dangerouslySetInnerHTML={{ __html: renderFormattedMessage(selectedTicket.solution_steps) }}
                  />
                </div>
              )}
            </div>

            {/* Discussion Thread */}
            {selectedTicket.replies && selectedTicket.replies.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <strong style={{ fontSize: "0.9rem", color: "#f1f5f9" }}>Discussion & Mentor Resolution:</strong>
                <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
                  {selectedTicket.replies.map((rep, idx) => (
                    <div key={idx} style={{ padding: "10px 14px", background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 6 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", color: "#a5b4fc", marginBottom: 4 }}>
                        <span>{rep.author} ({rep.role})</span>
                        <span>{rep.timestamp ? new Date(rep.timestamp).toLocaleTimeString() : ""}</span>
                      </div>
                      <div style={{ fontSize: "0.88rem", color: "#e2e8f0" }}>{rep.message}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Add Reply */}
            <div style={{ marginBottom: 16 }}>
              <textarea
                className="form-control"
                placeholder="Add a mentor response or update resolution notes..."
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                style={{ minHeight: 70 }}
              />
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
                <button className="btn-primary-action" style={{ padding: "8px 14px", fontSize: "0.82rem" }} onClick={handleSendTicketReply}>
                  Add Response
                </button>
              </div>
            </div>

            {/* Status Actions */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid var(--border-subtle)", paddingTop: 14 }}>
              <div style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>Update Status:</div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  className="quick-chip"
                  onClick={() => handleUpdateTicketStatus(selectedTicket.id || selectedTicket.ticket_number, "In Progress")}
                >
                  Mark In Progress
                </button>
                <button
                  className="btn-escalate-now"
                  style={{ padding: "6px 12px", fontSize: "0.78rem" }}
                  onClick={() => handleUpdateTicketStatus(selectedTicket.id || selectedTicket.ticket_number, "Escalated")}
                >
                  Escalate
                </button>
                <button
                  className="btn-primary-action"
                  style={{ padding: "6px 14px", fontSize: "0.78rem", background: "linear-gradient(135deg, #10b981, #059669)" }}
                  onClick={() => handleUpdateTicketStatus(selectedTicket.id || selectedTicket.ticket_number, "Resolved")}
                >
                  Mark Resolved
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Render React App
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

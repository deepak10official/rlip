const API_BASE = "http://127.0.0.1:8000";

const BILLING_CATEGORIES = {
  recurring: { label: "Recurring", color: "#10b981", bg: "rgba(16,185,129,0.12)" },
  project: { label: "Project-Based", color: "#667eea", bg: "rgba(102,126,234,0.12)" },
  usage: { label: "Usage-Based", color: "#f59e0b", bg: "rgba(245,158,11,0.12)" },
};

const BILLING_TYPE_META = {
  arc: {
    icon: "🔄",
    label: "ARC",
    category: "recurring",
    desc: "Actual resource consumption billing validated against usage evidence.",
    howItWorks: "Usage records → approved rates → invoice quantities",
  },
  rrc: {
    icon: "📋",
    label: "RRC",
    category: "recurring",
    desc: "Recurring reserved resource charges validated against allocation records.",
    howItWorks: "Reserved resource → active allocation → recurring charge",
  },
  managed_services: {
    icon: "⚙️",
    label: "Managed Services",
    category: "recurring",
    desc: "Monthly managed-services charges validated against SLA and approval evidence.",
    howItWorks: "SLA contract → service evidence → monthly billing",
  },
  milestone_based: {
    icon: "🎯",
    label: "Milestone Based",
    category: "project",
    desc: "Milestone invoices validated against explicit customer acceptance.",
    howItWorks: "Deliverable → acceptance → invoice release",
  },
  time_and_materials: {
    icon: "⏱️",
    label: "Time & Materials",
    category: "project",
    desc: "Hours and materials validated against approved timesheets and support.",
    howItWorks: "Approved hours + materials → rate calculation → invoice",
  },
  time_and_materials_over_cap: {
    icon: "⚠️",
    label: "T&M Over Cap",
    category: "project",
    desc: "Capped T&M billing validated against cap tracker and overage approvals.",
    howItWorks: "T&M total → cap check → approval for overage",
  },
  device_based: {
    icon: "📱",
    label: "Device Based",
    category: "usage",
    desc: "Per-device billing tied to covered active inventory.",
    howItWorks: "Device inventory → covered count → per-device rate",
  },
  outcome_based: {
    icon: "📊",
    label: "Outcome Based",
    category: "usage",
    desc: "Outcome billing validated against accepted business results.",
    howItWorks: "Outcome target → measurement → customer sign-off",
  },
};

const AUDIT_STEPS = [
  { id: "vision", label: "Vision Reading", icon: "👁️" },
  { id: "intake", label: "Doc Intake", icon: "📥" },
  { id: "contract", label: "Contract Rules", icon: "📜" },
  { id: "evidence", label: "Evidence Check", icon: "🔍" },
  { id: "invoice", label: "Invoice Validation", icon: "🧾" },
  { id: "payment", label: "Payment Recon", icon: "💳" },
  { id: "report", label: "Final Report", icon: "📊" },
];

const DOCUMENT_ZONES = [
  { key: "service_agreements", title: "Service Agreements", icon: "📝", hint: "Contracts, SOWs, MSAs" },
  { key: "invoices", title: "Invoices", icon: "🧾", hint: "Invoice DOCX, TXT, MD" },
  { key: "billing_evidence", title: "Billing Evidence", icon: "🔍", hint: "Timesheets, usage logs, SLA reports" },
  { key: "payment_records", title: "Payment Records", icon: "💳", hint: "ACH receipts, bank statements" },
];

class ApiService {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async request(path, options = {}) {
    const headers = options.rawBody ? {} : { "Content-Type": "application/json", ...(options.headers || {}) };
    let response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, { ...options, headers });
    } catch {
      throw new Error("Cannot connect to backend. Is the FastAPI server running?");
    }

    if (!response.ok) {
      const payload = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail || payload));
    }
    return response.json();
  }

  health() {
    return this.request("/health");
  }

  billingTypes() {
    return this.request("/billing-types");
  }

  billingRules(type) {
    return this.request(`/billing-types/${type}/rules`);
  }

  billingDocuments(type) {
    return this.request(`/billing-types/${type}/documents`);
  }

  auditCorpus(billingType, sessionId = null) {
    return this.request("/audit/corpus", {
      method: "POST",
      body: JSON.stringify({ billing_type: billingType, session_id: sessionId }),
    });
  }

  async auditUpload(billingType, files) {
    const formData = new FormData();
    formData.append("billing_type", billingType);
    for (const file of files.service_agreements || []) formData.append("service_agreements", file);
    for (const file of files.invoices || []) formData.append("invoices", file);
    for (const file of files.billing_evidence || []) formData.append("billing_evidence", file);
    for (const file of files.payment_records || []) formData.append("payment_records", file);
    return this.request("/audit/upload", { method: "POST", body: formData, rawBody: true });
  }
}

const api = new ApiService(API_BASE);

const state = {
  healthStatus: null,
  billingTypes: [],
  selectedBillingType: null,
  selectedRules: null,
  selectedDocuments: null,
  billingRulesModalOpen: false,
  billingRulesRequestId: 0,
  auditResult: null,
  auditHistory: [],
  isAuditing: false,
  uploadFiles: {
    service_agreements: [],
    invoices: [],
    billing_evidence: [],
    payment_records: [],
  },
};

const router = {
  routes: {},
  currentRoute: "home",
  register(name, initFn) {
    this.routes[name] = initFn;
  },
  navigate(name) {
    if (state.billingRulesModalOpen) closeBillingRulesModal();
    document.querySelectorAll(".nav-item").forEach((item) => {
      item.classList.toggle("active", item.dataset.route === name);
    });
    document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
    document.getElementById(`view-${name}`)?.classList.add("active");
    this.currentRoute = name;
    this.routes[name]?.();
    window.scrollTo({ top: 0, behavior: "smooth" });
  },
};

class Toast {
  static show(type, title, message, duration = 4200) {
    const container = document.getElementById("toast-container");
    const icons = { success: "✅", error: "❌", warning: "⚠️", info: "ℹ️" };
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || "ℹ️"}</span>
      <div class="toast-body">
        <div class="toast-title">${escapeHtml(title)}</div>
        <div class="toast-message">${escapeHtml(message)}</div>
      </div>
      <button class="toast-close" onclick="this.closest('.toast').remove()">×</button>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.add("removing");
      setTimeout(() => toast.remove(), 250);
    }, duration);
  }
  static success(title, message) { Toast.show("success", title, message); }
  static error(title, message) { Toast.show("error", title, message, 6500); }
  static warning(title, message) { Toast.show("warning", title, message); }
  static info(title, message) { Toast.show("info", title, message); }
}

async function checkHealth() {
  const dot = document.getElementById("health-dot");
  const label = document.getElementById("health-label");
  try {
    const data = await api.health();
    state.healthStatus = data;
    dot.className = "health-dot online";
    label.textContent = `Online · ${data.model}`;
    return true;
  } catch {
    state.healthStatus = null;
    dot.className = "health-dot offline";
    label.textContent = "Backend Offline";
    return false;
  }
}


async function initHome() {
  await checkHealth();
  await ensureBillingTypes();

  // Update live stat — AI model
  if (state.healthStatus?.model) {
    const el = document.getElementById("stat-model");
    if (el) el.textContent = state.healthStatus.model.split("-").slice(0, 2).join("-");
  }
  if (state.billingTypes.length) {
    const el = document.getElementById("stat-types");
    if (el) animateCounter(el, state.billingTypes.length);
  }

  // Staggered reveal for feature cards
  setTimeout(() => {
    document.querySelectorAll("#view-home .reveal").forEach((el, i) => {
      setTimeout(() => el.classList.add("visible"), i * 120);
    });
  }, 100);

  // Fill connector lines after step cards appear
  setTimeout(() => {
    document.querySelectorAll(".connector-fill").forEach((el, i) => {
      setTimeout(() => el.classList.add("filled"), i * 400 + 500);
    });
  }, 200);
}

function animateCounter(el, target, suffix = "") {
  const duration = 1200;
  const start = performance.now();
  const from = 0;
  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(from + (target - from) * eased) + suffix;
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}


async function initAudit() {
  await ensureBillingTypes();
  renderBillingTypes();
  renderAuditConfig();
}

async function ensureBillingTypes() {
  if (state.billingTypes.length) return;
  try {
    const payload = await api.billingTypes();
    state.billingTypes = payload.billing_types || [];
  } catch (error) {
    Toast.error("Connection Error", error.message);
  }
}

function renderBillingTypes() {
  const grid = document.getElementById("billing-types-grid");
  if (!state.billingTypes.length) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="empty-state-icon">🔌</div>
        <div class="empty-state-title">Cannot Load Billing Types</div>
        <div class="empty-state-desc">Make sure the backend is running.</div>
      </div>
    `;
    return;
  }

  const groups = {};
  for (const type of state.billingTypes) {
    const category = BILLING_TYPE_META[type]?.category || "usage";
    if (!groups[category]) groups[category] = [];
    groups[category].push(type);
  }

  let cardIndex = 0;
  grid.innerHTML = ["recurring", "project", "usage"].map((categoryKey) => {
    const types = groups[categoryKey];
    if (!types?.length) return "";
    const category = BILLING_CATEGORIES[categoryKey];
    return `
      <div class="billing-category-section" style="grid-column: 1 / -1;">
        <div class="billing-category-header">
          <span class="billing-category-dot" style="background: ${category.color};"></span>
          <span class="billing-category-label">${category.label}</span>
          <span class="billing-category-count">${types.length} types</span>
        </div>
      </div>
      ${types.map((type) => {
        const meta = BILLING_TYPE_META[type] || { icon: "📄", label: formatType(type), desc: "", howItWorks: "" };
        const selected = state.selectedBillingType === type ? "selected" : "";
        const delay = cardIndex++ * 50;
        return `
          <div class="billing-type-card ${selected} reveal visible" data-billing-type="${escapeHtml(type)}" role="button" tabindex="0"
               style="--accent-color: ${category.color}; --accent-bg: ${category.bg}; animation-delay: ${delay}ms;">
            <div class="bt-card-top">
              <div class="bt-icon-wrap" style="background: ${category.bg}; color: ${category.color};">${meta.icon}</div>
              <span class="bt-category-badge" style="background: ${category.bg}; color: ${category.color};">${category.label}</span>
            </div>
            <div class="billing-type-name">${escapeHtml(meta.label)}</div>
            <div class="billing-type-desc">${escapeHtml(meta.desc)}</div>
            <div class="bt-how-it-works">
              <span class="bt-flow-label">Flow</span>
              <span class="bt-flow-text">${escapeHtml(meta.howItWorks)}</span>
            </div>
          </div>
        `;
      }).join("")}
    `;
  }).join("");

  grid.querySelectorAll(".billing-type-card").forEach((card) => {
    const cardType = card.dataset.billingType;
    if (!cardType) return;
    card.addEventListener("click", () => selectBillingType(cardType));
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectBillingType(cardType);
      }
    });
  });
}

async function selectBillingType(type) {
  state.selectedBillingType = type;
  state.selectedRules = null;
  const requestId = ++state.billingRulesRequestId;
  renderBillingTypes();

  openBillingRulesModal(`
    <div class="rules-modal-loading">
      <div class="card-title" id="billing-rules-modal-title"><span class="icon">📜</span> Loading ${escapeHtml(formatType(type))} rules...</div>
      <div class="shimmer shimmer-line w-80"></div>
      <div class="shimmer shimmer-line w-60"></div>
      <div class="shimmer shimmer-line w-80"></div>
    </div>
  `);

  try {
    const rules = await api.billingRules(type);
    if (state.billingRulesRequestId !== requestId || !state.billingRulesModalOpen) return;
    state.selectedRules = rules;
    renderBillingTypes();
    renderBillingRulesModal(rules);
  } catch (error) {
    if (state.billingRulesRequestId !== requestId) return;
    Toast.error("Error", error.message);
    closeBillingRulesModal();
  }
}

function renderAuditConfig() {
  const el = document.getElementById("audit-config");
  if (el) el.innerHTML = "";
}

function renderBillingRulesModal(rules) {
  const meta = BILLING_TYPE_META[rules.billing_type] || {
    icon: "📄",
    label: formatType(rules.billing_type),
    desc: "",
    howItWorks: "",
    category: "usage",
  };
  const category = BILLING_CATEGORIES[meta.category] || BILLING_CATEGORIES.usage;

  openBillingRulesModal(`
    <div class="rules-modal-shell" style="--accent-color: ${category.color}; --accent-bg: ${category.bg};">
      <div class="rules-modal-header">
        <div class="bt-icon-wrap" style="background: ${category.bg}; color: ${category.color};">${meta.icon}</div>
        <div class="rules-modal-heading">
          <div class="modal-eyebrow">${escapeHtml(category.label)} Billing Type</div>
          <h2 id="billing-rules-modal-title">${escapeHtml(meta.label)}</h2>
          <p>${escapeHtml(meta.desc)}</p>
        </div>
      </div>
      ${meta.howItWorks ? `
        <div class="rules-modal-flow">
          <span class="bt-flow-label">Flow</span>
          <span class="bt-flow-text">${escapeHtml(meta.howItWorks)}</span>
        </div>
      ` : ""}
      <div class="modal-rules-content">
        ${renderRuleList("Invoice Validation", rules.invoice_validation_rules)}
        ${renderRuleList("Evidence Rules", rules.evidence_rules)}
        ${renderRuleList("Payment Rules", rules.payment_rules)}
        ${renderRuleList("Issue Indicators", rules.issue_scenario_indicators)}
      </div>
    </div>
  `);
}

function openBillingRulesModal(contentHtml) {
  const modal = document.getElementById("billing-rules-modal");
  const content = document.getElementById("billing-rules-modal-content");
  if (!modal || !content) return;
  state.billingRulesModalOpen = true;
  content.innerHTML = contentHtml;
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
  document.body.classList.add("modal-open");
  requestAnimationFrame(() => modal.querySelector(".billing-rules-dialog")?.focus());
}

function closeBillingRulesModal() {
  const modal = document.getElementById("billing-rules-modal");
  if (!modal) return;
  state.billingRulesModalOpen = false;
  state.billingRulesRequestId++;
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
  document.body.classList.remove("modal-open");
}

function handleBillingRulesBackdrop(event) {
  if (event.target?.id === "billing-rules-modal") closeBillingRulesModal();
}

function renderRuleList(title, items = []) {
  if (!items.length) return "";
  return `
    <div class="rules-category">
      <div class="rules-category-title">${escapeHtml(title)}</div>
      ${items.map((item) => `<div class="rule-item">${escapeHtml(item)}</div>`).join("")}
    </div>
  `;
}

function initUpload() {
  ensureBillingTypes().then(renderUploadTypeSelector);
  renderUploadTypeSelector();
  renderDropzones();
}

function renderUploadTypeSelector() {
  const el = document.getElementById("upload-type-selector");
  if (!el) return;
  el.innerHTML = `
    <label class="upload-selector-label">Select Billing Type</label>
    <select class="select-control" onchange="state.selectedBillingType = this.value">
      <option value="">— Choose billing type —</option>
      ${state.billingTypes.map((type) => `
        <option value="${escapeHtml(type)}" ${state.selectedBillingType === type ? "selected" : ""}>
          ${(BILLING_TYPE_META[type]?.icon || "📄")} ${escapeHtml(BILLING_TYPE_META[type]?.label || formatType(type))}
        </option>
      `).join("")}
    </select>
  `;
}

function renderDropzones() {
  const container = document.getElementById("upload-dropzones");
  container.innerHTML = `
    <div class="upload-grid">
      ${DOCUMENT_ZONES.map((zone) => renderDropzone(zone)).join("")}
    </div>
    <div class="upload-actions">
      <button class="btn btn-primary btn-lg" id="btn-upload-audit" onclick="runUploadAudit()">🚀 Run Upload Audit</button>
      <span>${Object.values(state.uploadFiles).flat().length} files selected</span>
    </div>
  `;
}

function renderDropzone(zone) {
  const files = state.uploadFiles[zone.key] || [];
  return `
    <div class="dropzone ${files.length ? "has-files" : ""}" id="dropzone-${zone.key}"
      ondragover="handleDragOver(event, '${zone.key}')"
      ondragleave="handleDragLeave(event, '${zone.key}')"
      ondrop="handleDrop(event, '${zone.key}')"
      onclick="document.getElementById('input-${zone.key}').click()">
      <input type="file" id="input-${zone.key}" multiple hidden onchange="handleFileSelect(event, '${zone.key}')">
      <div class="dropzone-icon">${zone.icon}</div>
      <div class="dropzone-title">${escapeHtml(zone.title)}</div>
      <div class="dropzone-hint">${escapeHtml(zone.hint)}</div>
      ${files.length ? `
        <div class="file-list">
          ${files.map((file, index) => `
            <div class="file-item">
              <span class="file-item-name">📄 ${escapeHtml(file.name)}</span>
              <button class="file-remove" onclick="event.stopPropagation(); removeFile('${zone.key}', ${index})">×</button>
            </div>
          `).join("")}
        </div>
      ` : ""}
    </div>
  `;
}

function handleDragOver(event, key) {
  event.preventDefault();
  document.getElementById(`dropzone-${key}`)?.classList.add("dragover");
}

function handleDragLeave(event, key) {
  event.preventDefault();
  document.getElementById(`dropzone-${key}`)?.classList.remove("dragover");
}

function handleDrop(event, key) {
  event.preventDefault();
  document.getElementById(`dropzone-${key}`)?.classList.remove("dragover");
  const files = Array.from(event.dataTransfer.files || []);
  state.uploadFiles[key].push(...files);
  renderDropzones();
  Toast.success("Files Added", `${files.length} file(s) added to ${formatType(key)}.`);
}

function handleFileSelect(event, key) {
  state.uploadFiles[key].push(...Array.from(event.target.files || []));
  renderDropzones();
}

function removeFile(key, index) {
  state.uploadFiles[key].splice(index, 1);
  renderDropzones();
}

async function runUploadAudit() {
  if (!state.selectedBillingType) {
    Toast.warning("Missing Type", "Please select a billing type first.");
    return;
  }
  for (const key of Object.keys(state.uploadFiles)) {
    if (!state.uploadFiles[key].length) {
      Toast.warning("Missing Files", `Please add at least one file to ${formatType(key)}.`);
      return;
    }
  }
  await executeAudit(() => api.auditUpload(state.selectedBillingType, state.uploadFiles));
}

async function executeAudit(auditFn) {
  state.isAuditing = true;
  showUploadStatusBar();
  const button = document.getElementById("btn-upload-audit");
  if (button) {
    button.disabled = true;
    button.innerHTML = '<div class="spinner"></div> Running Audit...';
  }

  animateAuditSteps();
  try {
    Toast.info("Audit Started", "Running agentic billing validation...");
    const result = await auditFn();
    state.auditResult = result;
    state.auditHistory.push(result);
    AUDIT_STEPS.forEach((step) => updateStepStatus(step.id, "completed"));
    Toast.success("Audit Complete", `Found ${result.validation_report?.findings?.length || 0} findings.`);
    showAuditCompleteButton(result);
  } catch (error) {
    Toast.error("Audit Failed", error.message);
    const titleEl = document.getElementById("status-bar-title");
    if (titleEl) {
      titleEl.innerHTML = `<span style="color: #f87171;">❌ Audit Failed: ${escapeHtml(error.message)}</span>`;
    }
  } finally {
    clearTimeout(state.auditTimeout);
    state.isAuditing = false;
    if (button) {
      button.disabled = false;
      button.innerHTML = "🚀 Run Upload Audit";
    }
  }
}

function showUploadStatusBar() {
  const container = document.getElementById("upload-status-bar");
  if (!container) return;
  container.style.display = "block";
  container.innerHTML = `
    <div class="status-bar">
      <div class="status-bar-title" id="status-bar-title">
        <div class="spinner"></div> Audit Pipeline — Processing...
      </div>
      <div class="status-steps">
        ${AUDIT_STEPS.map((step, index) => `
          <div class="status-step" id="step-${step.id}" data-index="${index}">
            <div class="step-indicator">${step.icon}</div>
            <div class="step-label">${step.label}</div>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

function showAuditCompleteButton(result) {
  const titleEl = document.getElementById("status-bar-title");
  if (!titleEl) return;
  const findingsCount = result.validation_report?.findings?.length || 0;
  const status = result.status || "unknown";
  const statusIcon = status === "valid" ? "✅" : status === "invalid" ? "❌" : "🔍";
  titleEl.innerHTML = `
    <div class="audit-complete-row">
      <span class="audit-complete-label">
        ${statusIcon} Audit Complete &mdash;
        <strong>${findingsCount} finding${findingsCount !== 1 ? "s" : ""}</strong> detected
      </span>
      <button class="btn btn-primary see-results-btn" onclick="router.navigate('results')">
        See Results →
      </button>
    </div>
  `;
}

function animateAuditSteps() {
  let index = 0;
  const tick = () => {
    if (index < AUDIT_STEPS.length) {
      updateStepStatus(AUDIT_STEPS[index].id, "active");
      if (index > 0) updateStepStatus(AUDIT_STEPS[index - 1].id, "completed");
      index += 1;
      state.auditTimeout = setTimeout(tick, 1800);
    }
  };
  state.auditTimeout = setTimeout(tick, 200);
}

function updateStepStatus(stepId, status) {
  const el = document.getElementById(`step-${stepId}`);
  if (el) el.className = `status-step ${status}`;
}

function initResults() {
  const container = document.getElementById("results-content");
  if (!state.auditResult) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📊</div>
        <div class="empty-state-title">No Audit Results</div>
        <div class="empty-state-desc">Run an audit first to see detailed results here.</div>
        <button class="btn btn-primary" onclick="router.navigate('audit')">Start Audit</button>
      </div>
    `;
    return;
  }
  renderResults(state.auditResult, container);
}

function renderResults(report, container) {
  const findings = report.validation_report?.findings || [];
  const totalVariance = findings.reduce((sum, finding) => sum + Math.abs(finding.variance_amount || 0), 0);
  const highCount = findings.filter((finding) => finding.severity === "high").length;
  const medCount = findings.filter((finding) => finding.severity === "medium").length;
  const lowCount = findings.filter((finding) => finding.severity === "low").length;

  container.innerHTML = `
    <div class="results-grid reveal visible">
      <div class="executive-summary">
        <div class="card-title"><span class="icon">📋</span> Executive Summary</div>
        <div class="summary-status">
          <strong>Status:</strong> ${statusBadge(report.status)}
          <strong class="type-label">Type:</strong> <span class="badge badge-info">${formatType(report.billing_type)}</span>
        </div>
        <div class="summary-text">${escapeHtml(report.executive_summary || "")}</div>
      </div>
      <div class="severity-chart">
        <div class="card-title"><span class="icon">📊</span> Severity Breakdown</div>
        ${renderDonutChart(highCount, medCount, lowCount)}
        <div class="chart-legend">
          <div class="legend-item"><span class="legend-dot high"></span> High — ${highCount}</div>
          <div class="legend-item"><span class="legend-dot medium"></span> Medium — ${medCount}</div>
          <div class="legend-item"><span class="legend-dot low"></span> Low — ${lowCount}</div>
        </div>
      </div>
    </div>

    <div class="kpi-grid reveal visible">
      <div class="kpi-card"><div class="kpi-header"><div class="kpi-icon red">🚨</div></div><div class="kpi-value">${formatCurrency(totalVariance)}</div><div class="kpi-label">Total Variance Impact</div></div>
      <div class="kpi-card"><div class="kpi-header"><div class="kpi-icon blue">🔍</div></div><div class="kpi-value">${findings.length}</div><div class="kpi-label">Total Findings</div></div>
      <div class="kpi-card"><div class="kpi-header"><div class="kpi-icon amber">📄</div></div><div class="kpi-value">${report.source_documents?.length || 0}</div><div class="kpi-label">Documents Analyzed</div></div>
      <div class="kpi-card"><div class="kpi-header"><div class="kpi-icon green">📊</div></div><div class="kpi-value">${Math.round((report.validation_report?.confidence || 0) * 100)}%</div><div class="kpi-label">Confidence Score</div></div>
    </div>

    <div class="glass-card section-full reveal visible">
      <div class="card-title"><span class="icon">💳</span> Payment Reconciliation</div>
      <div class="summary-status"><strong>Status:</strong> ${statusBadge(report.payment_summary?.status || "needs_review")}</div>
      <div class="summary-text">${escapeHtml(report.payment_summary?.reasoning || "No payment reconciliation data available.")}</div>
      <div class="payment-summary-card">
        <div class="payment-stat"><div class="payment-stat-value success">${formatCurrency(report.payment_summary?.paid_amount)}</div><div class="payment-stat-label">Paid Amount</div></div>
        <div class="payment-stat"><div class="payment-stat-value warning">${formatCurrency(report.payment_summary?.pending_amount)}</div><div class="payment-stat-label">Pending Amount</div></div>
        <div class="payment-stat"><div class="payment-stat-value info">${report.payment_summary?.issues?.length || 0}</div><div class="payment-stat-label">Payment Issues</div></div>
      </div>
      ${renderPaymentIssues(report.payment_summary?.issues || [])}
    </div>

    ${findings.length ? renderFindingsTable(findings) : ""}
    ${renderCorrectedInvoice(report.corrected_invoice)}
    ${renderGuardrails(report.guardrail_notes || [])}
    ${renderNextActions(report.next_actions || [])}
  `;
}

function renderPaymentIssues(issues) {
  if (!issues.length) return "";
  return `
    <div class="payment-issues">
      ${issues.map((issue) => `
        <div class="action-item">
          <div>${severityBadge(issue.severity)}</div>
          <div>
            <div class="issue-title">${escapeHtml(issue.issue_type)}</div>
            <div class="action-text">${escapeHtml(issue.description)}</div>
            ${issue.amount != null ? `<div class="finding-amount">${formatCurrency(issue.amount)}</div>` : ""}
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

function renderFindingsTable(findings) {
  return `
    <div class="findings-section reveal visible">
      <div class="card-title"><span class="icon">🔍</span> Detailed Findings</div>
      <div class="findings-table-wrapper">
        <table class="findings-table">
          <thead><tr><th></th><th>Type</th><th>Description</th><th>Severity</th><th>Variance</th><th>Action</th></tr></thead>
          <tbody>
            ${findings.map((finding, index) => `
              <tr>
                <td><button class="finding-expand" onclick="toggleFinding(${index})"><span id="expand-icon-${index}">▶</span></button></td>
                <td><span class="finding-type">${escapeHtml(finding.finding_type)}</span></td>
                <td><span class="finding-desc">${escapeHtml(finding.description)}</span></td>
                <td>${severityBadge(finding.severity)}</td>
                <td><span class="finding-amount">${finding.variance_amount != null ? formatCurrency(finding.variance_amount) : "—"}</span></td>
                <td><span class="muted-small">${escapeHtml(finding.recommended_action || "")}</span></td>
              </tr>
              <tr class="finding-details" id="finding-detail-${index}">
                <td colspan="6">
                  <div class="finding-detail-grid">
                    <div class="detail-item"><div class="detail-label">Expected Value</div><div class="detail-value">${escapeHtml(finding.expected_value || "—")}</div></div>
                    <div class="detail-item"><div class="detail-label">Actual Value</div><div class="detail-value">${escapeHtml(finding.actual_value || "—")}</div></div>
                    <div class="detail-item"><div class="detail-label">Source Documents</div><div class="detail-value">${escapeHtml((finding.source_documents || []).join(", ") || "—")}</div></div>
                    <div class="detail-item"><div class="detail-label">Recommended Action</div><div class="detail-value">${escapeHtml(finding.recommended_action || "—")}</div></div>
                  </div>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderCorrectedInvoice(invoice) {
  if (!invoice?.should_generate) return "";
  return `
    <div class="corrected-invoice reveal visible">
      <div class="card-title"><span class="icon">✏️</span> Corrected Invoice Draft</div>
      <div class="invoice-header">
        <div>
          <div class="invoice-customer">${escapeHtml(invoice.customer_name || "Customer")}</div>
          <div class="invoice-subtitle">${formatType(invoice.billing_type)} · ${escapeHtml(invoice.currency)}</div>
        </div>
        <div>${statusBadge("needs_review")}</div>
      </div>
      ${invoice.line_items?.length ? `
        <table class="invoice-lines">
          <thead><tr><th>Description</th><th>Qty</th><th>Unit Price</th><th>Amount</th></tr></thead>
          <tbody>
            ${invoice.line_items.map((line) => `
              <tr>
                <td><div>${escapeHtml(line.description)}</div><small>${escapeHtml(line.change_reason)}</small></td>
                <td>${line.quantity}</td>
                <td>${formatCurrency(line.unit_price)}</td>
                <td class="amount">${formatCurrency(line.amount)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
        <div class="invoice-total-row"><span>Total</span><span class="invoice-total-amount">${formatCurrency(invoice.total)}</span></div>
      ` : ""}
    </div>
  `;
}

function renderGuardrails(notes) {
  if (!notes.length) return "";
  return `
    <div class="guardrail-notes reveal visible">
      <div class="card-title"><span class="icon">🛡️</span> Guardrail Notes</div>
      ${notes.map((note) => `<div class="guardrail-item"><span>⚠️</span><span>${escapeHtml(note)}</span></div>`).join("")}
    </div>
  `;
}

function renderNextActions(actions) {
  if (!actions.length) return "";
  return `
    <div class="next-actions reveal visible">
      <div class="card-title"><span class="icon">✅</span> Recommended Next Actions</div>
      ${actions.map((action, index) => `
        <div class="action-item">
          <div class="action-check" id="action-check-${index}" onclick="toggleActionCheck(${index})"></div>
          <div class="action-text">${escapeHtml(action)}</div>
        </div>
      `).join("")}
    </div>
  `;
}

function renderDonutChart(high, medium, low) {
  const total = high + medium + low;
  if (!total) return `<div class="no-findings">No findings</div>`;
  const highPct = (high / total) * 100;
  const medPct = (medium / total) * 100;
  const lowPct = (low / total) * 100;
  return `
    <div class="donut-wrapper">
      <div class="donut-css" style="background: conic-gradient(var(--error) 0 ${highPct}%, var(--warning) ${highPct}% ${highPct + medPct}%, var(--info) ${highPct + medPct}% ${highPct + medPct + lowPct}%, rgba(255,255,255,0.08) 0);">
        <div><strong>${total}</strong><span>findings</span></div>
      </div>
    </div>
  `;
}

function showAuditResult(index) {
  state.auditResult = state.auditHistory[index];
  router.navigate("results");
}

function toggleFinding(index) {
  const detail = document.getElementById(`finding-detail-${index}`);
  const icon = document.getElementById(`expand-icon-${index}`);
  if (!detail || !icon) return;
  detail.classList.toggle("expanded");
  icon.textContent = detail.classList.contains("expanded") ? "▼" : "▶";
}

function toggleActionCheck(index) {
  const el = document.getElementById(`action-check-${index}`);
  if (!el) return;
  el.classList.toggle("checked");
  el.textContent = el.classList.contains("checked") ? "✓" : "";
}

function toggleSidebar() {
  document.getElementById("sidebar")?.classList.toggle("collapsed");
}

function formatCurrency(amount) {
  if (amount == null || Number.isNaN(Number(amount))) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 }).format(Number(amount));
}

function formatType(str) {
  return String(str || "").replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function severityBadge(severity = "medium") {
  const cls = severity === "high" ? "badge-high" : severity === "medium" ? "badge-medium" : "badge-low";
  return `<span class="badge ${cls}">${escapeHtml(severity)}</span>`;
}

function statusBadge(status = "needs_review") {
  const map = { valid: "badge-valid", invalid: "badge-invalid", needs_review: "badge-review" };
  const label = status === "needs_review" ? "Needs Review" : formatType(status);
  return `<span class="badge ${map[status] || "badge-info"}">${escapeHtml(label)}</span>`;
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

document.addEventListener("DOMContentLoaded", () => {
  router.register("home", initHome);
  router.register("upload", initUpload);
  router.register("audit", initAudit);
  router.register("results", initResults);
  router.register("pipeline", () => {});

  document.querySelectorAll(".nav-item").forEach((item) => {
    item.addEventListener("click", () => {
      if (item.dataset.route) router.navigate(item.dataset.route);
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && state.billingRulesModalOpen) closeBillingRulesModal();
  });

  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    if (localStorage.getItem("theme") === "light") {
      document.body.classList.add("light-theme");
      themeToggle.querySelector(".theme-icon").textContent = "☀️";
    }
    themeToggle.addEventListener("click", () => {
      document.body.classList.toggle("light-theme");
      const isLight = document.body.classList.contains("light-theme");
      localStorage.setItem("theme", isLight ? "light" : "dark");
      themeToggle.querySelector(".theme-icon").textContent = isLight ? "☀️" : "🌙";
    });
  }

  ensureBillingTypes();
  checkHealth();
  setInterval(checkHealth, 30000);
  router.navigate("home");
});

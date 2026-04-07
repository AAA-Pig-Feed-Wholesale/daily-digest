function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function parseDate(value) {
  const [y, m, d] = value.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function setStatus(text, spinning = false) {
  const statusText = document.getElementById("digest-status-text");
  const spinner = document.getElementById("status-spinner");
  statusText.textContent = text;
  if (spinning) {
    spinner.classList.remove("hidden");
  } else {
    spinner.classList.add("hidden");
  }
}

function setDetail(text) {
  const detail = document.getElementById("status-detail");
  if (detail) detail.textContent = text;
}

function renderMetrics(details) {
  const box = document.getElementById("status-metrics");
  if (!box) return;
  box.innerHTML = "";
  if (!details) {
    box.textContent = "暂无统计";
    return;
  }

  const parts = [];
  if (details.fetched_total !== undefined) {
    const breakdown = [];
    if (details.arxiv !== undefined) breakdown.push(`arXiv ${details.arxiv}`);
    if (details.huggingface !== undefined) breakdown.push(`HF ${details.huggingface}`);
    if (details.github !== undefined) breakdown.push(`GH ${details.github}`);
    if (details.info !== undefined) breakdown.push(`Info ${details.info}`);
    if (details.deduped !== undefined) breakdown.push(`去重 ${details.deduped}`);
    const suffix = breakdown.length ? `（${breakdown.join(" / ")}）` : "";
    parts.push(`抓取后：${details.fetched_total} 条${suffix}`);
  }
  if (details.scored !== undefined) {
    parts.push(`评分后：${details.scored} 条`);
  }
  if (details.stored !== undefined) {
    parts.push(`入库：${details.stored} 条`);
  }

  if (!parts.length) {
    box.textContent = "暂无统计";
    return;
  }

  parts.forEach(text => {
    const item = document.createElement("div");
    item.className = "metric";
    item.textContent = text;
    box.appendChild(item);
  });
}

function setStep(stepId, state) {
  const el = document.getElementById(stepId);
  if (!el) return;
  el.classList.remove("pending", "active", "done", "failed");
  el.classList.add(state);
}

function setProgress(value) {
  const fill = document.getElementById("progress-fill");
  if (!fill) return;
  const v = Math.max(0, Math.min(100, value || 0));
  fill.style.width = `${v}%`;
}

function resetSteps() {
  setStep("step-fetch", "pending");
  setStep("step-score", "pending");
  setStep("step-report", "pending");
  setProgress(0);
  renderMetrics(null);
}

function setStatusCollapsed(collapsed) {
  const section = document.getElementById("digest-status");
  const btn = document.getElementById("toggle-status");
  const body = document.getElementById("digest-status-body");
  if (!section || !btn) return;
  if (collapsed) {
    section.classList.add("collapsed");
    btn.textContent = "展开";
    btn.setAttribute("aria-expanded", "false");
    if (body) body.setAttribute("hidden", "");
  } else {
    section.classList.remove("collapsed");
    btn.textContent = "收起";
    btn.setAttribute("aria-expanded", "true");
    if (body) body.removeAttribute("hidden");
  }
  try {
    localStorage.setItem("digestStatusCollapsed", collapsed ? "1" : "0");
  } catch {
    // ignore storage errors
  }
}

function applyStatus(data) {
  const status = data?.status || "idle";
  const msg = data?.message || "就绪";
  const progress = data?.progress ?? 0;
  setStatus(msg, ["fetching", "scoring", "reporting"].includes(status));
  const updated = data?.updated_at ? new Date(data.updated_at).toLocaleTimeString() : "";
  setDetail(updated ? `${msg} · ${updated}` : msg);
  setProgress(progress);
  renderMetrics(data?.details);

  if (status === "fetching") {
    setStep("step-fetch", "active");
    setStep("step-score", "pending");
    setStep("step-report", "pending");
  } else if (status === "scoring") {
    setStep("step-fetch", "done");
    setStep("step-score", "active");
    setStep("step-report", "pending");
  } else if (status === "reporting") {
    setStep("step-fetch", "done");
    setStep("step-score", "done");
    setStep("step-report", "active");
  } else if (status === "done") {
    setStep("step-fetch", "done");
    setStep("step-score", "done");
    setStep("step-report", "done");
    setStatus("生成完成", false);
    setProgress(100);
  } else if (status === "failed") {
    setStep("step-fetch", "failed");
    setStep("step-score", "failed");
    setStep("step-report", "failed");
    setStatus("生成失败，请重试", false);
    setProgress(0);
  } else {
    resetSteps();
    setStatus("就绪", false);
  }
}

async function fetchStatus(dateStr) {
  const res = await fetch(`/api/daily-digest/status?date=${dateStr}`);
  return res.json();
}

async function loadDigest(dateStr) {
  const overviewEl = document.getElementById("digest-overview");
  const listEl = document.getElementById("digest-list");
  const countEl = document.getElementById("digest-count");
  const dateEl = document.getElementById("digest-date");

  overviewEl.textContent = "加载中...";
  listEl.innerHTML = "";
  countEl.textContent = "-";
  dateEl.textContent = dateStr;

  try {
    const status = await fetchStatus(dateStr);
    applyStatus(status);
  } catch {
    setStatus("状态获取失败", false);
  }

  const res = await fetch(`/api/daily-digest?date=${dateStr}`);
  const data = await res.json();
  if (!data.report) {
    overviewEl.textContent = "暂无日报，可点击“生成日报”。";
    countEl.textContent = "0";
    return;
  }

  overviewEl.textContent = data.report.summary_overview || "-";
  countEl.textContent = String(data.report.item_count ?? data.items.length);

  data.items.forEach(item => {
    const card = document.createElement("div");
    card.className = "digest-item";
    const title = document.createElement("h3");
    const link = document.createElement("a");
    link.href = item.url;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = item.title || item.url;
    title.appendChild(link);

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.innerHTML = `
      <span class="pill source">来源：${item.source_name || item.source}</span>
      <span class="pill">发布时间：${item.published_at ? item.published_at.slice(0,10) : "未知"}</span>
      <span class="pill score">相关性：${item.relevance_score ?? "-"}</span>
    `;

    const summary = document.createElement("div");
    summary.className = "summary";
    summary.textContent = item.short_summary || "";

    const reason = document.createElement("div");
    reason.className = "reason";
    reason.textContent = item.relevance_reason || "";

    card.appendChild(title);
    card.appendChild(meta);
    if (summary.textContent) card.appendChild(summary);
    if (reason.textContent) card.appendChild(reason);
    listEl.appendChild(card);
  });
}

async function runDigest(dateStr) {
  const btn = document.getElementById("run-digest");
  btn.disabled = true;
  btn.textContent = "生成中...";
  resetSteps();
  setStatus("已提交生成任务", true);

  let polling = true;
  const poll = async () => {
    if (!polling) return;
    try {
      const status = await fetchStatus(dateStr);
      applyStatus(status);
      if (status.status === "done" || status.status === "failed") {
        polling = false;
        return;
      }
    } catch {
      // ignore transient errors
    }
    setTimeout(poll, 5000);
  };

  poll();

  try {
    await fetch("/api/daily-digest/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date: dateStr, force: true })
    });
    polling = false;
    await loadDigest(dateStr);
  } catch (err) {
    polling = false;
    setStatus("生成失败，请重试", false);
    applyStatus({ status: "failed" });
  } finally {
    btn.disabled = false;
    btn.textContent = "生成日报";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const datePicker = document.getElementById("date-picker");
  const runBtn = document.getElementById("run-digest");
  const prevBtn = document.getElementById("prev-day");
  const nextBtn = document.getElementById("next-day");
  const toggleBtn = document.getElementById("toggle-status");

  const initialDate = datePicker.value;
  loadDigest(initialDate);

  let collapsed = false;
  try {
    collapsed = localStorage.getItem("digestStatusCollapsed") === "1";
  } catch {
    collapsed = false;
  }
  setStatusCollapsed(collapsed);
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const isCollapsed = document.getElementById("digest-status")?.classList.contains("collapsed");
      setStatusCollapsed(!isCollapsed);
    });
  }

  runBtn.addEventListener("click", () => runDigest(datePicker.value));

  datePicker.addEventListener("change", () => {
    loadDigest(datePicker.value);
  });

  prevBtn.addEventListener("click", () => {
    const d = parseDate(datePicker.value);
    d.setDate(d.getDate() - 1);
    datePicker.value = formatDate(d);
    loadDigest(datePicker.value);
  });

  nextBtn.addEventListener("click", () => {
    const d = parseDate(datePicker.value);
    d.setDate(d.getDate() + 1);
    datePicker.value = formatDate(d);
    loadDigest(datePicker.value);
  });
});

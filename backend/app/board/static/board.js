const state = {
  tasks: [],
  tasksById: new Map(),
  agents: [],
  summaries: [],
  approvals: [],
  recurring: [],
  system: { health: [], events: [], task_counts: [] },
};

const columns = [
  { key: "backlog", label: "Backlog" },
  { key: "todo", label: "To Do" },
  { key: "running", label: "Running" },
  { key: "review", label: "Review" },
  { key: "done", label: "Done" },
];

const boardGrid = document.getElementById("board-grid");
const headerMeta = document.getElementById("header-meta");
const taskForm = document.getElementById("task-form");
const taskFormPanel = document.getElementById("task-form-panel");
const openTaskForm = document.getElementById("open-task-form");
const detailDialog = document.getElementById("task-detail-dialog");
const detailContent = document.getElementById("detail-content");
const detailClose = document.getElementById("detail-close");

openTaskForm.addEventListener("click", () => {
  taskFormPanel.hidden = !taskFormPanel.hidden;
});

detailClose.addEventListener("click", () => detailDialog.close());

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(taskForm);
  const payload = Object.fromEntries(formData.entries());

  const response = await fetch("/board/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    alert("Could not create task.");
    return;
  }

  taskForm.reset();
  taskFormPanel.hidden = true;
  await refresh();
});

async function refresh() {
  const [tasks, agents, summaries, approvals, recurring, system] = await Promise.all([
    fetchJson("/board/api/tasks"),
    fetchJson("/board/api/agents"),
    fetchJson("/board/api/summaries"),
    fetchJson("/board/api/approvals"),
    fetchJson("/board/api/recurring"),
    fetchJson("/board/api/system"),
  ]);

  state.tasks = tasks.items;
  state.tasksById = new Map(tasks.items.map((item) => [String(item.id), item]));
  state.agents = agents.items;
  state.summaries = summaries.items;
  state.approvals = approvals.items;
  state.recurring = recurring.items;
  state.system = system;

  renderHeader();
  renderBoard();
  renderSummaries();
  renderAgents();
  renderApprovals();
  renderRecurring();
  renderSystem();
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return response.json();
}

function renderHeader() {
  const total = state.tasks.length;
  const running = state.tasks.filter((task) => task.status === "running").length;
  const pendingApprovals = state.approvals.filter((item) => item.state === "pending").length;
  headerMeta.innerHTML = `
    <span>${total} tasks</span>
    <span>${running} running</span>
    <span>${pendingApprovals} approvals pending</span>
  `;
}

function renderBoard() {
  boardGrid.innerHTML = "";

  columns.forEach((column) => {
    const items = state.tasks.filter((task) => task.status === column.key);
    const columnEl = document.createElement("section");
    columnEl.className = "board-column";
    columnEl.innerHTML = `
      <div class="column-meta">
        <h3>${column.label}</h3>
        <span>${items.length}</span>
      </div>
      <div class="task-list"></div>
    `;

    const list = columnEl.querySelector(".task-list");
    if (!items.length) {
      const empty = document.createElement("div");
      empty.className = "intel-item";
      empty.innerHTML = "<h4>Queue clear</h4><p>No tasks in this lane.</p>";
      list.appendChild(empty);
    }

    items.forEach((task) => list.appendChild(renderTaskCard(task)));
    boardGrid.appendChild(columnEl);
  });
}

function renderTaskCard(task) {
  const card = document.createElement("article");
  card.className = "task-card";
  card.innerHTML = `
    <div class="card-topline">
      <span class="badge">${task.assigned_agent}</span>
      <span class="priority-${task.priority}">${task.priority}</span>
    </div>
    <h4>${escapeHtml(task.title)}</h4>
    <p>${escapeHtml(task.summary)}</p>
    <div class="card-footer">
      <span class="status-pill">${task.status}</span>
      <span>${formatDate(task.updated_at || task.created_at)}</span>
    </div>
    <p>${escapeHtml(task.latest_activity)}</p>
  `;

  card.addEventListener("click", () => openDetail(task.id));
  return card;
}

function renderSummaries() {
  fillStack("summary-list", state.summaries, (item) => `
    <div class="intel-item">
      <div class="intel-inline">
        <h4>${escapeHtml(item.title)}</h4>
        <span class="badge">${item.source}</span>
      </div>
      <p>${escapeHtml(item.body)}</p>
    </div>
  `);
}

function renderAgents() {
  fillStack("agent-list", state.agents, (item) => `
    <div class="intel-item">
      <div class="intel-inline">
        <h4>${escapeHtml(item.agent_name)}</h4>
        <span class="status-pill">${item.state}</span>
      </div>
      <p>${escapeHtml(item.current_task || "Standing by")}</p>
      <p>${escapeHtml(item.latest_activity)}</p>
    </div>
  `);
}

function renderApprovals() {
  fillStack("approval-list", state.approvals, (item) => `
    <div class="intel-item">
      <div class="intel-inline">
        <h4>${escapeHtml(item.title)}</h4>
        <span class="badge">${item.state}</span>
      </div>
      <p>${escapeHtml(item.summary)}</p>
    </div>
  `);
}

function renderRecurring() {
  fillStack("recurring-list", state.recurring, (item) => `
    <div class="intel-item">
      <div class="intel-inline">
        <h4>${escapeHtml(item.title)}</h4>
        <span class="badge">${escapeHtml(item.owner)}</span>
      </div>
      <p>${escapeHtml(item.schedule)} · next ${formatDate(item.next_run_at)}</p>
    </div>
  `);
}

function renderSystem() {
  fillStack("system-health", state.system.health, (item) => `
    <div class="intel-item">
      <div class="intel-inline">
        <h4>${escapeHtml(item.name)}</h4>
        <span class="status-pill">${item.status}</span>
      </div>
      <p>${escapeHtml(item.detail)}</p>
      <p>Source: ${escapeHtml(item.source)}</p>
    </div>
  `);

  fillStack("system-events", state.system.events, (item) => `
    <div class="intel-item">
      <div class="intel-inline">
        <h4>${escapeHtml(item.event_type)}</h4>
        <span class="badge">${escapeHtml(item.source)}</span>
      </div>
      <p>${escapeHtml(item.message)}</p>
    </div>
  `);
}

function openDetail(taskId) {
  const task = state.tasksById.get(String(taskId));
  if (!task) return;

  detailContent.innerHTML = `
    <p class="section-kicker">Task detail</p>
    <h2>${escapeHtml(task.title)}</h2>
    <div class="intel-inline">
      <span class="badge">${escapeHtml(task.assigned_agent)}</span>
      <span class="status-pill">${escapeHtml(task.status)}</span>
      <span class="badge">${escapeHtml(task.priority)}</span>
      <span class="badge">${escapeHtml(task.source)}</span>
    </div>

    <section class="detail-section">
      <h4>Summary</h4>
      <p>${escapeHtml(task.summary)}</p>
    </section>

    <section class="detail-section">
      <h4>Latest activity</h4>
      <p>${escapeHtml(task.latest_activity)}</p>
    </section>

    <section class="detail-section">
      <h4>Detail</h4>
      <p>${escapeHtml(task.detail || "No additional detail yet.")}</p>
    </section>

    <section class="detail-section">
      <h4>Timestamps</h4>
      <p>Created: ${formatDate(task.created_at)}</p>
      <p>Updated: ${formatDate(task.updated_at)}</p>
    </section>
  `;

  detailDialog.showModal();
}

function fillStack(id, items, renderer) {
  const root = document.getElementById(id);
  root.innerHTML = items.map(renderer).join("");
}

function formatDate(value) {
  if (!value) return "n/a";
  const normalized = value.endsWith("Z") ? value : `${value}Z`;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

refresh().catch((error) => {
  console.error(error);
  headerMeta.textContent = "Board bootstrap failed";
});

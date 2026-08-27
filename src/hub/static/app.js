const state = {
  items: [],
  folder: "Tudo",
  subfolder: "",
  status: "open",
  view: "inbox",
  q: "",
  selected: null,
  folders: [],
  subfolderSeeds: {},
  finance: null,
  reports: null,
};

const VIEWS = [
  { id: "inbox", label: "Arquivo" },
  { id: "finance", label: "Finanças" },
  { id: "reports", label: "Relatórios" },
];

const STATUS_TABS = [
  { id: "open", label: "Abertos" },
  { id: "done", label: "Concluídos" },
  { id: "discarded", label: "Descartados" },
  { id: "all", label: "Todos" },
];

const KIND_LABEL = {
  note: "Nota",
  task: "Tarefa",
  link: "Link",
  document: "Documento",
  shopping: "Compras",
  workout: "Treino",
  prompt: "Prompt",
  finance: "Finanças",
  media: "Mídia",
};

async function api(path, options) {
  const res = await fetch(path, {
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function isOpen(item) {
  return item.status === "inbox" || item.status === "active";
}

function money(item) {
  if (item.financials?.length) return item.financials;
  return item.financial ? [item.financial] : [];
}

function visible() {
  const q = state.q.trim().toLowerCase();
  return state.items.filter((item) => {
    if (state.folder !== "Tudo" && item.folder !== state.folder) return false;
    if (state.subfolder && item.subfolder !== state.subfolder) return false;
    if (state.status === "open" && !isOpen(item)) return false;
    if (state.status === "done" && item.status !== "done") return false;
    if (state.status === "discarded" && item.status !== "discarded") return false;
    if (!q) return true;
    const blob = [
      item.title, item.subtitle, item.summary, item.body, item.raw_text, item.folder,
      item.subfolder, item.kind, item.url, ...(item.tags || []),
      ...(item.checklist || []).map((c) => c.text),
    ].join(" ").toLowerCase();
    return blob.includes(q);
  });
}

function folderCounts() {
  const counts = { Tudo: 0 };
  for (const item of state.items) {
    if (!isOpen(item)) continue;
    counts.Tudo += 1;
    counts[item.folder] = (counts[item.folder] || 0) + 1;
  }
  return counts;
}

function subfolderCounts() {
  const counts = {};
  for (const item of state.items) {
    if (!isOpen(item) || item.folder !== state.folder || !item.subfolder) continue;
    counts[item.subfolder] = (counts[item.subfolder] || 0) + 1;
  }
  return counts;
}

function setMenu(open) {
  document.body.classList.toggle("menu-open", open);
}

function renderViews() {
  document.getElementById("views").innerHTML = VIEWS.map((view) => {
    const active = state.view === view.id ? "active" : "";
    return `<button data-view="${view.id}" class="${active}">${view.label}</button>`;
  }).join("");
  document.querySelectorAll("[data-view]").forEach((btn) => {
    btn.onclick = () => {
      state.view = btn.dataset.view;
      setMenu(false);
      render();
    };
  });
}

function renderFolders(folders) {
  const counts = folderCounts();
  const names = ["Tudo", ...folders];
  document.getElementById("folders").innerHTML = names.map((name) => {
    const n = counts[name] || 0;
    const active = state.folder === name ? "active" : "";
    return `<button data-folder="${name}" class="${active}"><span>${name}</span><span>${n}</span></button>`;
  }).join("");
  document.querySelectorAll("[data-folder]").forEach((btn) => {
    btn.onclick = () => {
      state.folder = btn.dataset.folder;
      state.subfolder = "";
      state.view = "inbox";
      setMenu(false);
      render();
    };
  });
}

function renderSubfolders() {
  const el = document.getElementById("subfolders");
  if (state.view !== "inbox" || state.folder === "Tudo") {
    el.innerHTML = "";
    return;
  }
  const counts = subfolderCounts();
  const names = [...new Set([...(state.subfolderSeeds[state.folder] || []), ...Object.keys(counts)])];
  if (!names.length) {
    el.innerHTML = "";
    return;
  }
  el.innerHTML = ["Todas", ...names].map((name) => {
    const id = name === "Todas" ? "" : name;
    const active = state.subfolder === id ? "active" : "";
    const n = name === "Todas" ? "" : (counts[name] || 0);
    return `<button data-sub="${id}" class="${active}">${name}${n ? " " + n : ""}</button>`;
  }).join("");
  el.querySelectorAll("[data-sub]").forEach((btn) => {
    btn.onclick = () => {
      state.subfolder = btn.dataset.sub;
      setMenu(false);
      render();
    };
  });
}

function renderStatus() {
  document.getElementById("statusFilters").innerHTML = STATUS_TABS.map((tab) => {
    const active = state.status === tab.id ? "active" : "";
    return `<button data-status="${tab.id}" class="${active}">${tab.label}</button>`;
  }).join("");
  document.querySelectorAll("[data-status]").forEach((btn) => {
    btn.onclick = () => {
      state.status = btn.dataset.status;
      render();
    };
  });
}

function snippet(item) {
  const facts = money(item);
  if (facts.length) {
    const f = facts[0];
    const extra = facts.length > 1 ? ` +${facts.length - 1}` : "";
    return `${f.kind} · ${f.merchant || ""} · R$ ${f.amount ?? "—"} · ${f.occurred_at || f.due_at || ""}${extra}`;
  }
  if (item.checklist?.length) {
    const left = item.checklist.filter((c) => !c.checked).length;
    return `${item.checklist.length - left}/${item.checklist.length} itens`;
  }
  return item.summary || item.body || item.raw_text || "";
}

function brl(n) {
  return Number(n || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function workspace() {
  return document.getElementById("workspace");
}

function renderGrid() {
  const items = visible();
  const grid = workspace();
  grid.className = "grid";
  if (!items.length) {
    grid.innerHTML = `<p class="empty">Nada neste recorte. Mande um audio, link, PDF ou lista no Telegram.</p>`;
    return;
  }
  grid.innerHTML = items.map((item) => {
    const checks = (item.checklist || []).slice(0, 4).map((c) =>
      `<li><input type="checkbox" ${c.checked ? "checked" : ""} disabled/> ${escapeHtml(c.text)}</li>`
    ).join("");
    const place = item.subfolder ? `${item.folder} / ${item.subfolder}` : item.folder;
    return `
      <article class="card kind-${item.kind}" data-id="${item.id}">
        <div class="kicker"><span>${KIND_LABEL[item.kind] || item.kind} · ${escapeHtml(place)}</span><span>${(item.created_at || "").slice(5, 16)}</span></div>
        <h2>${escapeHtml(item.title || item.summary || item.id)}</h2>
        ${item.subtitle ? `<p class="subtitle">${escapeHtml(item.subtitle)}</p>` : ""}
        <p>${escapeHtml(snippet(item).slice(0, 160))}</p>
        ${checks ? `<ul class="check">${checks}</ul>` : ""}
        <div class="meta">${(item.tags || []).map((t) => "#" + t).join(" ")}</div>
      </article>`;
  }).join("");
  grid.querySelectorAll(".card").forEach((card) => {
    card.onclick = () => openDrawer(card.dataset.id);
  });
}

function typeLabel(kind) {
  return { receita: "Receita", gasto: "Gasto", boleto: "Boleto" }[kind] || kind;
}

function catLabel(cat) {
  return {
    renda: "Renda",
    alimentacao: "Alimentação",
    transporte: "Transporte",
    casa: "Casa",
    saude: "Saúde",
    lazer: "Lazer",
    outros: "Outros",
  }[cat] || cat || "";
}

function renderFinance() {
  const data = state.finance;
  const page = workspace();
  page.className = "page";
  if (!data) {
    page.innerHTML = `<p class="empty">Carregando P&amp;L…</p>`;
    return;
  }
  const rows = (data.entries || []).map((row) => `
    <tr data-id="${row.item_id}">
      <td>${escapeHtml((row.occurred_at || "").slice(0, 10))}</td>
      <td>${escapeHtml(typeLabel(row.kind))}</td>
      <td>${escapeHtml(catLabel(row.category))}</td>
      <td>${escapeHtml(row.merchant || row.title || "")}</td>
      <td class="${row.kind === "receita" ? "income" : "expense"}">${escapeHtml(brl(row.amount))}</td>
    </tr>`).join("");
  page.innerHTML = `
    <div class="stats">
      <div class="stat"><span>Entradas · ${escapeHtml(data.month)}</span><strong class="income">${escapeHtml(brl(data.income))}</strong></div>
      <div class="stat"><span>Saídas</span><strong class="expense">${escapeHtml(brl(data.expense))}</strong></div>
      <div class="stat"><span>Saldo</span><strong>${escapeHtml(brl(data.balance))}</strong></div>
    </div>
    <p class="hint">Mande no Telegram: “gastei 40 no almoço, recebi 200 no PIX”.</p>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Data</th><th>Tipo</th><th>Categoria</th><th>Descrição</th><th>Valor</th></tr></thead>
        <tbody>${rows || `<tr><td colspan="5">Sem lançamentos neste mês.</td></tr>`}</tbody>
      </table>
    </div>`;
  page.querySelectorAll("tr[data-id]").forEach((row) => {
    row.onclick = () => {
      state.view = "inbox";
      openDrawer(row.dataset.id);
      render();
    };
  });
}

function renderReports() {
  const data = state.reports;
  const page = workspace();
  page.className = "page";
  if (!data) {
    page.innerHTML = `<p class="empty">Carregando relatórios…</p>`;
    return;
  }
  const folders = Object.entries(data.folders || {}).map(([name, n]) =>
    `<tr><td>${escapeHtml(name)}</td><td>${n}</td></tr>`
  ).join("");
  const agenda = data.agenda || {};
  const tasks = (agenda.tasks || []).map((t) => `<li>${escapeHtml(t)}</li>`).join("")
    || "<li>Nada na Agenda desta semana.</li>";
  page.innerHTML = `
    <div class="stats">
      <div class="stat"><span>Capturas · 7 dias</span><strong>${data.captures_7d || 0}</strong></div>
      <div class="stat"><span>Calendar pendente</span><strong>${data.pending_calendar || 0}</strong></div>
    </div>
    <div class="split">
      <div>
        <h2>Pastas</h2>
        <div class="table-wrap"><table><tbody>${folders}</tbody></table></div>
      </div>
      <div>
        <h2>Agenda da semana</h2>
        <div class="panel-box"><ul class="check">${tasks}</ul></div>
      </div>
    </div>`;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function openDrawer(id) {
  state.selected = id;
  setMenu(false);
  renderDrawer();
}

async function patchItem(id, body) {
  const updated = await api(`/api/items/${id}`, { method: "PATCH", body: JSON.stringify(body) });
  state.items = state.items.map((item) => (item.id === id ? updated : item));
  render();
}

function renderDrawer() {
  const item = state.items.find((row) => row.id === state.selected);
  const drawer = document.getElementById("drawer");
  const body = document.body;
  if (!item || state.view !== "inbox") {
    drawer.hidden = true;
    drawer.classList.add("hidden");
    body.classList.remove("open");
    return;
  }
  drawer.hidden = false;
  drawer.classList.remove("hidden");
  body.classList.add("open");
  const media = (item.media_paths || []).map((_, idx) => {
    const src = `/api/files/${item.id}/${idx}`;
    const path = item.media_paths[idx] || "";
    if (path.toLowerCase().endsWith(".pdf")) {
      return `<iframe class="preview pdf" src="${src}"></iframe>`;
    }
    if (/\.(mp3|wav|ogg|m4a|flac)$/i.test(path)) {
      return `<audio class="preview" controls src="${src}"></audio>`;
    }
    return `<img class="preview" src="${src}" alt="midia"/>`;
  }).join("");
  const checks = (item.checklist || []).map((c) =>
    `<li><label><input type="checkbox" data-check="${c.id}" ${c.checked ? "checked" : ""}/> ${escapeHtml(c.text)}</label></li>`
  ).join("");
  const folderOpts = [...new Set([item.folder, ...(state.folders || [])].filter(Boolean))]
    .map((f) => `<option ${f === item.folder ? "selected" : ""}>${f}</option>`).join("");
  const subNames = [...new Set([item.subfolder, ...(state.subfolderSeeds[item.folder] || [])].filter(Boolean))];
  const subOpts = ["", ...subNames].map((s) =>
    `<option value="${escapeHtml(s)}" ${s === (item.subfolder || "") ? "selected" : ""}>${s || "—"}</option>`
  ).join("");
  const facts = money(item).map((f) =>
    `<p>${escapeHtml(f.kind)} · ${escapeHtml(f.category || "")} · ${escapeHtml(f.merchant || "")} · R$ ${f.amount ?? "—"}</p>`
  ).join("");
  drawer.innerHTML = `
    <div class="kicker">${KIND_LABEL[item.kind] || item.kind}</div>
    <h1>${escapeHtml(item.title || item.summary || "")}</h1>
    ${item.subtitle ? `<p class="subtitle">${escapeHtml(item.subtitle)}</p>` : ""}
    <div class="row">
      <select id="folder">${folderOpts}</select>
      <select id="subfolder">${subOpts}</select>
      ${item.url ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">Abrir no computador</a>` : ""}
    </div>
    ${media}
    ${facts}
    ${checks ? `<ul class="check">${checks}</ul>` : ""}
    <textarea id="body">${escapeHtml(item.body || item.raw_text || item.agent_reply || "")}</textarea>
    <div class="row">
      <button class="primary" id="save">Salvar</button>
      <button id="done">Concluir</button>
      <button class="ghost" id="discard">Descartar</button>
    </div>
  `;
  drawer.querySelector("#folder").onchange = (ev) => patchItem(item.id, { folder: ev.target.value, status: "active" });
  drawer.querySelector("#subfolder").onchange = (ev) => patchItem(item.id, { subfolder: ev.target.value });
  drawer.querySelector("#save").onclick = () => patchItem(item.id, { body: drawer.querySelector("#body").value, title: item.title });
  drawer.querySelector("#done").onclick = () => patchItem(item.id, { status: "done" });
  drawer.querySelector("#discard").onclick = () => patchItem(item.id, { status: "discarded" });
  drawer.querySelectorAll("[data-check]").forEach((box) => {
    box.onchange = async () => {
      const updated = await api(`/api/items/${item.id}/check/${box.dataset.check}`, {
        method: "PATCH",
        body: JSON.stringify({ checked: box.checked }),
      });
      state.items = state.items.map((row) => (row.id === item.id ? updated : row));
      render();
    };
  });
}

function render() {
  const inboxMode = state.view === "inbox";
  document.getElementById("searchWrap").hidden = !inboxMode;
  document.getElementById("statusFilters").hidden = !inboxMode;
  document.getElementById("makeBar").hidden = !inboxMode;
  const title = document.getElementById("pageTitle");
  title.hidden = inboxMode;
  title.textContent = state.view === "finance" ? "Finanças" : state.view === "reports" ? "Relatórios" : "";
  renderViews();
  renderStatus();
  renderFolders(state.folders || []);
  renderSubfolders();
  if (state.view === "finance") renderFinance();
  else if (state.view === "reports") renderReports();
  else renderGrid();
  renderDrawer();
}

async function refresh() {
  const meta = await api("/api/meta");
  state.folders = meta.folders;
  state.subfolderSeeds = meta.subfolders || {};
  const payload = await api("/api/inbox");
  state.items = payload.items || [];
  if (state.view === "finance" || !state.finance) {
    state.finance = await api("/api/finance");
  }
  if (state.view === "reports" || !state.reports) {
    state.reports = await api("/api/reports");
  }
}

async function boot() {
  const view = new URLSearchParams(location.search).get("view");
  if (["inbox", "finance", "reports"].includes(view)) state.view = view;
  workspace().innerHTML = `<p class="empty">Carregando arquivo…</p>`;
  document.getElementById("q").addEventListener("input", (ev) => {
    state.q = ev.target.value;
    render();
  });
  const status = document.getElementById("genStatus");
  document.getElementById("btnRecap").onclick = async () => {
    status.textContent = "Pedindo vídeo…";
    const result = await api("/api/reports/recap", { method: "POST" });
    status.textContent = result.message || JSON.stringify(result);
  };
  document.getElementById("btnTheme").onclick = async () => {
    status.textContent = "Pedindo áudio…";
    const result = await api("/api/reports/theme", { method: "POST" });
    status.textContent = result.message || result.prompt || JSON.stringify(result);
  };
  document.getElementById("menuBtn").onclick = () => {
    document.body.classList.toggle("menu-open");
  };
  document.getElementById("menuScrim").onclick = () => setMenu(false);
  await refresh();
  render();
  setInterval(async () => {
    try {
      await refresh();
      render();
    } catch (err) {
      console.error(err);
    }
  }, 8000);
}

boot().catch((err) => {
  workspace().innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
});

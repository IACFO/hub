const state = {
  items: [],
  folder: "Tudo",
  status: "open",
  q: "",
  selected: null,
};

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
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function isOpen(item) {
  return item.status === "inbox" || item.status === "active";
}

function visible() {
  const q = state.q.trim().toLowerCase();
  return state.items.filter((item) => {
    if (state.folder !== "Tudo" && item.folder !== state.folder) return false;
    if (state.status === "open" && !isOpen(item)) return false;
    if (state.status === "done" && item.status !== "done") return false;
    if (state.status === "discarded" && item.status !== "discarded") return false;
    if (!q) return true;
    const blob = [
      item.title, item.summary, item.body, item.raw_text, item.folder, item.kind,
      item.url, ...(item.tags || []), ...(item.checklist || []).map((c) => c.text),
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
  if (item.financial) {
    const f = item.financial;
    return `${f.kind} · ${f.merchant || ""} · R$ ${f.amount ?? "—"} · ${f.due_at || ""}`;
  }
  if (item.checklist?.length) {
    const left = item.checklist.filter((c) => !c.checked).length;
    return `${item.checklist.length - left}/${item.checklist.length} itens`;
  }
  return item.summary || item.body || item.raw_text || "";
}

function renderGrid() {
  const items = visible();
  const grid = document.getElementById("grid");
  if (!items.length) {
    grid.innerHTML = `<p class="empty">Nada neste recorte. Mande um audio, link, PDF ou lista no Telegram.</p>`;
    return;
  }
  grid.innerHTML = items.map((item) => {
    const checks = (item.checklist || []).slice(0, 4).map((c) =>
      `<li><input type="checkbox" ${c.checked ? "checked" : ""} disabled/> ${escapeHtml(c.text)}</li>`
    ).join("");
    return `
      <article class="card kind-${item.kind}" data-id="${item.id}">
        <div class="kicker"><span>${KIND_LABEL[item.kind] || item.kind} · ${escapeHtml(item.folder)}</span><span>${(item.created_at || "").slice(5, 16)}</span></div>
        <h2>${escapeHtml(item.title || item.summary || item.id)}</h2>
        <p>${escapeHtml(snippet(item).slice(0, 160))}</p>
        ${checks ? `<ul class="check">${checks}</ul>` : ""}
        <div class="meta">${(item.tags || []).map((t) => "#" + t).join(" ")}</div>
      </article>`;
  }).join("");
  grid.querySelectorAll(".card").forEach((card) => {
    card.onclick = () => openDrawer(card.dataset.id);
  });
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function openDrawer(id) {
  state.selected = id;
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
  if (!item) {
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
    return `<img class="preview" src="${src}" alt="midia"/>`;
  }).join("");
  const checks = (item.checklist || []).map((c) =>
    `<li><label><input type="checkbox" data-check="${c.id}" ${c.checked ? "checked" : ""}/> ${escapeHtml(c.text)}</label></li>`
  ).join("");
  const folderOpts = ["Inbox", "Agenda", "Financas", "Compras", "Documentos", "Links", "Treino", "Prompts", "Ideias", "Saude"]
    .map((f) => `<option ${f === item.folder ? "selected" : ""}>${f}</option>`).join("");
  drawer.innerHTML = `
    <div class="kicker">${KIND_LABEL[item.kind] || item.kind}</div>
    <h1>${escapeHtml(item.title || item.summary || "")}</h1>
    <div class="row">
      <select id="folder">${folderOpts}</select>
      ${item.url ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">Abrir no computador</a>` : ""}
    </div>
    ${media}
    ${item.financial ? `<p>${escapeHtml(snippet(item))}</p>` : ""}
    ${item.financial?.barcode ? `<p class="meta">${escapeHtml(item.financial.barcode)}</p>` : ""}
    ${checks ? `<ul class="check">${checks}</ul>` : ""}
    <textarea id="body">${escapeHtml(item.body || item.raw_text || item.agent_reply || "")}</textarea>
    <div class="row">
      <button class="primary" id="save">Salvar</button>
      <button id="done">Concluir</button>
      <button class="ghost" id="discard">Descartar</button>
    </div>
  `;
  drawer.querySelector("#folder").onchange = (ev) => patchItem(item.id, { folder: ev.target.value, status: "active" });
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
  renderStatus();
  renderFolders(state.folders || []);
  renderGrid();
  renderDrawer();
}

async function boot() {
  const meta = await api("/api/meta");
  state.folders = meta.folders;
  const payload = await api("/api/inbox");
  state.items = payload.items || [];
  document.getElementById("q").addEventListener("input", (ev) => {
    state.q = ev.target.value;
    render();
  });
  render();
  setInterval(async () => {
    const next = await api("/api/inbox");
    state.items = next.items || [];
    render();
  }, 8000);
}

boot().catch((err) => {
  document.getElementById("grid").innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
});

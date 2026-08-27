const ALL = "Tudo";

const state = {
  items: [],
  folder: ALL,
  subfolder: "",
  status: "open",
  view: "inbox",
  q: "",
  selected: null,
  folders: [],
  subfolderSeeds: {},
  finance: null,
  reports: null,
  lang: localStorage.getItem("hub_lang") || "en",
};

const I18N = {
  en: {
    brandTag: "living archive",
    railFoot: "Capture on Telegram<br/>Action on Calendar",
    search: "Search",
    searchPh: "invoice, workout, instagram, ID, suno…",
    menuOpen: "Open folders",
    weekVideo: "Week video",
    weekAudio: "Week audio",
    askingVideo: "Requesting video…",
    askingAudio: "Requesting audio…",
    loadingArchive: "Loading archive…",
    loadingFinance: "Loading P&L…",
    loadingReports: "Loading reports…",
    emptyInbox: "Nothing in this slice. Send audio, a link, a PDF, or a list on Telegram.",
    itemsOf: (done, total) => `${done}/${total} items`,
    openLink: "Open on computer",
    save: "Save",
    done: "Done",
    discard: "Discard",
    income: "Income",
    expense: "Spend",
    balance: "Balance",
    incomeLabel: (month) => `Income · ${month}`,
    financeHint: 'Send on Telegram: "spent 40 on lunch, received 200 via PIX".',
    date: "Date",
    type: "Type",
    category: "Category",
    description: "Description",
    amount: "Amount",
    noEntries: "No entries this month.",
    captures7d: "Captures · 7 days",
    pendingCal: "Pending Calendar",
    folders: "Folders",
    weekAgenda: "This week’s agenda",
    noAgenda: "Nothing on the Agenda this week.",
    all: "All",
    allSub: "All",
    views: { inbox: "Archive", finance: "Finance", reports: "Reports" },
    status: { open: "Open", done: "Done", discarded: "Discarded", all: "All" },
    kinds: {
      note: "Note",
      task: "Task",
      link: "Link",
      document: "Document",
      shopping: "Shopping",
      workout: "Workout",
      prompt: "Prompt",
      finance: "Finance",
      media: "Media",
    },
    moneyKinds: { receita: "Income", gasto: "Expense", boleto: "Bill" },
    cats: {
      renda: "Income",
      alimentacao: "Food",
      transporte: "Transport",
      casa: "Home",
      saude: "Health",
      lazer: "Leisure",
      outros: "Other",
    },
    foldersMap: {
      Tudo: "All",
      Inbox: "Inbox",
      Agenda: "Agenda",
      Financas: "Finance",
      Compras: "Shopping",
      Documentos: "Documents",
      Links: "Links",
      Treino: "Workout",
      Prompts: "Prompts",
      Ideias: "Ideas",
      Saude: "Health",
      Fotos: "Photos",
      Musica: "Music",
    },
    subsMap: {
      Selfies: "Selfies",
      Prints: "Screenshots",
      Capas: "Covers",
      Pessoal: "Personal",
      Profissional: "Work",
      Andamento: "In progress",
      Insights: "Insights",
      Curiosidades: "Curiosity",
      Vagas: "Jobs",
      Entretenimento: "Entertainment",
      Noticias: "News",
      Gastos: "Expenses",
      Receitas: "Income",
      Boletos: "Bills",
    },
  },
  pt: {
    brandTag: "arquivo vivo",
    railFoot: "Captura no Telegram<br/>Ação no Calendar",
    search: "Buscar",
    searchPh: "boleto, treino, instagram, CNH, suno…",
    menuOpen: "Abrir pastas",
    weekVideo: "Vídeo da semana",
    weekAudio: "Áudio da semana",
    askingVideo: "Pedindo vídeo…",
    askingAudio: "Pedindo áudio…",
    loadingArchive: "Carregando arquivo…",
    loadingFinance: "Carregando P&L…",
    loadingReports: "Carregando relatórios…",
    emptyInbox: "Nada neste recorte. Mande um áudio, link, PDF ou lista no Telegram.",
    itemsOf: (done, total) => `${done}/${total} itens`,
    openLink: "Abrir no computador",
    save: "Salvar",
    done: "Concluir",
    discard: "Descartar",
    income: "Entradas",
    expense: "Saídas",
    balance: "Saldo",
    incomeLabel: (month) => `Entradas · ${month}`,
    financeHint: "Mande no Telegram: “gastei 40 no almoço, recebi 200 no PIX”.",
    date: "Data",
    type: "Tipo",
    category: "Categoria",
    description: "Descrição",
    amount: "Valor",
    noEntries: "Sem lançamentos neste mês.",
    captures7d: "Capturas · 7 dias",
    pendingCal: "Calendar pendente",
    folders: "Pastas",
    weekAgenda: "Agenda da semana",
    noAgenda: "Nada na Agenda desta semana.",
    all: "Tudo",
    allSub: "Todas",
    views: { inbox: "Arquivo", finance: "Finanças", reports: "Relatórios" },
    status: { open: "Abertos", done: "Concluídos", discarded: "Descartados", all: "Todos" },
    kinds: {
      note: "Nota",
      task: "Tarefa",
      link: "Link",
      document: "Documento",
      shopping: "Compras",
      workout: "Treino",
      prompt: "Prompt",
      finance: "Finanças",
      media: "Mídia",
    },
    moneyKinds: { receita: "Receita", gasto: "Gasto", boleto: "Boleto" },
    cats: {
      renda: "Renda",
      alimentacao: "Alimentação",
      transporte: "Transporte",
      casa: "Casa",
      saude: "Saúde",
      lazer: "Lazer",
      outros: "Outros",
    },
    foldersMap: {
      Tudo: "Tudo",
      Inbox: "Inbox",
      Agenda: "Agenda",
      Financas: "Finanças",
      Compras: "Compras",
      Documentos: "Documentos",
      Links: "Links",
      Treino: "Treino",
      Prompts: "Prompts",
      Ideias: "Ideias",
      Saude: "Saúde",
      Fotos: "Fotos",
      Musica: "Música",
    },
    subsMap: {
      Selfies: "Selfies",
      Prints: "Prints",
      Capas: "Capas",
      Pessoal: "Pessoal",
      Profissional: "Profissional",
      Andamento: "Andamento",
      Insights: "Insights",
      Curiosidades: "Curiosidades",
      Vagas: "Vagas",
      Entretenimento: "Entretenimento",
      Noticias: "Notícias",
      Gastos: "Gastos",
      Receitas: "Receitas",
      Boletos: "Boletos",
    },
  },
};

function dict() {
  return I18N[state.lang] || I18N.en;
}

function t(key) {
  return dict()[key];
}

function folderLabel(name) {
  return dict().foldersMap[name] || name;
}

function subLabel(name) {
  return dict().subsMap[name] || name;
}

function kindLabel(kind) {
  return dict().kinds[kind] || kind;
}

function typeLabel(kind) {
  return dict().moneyKinds[kind] || kind;
}

function catLabel(cat) {
  return dict().cats[cat] || cat || "";
}

function setLang(lang) {
  state.lang = lang === "pt" ? "pt" : "en";
  localStorage.setItem("hub_lang", state.lang);
  document.documentElement.lang = state.lang === "pt" ? "pt-BR" : "en";
  applyChrome();
  render();
}

function applyChrome() {
  const d = dict();
  document.getElementById("brandTag").textContent = d.brandTag;
  document.getElementById("railFoot").innerHTML = d.railFoot;
  document.getElementById("searchLabel").textContent = d.search;
  document.getElementById("q").placeholder = d.searchPh;
  document.getElementById("menuBtn").setAttribute("aria-label", d.menuOpen);
  document.getElementById("btnRecap").textContent = d.weekVideo;
  document.getElementById("btnTheme").textContent = d.weekAudio;
  document.querySelectorAll("#langToggle [data-lang]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === state.lang);
  });
}

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
    if (state.folder !== ALL && item.folder !== state.folder) return false;
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
  const counts = { [ALL]: 0 };
  for (const item of state.items) {
    if (!isOpen(item)) continue;
    counts[ALL] += 1;
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
  const views = dict().views;
  document.getElementById("views").innerHTML = Object.entries(views).map(([id, label]) => {
    const active = state.view === id ? "active" : "";
    return `<button data-view="${id}" class="${active}">${label}</button>`;
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
  const names = [ALL, ...folders];
  document.getElementById("folders").innerHTML = names.map((name) => {
    const n = counts[name] || 0;
    const active = state.folder === name ? "active" : "";
    return `<button data-folder="${name}" class="${active}"><span>${escapeHtml(folderLabel(name))}</span><span>${n}</span></button>`;
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
  if (state.view !== "inbox" || state.folder === ALL) {
    el.innerHTML = "";
    return;
  }
  const counts = subfolderCounts();
  const names = [...new Set([...(state.subfolderSeeds[state.folder] || []), ...Object.keys(counts)])];
  if (!names.length) {
    el.innerHTML = "";
    return;
  }
  const chips = [{ id: "", label: t("allSub") }, ...names.map((name) => ({
    id: name,
    label: subLabel(name),
  }))];
  el.innerHTML = chips.map((chip) => {
    const active = state.subfolder === chip.id ? "active" : "";
    const n = chip.id ? (counts[chip.id] || 0) : "";
    return `<button data-sub="${escapeHtml(chip.id)}" class="${active}">${escapeHtml(chip.label)}${n ? " " + n : ""}</button>`;
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
  const tabs = dict().status;
  document.getElementById("statusFilters").innerHTML = Object.entries(tabs).map(([id, label]) => {
    const active = state.status === id ? "active" : "";
    return `<button data-status="${id}" class="${active}">${label}</button>`;
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
    return `${typeLabel(f.kind)} · ${f.merchant || ""} · R$ ${f.amount ?? "—"} · ${f.occurred_at || f.due_at || ""}${extra}`;
  }
  if (item.checklist?.length) {
    const left = item.checklist.filter((c) => !c.checked).length;
    return t("itemsOf")(item.checklist.length - left, item.checklist.length);
  }
  return item.summary || item.body || item.raw_text || "";
}

function brl(n) {
  const locale = state.lang === "pt" ? "pt-BR" : "en-US";
  return Number(n || 0).toLocaleString(locale, { style: "currency", currency: "BRL" });
}

function workspace() {
  return document.getElementById("workspace");
}

function renderGrid() {
  const items = visible();
  const grid = workspace();
  grid.className = "grid";
  if (!items.length) {
    grid.innerHTML = `<p class="empty">${escapeHtml(t("emptyInbox"))}</p>`;
    return;
  }
  grid.innerHTML = items.map((item) => {
    const checks = (item.checklist || []).slice(0, 4).map((c) =>
      `<li><input type="checkbox" ${c.checked ? "checked" : ""} disabled/> ${escapeHtml(c.text)}</li>`
    ).join("");
    const place = item.subfolder
      ? `${folderLabel(item.folder)} / ${subLabel(item.subfolder)}`
      : folderLabel(item.folder);
    return `
      <article class="card kind-${item.kind}" data-id="${item.id}">
        <div class="kicker"><span>${escapeHtml(kindLabel(item.kind))} · ${escapeHtml(place)}</span><span>${(item.created_at || "").slice(5, 16)}</span></div>
        <h2>${escapeHtml(item.title || item.summary || item.id)}</h2>
        ${item.subtitle ? `<p class="subtitle">${escapeHtml(item.subtitle)}</p>` : ""}
        <p>${escapeHtml(snippet(item).slice(0, 160))}</p>
        ${checks ? `<ul class="check">${checks}</ul>` : ""}
        <div class="meta">${(item.tags || []).map((tag) => "#" + tag).join(" ")}</div>
      </article>`;
  }).join("");
  grid.querySelectorAll(".card").forEach((card) => {
    card.onclick = () => openDrawer(card.dataset.id);
  });
}

function renderFinance() {
  const data = state.finance;
  const page = workspace();
  page.className = "page";
  if (!data) {
    page.innerHTML = `<p class="empty">${escapeHtml(t("loadingFinance"))}</p>`;
    return;
  }
  const d = dict();
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
      <div class="stat"><span>${escapeHtml(d.incomeLabel(data.month))}</span><strong class="income">${escapeHtml(brl(data.income))}</strong></div>
      <div class="stat"><span>${escapeHtml(d.expense)}</span><strong class="expense">${escapeHtml(brl(data.expense))}</strong></div>
      <div class="stat"><span>${escapeHtml(d.balance)}</span><strong>${escapeHtml(brl(data.balance))}</strong></div>
    </div>
    <p class="hint">${escapeHtml(d.financeHint)}</p>
    <div class="table-wrap">
      <table>
        <thead><tr><th>${d.date}</th><th>${d.type}</th><th>${d.category}</th><th>${d.description}</th><th>${d.amount}</th></tr></thead>
        <tbody>${rows || `<tr><td colspan="5">${escapeHtml(d.noEntries)}</td></tr>`}</tbody>
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
    page.innerHTML = `<p class="empty">${escapeHtml(t("loadingReports"))}</p>`;
    return;
  }
  const d = dict();
  const folders = Object.entries(data.folders || {}).map(([name, n]) =>
    `<tr><td>${escapeHtml(folderLabel(name))}</td><td>${n}</td></tr>`
  ).join("");
  const agenda = data.agenda || {};
  const tasks = (agenda.tasks || []).map((task) => `<li>${escapeHtml(task)}</li>`).join("")
    || `<li>${escapeHtml(d.noAgenda)}</li>`;
  page.innerHTML = `
    <div class="stats">
      <div class="stat"><span>${escapeHtml(d.captures7d)}</span><strong>${data.captures_7d || 0}</strong></div>
      <div class="stat"><span>${escapeHtml(d.pendingCal)}</span><strong>${data.pending_calendar || 0}</strong></div>
    </div>
    <div class="split">
      <div>
        <h2>${escapeHtml(d.folders)}</h2>
        <div class="table-wrap"><table><tbody>${folders}</tbody></table></div>
      </div>
      <div>
        <h2>${escapeHtml(d.weekAgenda)}</h2>
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
  const d = dict();
  const media = (item.media_paths || []).map((_, idx) => {
    const src = `/api/files/${item.id}/${idx}`;
    const path = item.media_paths[idx] || "";
    if (path.toLowerCase().endsWith(".pdf")) {
      return `<iframe class="preview pdf" src="${src}"></iframe>`;
    }
    if (/\.(mp3|wav|ogg|m4a|flac)$/i.test(path)) {
      return `<audio class="preview" controls src="${src}"></audio>`;
    }
    return `<img class="preview" src="${src}" alt="media"/>`;
  }).join("");
  const checks = (item.checklist || []).map((c) =>
    `<li><label><input type="checkbox" data-check="${c.id}" ${c.checked ? "checked" : ""}/> ${escapeHtml(c.text)}</label></li>`
  ).join("");
  const folderOpts = [...new Set([item.folder, ...(state.folders || [])].filter(Boolean))]
    .map((f) => `<option value="${escapeHtml(f)}" ${f === item.folder ? "selected" : ""}>${escapeHtml(folderLabel(f))}</option>`).join("");
  const subNames = [...new Set([item.subfolder, ...(state.subfolderSeeds[item.folder] || [])].filter(Boolean))];
  const subOpts = ["", ...subNames].map((s) =>
    `<option value="${escapeHtml(s)}" ${s === (item.subfolder || "") ? "selected" : ""}>${escapeHtml(s ? subLabel(s) : "—")}</option>`
  ).join("");
  const facts = money(item).map((f) =>
    `<p>${escapeHtml(typeLabel(f.kind))} · ${escapeHtml(catLabel(f.category))} · ${escapeHtml(f.merchant || "")} · R$ ${f.amount ?? "—"}</p>`
  ).join("");
  drawer.innerHTML = `
    <div class="kicker">${escapeHtml(kindLabel(item.kind))}</div>
    <h1>${escapeHtml(item.title || item.summary || "")}</h1>
    ${item.subtitle ? `<p class="subtitle">${escapeHtml(item.subtitle)}</p>` : ""}
    <div class="row">
      <select id="folder">${folderOpts}</select>
      <select id="subfolder">${subOpts}</select>
      ${item.url ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(d.openLink)}</a>` : ""}
    </div>
    ${media}
    ${facts}
    ${checks ? `<ul class="check">${checks}</ul>` : ""}
    <textarea id="body">${escapeHtml(item.body || item.raw_text || item.agent_reply || "")}</textarea>
    <div class="row">
      <button class="primary" id="save">${escapeHtml(d.save)}</button>
      <button id="done">${escapeHtml(d.done)}</button>
      <button class="ghost" id="discard">${escapeHtml(d.discard)}</button>
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
  title.textContent = state.view === "finance" || state.view === "reports"
    ? dict().views[state.view]
    : "";
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
  document.documentElement.lang = state.lang === "pt" ? "pt-BR" : "en";
  applyChrome();
  workspace().innerHTML = `<p class="empty">${escapeHtml(t("loadingArchive"))}</p>`;
  document.getElementById("q").addEventListener("input", (ev) => {
    state.q = ev.target.value;
    render();
  });
  document.querySelectorAll("#langToggle [data-lang]").forEach((btn) => {
    btn.onclick = () => setLang(btn.dataset.lang);
  });
  const status = document.getElementById("genStatus");
  document.getElementById("btnRecap").onclick = async () => {
    status.textContent = t("askingVideo");
    const result = await api("/api/reports/recap", { method: "POST" });
    status.textContent = result.message || JSON.stringify(result);
  };
  document.getElementById("btnTheme").onclick = async () => {
    status.textContent = t("askingAudio");
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

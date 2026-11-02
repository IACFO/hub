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
  financeEdit: null,
  financeDraft: null,
  financeTab: "ledger",
  financeMonth: "",
  payableEdit: null,
  payableDraft: null,
  reports: null,
  accounting: null,
  accountingTab: "calc",
  accountingMonth: "",
  accountingDraft: null,
  accountingExpenseEdit: null,
  lang: localStorage.getItem("hub_lang") || "en",
  readOnly: false,
  auth: false,
};

const I18N = {
  en: {
    brandTag: "living archive",
    search: "Search",
    searchPh: "invoice, workout, instagram, ID, suno…",
    menuOpen: "Open folders",
    readOnlyBanner: "Public demo · read-only (view only)",
    logout: "Log out",
    newFolder: "+ Folder",
    newSubfolder: "+ Subfolder",
    folderPrompt: "New folder name",
    subfolderPrompt: "New subfolder name",
    renamePrompt: "New name",
    rename: "Rename",
    delete: "Delete",
    addEntry: "Add entry",
    saveEntry: "Save entry",
    cancel: "Cancel",
    newCategory: "New category",
    categoryPrompt: "New category name",
    deleteCategoryConfirm: "Delete this category? Existing entries move to Other.",
    newType: "New type",
    typePrompt: "New type name",
    typeSidePrompt: "Income or expense? Type income or expense",
    sideIn: "income",
    sideOut: "expense",
    deleteTypeConfirm: "Delete this type? Entries move to Income or Expense.",
    month: "Month",
    dueDate: "Due date",
    billStatus: "Status",
    billLate: "Overdue",
    billStatuses: { aberto: "Open", pago: "Paid", cancelado: "Cancelled" },
    financeTabs: { ledger: "Entries", payables: "Bills due", report: "Report" },
    acctTabs: { calc: "Calculator", manage: "Overview" },
    acctRevenue: "Invoice revenue",
    acctDistribution: "Profit distribution",
    acctAddExpense: "Add expense",
    acctSaveExpense: "Save expense",
    acctNoExpenses: "No expenses this month.",
    acctItem: "Item",
    acctRule: "Rule",
    acctValue: "Amount",
    acctReceipts: "Receipts",
    acctPayments: "Payments",
    acctMovement: "Net movement",
    acctMovements: "Movements",
    acctIn: "In",
    acctOut: "Out",
    loadingAccounting: "Loading accounting…",
    deleteExpenseConfirm: "Delete this expense?",
    acctLines: {
      revenue: "Invoice revenue",
      prolabore: "Gross pró-labore (28%)",
      inss: "INSS on pró-labore",
      ir: "Income tax on pró-labore",
      net: "Net pró-labore",
      das: "Company DAS",
      profit: "Available net profit",
      distribution: "Profit distribution",
      after: "Cash left after distribution",
    },
    addPayable: "Add bill",
    savePayable: "Save bill",
    deletePayableConfirm: "Delete this bill?",
    noPayables: "No bills in this month.",
    paidOn: "Paid on",
    recurring: "Recurring",
    recurringMonths: "Months",
    debits: "Debits",
    debitHint: "Variable expenses and bills paid this month.",
    payments: "Bills paid",
    byCategory: "By category",
    byMonth: "By month",
    overdue: "Overdue",
    payablesTotal: "Bills due",
    noReport: "Nothing in this month.",
    deleteFolderConfirm: "Delete this folder? Items move to Inbox.",
    deleteSubConfirm: "Delete this subfolder? Items stay in the parent folder.",
    deleteItemConfirm: "Delete this item permanently?",
    deleteFileConfirm: "Remove this file?",
    deleteEntryConfirm: "Delete this entry?",
    upload: "Upload",
    uploading: "Uploading…",
    uploaded: (n) => (n === 1 ? "1 file saved" : `${n} files saved`),
    loadingArchive: "Loading archive…",
    loadingFinance: "Loading P&L…",
    loadingReports: "Loading reports…",
    emptyInbox: "Nothing here yet. Upload a file or send it on Telegram.",
    itemsOf: (done, total) => `${done}/${total} items`,
    openLink: "Open on computer",
    download: "Download",
    save: "Save",
    done: "Done",
    discard: "Discard",
    income: "Income",
    expense: "Spend",
    balance: "Balance",
    incomeLabel: (month) => `Income · ${month}`,
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
    views: { inbox: "Archive", finance: "Finance", accounting: "Accounting", reports: "Reports" },
    status: { open: "Open", done: "Done", all: "All" },
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
      Contas: "Bills due",
    },
  },
  pt: {
    brandTag: "arquivo vivo",
    search: "Buscar",
    searchPh: "boleto, treino, instagram, CNH, suno…",
    menuOpen: "Abrir pastas",
    readOnlyBanner: "Demo pública · somente leitura",
    logout: "Sair",
    newFolder: "+ Pasta",
    newSubfolder: "+ Subpasta",
    folderPrompt: "Nome da nova pasta",
    subfolderPrompt: "Nome da nova subpasta",
    renamePrompt: "Novo nome",
    rename: "Renomear",
    delete: "Excluir",
    addEntry: "Adicionar lançamento",
    saveEntry: "Salvar lançamento",
    cancel: "Cancelar",
    newCategory: "Nova categoria",
    categoryPrompt: "Nome da nova categoria",
    deleteCategoryConfirm: "Excluir esta categoria? Os lançamentos vão para Outros.",
    newType: "Novo tipo",
    typePrompt: "Nome do novo tipo",
    typeSidePrompt: "Entrada ou saída? Digite entrada ou saida",
    sideIn: "entrada",
    sideOut: "saida",
    deleteTypeConfirm: "Excluir este tipo? Os lançamentos vão para Receita ou Gasto.",
    month: "Mês",
    dueDate: "Vencimento",
    billStatus: "Status",
    billLate: "Atrasado",
    billStatuses: { aberto: "A vencer", pago: "Pago", cancelado: "Cancelado" },
    financeTabs: { ledger: "Lançamentos", payables: "Contas a pagar", report: "Relatório" },
    acctTabs: { calc: "Calculadora", manage: "Gerencial" },
    acctRevenue: "Faturamento",
    acctDistribution: "Distribuição de lucros",
    acctAddExpense: "Adicionar despesa",
    acctSaveExpense: "Salvar despesa",
    acctNoExpenses: "Nenhuma despesa neste mês.",
    acctItem: "Item",
    acctRule: "Regra",
    acctValue: "Valor",
    acctReceipts: "Recebimentos",
    acctPayments: "Pagamentos",
    acctMovement: "Movimento",
    acctMovements: "Movimentações",
    acctIn: "Entrada",
    acctOut: "Saída",
    loadingAccounting: "Carregando contabilidade…",
    deleteExpenseConfirm: "Excluir esta despesa?",
    acctLines: {
      revenue: "Faturamento da nota",
      prolabore: "Pró-labore bruto (28%)",
      inss: "INSS sobre pró-labore",
      ir: "IRPF sobre pró-labore",
      net: "Pró-labore líquido",
      das: "DAS da empresa",
      profit: "Lucro líquido disponível",
      distribution: "Distribuição de lucros",
      after: "Saldo após a distribuição",
    },
    addPayable: "Adicionar conta",
    savePayable: "Salvar conta",
    deletePayableConfirm: "Excluir esta conta?",
    noPayables: "Nenhuma conta neste mês.",
    paidOn: "Pago em",
    recurring: "Recorrente",
    recurringMonths: "Meses",
    debits: "Débitos",
    debitHint: "Gastos variáveis e contas pagas neste mês.",
    payments: "Contas pagas",
    byCategory: "Por categoria",
    byMonth: "Por mês",
    overdue: "Em atraso",
    payablesTotal: "Contas a pagar",
    noReport: "Nada neste mês.",
    deleteFolderConfirm: "Excluir esta pasta? Os itens vão para a Inbox.",
    deleteSubConfirm: "Excluir esta subpasta? Os itens ficam na pasta pai.",
    deleteItemConfirm: "Excluir este item definitivamente?",
    deleteFileConfirm: "Remover este arquivo?",
    deleteEntryConfirm: "Excluir este lançamento?",
    upload: "Enviar arquivo",
    uploading: "Enviando…",
    uploaded: (n) => (n === 1 ? "1 arquivo salvo" : `${n} arquivos salvos`),
    loadingArchive: "Carregando arquivo…",
    loadingFinance: "Carregando P&L…",
    loadingReports: "Carregando relatórios…",
    emptyInbox: "Nada aqui ainda. Envie um arquivo ou mande pelo Telegram.",
    itemsOf: (done, total) => `${done}/${total} itens`,
    openLink: "Abrir no computador",
    download: "Baixar",
    save: "Salvar",
    done: "Concluir",
    discard: "Descartar",
    income: "Entradas",
    expense: "Saídas",
    balance: "Saldo",
    incomeLabel: (month) => `Entradas · ${month}`,
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
    views: { inbox: "Arquivo", finance: "Finanças", accounting: "Contabilidade", reports: "Relatórios" },
    status: { open: "Abertos", done: "Concluídos", all: "Todos" },
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
      Contas: "Contas",
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

function financeTypes() {
  const rows = (state.finance && state.finance.types) || [];
  if (rows.length) return rows;
  return Object.keys(dict().moneyKinds).map((id) => ({
    id,
    label: "",
    side: id === "receita" ? "entrada" : "saida",
  }));
}

function typeLabel(kind) {
  const row = financeTypes().find((item) => item.id === kind);
  if (row && row.label) return row.label;
  return dict().moneyKinds[kind] || kind || "";
}

function isIncomeKind(kind) {
  const row = financeTypes().find((item) => item.id === kind);
  return row ? row.side === "entrada" : kind === "receita";
}

function typeOptions(selected) {
  const rows = [...financeTypes()];
  if (selected && !rows.some((item) => item.id === selected)) {
    rows.push({ id: selected, label: "", side: "saida" });
  }
  return rows.map((row) =>
    `<option value="${escapeHtml(row.id)}">${escapeHtml(typeLabel(row.id))}</option>`
  ).join("");
}

function parseTypeSide(raw, fallback) {
  const value = String(raw || "").trim().toLowerCase();
  if (["entrada", "credito", "crédito", "receita", "income", "credit"].includes(value)) return "entrada";
  if (["saida", "saída", "debito", "débito", "gasto", "expense", "debit"].includes(value)) return "saida";
  return fallback || "saida";
}

function askTypeSide(current) {
  const word = current === "entrada" ? t("sideIn") : t("sideOut");
  const raw = window.prompt(t("typeSidePrompt"), word);
  if (raw == null) return null;
  return parseTypeSide(raw, current || "saida");
}

function financeMonthValue() {
  return state.financeMonth || (state.finance && state.finance.month) || "";
}

function billStatusLabel(row) {
  const due = (row.due_at || "").slice(0, 10);
  if (row.status === "aberto" && due && due < todayISO()) return t("billLate");
  return (dict().billStatuses || {})[row.status] || row.status || "";
}

function visiblePayables(data) {
  const month = data.month || "";
  return (data.payables || []).filter((row) => (row.due_at || "").slice(0, 7) === month);
}

function financeCategories() {
  return (state.finance && state.finance.categories) || [];
}

function catLabel(cat) {
  const row = financeCategories().find((item) => item.id === cat);
  if (row && row.label) return row.label;
  return dict().cats[cat] || cat || "";
}

function categoryOptions(selected) {
  const rows = [...financeCategories()];
  if (selected && !rows.some((item) => item.id === selected)) {
    rows.push({ id: selected, label: "" });
  }
  if (!rows.length) rows.push({ id: "outros", label: "" });
  return rows.map((row) =>
    `<option value="${escapeHtml(row.id)}">${escapeHtml(catLabel(row.id))}</option>`
  ).join("");
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
  document.getElementById("searchLabel").textContent = d.search;
  document.getElementById("q").placeholder = d.searchPh;
  document.getElementById("menuBtn").setAttribute("aria-label", d.menuOpen);
  const banner = document.getElementById("readOnlyBanner");
  if (banner) {
    banner.hidden = !state.readOnly;
    banner.textContent = d.readOnlyBanner;
  }
  document.body.classList.toggle("read-only", state.readOnly);
  const logoutForm = document.getElementById("logoutForm");
  const btnLogout = document.getElementById("btnLogout");
  if (logoutForm && btnLogout) {
    logoutForm.hidden = !state.auth;
    btnLogout.textContent = d.logout;
  }
  const btnUpload = document.getElementById("btnUpload");
  if (btnUpload) btnUpload.textContent = d.upload;
  document.querySelectorAll(".lang-toggle [data-lang]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === state.lang);
  });
}

function mediaFileName(path, itemId, index) {
  const raw = (path || "").split("?")[0];
  const base = raw.split("/").pop() || "";
  if (base && base !== itemId && !base.startsWith("itm_")) {
    return base;
  }
  const lower = raw.toLowerCase();
  if (lower.endsWith(".pdf")) return `${itemId}-${index}.pdf`;
  if (/\.(mp3|wav|ogg|m4a|flac)$/i.test(lower)) return `${itemId}-${index}.audio`;
  if (/\.(png|webp|gif)$/i.test(lower)) return `${itemId}-${index}${lower.slice(lower.lastIndexOf("."))}`;
  return `${itemId}-${index}.jpg`;
}

async function api(path, options) {
  const opts = { cache: "no-store", ...options };
  const headers = { ...(opts.headers || {}) };
  if (!(opts.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  opts.headers = headers;
  const res = await fetch(path, opts);
  if (res.status === 401) {
    location.href = "/login";
    throw new Error("unauthorized");
  }
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
    // Discarded cards stay in the DB but never appear in the gallery.
    if (item.status === "discarded") return false;
    if (state.folder !== ALL && item.folder !== state.folder) return false;
    if (state.subfolder && item.subfolder !== state.subfolder) return false;
    if (state.status === "open" && !isOpen(item)) return false;
    if (state.status === "done" && item.status !== "done") return false;
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
    btn.onclick = async () => {
      if (state.view === "accounting" && btn.dataset.view !== "accounting") {
        await saveAccountingFields();
      }
      state.view = btn.dataset.view;
      setMenu(false);
      render();
    };
  });
}

function isProtectedFolder(name) {
  return !name || name === ALL || String(name).toLowerCase() === "inbox";
}

function applyTaxonomy(result) {
  if (result.folders) state.folders = result.folders;
  if (result.subfolders) state.subfolderSeeds = result.subfolders;
}

function renderFolders(folders) {
  const counts = folderCounts();
  const names = [ALL, ...folders];
  const addBtn = state.readOnly
    ? ""
    : `<button type="button" class="add-folder" id="btnNewFolder">${escapeHtml(t("newFolder"))}</button>`;
  document.getElementById("folders").innerHTML = names.map((name) => {
    const n = counts[name] || 0;
    const active = state.folder === name ? "active" : "";
    const ops = state.readOnly || isProtectedFolder(name) ? "" : `
      <button type="button" class="icon-btn" data-rename-folder="${escapeHtml(name)}" title="${escapeHtml(t("rename"))}">✎</button>
      <button type="button" class="icon-btn danger" data-delete-folder="${escapeHtml(name)}" title="${escapeHtml(t("delete"))}">×</button>`;
    return `<div class="folder-row ${active}">
      <button type="button" class="folder-pick" data-folder="${escapeHtml(name)}"><span>${escapeHtml(folderLabel(name))}</span><span>${n}</span></button>
      ${ops}
    </div>`;
  }).join("") + addBtn;
  document.querySelectorAll("[data-folder]").forEach((btn) => {
    btn.onclick = () => {
      state.folder = btn.dataset.folder;
      state.subfolder = "";
      state.view = "inbox";
      setMenu(false);
      render();
    };
  });
  document.querySelectorAll("[data-rename-folder]").forEach((btn) => {
    btn.onclick = (ev) => { ev.stopPropagation(); renameFolder(btn.dataset.renameFolder); };
  });
  document.querySelectorAll("[data-delete-folder]").forEach((btn) => {
    btn.onclick = (ev) => { ev.stopPropagation(); deleteFolder(btn.dataset.deleteFolder); };
  });
  const add = document.getElementById("btnNewFolder");
  if (add) add.onclick = createFolder;
}

function renderSubfolders() {
  const el = document.getElementById("subfolders");
  if (state.view !== "inbox" || state.folder === ALL) {
    el.innerHTML = "";
    return;
  }
  const counts = subfolderCounts();
  const names = [...new Set([...(state.subfolderSeeds[state.folder] || []), ...Object.keys(counts)])];
  const chips = names.length
    ? [{ id: "", label: t("allSub") }, ...names.map((name) => ({ id: name, label: subLabel(name) }))]
    : [];
  const addBtn = state.readOnly
    ? ""
    : `<button type="button" class="add-chip" id="btnNewSubfolder">${escapeHtml(t("newSubfolder"))}</button>`;
  el.innerHTML = chips.map((chip) => {
    const active = state.subfolder === chip.id ? "active" : "";
    const n = chip.id ? (counts[chip.id] || 0) : "";
    const ops = state.readOnly || !chip.id ? "" : `
      <button type="button" class="icon-btn" data-rename-sub="${escapeHtml(chip.id)}" title="${escapeHtml(t("rename"))}">✎</button>
      <button type="button" class="icon-btn danger" data-delete-sub="${escapeHtml(chip.id)}" title="${escapeHtml(t("delete"))}">×</button>`;
    return `<span class="chip-wrap">
      <button type="button" data-sub="${escapeHtml(chip.id)}" class="${active}">${escapeHtml(chip.label)}${n ? " " + n : ""}</button>
      ${ops}
    </span>`;
  }).join("") + addBtn;
  el.querySelectorAll("[data-sub]").forEach((btn) => {
    btn.onclick = () => {
      state.subfolder = btn.dataset.sub;
      setMenu(false);
      render();
    };
  });
  el.querySelectorAll("[data-rename-sub]").forEach((btn) => {
    btn.onclick = (ev) => { ev.stopPropagation(); renameSubfolder(btn.dataset.renameSub); };
  });
  el.querySelectorAll("[data-delete-sub]").forEach((btn) => {
    btn.onclick = (ev) => { ev.stopPropagation(); deleteSubfolder(btn.dataset.deleteSub); };
  });
  const add = document.getElementById("btnNewSubfolder");
  if (add) add.onclick = createSubfolder;
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

function todayISO() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
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
  const tab = state.financeTab || "ledger";
  const tabs = ["ledger", "payables", "report"].map((id) =>
    `<button type="button" data-fin-tab="${id}" class="${tab === id ? "active" : ""}">${escapeHtml(d.financeTabs[id])}</button>`
  ).join("");
  page.innerHTML = `
    <div class="finance-head">
      <nav class="subtabs">${tabs}</nav>
      <label class="month-field">${escapeHtml(d.month)}
        <input type="month" id="finMonth" value="${escapeHtml(data.month || "")}"/>
      </label>
    </div>
    <div id="financePanel"></div>`;
  page.querySelectorAll("[data-fin-tab]").forEach((btn) => {
    btn.onclick = () => {
      state.financeTab = btn.dataset.finTab;
      render();
    };
  });
  const monthEl = document.getElementById("finMonth");
  if (monthEl) monthEl.onchange = (ev) => changeFinanceMonth(ev.target.value);
  if (tab === "payables") renderPayables(data);
  else if (tab === "report") renderFinanceReport(data);
  else renderLedger(data);
}

async function changeFinanceMonth(month) {
  if (!month) return;
  state.financeMonth = month;
  state.finance = await api(`/api/finance?month=${encodeURIComponent(month)}`);
  render();
}

function renderLedger(data) {
  const panel = document.getElementById("financePanel");
  if (!panel) return;
  const d = dict();
  const editing = state.financeEdit;
  const selectedRow = editing && (data.entries || []).find((row) => row.item_id === editing.item_id && row.fact_id === editing.fact_id);
  const selectedCat = (state.financeDraft && state.financeDraft.category) || (selectedRow && selectedRow.category) || "";
  const selectedKind = (state.financeDraft && state.financeDraft.kind) || (selectedRow && selectedRow.kind) || "";
  const catOpts = categoryOptions(selectedCat);
  const kindOpts = typeOptions(selectedKind);
  const ro = state.readOnly;
  const rows = (data.entries || []).map((row) => {
    const ops = ro ? "" : `
      <td class="ops">
        <button type="button" class="icon-btn" data-edit-entry="${row.item_id}:${row.fact_id}" title="${escapeHtml(d.rename)}">✎</button>
        <button type="button" class="icon-btn danger" data-del-entry="${row.item_id}:${row.fact_id}" title="${escapeHtml(d.delete)}">×</button>
      </td>`;
    return `
    <tr data-id="${row.item_id}" data-fact="${row.fact_id || ""}">
      <td>${escapeHtml((row.occurred_at || "").slice(0, 10))}</td>
      <td>${escapeHtml(typeLabel(row.kind))}</td>
      <td>${escapeHtml(catLabel(row.category))}</td>
      <td>${escapeHtml(row.merchant || row.title || "")}</td>
      <td class="${isIncomeKind(row.kind) ? "income" : "expense"}">${escapeHtml(brl(row.amount))}</td>
      ${ops}
    </tr>`;
  }).join("");
  const form = ro ? "" : `
    <form class="ledger-form" id="ledgerForm">
      <label>${escapeHtml(d.date)}<input type="date" id="finDate" required/></label>
      <label class="fin-cat-field">${escapeHtml(d.type)}<span class="fin-cat-row">
        <select id="finKind">${kindOpts}</select>
        <button type="button" class="icon-btn" id="finTypeAdd" title="${escapeHtml(d.newType)}">+</button>
        <button type="button" class="icon-btn" id="finTypeEdit" title="${escapeHtml(d.rename)}">✎</button>
        <button type="button" class="icon-btn danger" id="finTypeDel" title="${escapeHtml(d.delete)}">×</button>
      </span></label>
      <label class="fin-cat-field">${escapeHtml(d.category)}<span class="fin-cat-row">
        <select id="finCat">${catOpts}</select>
        <button type="button" class="icon-btn" id="finCatAdd" title="${escapeHtml(d.newCategory)}">+</button>
        <button type="button" class="icon-btn" id="finCatEdit" title="${escapeHtml(d.rename)}">✎</button>
        <button type="button" class="icon-btn danger" id="finCatDel" title="${escapeHtml(d.delete)}">×</button>
      </span></label>
      <label>${escapeHtml(d.description)}<input type="text" id="finDesc" maxlength="80"/></label>
      <label>${escapeHtml(d.amount)}<input type="number" id="finAmount" step="0.01" min="0" required/></label>
      <button type="submit" class="primary" id="finSubmit">${escapeHtml(editing ? d.saveEntry : d.addEntry)}</button>
      ${editing ? `<button type="button" id="finCancel">${escapeHtml(d.cancel)}</button>` : ""}
    </form>`;
  panel.innerHTML = `
    <div class="stats">
      <div class="stat"><span>${escapeHtml(d.incomeLabel(data.month))}</span><strong class="income">${escapeHtml(brl(data.income))}</strong></div>
      <div class="stat"><span>${escapeHtml(d.expense)}</span><strong class="expense">${escapeHtml(brl(data.expense))}</strong></div>
      <div class="stat"><span>${escapeHtml(d.payments)}</span><strong class="expense">${escapeHtml(brl(data.payments))}</strong></div>
      <div class="stat"><span>${escapeHtml(d.balance)}</span><strong>${escapeHtml(brl(data.balance))}</strong></div>
    </div>
    ${form}
    <div class="table-wrap">
      <table>
        <thead><tr><th>${d.date}</th><th>${d.type}</th><th>${d.category}</th><th>${d.description}</th><th>${d.amount}</th>${ro ? "" : `<th class="ops"></th>`}</tr></thead>
        <tbody>${rows || `<tr><td colspan="${ro ? 5 : 6}">${escapeHtml(d.noEntries)}</td></tr>`}</tbody>
      </table>
    </div>`;
  if (!ro) bindFinanceForm(data);
}

function renderPayables(data) {
  const panel = document.getElementById("financePanel");
  if (!panel) return;
  const d = dict();
  const ro = state.readOnly;
  const editing = state.payableEdit;
  const bills = visiblePayables(data);
  const selected = editing && (data.payables || []).find((row) => row.item_id === editing.item_id && row.fact_id === editing.fact_id);
  const selectedCat = (state.payableDraft && state.payableDraft.category) || (selected && selected.category) || "";
  const catOpts = categoryOptions(selectedCat);
  const statusOpts = Object.entries(d.billStatuses).map(([id, label]) =>
    `<option value="${id}">${escapeHtml(label)}</option>`
  ).join("");
  const openSum = bills.filter((row) => row.status === "aberto").reduce((sum, row) => sum + Number(row.amount || 0), 0);
  const rows = bills.map((row) => {
    const ops = ro ? "" : `
      <td class="ops">
        <button type="button" class="icon-btn" data-edit-bill="${row.item_id}:${row.fact_id}" title="${escapeHtml(d.rename)}">✎</button>
        <button type="button" class="icon-btn danger" data-del-bill="${row.item_id}:${row.fact_id}" title="${escapeHtml(d.delete)}">×</button>
      </td>`;
    const late = row.status === "aberto" && (row.due_at || "") < todayISO();
    return `
    <tr>
      <td>${escapeHtml((row.due_at || "").slice(0, 10))}</td>
      <td>${escapeHtml(row.description || "")}</td>
      <td>${escapeHtml(catLabel(row.category))}</td>
      <td class="${late ? "expense" : ""}">${escapeHtml(billStatusLabel(row))}</td>
      <td class="${row.status === "pago" ? "income" : "expense"}">${escapeHtml(brl(row.amount))}</td>
      ${ops}
    </tr>`;
  }).join("");
  const form = ro ? "" : `
    <form class="ledger-form" id="payableForm">
      <label>${escapeHtml(d.dueDate)}<input type="date" id="payDate" required/></label>
      <label>${escapeHtml(d.description)}<input type="text" id="payDesc" maxlength="80" required/></label>
      <label class="fin-cat-field">${escapeHtml(d.category)}<span class="fin-cat-row">
        <select id="finCat">${catOpts}</select>
        <button type="button" class="icon-btn" id="finCatAdd" title="${escapeHtml(d.newCategory)}">+</button>
        <button type="button" class="icon-btn" id="finCatEdit" title="${escapeHtml(d.rename)}">✎</button>
        <button type="button" class="icon-btn danger" id="finCatDel" title="${escapeHtml(d.delete)}">×</button>
      </span></label>
      <label>${escapeHtml(d.billStatus)}<select id="payStatus">${statusOpts}</select></label>
      <label id="payPaidWrap">${escapeHtml(d.paidOn)}<input type="date" id="payPaid"/></label>
      <label>${escapeHtml(d.amount)}<input type="number" id="payAmount" step="0.01" min="0" required/></label>
      ${editing ? "" : `<label class="checkline"><input type="checkbox" id="payRepeat"/> ${escapeHtml(d.recurring)}</label>
      <label id="payRepeatWrap" hidden>${escapeHtml(d.recurringMonths)}<input type="number" id="payRepeatMonths" min="2" max="36" value="12"/></label>`}
      <button type="submit" class="primary" id="paySubmit">${escapeHtml(editing ? d.savePayable : d.addPayable)}</button>
      ${editing ? `<button type="button" id="payCancel">${escapeHtml(d.cancel)}</button>` : ""}
    </form>`;
  panel.innerHTML = `
    <div class="stats">
      <div class="stat"><span>${escapeHtml(d.payablesTotal)}</span><strong class="expense">${escapeHtml(brl(openSum))}</strong></div>
    </div>
    ${form}
    <div class="table-wrap">
      <table>
        <thead><tr><th>${d.dueDate}</th><th>${d.description}</th><th>${d.category}</th><th>${d.billStatus}</th><th>${d.amount}</th>${ro ? "" : `<th class="ops"></th>`}</tr></thead>
        <tbody>${rows || `<tr><td colspan="${ro ? 5 : 6}">${escapeHtml(d.noPayables)}</td></tr>`}</tbody>
      </table>
    </div>`;
  if (!ro) bindPayableForm(data);
}

function renderFinanceReport(data) {
  const panel = document.getElementById("financePanel");
  if (!panel) return;
  const d = dict();
  const report = data.report || {};
  const incomeName = d.moneyKinds.receita;
  const incomeRows = (report.income_categories || []).map((row) => `
    <tr>
      <td>${escapeHtml(catLabel(row.id))}</td>
      <td class="income">${escapeHtml(brl(row.amount))}</td>
    </tr>`).join("");
  const expenseRows = (report.expense_categories || []).map((row) => `
    <tr>
      <td>${escapeHtml(catLabel(row.id))}</td>
      <td class="expense">${escapeHtml(brl(row.amount))}</td>
    </tr>`).join("");
  const months = (report.by_month || []).map((row) => `
    <tr data-report-month="${escapeHtml(row.month)}" class="${row.month === data.month ? "active" : ""}">
      <td>${escapeHtml(row.month)}</td>
      <td class="income">${escapeHtml(brl(row.income))}</td>
      <td class="expense">${escapeHtml(brl(row.expense))}</td>
      <td>${escapeHtml(brl(row.balance))}</td>
      <td>${escapeHtml(brl(row.payable))}</td>
    </tr>`).join("");
  panel.innerHTML = `
    <div class="stats">
      <div class="stat"><span>${escapeHtml(incomeName)}</span><strong class="income">${escapeHtml(brl(report.income))}</strong></div>
      <div class="stat"><span>${escapeHtml(d.debits)}</span><strong class="expense">${escapeHtml(brl(report.expense))}</strong></div>
      <div class="stat"><span>${escapeHtml(d.balance)}</span><strong>${escapeHtml(brl(report.balance))}</strong></div>
      <div class="stat"><span>${escapeHtml(d.payablesTotal)}</span><strong class="expense">${escapeHtml(brl(report.payable))}</strong></div>
      <div class="stat"><span>${escapeHtml(d.overdue)}</span><strong class="expense">${escapeHtml(brl(report.payable_overdue))}</strong></div>
    </div>
    <p class="hint">${escapeHtml(d.debitHint)}</p>
    <div class="split">
      <div>
        <h2>${escapeHtml(incomeName)}</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>${d.category}</th><th>${d.amount}</th></tr></thead>
            <tbody>${incomeRows || `<tr><td colspan="2">${escapeHtml(d.noReport)}</td></tr>`}</tbody>
          </table>
        </div>
      </div>
      <div>
        <h2>${escapeHtml(d.debits)}</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>${d.category}</th><th>${d.amount}</th></tr></thead>
            <tbody>${expenseRows || `<tr><td colspan="2">${escapeHtml(d.noReport)}</td></tr>`}</tbody>
          </table>
        </div>
      </div>
    </div>
    <h2>${escapeHtml(d.byMonth)}</h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>${d.month}</th><th>${incomeName}</th><th>${d.debits}</th><th>${d.balance}</th><th>${d.payablesTotal}</th></tr></thead>
        <tbody>${months || `<tr><td colspan="5">${escapeHtml(d.noReport)}</td></tr>`}</tbody>
      </table>
    </div>`;
  panel.querySelectorAll("[data-report-month]").forEach((row) => {
    row.onclick = () => changeFinanceMonth(row.dataset.reportMonth);
  });
}

function financeDraftFromForm() {
  return {
    date: document.getElementById("finDate")?.value || "",
    kind: document.getElementById("finKind")?.value || "",
    category: document.getElementById("finCat")?.value || "",
    merchant: document.getElementById("finDesc")?.value || "",
    amount: document.getElementById("finAmount")?.value || "",
    edit: state.financeEdit,
  };
}

function payableDraftFromForm() {
  return {
    date: document.getElementById("payDate")?.value || "",
    category: document.getElementById("finCat")?.value || "",
    description: document.getElementById("payDesc")?.value || "",
    amount: document.getElementById("payAmount")?.value || "",
    status: document.getElementById("payStatus")?.value || "aberto",
    paid: document.getElementById("payPaid")?.value || "",
    repeat: Boolean(document.getElementById("payRepeat")?.checked),
    months: document.getElementById("payRepeatMonths")?.value || "",
    edit: state.payableEdit,
  };
}

function isFinanceFormBusy() {
  const ledger = document.getElementById("ledgerForm");
  const payable = document.getElementById("payableForm");
  const active = document.activeElement;
  if (ledger && ledger.contains(active)) return true;
  if (payable && payable.contains(active)) return true;
  return Boolean(state.financeDraft || state.payableDraft);
}

function bindCategoryButtons(catEl, data, applyResult) {
  const addCat = document.getElementById("finCatAdd");
  if (addCat) addCat.onclick = async (ev) => {
    ev.preventDefault();
    const name = window.prompt(t("categoryPrompt"), "");
    if (!name || !name.trim()) return;
    const result = await api("/api/finance/categories", {
      method: "POST",
      body: JSON.stringify({ name: name.trim(), month: data.month }),
    });
    applyResult(result, (result.category && result.category.id) || result.id);
  };
  const editCat = document.getElementById("finCatEdit");
  if (editCat) editCat.onclick = async (ev) => {
    ev.preventDefault();
    const current = catEl.value;
    if (!current) return;
    const name = window.prompt(t("renamePrompt"), catLabel(current));
    if (!name || !name.trim()) return;
    const result = await api("/api/finance/categories", {
      method: "PATCH",
      body: JSON.stringify({ id: current, name: name.trim(), month: data.month }),
    });
    applyResult(result, (result.category && result.category.id) || current);
  };
  const delCat = document.getElementById("finCatDel");
  const syncCatDel = () => {
    if (delCat) delCat.hidden = catEl.value === "outros";
  };
  syncCatDel();
  catEl.addEventListener("change", syncCatDel);
  if (delCat) delCat.onclick = async (ev) => {
    ev.preventDefault();
    const current = catEl.value;
    if (!current || current === "outros") return;
    if (!window.confirm(t("deleteCategoryConfirm"))) return;
    const result = await api(`/api/finance/categories?id=${encodeURIComponent(current)}&month=${encodeURIComponent(data.month || "")}`, { method: "DELETE" });
    applyResult(result, "outros");
  };
}

function bindFinanceForm(data) {
  const form = document.getElementById("ledgerForm");
  if (!form) return;
  const dateEl = document.getElementById("finDate");
  const kindEl = document.getElementById("finKind");
  const catEl = document.getElementById("finCat");
  const descEl = document.getElementById("finDesc");
  const amountEl = document.getElementById("finAmount");
  const editing = state.financeEdit;
  const draft = state.financeDraft;
  const draftMatches = draft && JSON.stringify(draft.edit || null) === JSON.stringify(editing || null);
  if (draftMatches) {
    if (draft.date) dateEl.value = draft.date;
    if (draft.kind) kindEl.value = draft.kind;
    if (draft.category) catEl.value = draft.category;
    descEl.value = draft.merchant || "";
    amountEl.value = draft.amount || "";
  } else if (editing) {
    const row = (data.entries || []).find((e) => e.item_id === editing.item_id && e.fact_id === editing.fact_id);
    if (row) {
      dateEl.value = (row.occurred_at || "").slice(0, 10);
      kindEl.value = row.kind;
      catEl.value = row.category;
      descEl.value = row.merchant || row.title || "";
      amountEl.value = row.amount;
    }
  } else {
    dateEl.value = todayISO();
  }
  const saveDraft = () => { state.financeDraft = financeDraftFromForm(); };
  const applyCategoryResult = (result, categoryId) => {
    state.finance = result;
    saveDraft();
    if (state.financeDraft) state.financeDraft.category = categoryId || result.id || "outros";
    render();
  };
  form.addEventListener("input", saveDraft);
  form.addEventListener("change", saveDraft);
  form.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && ev.target && ev.target.tagName !== "BUTTON") {
      ev.preventDefault();
    }
  });
  form.onsubmit = async (ev) => {
    ev.preventDefault();
    const payload = {
      occurred_at: dateEl.value,
      kind: kindEl.value,
      category: catEl.value,
      merchant: descEl.value.trim(),
      amount: Number(amountEl.value),
      month: data.month,
    };
    const path = editing
      ? `/api/finance/entries/${editing.item_id}/${editing.fact_id}`
      : "/api/finance/entries";
    const method = editing ? "PATCH" : "POST";
    const result = await api(path, { method, body: JSON.stringify(payload) });
    state.finance = result;
    state.financeEdit = null;
    state.financeDraft = null;
    try { state.reports = await api("/api/reports"); } catch (err) { console.error(err); }
    await refresh();
    render();
  };
  const cancel = document.getElementById("finCancel");
  if (cancel) cancel.onclick = () => { state.financeEdit = null; state.financeDraft = null; render(); };
  bindCategoryButtons(catEl, data, applyCategoryResult);
  const applyTypeResult = (result, typeId) => {
    state.finance = result;
    saveDraft();
    if (state.financeDraft) state.financeDraft.kind = typeId || "gasto";
    render();
  };
  const addType = document.getElementById("finTypeAdd");
  if (addType) addType.onclick = async (ev) => {
    ev.preventDefault();
    const name = window.prompt(t("typePrompt"), "");
    if (!name || !name.trim()) return;
    const side = askTypeSide("saida");
    if (!side) return;
    const result = await api("/api/finance/types", {
      method: "POST",
      body: JSON.stringify({ name: name.trim(), side, month: data.month }),
    });
    applyTypeResult(result, (result.type && result.type.id) || "gasto");
  };
  const editType = document.getElementById("finTypeEdit");
  if (editType) editType.onclick = async (ev) => {
    ev.preventDefault();
    const current = kindEl.value;
    if (!current) return;
    const name = window.prompt(t("renamePrompt"), typeLabel(current));
    if (!name || !name.trim()) return;
    const row = financeTypes().find((item) => item.id === current);
    const side = askTypeSide((row && row.side) || "saida");
    if (!side) return;
    const result = await api("/api/finance/types", {
      method: "PATCH",
      body: JSON.stringify({ id: current, name: name.trim(), side, month: data.month }),
    });
    applyTypeResult(result, (result.type && result.type.id) || current);
  };
  const delType = document.getElementById("finTypeDel");
  const syncTypeDel = () => {
    if (delType) delType.hidden = kindEl.value === "receita" || kindEl.value === "gasto";
  };
  syncTypeDel();
  kindEl.addEventListener("change", syncTypeDel);
  if (delType) delType.onclick = async (ev) => {
    ev.preventDefault();
    const current = kindEl.value;
    if (!current || current === "receita" || current === "gasto") return;
    if (!window.confirm(t("deleteTypeConfirm"))) return;
    const row = financeTypes().find((item) => item.id === current);
    const result = await api(`/api/finance/types?id=${encodeURIComponent(current)}&month=${encodeURIComponent(data.month || "")}`, { method: "DELETE" });
    applyTypeResult(result, row && row.side === "entrada" ? "receita" : "gasto");
  };
  document.querySelectorAll("[data-edit-entry]").forEach((btn) => {
    btn.onclick = (ev) => {
      ev.stopPropagation();
      const [item_id, fact_id] = btn.dataset.editEntry.split(":");
      state.financeEdit = { item_id, fact_id };
      render();
    };
  });
  document.querySelectorAll("[data-del-entry]").forEach((btn) => {
    btn.onclick = async (ev) => {
      ev.stopPropagation();
      if (!window.confirm(t("deleteEntryConfirm"))) return;
      const [item_id, fact_id] = btn.dataset.delEntry.split(":");
      const result = await api(`/api/finance/entries/${item_id}/${fact_id}?month=${encodeURIComponent(data.month)}`, { method: "DELETE" });
      state.finance = result;
      if (state.financeEdit && state.financeEdit.item_id === item_id && state.financeEdit.fact_id === fact_id) {
        state.financeEdit = null;
      }
      await refresh();
      render();
    };
  });
}

function bindPayableForm(data) {
  const form = document.getElementById("payableForm");
  if (!form) return;
  const dateEl = document.getElementById("payDate");
  const descEl = document.getElementById("payDesc");
  const catEl = document.getElementById("finCat");
  const statusEl = document.getElementById("payStatus");
  const paidEl = document.getElementById("payPaid");
  const paidWrap = document.getElementById("payPaidWrap");
  const amountEl = document.getElementById("payAmount");
  const repeatEl = document.getElementById("payRepeat");
  const repeatWrap = document.getElementById("payRepeatWrap");
  const repeatMonthsEl = document.getElementById("payRepeatMonths");
  const editing = state.payableEdit;
  const draft = state.payableDraft;
  const draftMatches = draft && JSON.stringify(draft.edit || null) === JSON.stringify(editing || null);
  const syncPayableExtras = () => {
    const pago = statusEl.value === "pago";
    if (paidWrap) paidWrap.hidden = !pago;
    if (pago && paidEl && !paidEl.value) paidEl.value = dateEl.value || todayISO();
    if (repeatWrap && repeatEl) repeatWrap.hidden = !repeatEl.checked;
  };
  if (draftMatches) {
    if (draft.date) dateEl.value = draft.date;
    descEl.value = draft.description || "";
    if (draft.category) catEl.value = draft.category;
    if (draft.status) statusEl.value = draft.status;
    if (paidEl && draft.paid) paidEl.value = draft.paid;
    amountEl.value = draft.amount || "";
    if (repeatEl) repeatEl.checked = Boolean(draft.repeat);
    if (repeatMonthsEl && draft.months) repeatMonthsEl.value = draft.months;
  } else if (editing) {
    const row = (data.payables || []).find((e) => e.item_id === editing.item_id && e.fact_id === editing.fact_id);
    if (row) {
      dateEl.value = (row.due_at || "").slice(0, 10);
      descEl.value = row.description || "";
      catEl.value = row.category;
      statusEl.value = row.status || "aberto";
      if (paidEl) paidEl.value = (row.paid_at || "").slice(0, 10);
      amountEl.value = row.amount;
    }
  } else {
    dateEl.value = todayISO();
    statusEl.value = "aberto";
  }
  syncPayableExtras();
  statusEl.addEventListener("change", syncPayableExtras);
  if (repeatEl) repeatEl.addEventListener("change", syncPayableExtras);
  const saveDraft = () => { state.payableDraft = payableDraftFromForm(); };
  const applyCategoryResult = (result, categoryId) => {
    state.finance = result;
    saveDraft();
    if (state.payableDraft) state.payableDraft.category = categoryId || "outros";
    render();
  };
  form.addEventListener("input", saveDraft);
  form.addEventListener("change", saveDraft);
  form.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && ev.target && ev.target.tagName !== "BUTTON") ev.preventDefault();
  });
  form.onsubmit = async (ev) => {
    ev.preventDefault();
    const payload = {
      due_at: dateEl.value,
      description: descEl.value.trim(),
      category: catEl.value,
      status: statusEl.value,
      paid_at: statusEl.value === "pago" ? (paidEl && paidEl.value) : "",
      recurring_months: !editing && repeatEl && repeatEl.checked ? Number(repeatMonthsEl && repeatMonthsEl.value) : 1,
      amount: Number(amountEl.value),
      month: data.month,
    };
    const path = editing
      ? `/api/finance/payables/${editing.item_id}/${editing.fact_id}`
      : "/api/finance/payables";
    const method = editing ? "PATCH" : "POST";
    const result = await api(path, { method, body: JSON.stringify(payload) });
    state.finance = result;
    state.payableEdit = null;
    state.payableDraft = null;
    await refresh();
    render();
  };
  const cancel = document.getElementById("payCancel");
  if (cancel) cancel.onclick = () => { state.payableEdit = null; state.payableDraft = null; render(); };
  bindCategoryButtons(catEl, data, applyCategoryResult);
  document.querySelectorAll("[data-edit-bill]").forEach((btn) => {
    btn.onclick = (ev) => {
      ev.stopPropagation();
      const [item_id, fact_id] = btn.dataset.editBill.split(":");
      state.payableEdit = { item_id, fact_id };
      state.payableDraft = null;
      render();
    };
  });
  document.querySelectorAll("[data-del-bill]").forEach((btn) => {
    btn.onclick = async (ev) => {
      ev.stopPropagation();
      if (!window.confirm(t("deletePayableConfirm"))) return;
      const [item_id, fact_id] = btn.dataset.delBill.split(":");
      const result = await api(`/api/finance/payables/${item_id}/${fact_id}?month=${encodeURIComponent(data.month || "")}`, { method: "DELETE" });
      state.finance = result;
      if (state.payableEdit && state.payableEdit.item_id === item_id && state.payableEdit.fact_id === fact_id) {
        state.payableEdit = null;
      }
      state.payableDraft = null;
      await refresh();
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
  if (state.readOnly) return;
  const updated = await api(`/api/items/${id}`, { method: "PATCH", body: JSON.stringify(body) });
  state.items = state.items.map((item) => (item.id === id ? updated : item));
  if (body.status === "discarded" || body.status === "done") {
    state.selected = null;
  }
  try {
    const month = state.financeMonth;
    state.finance = await api(month ? `/api/finance?month=${encodeURIComponent(month)}` : "/api/finance");
    state.reports = await api("/api/reports");
  } catch (err) {
    console.error(err);
  }
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
  const ro = state.readOnly;
  const media = (item.media_paths || []).map((_, idx) => {
    const src = `/api/files/${item.id}/${idx}`;
    const path = item.media_paths[idx] || "";
    const fileName = mediaFileName(path, item.id, idx);
    const remove = ro ? "" : `<button type="button" class="ghost" data-del-file="${idx}">${escapeHtml(d.delete)}</button>`;
    const dl = `<div class="file-ops"><a class="download" href="${src}?download=1" download="${escapeHtml(fileName)}">${escapeHtml(d.download)}</a>${remove}</div>`;
    if (path.toLowerCase().endsWith(".pdf")) {
      return `<div class="media-block"><iframe class="preview pdf" src="${src}"></iframe>${dl}</div>`;
    }
    if (/\.(mp3|wav|ogg|m4a|flac)$/i.test(path)) {
      return `<div class="media-block"><audio class="preview" controls src="${src}"></audio>${dl}</div>`;
    }
    return `<div class="media-block"><img class="preview" src="${src}" alt="media"/>${dl}</div>`;
  }).join("");
  const checks = (item.checklist || []).map((c) =>
    `<li><label><input type="checkbox" data-check="${c.id}" ${c.checked ? "checked" : ""} ${ro ? "disabled" : ""}/> ${escapeHtml(c.text)}</label></li>`
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
  const actions = ro
    ? ""
    : `<div class="row">
      <button class="primary" id="save">${escapeHtml(d.save)}</button>
      <button id="done">${escapeHtml(d.done)}</button>
      <button class="ghost" id="discard">${escapeHtml(d.discard)}</button>
      <button class="ghost" id="deleteItem">${escapeHtml(d.delete)}</button>
    </div>`;
  drawer.innerHTML = `
    <div class="kicker">${escapeHtml(kindLabel(item.kind))}${ro ? ` · ${escapeHtml(d.readOnlyBanner)}` : ""}</div>
    ${ro ? `<h1>${escapeHtml(item.title || item.summary || "")}</h1>` : `<input type="text" id="title" value="${escapeHtml(item.title || item.summary || "")}"/>`}
    ${item.subtitle ? `<p class="subtitle">${escapeHtml(item.subtitle)}</p>` : ""}
    <div class="row">
      <select id="folder" ${ro ? "disabled" : ""}>${folderOpts}</select>
      <select id="subfolder" ${ro ? "disabled" : ""}>${subOpts}</select>
      ${item.url ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(d.openLink)}</a>` : ""}
    </div>
    ${media}
    ${facts}
    ${checks ? `<ul class="check">${checks}</ul>` : ""}
    <textarea id="body" ${ro ? "readonly" : ""}>${escapeHtml(item.body || item.raw_text || item.agent_reply || "")}</textarea>
    ${actions}
  `;
  if (!ro) {
    drawer.querySelector("#folder").onchange = (ev) => patchItem(item.id, { folder: ev.target.value, status: "active" });
    drawer.querySelector("#subfolder").onchange = (ev) => patchItem(item.id, { subfolder: ev.target.value });
    drawer.querySelector("#save").onclick = () => patchItem(item.id, {
      body: drawer.querySelector("#body").value,
      title: drawer.querySelector("#title").value.trim(),
    });
    drawer.querySelector("#done").onclick = () => patchItem(item.id, { status: "done" });
    drawer.querySelector("#discard").onclick = () => patchItem(item.id, { status: "discarded" });
    drawer.querySelector("#deleteItem").onclick = async () => {
      if (!window.confirm(t("deleteItemConfirm"))) return;
      await api(`/api/items/${item.id}`, { method: "DELETE" });
      state.items = state.items.filter((row) => row.id !== item.id);
      state.selected = null;
      await refresh();
      render();
    };
    drawer.querySelectorAll("[data-del-file]").forEach((btn) => {
      btn.onclick = async () => {
        if (!window.confirm(t("deleteFileConfirm"))) return;
        const updated = await api(`/api/files/${item.id}/${btn.dataset.delFile}`, { method: "DELETE" });
        state.items = state.items.map((row) => (row.id === item.id ? updated : row));
        render();
      };
    });
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
}

const ACCT_INSS_CEILING = 8475.55;
const ACCT_IR = [
  [2428.80, 0, 0],
  [2826.65, 0.075, 182.16],
  [3751.05, 0.15, 394.16],
  [4664.68, 0.225, 675.49],
  [Infinity, 0.275, 908.73],
];

function acctMoney(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 0;
  return Math.round((number + 1e-9) * 100) / 100;
}

function acctIr(base, taxable) {
  let tax = 0;
  for (const [limit, rate, deduction] of ACCT_IR) {
    if (base <= limit + 1e-9) {
      tax = Math.max(0, base * rate - deduction);
      break;
    }
  }
  if (taxable <= 5000 + 1e-9) return 0;
  if (taxable <= 7350 + 1e-9) {
    const reduction = 978.62 - (0.133145 * taxable);
    tax = Math.max(0, tax - Math.max(0, reduction));
  }
  return acctMoney(tax);
}

function acctCompute(revenue, distribution, expenses) {
  const rev = acctMoney(Math.max(0, Number(revenue) || 0));
  const prolabore = acctMoney(rev * 0.28);
  const inssBase = acctMoney(Math.min(prolabore, ACCT_INSS_CEILING));
  const inss = acctMoney(inssBase * 0.11);
  const ir = acctIr(acctMoney(prolabore - inss), prolabore);
  const net = acctMoney(prolabore - inss - ir);
  const das = acctMoney(rev * 0.06);
  const rows = (expenses || []).map((row) => ({
    id: row.id,
    description: row.description || "",
    amount: acctMoney(Math.max(0, Number(row.amount) || 0)),
  }));
  const expensesTotal = acctMoney(rows.reduce((sum, row) => sum + row.amount, 0));
  const profit = acctMoney(rev - prolabore - das - expensesTotal);
  const dist = acctMoney(Math.max(0, Number(distribution) || 0));
  const payments = acctMoney(prolabore + das + expensesTotal + dist);
  return {
    revenue: rev,
    prolabore_gross: prolabore,
    inss_base: inssBase,
    inss,
    ir,
    prolabore_net: net,
    das,
    expenses: rows,
    expenses_total: expensesTotal,
    profit,
    distribution: dist,
    after_distribution: acctMoney(profit - dist),
    receipts: rev,
    payments,
    movement: acctMoney(rev - payments),
  };
}

function accountingSheet() {
  const data = state.accounting || { input: { revenue: 0, distribution: 0, expenses: [] } };
  const input = data.input || {};
  const draft = state.accountingDraft;
  const revenue = draft ? draft.revenue : input.revenue;
  const distribution = draft ? draft.distribution : input.distribution;
  return acctCompute(revenue, distribution, input.expenses || []);
}

function acctRuleText(sheet) {
  const pt = state.lang === "pt";
  const inssBase = brl(sheet.inss_base);
  return {
    revenue: pt ? "Entrada na conta PJ" : "PJ account inflow",
    prolabore: pt ? "28% do faturamento, para manter o DAS em 6%" : "28% of revenue, to keep DAS at 6%",
    inss: pt ? `11% sobre ${inssBase}` : `11% of ${inssBase}`,
    ir: pt ? "Tabela 2026, isento até R$ 5.000" : "2026 table, exempt up to R$ 5,000",
    net: pt ? "O que você recebe de pró-labore" : "What you receive as pay",
    das: pt ? `6% sobre ${brl(sheet.revenue)}` : `6% of ${brl(sheet.revenue)}`,
    expense: pt ? "Despesa do mês" : "Expense this month",
    profit: pt ? "Faturamento − pró-labore bruto − DAS − despesas" : "Revenue − gross pró-labore − DAS − expenses",
    distribution: pt ? "Retirada do lucro disponível" : "Cash taken from available profit",
    after: pt ? "Lucro disponível − distribuição" : "Available profit minus distribution",
  };
}

function acctCalcRows(sheet) {
  const lines = dict().acctLines;
  const rules = acctRuleText(sheet);
  const minus = (n) => `−${brl(n)}`;
  const rows = [
    ["revenue", lines.revenue, rules.revenue, brl(sheet.revenue), "income", false],
    ["prolabore", lines.prolabore, rules.prolabore, minus(sheet.prolabore_gross), "expense", false],
    ["inss", lines.inss, rules.inss, minus(sheet.inss), "expense", false],
    ["ir", lines.ir, rules.ir, minus(sheet.ir), "expense", false],
    ["net", lines.net, rules.net, brl(sheet.prolabore_net), "", true],
    ["das", lines.das, rules.das, minus(sheet.das), "expense", false],
  ];
  for (const exp of sheet.expenses) {
    rows.push([`exp-${exp.id}`, exp.description, rules.expense, minus(exp.amount), "expense", false, exp.id]);
  }
  rows.push(["profit", lines.profit, rules.profit, brl(sheet.profit), "", true]);
  rows.push(["distribution", lines.distribution, rules.distribution, minus(sheet.distribution), "expense", false]);
  rows.push(["after", lines.after, rules.after, brl(sheet.after_distribution), "", true]);
  return rows;
}

function acctTableBody(sheet) {
  const ro = state.readOnly;
  const d = dict();
  return acctCalcRows(sheet).map((row) => {
    const [key, label, rule, value, tone, total, expenseId] = row;
    const ops = !ro && expenseId
      ? `<td class="ops">
          <button type="button" class="icon-btn" data-acct-edit="${escapeHtml(expenseId)}" title="${escapeHtml(d.rename)}">✎</button>
          <button type="button" class="icon-btn danger" data-acct-del="${escapeHtml(expenseId)}" title="${escapeHtml(d.delete)}">×</button>
        </td>`
      : (ro ? "" : "<td></td>");
    return `<tr class="${total ? "total" : ""}" data-acct-row="${escapeHtml(key)}">
      <td>${escapeHtml(label)}</td>
      <td class="rule">${escapeHtml(rule)}</td>
      <td class="${tone}">${escapeHtml(value)}</td>
      ${ops}
    </tr>`;
  }).join("");
}

function accountingMovements(sheet) {
  const lines = dict().acctLines;
  const rows = [
    { side: "in", label: lines.revenue, amount: sheet.revenue },
    { side: "out", label: lines.net, amount: sheet.prolabore_net },
    { side: "out", label: lines.inss, amount: sheet.inss },
    { side: "out", label: lines.ir, amount: sheet.ir },
    { side: "out", label: lines.das, amount: sheet.das },
  ];
  for (const exp of sheet.expenses) {
    rows.push({ side: "out", label: exp.description, amount: exp.amount });
  }
  rows.push({ side: "out", label: lines.distribution, amount: sheet.distribution });
  return rows;
}

function renderAccounting() {
  const page = workspace();
  page.className = "page";
  if (!state.accounting) {
    page.innerHTML = `<p class="empty">${escapeHtml(t("loadingAccounting"))}</p>`;
    if (!state.accountingLoading) {
      state.accountingLoading = true;
      const month = state.accountingMonth;
      api(month ? `/api/accounting?month=${encodeURIComponent(month)}` : "/api/accounting")
        .then((data) => {
          state.accounting = data;
          state.accountingMonth = data.month || month;
          if (state.view === "accounting") render();
        })
        .catch((err) => {
          page.innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
        })
        .finally(() => {
          state.accountingLoading = false;
        });
    }
    return;
  }
  const d = dict();
  const data = state.accounting;
  const tab = state.accountingTab || "calc";
  const tabs = ["calc", "manage"].map((id) =>
    `<button type="button" data-acct-tab="${id}" class="${tab === id ? "active" : ""}">${escapeHtml(d.acctTabs[id])}</button>`
  ).join("");
  page.innerHTML = `
    <div class="finance-head">
      <nav class="subtabs">${tabs}</nav>
      <label class="month-field">${escapeHtml(d.month)}
        <input type="month" id="acctMonth" value="${escapeHtml(data.month || "")}"/>
      </label>
    </div>
    <div id="acctPanel"></div>`;
  page.querySelectorAll("[data-acct-tab]").forEach((btn) => {
    btn.onclick = async () => {
      if (state.accountingTab === "calc") await saveAccountingFields();
      state.accountingTab = btn.dataset.acctTab;
      render();
    };
  });
  const monthEl = document.getElementById("acctMonth");
  if (monthEl) {
    monthEl.onchange = async (ev) => {
      const next = ev.target.value;
      if (!next || next === data.month) return;
      await saveAccountingFields();
      state.accountingDraft = null;
      state.accountingExpenseEdit = null;
      state.accountingMonth = next;
      state.accounting = await api(`/api/accounting?month=${encodeURIComponent(next)}`);
      render();
    };
  }
  if (tab === "manage") renderAccountingManage();
  else renderAccountingCalc();
}

function renderAccountingCalc() {
  const panel = document.getElementById("acctPanel");
  if (!panel) return;
  const d = dict();
  const data = state.accounting;
  const input = data.input || {};
  const draft = state.accountingDraft;
  const revenue = draft ? draft.revenue : (input.revenue ?? "");
  const distribution = draft ? draft.distribution : (input.distribution ?? "");
  const editingId = state.accountingExpenseEdit;
  const editing = editingId && (input.expenses || []).find((row) => row.id === editingId);
  const ro = state.readOnly;
  const sheet = accountingSheet();
  const form = ro ? "" : `
    <form id="acctForm" class="ledger-form">
      <label>${escapeHtml(d.acctRevenue)}
        <input id="acctRevenue" type="number" min="0" step="0.01" inputmode="decimal" value="${escapeHtml(String(revenue))}"/>
      </label>
      <label>${escapeHtml(d.acctDistribution)}
        <input id="acctDistribution" type="number" min="0" step="0.01" inputmode="decimal" value="${escapeHtml(String(distribution))}"/>
      </label>
    </form>`;
  const expenseForm = ro ? "" : `
    <form id="acctExpenseForm" class="ledger-form">
      <label>${escapeHtml(d.description)}
        <input id="acctExpDesc" maxlength="80" required value="${escapeHtml(editing ? editing.description : "")}"/>
      </label>
      <label>${escapeHtml(d.amount)}
        <input id="acctExpAmount" type="number" min="0.01" step="0.01" inputmode="decimal" required value="${editing ? escapeHtml(String(editing.amount)) : ""}"/>
      </label>
      <button type="submit">${escapeHtml(editing ? d.acctSaveExpense : d.acctAddExpense)}</button>
      ${editing ? `<button type="button" id="acctExpCancel">${escapeHtml(d.cancel)}</button>` : ""}
    </form>`;
  panel.innerHTML = `
    ${form}
    <div class="table-wrap">
      <table>
        <thead><tr><th>${escapeHtml(d.acctItem)}</th><th>${escapeHtml(d.acctRule)}</th><th>${escapeHtml(d.acctValue)}</th>${ro ? "" : "<th></th>"}</tr></thead>
        <tbody id="acctCalcBody">${acctTableBody(sheet)}</tbody>
      </table>
    </div>
    ${expenseForm}`;
  bindAccountingCalc(data);
}

function bindAccountingCalc(data) {
  const rev = document.getElementById("acctRevenue");
  const dist = document.getElementById("acctDistribution");
  const remember = () => {
    state.accountingDraft = {
      revenue: rev ? rev.value : "",
      distribution: dist ? dist.value : "",
    };
    const body = document.getElementById("acctCalcBody");
    if (body) {
      body.innerHTML = acctTableBody(accountingSheet());
      bindAccountingExpenseButtons(data);
    }
  };
  if (rev) {
    rev.oninput = remember;
    rev.onchange = () => saveAccountingFields();
  }
  if (dist) {
    dist.oninput = remember;
    dist.onchange = () => saveAccountingFields();
  }
  const form = document.getElementById("acctForm");
  if (form) {
    form.onsubmit = (ev) => {
      ev.preventDefault();
      saveAccountingFields();
    };
  }
  const expenseForm = document.getElementById("acctExpenseForm");
  if (expenseForm) {
    expenseForm.onsubmit = async (ev) => {
      ev.preventDefault();
      await saveAccountingFields();
      const description = document.getElementById("acctExpDesc").value.trim();
      const amount = Number(document.getElementById("acctExpAmount").value || 0);
      const month = state.accounting.month;
      const editing = state.accountingExpenseEdit;
      const path = "/api/accounting/expenses";
      const body = { month, description, amount, id: editing || undefined };
      state.accounting = await api(path, {
        method: editing ? "PATCH" : "POST",
        body: JSON.stringify(body),
      });
      state.accountingExpenseEdit = null;
      state.accountingDraft = null;
      render();
    };
  }
  const cancel = document.getElementById("acctExpCancel");
  if (cancel) {
    cancel.onclick = () => {
      state.accountingExpenseEdit = null;
      render();
    };
  }
  bindAccountingExpenseButtons(data);
}

function bindAccountingExpenseButtons(data) {
  document.querySelectorAll("[data-acct-edit]").forEach((btn) => {
    btn.onclick = async () => {
      await saveAccountingFields();
      state.accountingExpenseEdit = btn.dataset.acctEdit;
      render();
    };
  });
  document.querySelectorAll("[data-acct-del]").forEach((btn) => {
    btn.onclick = async () => {
      if (!window.confirm(t("deleteExpenseConfirm"))) return;
      await saveAccountingFields();
      const month = (state.accounting && state.accounting.month) || data.month;
      state.accounting = await api(`/api/accounting/expenses?month=${encodeURIComponent(month)}&expense_id=${encodeURIComponent(btn.dataset.acctDel)}`, { method: "DELETE" });
      if (state.accountingExpenseEdit === btn.dataset.acctDel) state.accountingExpenseEdit = null;
      state.accountingDraft = null;
      render();
    };
  });
}

async function saveAccountingFields() {
  const rev = document.getElementById("acctRevenue");
  if (!rev || state.readOnly || !state.accounting) return;
  const dist = document.getElementById("acctDistribution");
  const revenue = acctMoney(rev.value || 0);
  const distribution = acctMoney(dist ? dist.value || 0 : 0);
  const input = state.accounting.input || {};
  if (acctMoney(input.revenue || 0) === revenue && acctMoney(input.distribution || 0) === distribution) {
    state.accountingDraft = null;
    return;
  }
  state.accounting = await api("/api/accounting", {
    method: "PUT",
    body: JSON.stringify({ month: state.accounting.month, revenue, distribution }),
  });
  state.accountingDraft = null;
}

function renderAccountingManage() {
  const panel = document.getElementById("acctPanel");
  if (!panel) return;
  const d = dict();
  const data = state.accounting;
  const sheet = accountingSheet();
  const movements = accountingMovements(sheet).map((row) => `
    <tr>
      <td>${escapeHtml(row.side === "in" ? d.acctIn : d.acctOut)}</td>
      <td>${escapeHtml(row.label)}</td>
      <td class="${row.side === "in" ? "income" : "expense"}">${escapeHtml(row.side === "in" ? brl(row.amount) : `−${brl(row.amount)}`)}</td>
    </tr>`).join("");
  const months = (data.months || []).map((row) => `
    <tr data-acct-month="${escapeHtml(row.month)}" class="${row.month === data.month ? "active" : ""}">
      <td>${escapeHtml(row.month)}</td>
      <td class="income">${escapeHtml(brl(row.revenue))}</td>
      <td class="expense">${escapeHtml(brl(row.payments))}</td>
      <td>${escapeHtml(brl(row.profit))}</td>
      <td class="expense">${escapeHtml(brl(row.distribution))}</td>
      <td>${escapeHtml(brl(row.movement))}</td>
    </tr>`).join("");
  panel.innerHTML = `
    <div class="stats">
      <div class="stat"><span>${escapeHtml(d.acctReceipts)}</span><strong class="income">${escapeHtml(brl(sheet.receipts))}</strong></div>
      <div class="stat"><span>${escapeHtml(d.acctPayments)}</span><strong class="expense">${escapeHtml(brl(sheet.payments))}</strong></div>
      <div class="stat"><span>${escapeHtml(d.acctMovement)}</span><strong>${escapeHtml(brl(sheet.movement))}</strong></div>
    </div>
    <h2>${escapeHtml(d.acctMovements)}</h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>${escapeHtml(d.type)}</th><th>${escapeHtml(d.description)}</th><th>${escapeHtml(d.acctValue)}</th></tr></thead>
        <tbody>${movements}</tbody>
      </table>
    </div>
    <h2>${escapeHtml(d.byMonth)}</h2>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>${escapeHtml(d.month)}</th>
          <th>${escapeHtml(d.acctReceipts)}</th>
          <th>${escapeHtml(d.acctPayments)}</th>
          <th>${escapeHtml(d.acctLines.profit)}</th>
          <th>${escapeHtml(d.acctDistribution)}</th>
          <th>${escapeHtml(d.acctMovement)}</th>
        </tr></thead>
        <tbody>${months}</tbody>
      </table>
    </div>`;
  panel.querySelectorAll("[data-acct-month]").forEach((row) => {
    row.onclick = async () => {
      const next = row.dataset.acctMonth;
      if (!next || next === data.month) return;
      state.accountingMonth = next;
      state.accountingDraft = null;
      state.accounting = await api(`/api/accounting?month=${encodeURIComponent(next)}`);
      render();
    };
  });
}

function isAccountingBusy() {
  if (state.view !== "accounting") return false;
  const form = document.getElementById("acctForm");
  const expense = document.getElementById("acctExpenseForm");
  const active = document.activeElement;
  if (form && form.contains(active)) return true;
  if (expense && expense.contains(active)) return true;
  return Boolean(state.accountingDraft || state.accountingExpenseEdit);
}

function render() {
  const inboxMode = state.view === "inbox";
  document.getElementById("searchWrap").hidden = !inboxMode;
  document.getElementById("statusFilters").hidden = !inboxMode;
  const captureBar = document.getElementById("captureBar");
  if (captureBar) captureBar.hidden = !inboxMode || state.readOnly;
  const title = document.getElementById("pageTitle");
  title.hidden = inboxMode;
  title.textContent = ["finance", "reports", "accounting"].includes(state.view)
    ? dict().views[state.view]
    : "";
  applyChrome();
  renderViews();
  renderStatus();
  renderFolders(state.folders || []);
  renderSubfolders();
  if (state.view === "finance") renderFinance();
  else if (state.view === "accounting") renderAccounting();
  else if (state.view === "reports") renderReports();
  else renderGrid();
  renderDrawer();
}

async function createFolder() {
  const name = window.prompt(t("folderPrompt"), "");
  if (!name || !name.trim()) return;
  const result = await api("/api/folders", { method: "POST", body: JSON.stringify({ name: name.trim() }) });
  applyTaxonomy(result);
  state.folder = result.name;
  state.subfolder = "";
  state.view = "inbox";
  render();
}

async function renameFolder(folder) {
  const name = window.prompt(t("renamePrompt"), folder);
  if (!name || !name.trim() || name.trim() === folder) return;
  const result = await api("/api/folders", {
    method: "PATCH",
    body: JSON.stringify({ folder, name: name.trim() }),
  });
  applyTaxonomy(result);
  if (state.folder === folder) state.folder = result.name;
  await refresh();
  render();
}

async function deleteFolder(folder) {
  if (!window.confirm(t("deleteFolderConfirm"))) return;
  const result = await api(`/api/folders?name=${encodeURIComponent(folder)}`, { method: "DELETE" });
  applyTaxonomy(result);
  if (state.folder === folder) {
    state.folder = ALL;
    state.subfolder = "";
  }
  await refresh();
  render();
}

async function createSubfolder() {
  if (!state.folder || state.folder === ALL) return;
  const name = window.prompt(t("subfolderPrompt"), "");
  if (!name || !name.trim()) return;
  const result = await api("/api/folders/subfolders", {
    method: "POST",
    body: JSON.stringify({ folder: state.folder, name: name.trim() }),
  });
  applyTaxonomy(result);
  state.subfolder = result.name;
  render();
}

async function renameSubfolder(subfolder) {
  const name = window.prompt(t("renamePrompt"), subfolder);
  if (!name || !name.trim() || name.trim() === subfolder) return;
  const result = await api("/api/folders/subfolders", {
    method: "PATCH",
    body: JSON.stringify({ folder: state.folder, subfolder, name: name.trim() }),
  });
  applyTaxonomy(result);
  if (state.subfolder === subfolder) state.subfolder = result.name;
  await refresh();
  render();
}

async function deleteSubfolder(subfolder) {
  if (!window.confirm(t("deleteSubConfirm"))) return;
  const qs = `folder=${encodeURIComponent(state.folder)}&name=${encodeURIComponent(subfolder)}`;
  const result = await api(`/api/folders/subfolders?${qs}`, { method: "DELETE" });
  applyTaxonomy(result);
  if (state.subfolder === subfolder) state.subfolder = "";
  await refresh();
  render();
}

async function uploadFiles(fileList) {
  const files = [...(fileList || [])];
  if (!files.length || state.readOnly) return;
  const status = document.getElementById("uploadStatus");
  if (status) status.textContent = t("uploading");
  const body = new FormData();
  if (state.folder && state.folder !== ALL) body.append("folder", state.folder);
  if (state.subfolder) body.append("subfolder", state.subfolder);
  for (const file of files) body.append("files", file, file.name);
  try {
    const result = await api("/api/uploads", { method: "POST", body });
    if (status) status.textContent = t("uploaded")(result.count || files.length);
    await refresh();
    render();
  } catch (err) {
    if (status) status.textContent = err.message || String(err);
  }
}

async function refresh() {
  const meta = await api("/api/meta");
  state.folders = meta.folders;
  state.subfolderSeeds = meta.subfolders || {};
  state.readOnly = !!meta.read_only;
  state.auth = !!meta.auth;
  const payload = await api("/api/inbox");
  state.items = payload.items || [];
  if (state.view === "finance" || !state.finance) {
    const month = state.financeMonth;
    state.finance = await api(month ? `/api/finance?month=${encodeURIComponent(month)}` : "/api/finance");
  }
  if (state.view === "reports" || !state.reports) {
    state.reports = await api("/api/reports");
  }
  if (state.view === "accounting") {
    const month = state.accountingMonth;
    state.accounting = await api(month ? `/api/accounting?month=${encodeURIComponent(month)}` : "/api/accounting");
    if (state.accounting && state.accounting.month) state.accountingMonth = state.accounting.month;
  }
}

async function boot() {
  const view = new URLSearchParams(location.search).get("view");
  if (["inbox", "finance", "accounting", "reports"].includes(view)) state.view = view;
  document.documentElement.lang = state.lang === "pt" ? "pt-BR" : "en";
  applyChrome();
  workspace().innerHTML = `<p class="empty">${escapeHtml(t("loadingArchive"))}</p>`;
  document.getElementById("q").addEventListener("input", (ev) => {
    state.q = ev.target.value;
    render();
  });
  document.querySelectorAll(".lang-toggle [data-lang]").forEach((btn) => {
    btn.onclick = () => setLang(btn.dataset.lang);
  });
  const fileInput = document.getElementById("fileInput");
  document.getElementById("btnUpload").onclick = () => fileInput.click();
  fileInput.addEventListener("change", async (ev) => {
    await uploadFiles(ev.target.files);
    ev.target.value = "";
  });
  window.addEventListener("dragover", (ev) => {
    if (![...ev.dataTransfer.items].some((it) => it.kind === "file")) return;
    ev.preventDefault();
    document.body.classList.add("dropping");
  });
  window.addEventListener("dragleave", (ev) => {
    if (ev.relatedTarget) return;
    document.body.classList.remove("dropping");
  });
  window.addEventListener("drop", async (ev) => {
    ev.preventDefault();
    document.body.classList.remove("dropping");
    if (state.view !== "inbox" || state.readOnly) return;
    await uploadFiles(ev.dataTransfer.files);
  });
  document.getElementById("menuBtn").onclick = () => {
    document.body.classList.toggle("menu-open");
  };
  document.getElementById("menuScrim").onclick = () => setMenu(false);
  await refresh();
  render();
  // Slow poll, only while the tab is visible, so Cloud Run can scale to zero.
  setInterval(async () => {
    try {
      if (document.hidden || isFinanceFormBusy() || isAccountingBusy()) return;
      await refresh();
      if (isFinanceFormBusy() || isAccountingBusy()) return;
      render();
    } catch (err) {
      console.error(err);
    }
  }, 60000);
}

boot().catch((err) => {
  workspace().innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
});

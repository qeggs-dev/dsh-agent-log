// 固定外壳：日期栏 → 当日条目索引 → 单条正文。
// 页面不随数据变化；只有 index.json 需要每次校验，其余文件按日期不可变。

import { renderMarkdown, renderInline, splitItems, escapeHtml } from './markdown.js';

const INDEX_URL = 'index.json';
const SEARCH_URL = 'search.json';
const TITLE = '工作区日志';

// 单文件预览用：preview.html 把整站塞进 __DEVLOG_FS__，省掉 HTTP 服务
const FS = window.__DEVLOG_FS__ || null;

const state = { index: null, day: null, current: null, search: null, query: '' };
const $days = document.getElementById('days');
const $entries = document.getElementById('entries');
const $dayDate = document.getElementById('dayDate');
const $dayMeta = document.getElementById('dayMeta');
const $overview = document.getElementById('overview');
const $items = document.getElementById('items');
const $entry = document.getElementById('entry');
const $main = document.getElementById('main');
const $updated = document.getElementById('updated');
const $latest = document.getElementById('latest');
const $search = document.getElementById('searchInput');
const $search2 = document.getElementById('searchInput2');
const $searches = [$search, $search2];

// ---------------------------------------------------------------- 设置与主题
// 主题四档：yellow 是 :root 默认，paper / dark 覆盖变量，system 跟随系统。

const THEME_KEY = 'devlog-theme';
const THEMES = [
  ['yellow', '笔记本'],
  ['paper', '纸白'],
  ['dark', '深色'],
  ['system', '跟随系统'],
];

const darkQuery = window.matchMedia('(prefers-color-scheme: dark)');
const $settingsBtn = document.getElementById('settingsBtn');
const $settings = document.getElementById('settings');
const $themes = document.getElementById('themes');

let themeChoice = 'yellow';

function resolveTheme(name) {
  if (name === 'system') return darkQuery.matches ? 'dark' : 'paper';
  return name;
}

function applyTheme(name) {
  themeChoice = name;
  const resolved = resolveTheme(name);
  if (resolved === 'yellow') delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = resolved;
  localStorage.setItem(THEME_KEY, name);
  for (const btn of $themes.querySelectorAll('button')) {
    btn.setAttribute('aria-pressed', String(btn.dataset.theme === name));
  }
}

for (const [name, label] of THEMES) {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.dataset.theme = name;
  btn.textContent = label;
  btn.addEventListener('click', () => applyTheme(name));
  $themes.append(btn);
}

const savedTheme = localStorage.getItem(THEME_KEY);
applyTheme(THEMES.some(([name]) => name === savedTheme) ? savedTheme : 'yellow');

function toggleSettings(open) {
  $settings.hidden = !open;
  $settingsBtn.setAttribute('aria-expanded', String(open));
}

$settingsBtn.addEventListener('click', () => toggleSettings($settings.hidden));

darkQuery.addEventListener('change', () => {
  if (themeChoice === 'system') applyTheme('system');
});

window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !$settings.hidden) toggleSettings(false);
});

// ---------------------------------------------------------------- 取数

function fsGet(url) {
  if (!FS) return undefined;
  const key = url.split('?')[0];
  return Object.prototype.hasOwnProperty.call(FS, key) ? FS[key] : undefined;
}

async function loadText(url, { fresh = false } = {}) {
  const hit = fsGet(url);
  if (hit !== undefined) return hit;
  const res = await fetch(fresh ? `${url}?t=${Date.now()}` : url, fresh ? { cache: 'no-store' } : undefined);
  if (!res.ok) throw new Error(`${url} 读取失败：HTTP ${res.status}`);
  return res.text();
}

async function loadJson(url, opts) {
  return JSON.parse(await loadText(url, opts));
}

function formatStamp(iso) {
  return iso ? String(iso).replace('T', ' ').slice(0, 16) : '未知';
}

async function loadDay(date) {
  const meta = state.index.days.find((d) => d.date === date);
  if (!meta) throw new Error(`索引里没有 ${date}`);
  const index = await loadJson(meta.index);
  const bodies = await Promise.all(index.projects.map((p) => loadText(p.body)));

  // 标题来自当日索引的 items（数据通道），不从 Markdown 结构里解析
  const titles = new Map((index.items || []).map((e) => [e.id, e.title]));
  const items = [];
  index.projects.forEach((project, i) => {
    const base = project.body.slice(0, project.body.lastIndexOf('/') + 1);
    for (const piece of splitItems(bodies[i])) {
      items.push({
        ...piece,
        title: titles.get(piece.id) || '(无标题)',
        base,
        project: project.name,
      });
    }
  });
  return { index, items, meta };
}

// ---------------------------------------------------------------- 渲染

function renderSidebar() {
  $days.replaceChildren();
  for (const d of state.index.days) {
    const a = document.createElement('a');
    a.href = `#/${d.date}`;
    a.textContent = d.date;
    if (state.day && d.date === state.day.index.date) a.setAttribute('aria-current', 'true');
    const count = document.createElement('span');
    count.className = 'count';
    count.textContent = d.entries ?? '';
    a.append(count);
    $days.append(a);
  }
}

function renderHeader() {
  const { latest } = state.index;
  $latest.innerHTML = latest
    ? `最新 <b>${escapeHtml(latest.id)}</b> · ${escapeHtml(latest.project)}`
    : '还没有数据';
  $updated.textContent = `更新于 ${formatStamp(state.index.updated)}`;
}

async function ensureSearch() {
  if (state.search) return;
  state.search = await loadJson(state.index.search || SEARCH_URL, { fresh: true });
}

function searchEntries(query) {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (!terms.length || !state.search) return [];
  const hits = [];

  for (const entry of state.search.entries) {
    const t = (entry.t || '').toLowerCase();
    const p = (entry.p || '').toLowerCase();
    const k = (entry.k || []).join(' ').toLowerCase();
    const x = (entry.x || '').toLowerCase();
    const id = (entry.i || '').toLowerCase();

    let score = 0;
    let ok = true;
    for (const term of terms) {
      if (t.includes(term)) score += 10;
      else if (k.includes(term)) score += 5;
      else if (p.includes(term)) score += 3;
      else if (id.includes(term)) score += 3;
      else if (x.includes(term)) score += 1;
      else { ok = false; break; }
    }
    if (ok) hits.push({ entry, score });
  }

  hits.sort((a, b) => b.score - a.score || (a.entry.d < b.entry.d ? 1 : -1));
  return hits.slice(0, 60).map((h) => h.entry);
}

function renderResults(query) {
  const results = searchEntries(query);
  $overview.hidden = true;
  $items.replaceChildren();

  const head = document.createElement('p');
  head.className = 'group-name';
  head.textContent = results.length ? `${results.length} 条结果` : '没有匹配的条目';
  $items.append(head);

  for (const r of results) {
    const a = document.createElement('a');
    a.className = 'entry-link result';
    a.href = `#/${r.d}/${r.i}`;
    const date = document.createElement('span');
    date.className = 'r-date';
    date.textContent = r.d;
    const title = document.createElement('span');
    title.className = 't';
    title.innerHTML = renderInline(r.t);
    const proj = document.createElement('span');
    proj.className = 'eid';
    proj.textContent = r.p;
    a.append(date, title, proj);
    $items.append(a);
  }
}

function renderEntries() {
  const { index, items } = state.day;

  $dayDate.textContent = index.date;
  $dayMeta.textContent = `${index.weekday || ''} · ${index.projects.length} 个板块 · ${items.length} 条`;

  if (state.query.trim()) {
    renderResults(state.query);
    return;
  }

  if (index.overview) {
    $overview.src = index.overview;
    $overview.hidden = false;
  } else {
    $overview.hidden = true;
  }

  $items.replaceChildren();
  let lastProject = null;
  for (const item of items) {
    if (item.project !== lastProject) {
      const group = document.createElement('p');
      group.className = 'group-name';
      group.textContent = item.project;
      $items.append(group);
      lastProject = item.project;
    }
    const a = document.createElement('a');
    a.className = 'entry-link';
    a.href = `#/${index.date}/${item.id || ''}`;
    if (state.current && item.id === state.current.id) a.setAttribute('aria-current', 'true');
    const title = document.createElement('span');
    title.className = 't';
    title.innerHTML = renderInline(item.title);
    a.append(title);
    if (item.id) {
      const eid = document.createElement('span');
      eid.className = 'eid';
      eid.textContent = item.id;
      a.append(eid);
    }
    $items.append(a);
  }
}

function pagerLink(direction) {
  const items = state.day.items;
  const i = items.findIndex((x) => state.current && x.id === state.current.id);
  const j = direction === 'prev' ? i - 1 : i + 1;
  if (j < 0 || j >= items.length) return '<span class="disabled"></span>';
  const label = direction === 'prev' ? '← 上一条' : '下一条 →';
  return `<a href="#/${state.day.index.date}/${items[j].id}">${label}</a>`;
}

function renderEntry() {
  const { index, items } = state.day;
  const item = state.current;

  if (!item) {
    $entry.innerHTML = '<p class="muted">这一天还没有条目。</p>';
    document.title = TITLE;
    return;
  }

  const idx = items.findIndex((x) => x.id === item.id) + 1;
  $entry.innerHTML = [
    `<p class="kicker">${escapeHtml(item.project)} · ${escapeHtml(index.date)}` +
      `<span class="kicker-chip">第 ${idx} / ${items.length} 条</span></p>`,
    `<h2>${renderInline(item.title)}</h2>`,
    item.id ? `<p class="entry-id">✦ ${escapeHtml(item.id)}</p>` : '',
    `<div class="entry-card">${renderMarkdown(item.body, { base: item.base })}</div>`,
    `<div class="pager">${pagerLink('prev')}${pagerLink('next')}</div>`,
  ].join('\n');

  document.title = `${item.title} · ${index.date} · ${TITLE}`;
  $main.scrollTop = 0;
  const active = $items.querySelector('a[aria-current="true"]');
  if (active) active.scrollIntoView({ block: 'nearest' });
}

function showError(err) {
  $entry.innerHTML = `<p class="error">${escapeHtml(err.message || String(err))}</p>`;
}

// ---------------------------------------------------------------- 路由

async function route() {
  try {
    if (!state.index) {
      state.index = await loadJson(INDEX_URL, { fresh: true });
      if (!Array.isArray(state.index.days) || !state.index.days.length) {
        throw new Error('index.json 里没有日期');
      }
      renderHeader();
    }

    const raw = decodeURIComponent(location.hash.replace(/^#\/?/, '')).trim();
    const [datePart = '', entryPart = ''] = raw.split('/');
    if (datePart && !/^\d{4}-\d{2}-\d{2}$/.test(datePart)) {
      throw new Error(`日期格式不对：${datePart}`);
    }

    // 导航时退出搜索态，第二栏回到当天条目
    if (state.query) {
      state.query = '';
      for (const input of $searches) input.value = '';
    }

    const date = datePart || state.index.days[0].date;
    if (!state.day || state.day.index.date !== date) {
      state.day = await loadDay(date);
    }
    state.current = state.day.items.find((x) => x.id === entryPart) || state.day.items[0] || null;

    renderSidebar();
    renderEntries();
    renderEntry();
  } catch (err) {
    showError(err);
  }
}

window.addEventListener('hashchange', route);

// 站内链接统一走 hash 路由，避免 iframe / 预览环境里触发默认跳转
document.addEventListener('click', (e) => {
  const link = e.target.closest ? e.target.closest('a[href^="#/"]') : null;
  if (!link) return;
  e.preventDefault();
  const target = link.getAttribute('href');
  if (location.hash === target) route();
  else location.hash = target;
});

window.addEventListener('keydown', (e) => {
  if (e.key === '/' && document.activeElement !== $search) {
    e.preventDefault();
    $search.focus();
    return;
  }
  if ($searches.includes(document.activeElement)) return;
  if (!state.current) return;
  const step = e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1
    : (e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : 0);
  if (!step) return;
  const items = state.day.items;
  const i = items.findIndex((x) => x.id === state.current.id);
  const j = i + step;
  if (j >= 0 && j < items.length) location.hash = `#/${state.day.index.date}/${items[j].id}`;
});

for (const input of $searches) {
  input.addEventListener('input', async () => {
    state.query = input.value;
    if (state.query.trim()) {
      try {
        await ensureSearch();
      } catch (err) {
        showError(err);
        return;
      }
    }
    for (const other of $searches) {
      if (other !== input) other.value = state.query;
    }
    if (state.day) renderEntries();
  });

  input.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    state.query = '';
    for (const other of $searches) other.value = '';
    if (state.day) renderEntries();
    input.blur();
  });
}

route();

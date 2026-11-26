// 固定外壳：读根索引 → 读当日索引 → 读各板块 Markdown → 渲染。
// 页面本身不随数据变化；只有 index.json 需要每次校验，其余文件按日期不可变。

import { renderMarkdown, escapeHtml } from './markdown.js';

const INDEX_URL = 'index.json';
const TITLE = '工作区日志';

// 单文件预览用：preview.html 把整站塞进 __DEVLOG_FS__，省掉 HTTP 服务
const FS = window.__DEVLOG_FS__ || null;

const state = { index: null, day: null };
const $days = document.getElementById('days');
const $day = document.getElementById('day');
const $updated = document.getElementById('updated');
const $latest = document.getElementById('latest');

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
  return { index, bodies, meta };
}

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

function pagerLink(direction) {
  const days = state.index.days;
  const i = days.findIndex((d) => d.date === state.day.index.date);
  const j = direction === 'older' ? i + 1 : i - 1;
  if (j < 0 || j >= days.length) return '<span class="disabled"></span>';
  const arrow = direction === 'older' ? '←' : '→';
  return `<a href="#/${days[j].date}">${arrow} ${days[j].date}</a>`;
}

function renderDay() {
  const { index, bodies } = state.day;
  const parts = [];

  parts.push(`<h2>${escapeHtml(index.date)}</h2>`);
  parts.push(
    `<div class="meta"><span>${escapeHtml(index.weekday || '')}</span>` +
      `<span class="chip">${index.projects.length} 个板块 · ${index.entries} 条</span></div>`
  );

  if (index.overview) {
    parts.push(
      `<img class="overview" src="${escapeHtml(index.overview)}" alt="当日概览" loading="lazy">`
    );
  }

  index.projects.forEach((project, i) => {
    const kw = (project.keywords || [])
      .map((k) => `<span>${escapeHtml(k)}</span>`)
      .join('');
    const base = project.body.slice(0, project.body.lastIndexOf('/') + 1);
    parts.push(`<section class="project"><h3>${escapeHtml(project.name)}</h3>`);
    if (kw) parts.push(`<div class="kw">${kw}</div>`);
    parts.push(renderMarkdown(bodies[i], { base }));
    parts.push('</section>');
  });

  parts.push(`<div class="pager">${pagerLink('older')}${pagerLink('newer')}</div>`);

  $day.innerHTML = parts.join('\n');
  document.title = `${index.date} · ${TITLE}`;
  document.getElementById('main').scrollTop = 0;
}

function showError(err) {
  $day.innerHTML = `<p class="error">${escapeHtml(err.message || String(err))}</p>`;
}

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
    if (raw && !/^\d{4}-\d{2}-\d{2}$/.test(raw)) throw new Error(`日期格式不对：${raw}`);

    state.day = await loadDay(raw || state.index.days[0].date);
    renderSidebar();
    renderDay();
  } catch (err) {
    showError(err);
  }
}

window.addEventListener('hashchange', route);
window.addEventListener('keydown', (e) => {
  if (!state.day || !state.index) return;
  if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
  const days = state.index.days;
  const i = days.findIndex((d) => d.date === state.day.index.date);
  const j = e.key === 'ArrowLeft' ? i + 1 : i - 1;
  if (j >= 0 && j < days.length) location.hash = `#/${days[j].date}`;
});

route();

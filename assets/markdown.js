// 只渲染生成器会产出的 Markdown 子集：
// 标题 / 段落 / 无序列表 / 粗体 / 行内代码 / 链接 / 图片，
// 外加 `<!-- 条目id -->` 注释（GitHub 不渲染，这里变成条目徽标）。
// 不做通用 Markdown——渲染器越小，能出错的地方越少。

const ID_COMMENT = /^<!--\s*([0-9]{8}-[0-9]{3})\s*-->$/;
const HEADING = /^(#{1,6})\s+(.+)$/;

export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

export function resolveSrc(src, base) {
  if (!src) return '';
  if (/^[a-z][a-z0-9+.-]*:/i.test(src) || src.startsWith('/') || src.startsWith('#')) return src;
  return (base || '') + src.replace(/^\.\//, '');
}

function inline(raw, base) {
  return escapeHtml(raw)
    .replace(
      /!\[([^\]]*)\]\(([^)\s]+)\)/g,
      (_, alt, src) => `<img src="${resolveSrc(src, base)}" alt="${alt}">`
    )
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(
      /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
      '<a href="$2" rel="noopener noreferrer" target="_blank">$1</a>'
    );
}

export function renderMarkdown(src, opts = {}) {
  const base = opts.base || '';
  const lines = String(src ?? '').replace(/\r\n?/g, '\n').split('\n');
  const out = [];
  let para = [];
  let list = [];
  let itemOpen = false;

  const flushPara = () => {
    if (!para.length) return;
    out.push(`<p>${para.map((l) => inline(l, base)).join('<br>')}</p>`);
    para = [];
  };
  const flushList = () => {
    if (!list.length) return;
    out.push(`<ul>${list.map((t) => `<li>${inline(t, base)}</li>`).join('')}</ul>`);
    list = [];
  };
  const flushAll = () => { flushPara(); flushList(); };
  const openItem = (id) => {
    if (itemOpen) out.push('</div>');
    out.push(`<div class="item"${id ? ` data-id="${id}"` : ''}>`);
    itemOpen = true;
  };

  for (const raw of lines) {
    const line = raw.replace(/\s+$/, '');
    if (!line.trim()) { flushAll(); continue; }

    const idMatch = line.trim().match(ID_COMMENT);
    if (idMatch) { flushAll(); openItem(idMatch[1]); continue; }

    if (!itemOpen) openItem(null);

    const heading = line.match(HEADING);
    if (heading) {
      flushAll();
      const level = Math.min(heading[1].length + 2, 6);
      out.push(`<h${level}>${inline(heading[2].trim(), base)}</h${level}>`);
      continue;
    }

    const li = line.match(/^\s{0,3}[-*]\s+(.*)$/);
    if (li) { flushPara(); list.push(li[1]); continue; }

    flushList();
    para.push(line.trim());
  }

  flushAll();
  if (itemOpen) out.push('</div>');
  return out.join('\n');
}

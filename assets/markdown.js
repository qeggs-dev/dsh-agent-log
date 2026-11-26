// 只渲染生成器会产出的 Markdown 子集：段落 / 无序列表 / 粗体 / 行内代码 / 链接，
// 外加 `<!-- 条目id -->` 注释（GitHub 不渲染，这里变成条目徽标）。
// 不做通用 Markdown——渲染器越小，能出错的地方越少。

const ID_COMMENT = /^<!--\s*([0-9]{8}-[0-9]{3})\s*-->$/;

export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function inline(raw) {
  return escapeHtml(raw)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(
      /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
      '<a href="$2" rel="noopener noreferrer" target="_blank">$1</a>'
    );
}

export function renderMarkdown(src) {
  const lines = String(src ?? '').replace(/\r\n?/g, '\n').split('\n');
  const out = [];
  let para = [];
  let list = [];
  let itemOpen = false;

  const flushPara = () => {
    if (!para.length) return;
    out.push(`<p>${para.map(inline).join('<br>')}</p>`);
    para = [];
  };
  const flushList = () => {
    if (!list.length) return;
    out.push(`<ul>${list.map((t) => `<li>${inline(t)}</li>`).join('')}</ul>`);
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

    const li = line.match(/^\s{0,3}[-*]\s+(.*)$/);
    if (li) { flushPara(); list.push(li[1]); continue; }

    flushList();
    para.push(line.trim());
  }

  flushAll();
  if (itemOpen) out.push('</div>');
  return out.join('\n');
}

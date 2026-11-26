import assert from 'node:assert/strict';
import { renderMarkdown, escapeHtml, resolveSrc } from '../assets/markdown.js';

// 转义
assert.equal(escapeHtml('<b>&"'), '&lt;b&gt;&amp;&quot;');

// 段落 + 空行分段
assert.equal(renderMarkdown('第一段'), '<div class="item">\n<p>第一段</p>\n</div>');

assert.equal(
  renderMarkdown('第一段\n\n第二段'),
  '<div class="item">\n<p>第一段</p>\n<p>第二段</p>\n</div>'
);

// 单换行变 <br>
assert.equal(renderMarkdown('a\nb'), '<div class="item">\n<p>a<br>b</p>\n</div>');

// 行内格式
assert.equal(
  renderMarkdown('**粗** 和 `code`'),
  '<div class="item">\n<p><strong>粗</strong> 和 <code>code</code></p>\n</div>'
);

// 链接
assert.equal(
  renderMarkdown('[文档](https://example.com/a)'),
  '<div class="item">\n<p><a href="https://example.com/a" rel="noopener noreferrer" target="_blank">文档</a></p>\n</div>'
);

// 标题：## → h4（正文嵌在页面 h2/h3 之下）
assert.equal(
  renderMarkdown('## 条目标题\n正文'),
  '<div class="item">\n<h4>条目标题</h4>\n<p>正文</p>\n</div>'
);
assert.equal(
  renderMarkdown('# 一级'),
  '<div class="item">\n<h3>一级</h3>\n</div>'
);

// 图片：相对路径按正文所在目录解析
assert.equal(resolveSrc('evo-1.png', 'data/2026-11-26/'), 'data/2026-11-26/evo-1.png');
assert.equal(resolveSrc('./evo-1.png', 'data/2026-11-26/'), 'data/2026-11-26/evo-1.png');
assert.equal(resolveSrc('https://x/y.png', 'data/2026-11-26/'), 'https://x/y.png');
assert.equal(resolveSrc('data:image/png;base64,AAA', 'data/2026-11-26/'), 'data:image/png;base64,AAA');

assert.equal(
  renderMarkdown('![截图](evo-1.png)', { base: 'data/2026-11-26/' }),
  '<div class="item">\n<p><img src="data/2026-11-26/evo-1.png" alt="截图"></p>\n</div>'
);

// 图片不能被当成链接
const imgHtml = renderMarkdown('![a](b.png)', { base: 'd/' });
assert.ok(!imgHtml.includes('<a '), imgHtml);

// 条目注释 → 独立的 item，且不留注释原文
const items = renderMarkdown('<!-- 20261126-007 -->\n第一条\n\n<!-- 20261126-009 -->\n第二条');
assert.equal(
  items,
  [
    '<div class="item" data-id="20261126-007">',
    '<p>第一条</p>',
    '</div>',
    '<div class="item" data-id="20261126-009">',
    '<p>第二条</p>',
    '</div>',
  ].join('\n')
);
assert.ok(!items.includes('<!--'));

// 生成器的真实块结构：id + 标题 + 正文 + 图
const real = renderMarkdown(
  '<!-- 20261126-007 -->\n\n## 标题\n\n正文一段\n\n![截图](shot.png)',
  { base: 'data/2026-11-26/' }
);
assert.ok(real.includes('data-id="20261126-007"'), real);
assert.ok(real.includes('<h4>标题</h4>'), real);
assert.ok(real.includes('src="data/2026-11-26/shot.png"'), real);

// 列表
assert.equal(
  renderMarkdown('- 一\n- 二'),
  '<div class="item">\n<ul><li>一</li><li>二</li></ul>\n</div>'
);

// 危险内容必须被转义，不能变成标签
const evil = renderMarkdown('<img src=x onerror=alert(1)>');
assert.ok(!evil.includes('<img'), evil);
assert.ok(evil.includes('&lt;img'), evil);

// 非法 id 注释按普通文本处理
assert.ok(renderMarkdown('<!-- 2026-11-26 -->').includes('&lt;!--'));

// 空输入
assert.equal(renderMarkdown(''), '');
assert.equal(renderMarkdown(null), '');

console.log('markdown renderer: 15 groups ok');

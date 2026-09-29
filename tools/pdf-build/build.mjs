// Build one PDF from every tracked Markdown document under curriculum/.
// Usage: node build.mjs <pass: 1|2> [tocPages.json]
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
import MarkdownIt from 'markdown-it';
import GithubSlugger from 'github-slugger';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '..', '..');   // the repository root
const HERE_URL = pathToFileURL(HERE).href;   // file URL of this folder, safe for paths with spaces
const OUT = path.join(HERE, 'out');
const GH = process.env.REPO_URL || 'https://github.com/nagarjunak-pixel/02-autogpt-autonomous-agent';
const COMMIT = process.env.COMMIT || 'main';
const pass = process.argv[2] || '1';
const tocPages = process.argv[3] ? JSON.parse(fs.readFileSync(process.argv[3], 'utf8')) : null;
fs.mkdirSync(OUT, { recursive: true });

// ---- document order -------------------------------------------------------
const ls = (dir, re) => fs.readdirSync(path.join(REPO, dir)).filter(f => re.test(f)).sort().map(f => `${dir}/${f}`);
const kits = fs.readdirSync(path.join(REPO, 'curriculum/projects/starter-kits'))
  .filter(d => /^P\d\d-/.test(d)).sort();
const PARTS = [
  { id: 'part-overview', title: 'Overview and curriculum review', blurb: 'Headline findings, then the structural review of Vol 2 and a stress-test of the existing gap analysis.',
    files: ['curriculum/README.md', 'curriculum/01-curriculum-review.md'] },
  { id: 'part-gaps', title: 'Gap register', blurb: '61 verified missing topics, ranked, with evidence and interview Q&As; then the six area files.',
    files: ['curriculum/02-gap-register.md', ...ls('curriculum/gap-register', /\.md$/)] },
  { id: 'part-errata', title: 'Errata and fact-check', blurb: 'What in Vol 2 and the gap document is wrong, outdated or needs nuance, with sources.',
    files: ['curriculum/03-errata-and-fact-check.md'] },
  { id: 'part-future', title: 'Future topics and revised syllabus', blurb: 'The 2026–2028 horizon scan and dated calendar, then the revised syllabus and 16-week FDE track.',
    files: ['curriculum/04-future-topics-2026-2028.md', 'curriculum/05-revised-syllabus-and-learning-path.md'] },
  { id: 'part-projects', title: 'FDE project briefs', blurb: 'How every project runs, the rubric and coverage matrix, then the 16\u00a0engagement briefs.',
    files: ['curriculum/projects/README.md', ...ls('curriculum/projects', /^P\d\d-.*\.md$/)] },
  { id: 'part-templates', title: 'Engagement templates', blurb: 'The ten reusable templates every project uses.',
    files: ls('curriculum/projects/templates', /\.md$/) },
  { id: 'part-kits', title: 'Starter kits', blurb: 'Run commands, metric-to-criterion maps and limits for each offline kit, and the P02 validation report. The kit source code is in the repository, not reproduced here.',
    files: ['curriculum/projects/starter-kits/README.md',
      ...kits.flatMap(k => [`curriculum/projects/starter-kits/${k}/README.md`,
        ...(fs.existsSync(path.join(REPO, `curriculum/projects/starter-kits/${k}/spec_stub.md`)) ? [`curriculum/projects/starter-kits/${k}/spec_stub.md`] : []),
        // a kit's validation report (instructor note) follows the kit it scored
        ...(fs.existsSync(path.join(REPO, `curriculum/projects/validation/${k.slice(0, 3)}-validation-report.md`)) ? [`curriculum/projects/validation/${k.slice(0, 3)}-validation-report.md`] : [])])] },
];
const ALL = PARTS.flatMap(p => p.files);
// every tracked Markdown file under curriculum/ must be in the book, and nothing else (skipped outside a git checkout)
const coverage = [];
try {
  const tracked = execFileSync('git', ['-C', REPO, 'ls-files', '--', 'curriculum/*.md', 'curriculum/**/*.md'], { encoding: 'utf8' }).split('\n').filter(Boolean);
  for (const f of tracked) if (!ALL.includes(f)) coverage.push(`tracked but not in the book: ${f} (add it to PARTS in build.mjs)`);
  for (const f of ALL) if (!tracked.includes(f)) coverage.push(`in the book but not tracked by git: ${f}`);
} catch { /* not a git checkout */ }
// chapters whose last page held only a line or two in an earlier pass are set a little tighter (build_loop.py)
const TIGHT = fs.existsSync(path.join(OUT, 'tight.json')) ? JSON.parse(fs.readFileSync(path.join(OUT, 'tight.json'), 'utf8')) : {};
const TITLE_OVERRIDE = { 'curriculum/projects/starter-kits/P09-legacy-modernisation-with-coding-agents/spec_stub.md': 'P09 Kit File · PRMCALC Premium Basis: Product-Filing Summary' };
const KICKER_FILE = { 'curriculum/projects/starter-kits/P09-legacy-modernisation-with-coding-agents/spec_stub.md': 'P09 kit file · <span class="kf">spec_stub.md</span>' };
const fileId = f => 'f-' + f.replace(/^curriculum\//, '').replace(/\.md$/, '').replace(/[^A-Za-z0-9]+/g, '-').toLowerCase();
const byPath = new Map(ALL.map(f => [f, fileId(f)]));
const dirTarget = { 'curriculum/gap-register': 'part-gaps', 'curriculum/projects/templates': 'part-templates' };

// ---- markdown ---------------------------------------------------------------
const md = new MarkdownIt({ html: false, linkify: false, typographer: true });
md.disable('replacements');
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const defaultFence = md.renderer.rules.fence;
const hljs = require('highlight.js');
// split highlighted HTML into lines, closing and reopening spans that cross a line break
function splitHighlighted(html) {
  const out = [], open = []; let cur = '';
  for (const part of html.split(/(<span[^>]*>|<\/span>|\n)/)) {
    if (!part) continue;
    if (part === '\n') { out.push(cur + '</span>'.repeat(open.length)); cur = open.join(''); }
    else if (part.startsWith('<span')) { open.push(part); cur += part; }
    else if (part === '</span>') { open.pop(); cur += part; }
    else cur += part;
  }
  out.push(cur + '</span>'.repeat(open.length));
  return out;
}
md.renderer.rules.fence = (tokens, idx, opts, env, self) => {
  const t = tokens[idx];
  if (t.info.trim() === 'mermaid') { env.mermaid = (env.mermaid || 0) + 1; return `<div class="diagram"><pre class="mermaid-src">${esc(t.content)}</pre></div>\n`; }
  const lang = t.info.trim().split(/\s+/)[0];
  const src = t.content.replace(/\n$/, '');
  const hlLang = { py: 'python', python: 'python', bash: 'bash', sh: 'bash', shell: 'bash', json: 'json', jsonl: 'json',
    sql: 'sql', ts: 'typescript', typescript: 'typescript', js: 'javascript', javascript: 'javascript', yaml: 'yaml',
    yml: 'yaml', http: 'http', diff: 'diff', cobol: null }[lang.toLowerCase()];
  let htmlCode = esc(src);
  if (/^(bash|sh|shell|console)$/i.test(lang)) {
    // shell: colour comments only, and keep hyphenated words (--limit, eval-harness) whole when a long line wraps
    htmlCode = src.split('\n').map(line => {
      let ci = -1, q = null;
      for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        if (q) { if (ch === q) q = null; } else if (ch === '"' || ch === "'") q = ch;
        else if (ch === '#' && (i === 0 || /\s/.test(line[i - 1]))) { ci = i; break; }
      }
      const code = ci >= 0 ? line.slice(0, ci) : line, com = ci >= 0 ? line.slice(ci) : '';
      return esc(code).replace(/\S*-\S*/g, t => t.length <= 60 ? `<span class="nb">${t}</span>` : t) + (com ? `<span class="hljs-comment">${esc(com)}</span>` : '');
    }).join('\n');
  }
  if (hlLang && hlLang !== 'bash' && hljs.getLanguage(hlLang)) { try { htmlCode = hljs.highlight(src, { language: hlLang, ignoreIllegals: true }).value; env.hl = (env.hl || 0) + 1; } catch { /* plain */ } }
  // a wrapped line continues 4 columns right of its indent; a wrapped trailing comment continues under the comment text
  if (hlLang === 'python') htmlCode = htmlCode.replace(/\.<span class="hljs-(?:built_in|keyword|type)">(\w+)<\/span>/g, '.$1')
    .replace(/^(\s+)<span class="hljs-built_in">(\w+)<\/span>(?=:\s)/gm, '$1$2');
  const indents = src.split('\n').map(l => {
    const lead = (l.match(/^ */) || [''])[0].length, c = l.search(/\S\s{2,}(#|\/\/|--) /);
    return Math.min(90, c > 0 && c < 95 ? c + 1 + l.slice(c + 1).search(/\S/) - 2 : lead);
  });
  const longest = Math.max(...src.split('\n').map(l => l.length));
  const size = longest > 109 ? Math.max(6.3, 7.3 * 109 / longest).toFixed(2) : null;   // about 109 columns fit at 7.3 pt; 126 at 6.3 pt
  const raw = src.split('\n');
  // keep the first and last three non-blank lines with their neighbours; a blank line never starts a page; an opener never ends one
  const nb = raw.map((l, i) => l.trim() ? i : -1).filter(i => i >= 0);
  const headEnd = nb.length > 6 ? nb[2] : -1, tailStart = nb.length > 6 ? nb[nb.length - 3] : raw.length;
  const cls = i => {
    const l = raw[i] || '', c = [];
    if (!l.trim()) c.push('bl');
    if (i < headEnd) c.push('kh');
    if (i >= tailStart) c.push('kt');
    const opener = (/[:{(\[]\s*$/.test(l) && !/^\s*(#|\/\/)/.test(l)) || (/^(markdown|md)$/.test(hlLang || lang || '') && /^#{1,6} /.test(l));
    if (opener && i < tailStart - 1) c.push('op');
    return c.length ? ' ' + c.join(' ') : '';
  };
  const lines = splitHighlighted(htmlCode).map((l, i) => `<span class="ln${cls(i)}" style="--i:${indents[i] || 0}">${l || ' '}</span>`).join('');
  return `<pre class="code"${lang ? ` data-lang="${esc(lang)}"` : ''}${size ? ` style="font-size:${size}pt;line-height:${Math.round(size * 1.42 * 4 / 3)}px"` : ''}><code>${lines}</code></pre>\n`;
};
// keep short IDs such as MOD-1, AC-13, HOR-10 on one line; bind units, dates, standards and status tags with no-break spaces
const NB = ' ';
const MONTH = '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December)';
const bind = t => t
  .replace(/ — /g, `${NB}— `)                                                   // an em dash never starts a line
  .replace(/([≤≥~≈±]) (?=\d)/g, `$1${NB}`)
  .replace(/\b(USD|EUR|INR|GBP|Rs\.?|₹) (?=\d)/g, `$1${NB}`)
  .replace(new RegExp(`\\b(\\d{1,2}) (${MONTH})\\b`, 'g'), `$1${NB}$2`)
  .replace(new RegExp(`\\b(${MONTH}) (\\d{4})\\b`, 'g'), `$1${NB}$2`)
  .replace(/\b([Tt]urns?|[Ss]ections?|Part|[Ww]eeks?|[Ss]teps?|[Pp]hases?|[Cc]hapters?|[Tt]emplates?|Q) (\d+|[A-Z])\b/g, `$1${NB}$2`)
  .replace(/\b([A-Z]{2,}) (?=\d)/g, `$1${NB}`)                                  // EN 301 549, WCAG 2.1, SR 26-2
  .replace(/(\d) (?=\d{3}\b)/g, `$1${NB}`)
  .replace(/(\d) (?=A{1,3}\b)/g, `$1${NB}`)                                       // WCAG 2.1 AA
  .replace(/(\d) (?=(?:tok\/s|tokens?\/s|points?|pp|s|ms|h|min|GB|TB|MB|KB|B|GiB|tokens?|weeks?|days?|hours?|minutes?|seconds?|months?|years?|pages?|rows?|users?|calls?|business)\b)/g, `$1${NB}`)
  .replace(/\((?:[A-Z]{2,} )+[A-Z]{2,}\)/g, m => m.replace(/ /g, NB))             // (NEEDS NUANCE)
  .replace(/\b(Arts?\.|Reg\.|paras?|ss?\.|Nos?\.|Annex|Rule|Recital|Sec\.) (?=\(?[\dIVX(])/g, `$1${NB}`)  // Art. 50(2), Reg. (EU), para 218
  .replace(/ v\. /g, `${NB}v.${NB}`)                                               // NYT v. OpenAI
  .replace(/ ([=×]) (?=\d)/g, `${NB}$1${NB}`)                                     // n = 300, 3 × 4
  .replace(/ → /g, ` →${NB}`)                                                      // an arrow stays with what it points to
  .replace(/ \+ /g, ` +${NB}`)                                                     // Security + Platform
  .replace(/(^|[\s(])([A-Za-zκδσμρτ]{1,3}|\d+) ([≤≥])(?=[ \u00a0]\d)/g, `$1$2${NB}$3`)     // (κ ≥ 0.7) stays together; never after ; , /
  .replace(/([≤≥~≈±]) /g, `$1${NB}`)                                              // ≤ USD 50
  .replace(/(&gt;|&lt;|&gt;=|&lt;=) (?=[\d₹$]|USD|INR|EUR)/g, `$1${NB}`)                  // CI > 0 (text is already escaped here)
  .replace(/ · /g, `${NB}· `)                                                      // a separator dot never starts a line
  .replace(/· (\d+[a-z]?) /g, `· $1${NB}`)                                              // turn number stays with its title
  .replace(/\b([A-Z][A-Za-z]{1,12}|arXiv) (?=\d)/g, `$1${NB}`)                  // Llama 4, OAuth 2.1, arXiv 2411.12240
  .replace(/\b(US|EU|UK) (?=[A-Z]{2,}\b)/g, `$1${NB}`)                          // US ADA, EU EAA
  .replace(/\(([A-Z]{2,})\) (?=\d)/g, `($1)${NB}`)                             // Reg. (EU) 2025/301
  .replace(/\b((?:[A-Z]\.){2,}) (?=\d)/g, `$1${NB}`)                           // G.S.R. 846(E)
  .replace(/, (\d{1,4}\))/g, `,${NB}$1`)                                        // (Turns 79, 84): the last number keeps company
  .replace(/ ×(?=\d)/g, `${NB}×`)                                                // FAIL ×3
  .replace(/(\d%?) (?=[A-Z]{2}\b)/g, `$1${NB}`)                                  // 60 HI, 30% TE
  .replace(/\b(C\(\d{4}\)) (?=\d)/g, `$1${NB}`)                                 // C(2026) 5252
  .replace(/(\d{1,2}:\d{2}) (?=[A-Z]{2,4}(?:\/[A-Z]{2,4})?\b)/g, `$1${NB}`)       // 22:00 ET/PT
  .replace(/\((\d[\d.,]*) /g, `($1${NB}`)                                        // (8 ECI points)
  .replace(/\b(p\d{2,3}) (?=\d)/g, `$1${NB}`)                                   // p95 5.8 s
  .replace(/\(\+ /g, `(+${NB}`)                                                  // (+ provider
  .replace(/(^|[\s(])(\d{2}|P\d{2})( |\u00a0)· /g, `$1$2${NB}·${NB}`)           // 04 · Future topics
  .replace(/ \/ /g, `${NB}/ `)                                                    // a spaced slash never starts a line
  .replace(/ &amp; /g, `${NB}&amp; `)                                            // Hellman & Friedman: '&' never starts a line
  .replace(/ = (?=[A-Za-z])/g, `${NB}=${NB}`)                                     // CERT-In = Indian …
  .replace(/\b(\d{5}) (?=\d{5}\b)/g, `$1${NB}`)                                   // 98490 12345
  .replace(/(\d×) (?=[A-Z0-9])/g, `$1${NB}`)                                     // 2× L40S
  .replace(/\(([^\s()]{1,2}) /g, `($1${NB}`)                                      // (κ per language)
  .replace(/ − (?=\S{1,3}(?:\s|$|[).,;:]))/g, `${NB}−${NB}`)                     // baseline − δ
  .replace(/(\w) (§\d)/g, `$1${NB}$2`)                                            // brief §5
  .replace(/\(([A-Za-z]{1,8}) ([A-Za-z§\d]{1,8})\)/g, `($1${NB}$2)`)              // (real phase), (quote API)
  .replace(/(^|[\s(;,:])(\d{1,3}(?:–\d{1,3})?) (?=[A-Za-z])/g, `$1$2${NB}`)       // a count stays with what it counts
  .replace(/(\w) ([A-Z]{2,3})$/g, `$1${NB}$2`);                                    // … Almarosa IT (a short final acronym)
md.renderer.rules.text = (tokens, idx) => bind(esc(tokens[idx].content))
  .replace(/\b(?:CVE|GHSA|FIN|CWE|RFC|ISO|IEC)(?:-[0-9A-Za-z]{2,10}){1,4}\b|\b\d{4}-\d{2}-\d{2}(?:-[a-z]+)?\b|\b[A-Z][A-Za-z]{0,7}-\d{1,4}[A-Za-z]{0,2}\b|\b\d+(?:\.\d+)?-[A-Za-z]{1,10}\b|(?<![\w-])[A-Za-z]{1,8}-(?:[A-Z]{2,6}|[A-Z][a-z]?)\b(?!-)|(?<![\w-])(?:re|co|de|un|non|pre|sub)-[a-z]{3,10}\b(?!-)|\b\d+\([0-9a-z]+\)[–-]\([0-9a-z]+\)|\b\d{1,2}:\d{2}[–-]\d{1,2}:\d{2}\b|\b[A-Z][A-Za-z]{1,10}–[A-Z][A-Za-z]{1,10}\b|(?<![\w-])[a-z]{2,4}-[a-z]{2,4}\b(?!-)|\(?\d[\d.,]*\s?[–-]\s?\d[\d.,]*%?\)?[;,.:]?|\b(?![A-Za-z0-9.-]{21})(?=[A-Za-z0-9.-]*\d)[A-Za-z][A-Za-z0-9.]*(?:-[A-Za-z0-9.]+){1,4}\b/g, m => `<span class="nw">${m}</span>`)
  .replace(/\b(\d+|pass|k)\^(\d+|[a-z])\b/g, '$1<sup>$2</sup>')
  .replace(/\)\^(\d+|[a-z])\b/g, ')<sup>$1</sup>');

const ids = new Set(), internalLinks = [], problems = [...coverage];
let escapedPipes = 0, labelBreaks = 0, metaHeadings = 0, droppedRules = 0;
const inlineText = tok => (tok.children || []).map(c => (c.type === 'text' || c.type === 'code_inline') ? c.content : '').join('');

function resolveHref(href, file) {
  if (/^[a-z][a-z0-9+.-]*:/i.test(href)) return href;               // external
  const [p, anchor] = href.split('#');
  if (!p) return `#${fileId(file)}--${anchor}`;                        // same-file anchor
  let target = path.posix.normalize(path.posix.join(path.posix.dirname(file), p)).replace(/\/$/, '');
  if (byPath.has(target)) return anchor ? `#${byPath.get(target)}--${anchor}` : `#${byPath.get(target)}`;
  if (byPath.has(`${target}/README.md`)) return `#${byPath.get(`${target}/README.md`)}`;
  if (dirTarget[target]) return `#${dirTarget[target]}`;
  const isDir = fs.existsSync(path.join(REPO, target)) && fs.statSync(path.join(REPO, target)).isDirectory();
  if (!fs.existsSync(path.join(REPO, target))) problems.push(`missing link target ${href} in ${file}`);
  return `${GH}/${isDir ? 'tree' : 'blob'}/${COMMIT}/${target}${anchor ? '#' + anchor : ''}`;
}

function renderFile(file) {
  const raw = fs.readFileSync(path.join(REPO, file), 'utf8');
  // GFM splits table cells on '|' even inside code spans; escape those so the row keeps all its text
  let inFence = false;
  const out = [];
  raw.split('\n').forEach(l => out.push(((l) => {
    if (/^\s*```/.test(l)) { inFence = !inFence; return l; }
    if (inFence) return l;
    if (!/^\s*\|/.test(l)) {
      const prev = out.length ? out[out.length - 1] : '';
      if (/^(\*\*[^*\s][^*]*[.:]\*\*|\*[A-Z][^*]*:\*)/.test(l) && prev.trim() !== '' && !/^\s*\|/.test(prev)) { out.push(''); labelBreaks++; }  // a label is bold text ending in . or :
      return l;
    }
    return l.replace(/(`+)(.+?)\1/g, (m, tick, body) => { const e = body.replace(/(?<!\\)\|/g, '\\|'); if (e !== body) escapedPipes++; return tick + e + tick; });
  })(l)));
  const src = out.join('\n');
  const env = { file };
  const tokens = md.parse(src, env);
  const slugger = new GithubSlugger();
  let title = null;
  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i];
    if (t.type === 'heading_open') {
      const text = inlineText(tokens[i + 1]);
      const id = `${fileId(file)}--${slugger.slug(text)}`;
      t.attrSet('id', id); ids.add(id);
      const lvl = Math.min(6, Number(t.tag[1]) + 1);                 // file h1 -> h2 under the part's h1
      t.attrSet('class', `h${t.tag[1]}`);
      t.tag = `h${lvl}`; tokens[i + 2].tag = `h${lvl}`;
      const kids = tokens[i + 1].children || [];
      // "Title — P2 · MISSING · …" or "Title — **P2** · MISSING · …"
      const k = kids.findIndex((c, j) => c.type === 'text' && (/\s—\s+(?=(?:P\d|Watch)\b)/.test(c.content) ||
        (/\s—\s*$/.test(c.content) && kids[j + 1]?.type === 'strong_open' && /^(?:P\d|Watch)\b/.test(kids[j + 2]?.content || ''))));
      if (k >= 0) {
        const parts = kids[k].content.split(/\s—\s*(?=(?:P\d|Watch)\b|$)/);
        const T = tokens[i + 1].children[0].constructor;
        const mk = (type, content) => { const x = new T(type, '', 0); x.content = content; return x; };
        kids.splice(k, 1, mk('text', parts[0].trimEnd()), mk('html_inline', '<span class="h-meta">'), ...(parts[1] ? [mk('text', parts[1])] : []));
        kids.push(mk('html_inline', '</span>')); metaHeadings++;
      }
      if (!title && t.markup === '#') title = text;
    }
    if (t.type === 'inline') for (const c of t.children || []) if (c.type === 'link_open') {
      const href = c.attrGet('href'); const out = resolveHref(href, file);
      c.attrSet('href', out);
      if (out.startsWith('#')) internalLinks.push({ file, href, out });
      else if (out.startsWith(GH)) c.attrSet('class', 'repo');
    }
  }
  if (!title) title = path.basename(file);
  if (TITLE_OVERRIDE[file]) title = TITLE_OVERRIDE[file];
  ids.add(fileId(file));
  const html = md.renderer.render(tokens, md.options, env).replace(/<hr>\s*(?=<h[1-6][ >]|$)/g, () => { droppedRules++; return ''; })
    .replace(/<li>(<p>)?\[([ xX])\] /g, (m, p, x) => `<li class="task">${p || ''}<span class="tbox${x.trim() ? ' done' : ''}"></span>`);
  return { title, html, mermaid: env.mermaid || 0, hl: env.hl || 0 };
}

// ---- assemble ---------------------------------------------------------------
const pageNo = key => tocPages ? String(tocPages[key] ?? '?') : '888';
let body = '', toc = '', chapterIdx = 0, mermaidCount = 0, highlighted = 0;
const chapters = [];
PARTS.forEach((part, pi) => {
  ids.add(part.id);
  const n = pi + 1;
  toc += `<div class="toc-group"><div class="toc-part"><a href="#${part.id}"><span class="t">Part ${n} · ${esc(part.title)}</span><span class="dots"></span><span class="n">${pageNo(part.id)}</span></a></div>\n`;
  body += `<section class="part" id="${part.id}"><div class="part-num">Part</div><div class="part-big">${String(n).padStart(2, '0')}</div><h1 class="part-title">${esc(part.title)}</h1><p class="part-blurb">${esc(part.blurb)}</p><ol class="part-list">`;
  const rendered = part.files.map(f => ({ f, ...renderFile(f) }));
  for (const r of rendered) body += `<li><a href="#${fileId(r.f)}"><span class="pl-t">${esc(r.title)}</span></a><span class="pl-dots"></span><span class="pl-n">${pageNo(fileId(r.f))}</span></li>`;
  body += `</ol></section>\n`;
  for (const r of rendered) {
    chapterIdx++; mermaidCount += r.mermaid; highlighted += r.hl;
    const id = fileId(r.f);
    chapters.push({ id, title: r.title, file: r.f });
    toc += `<div class="toc-ch"><a href="#${id}"><span class="t">${esc(r.title)}</span><span class="dots"></span><span class="n">${pageNo(id)}</span></a></div>\n`;
    const cut = r.html.indexOf('</h2>') + 5;
    const head = cut > 4 && r.html.trimStart().startsWith('<h2') ? r.html.slice(0, cut) : '';
    body += `<section class="chapter${TIGHT[id] ? ' tight' : ''}${TIGHT[id] >= 2 ? ' tight2' : ''}" id="${id}"><header class="chap-head"><div class="chap-kicker">Part ${n} · ${esc(part.title)}${KICKER_FILE[r.f] ? ' · ' + KICKER_FILE[r.f] : ''}</div>${head}<div class="chap-src">${esc(r.f)}</div></header>\n${head ? r.html.slice(cut) : r.html}</section>\n`;
  }
  toc += `</div>\n`;
});

// internal link check (after all ids are known)
const missingAnchors = internalLinks.filter(l => !ids.has(l.out.slice(1)));
for (const l of missingAnchors) problems.push(`unresolved anchor ${l.href} in ${l.file} -> ${l.out}`);
// fall back to the target chapter when a heading anchor does not exist
body = body.replace(/href="#(f-[a-z0-9-]+?)--([^"]+)"/g, (m, fid, a) => ids.has(`${fid}--${a}`) ? m : `href="#${fid}"`);

const css = fs.readFileSync(path.join(HERE, 'style.css'), 'utf8');
const FS = `${HERE_URL}/node_modules/@fontsource`;
const FONT_LINKS = ['source-serif-4/400.css', 'source-serif-4/400-italic.css',
  'source-serif-4/600.css', 'source-serif-4/600-italic.css', 'jetbrains-mono/400.css', 'noto-sans-devanagari/400.css',
  'noto-sans-devanagari/600.css'].map(f => `<link rel="stylesheet" href="${FS}/${f}">`).join('\n');
// Inter: the full release (arrows, ≤ ≥, ₹, Greek), with the tailed l (cv05) made the default so l and I never look alike
const FACE = (fam, file, w, style, range) => `@font-face { font-family: '${fam}'; font-style: ${style}; font-weight: ${w}; font-display: block; src: url('${HERE_URL}/fonts/${file}') format('truetype');${range ? ` unicode-range: ${range};` : ''} }`;
// symbols the web subsets lack: arrows and maths from the full Source Serif 4 and JetBrains Mono; stars and ↗ in serif text from Inter;
// ✓ and ✗ from DejaVu Sans everywhere, so the ballot shapes match in text, tables and keys
const SERIF_SYM = 'U+2190-2193, U+2212, U+2248, U+2264-2265';
const INTER_FACES = `<style>${[
  ...[400, 600, 700].map(w => FACE('Inter', `Inter-${w}.ttf`, w, 'normal')),
  FACE('Source Serif 4', 'SourceSerif4-Regular.ttf', 400, 'normal', SERIF_SYM), FACE('Source Serif 4', 'SourceSerif4-It.ttf', 400, 'italic', SERIF_SYM),
  FACE('Source Serif 4', 'SourceSerif4-Semibold.ttf', 600, 'normal', SERIF_SYM), FACE('Source Serif 4', 'SourceSerif4-SemiboldIt.ttf', 600, 'italic', SERIF_SYM),
  FACE('JetBrains Mono', 'JetBrainsMono-Regular.ttf', 400, 'normal', 'U+2190-21FF, U+2200-22FF'),
  FACE('Serif Sym', 'Inter-400.ttf', 400, 'normal', 'U+2197, U+2605-2606'), FACE('Serif Sym', 'Inter-600.ttf', 600, 'normal', 'U+2197, U+2605-2606'),
  FACE('Marks', 'DejaVuSans.ttf', 400, 'normal', 'U+2713-2718'),
].join('\n')}</style>`;
const front = fs.readFileSync(path.join(HERE, 'front.html'), 'utf8');
const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>LLM Training Flow Vol. 2 — Curriculum Review, Gap Register and FDE Projects</title>
${FONT_LINKS}
${INTER_FACES}
<style>${css}</style></head><body>
${front}
<section class="toc" id="contents"><h1 class="toc-title">Contents</h1>${toc}</section>
${body}
<script src="${HERE_URL}/node_modules/mermaid/dist/mermaid.min.js"></script>
<script type="module">import elk from "${HERE_URL}/vendor/elk/mermaid-layout-elk.esm.min.mjs"; mermaid.registerLayoutLoaders(elk); window.__elk = true;</script>
</body></html>`;
fs.writeFileSync(path.join(OUT, `book-pass${pass}.html`), html);

// ---- render ------------------------------------------------------------------
const browser = await chromium.launch({ ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : { channel: 'chromium' }), args: ['--allow-file-access-from-files'] });   // no fallback: the headless shell lays text out differently
const browserVersion = browser.version();
const page = await browser.newPage({ viewport: { width: 665, height: 1100 } });
await page.emulateMedia({ media: 'print' });
await page.goto(pathToFileURL(path.join(OUT, `book-pass${pass}.html`)).href, { waitUntil: 'load' });
const BREAKS = fs.existsSync(path.join(OUT, 'breaks.json')) ? JSON.parse(fs.readFileSync(path.join(OUT, 'breaks.json'), 'utf8')) : [];
await page.evaluate(b => { window.__breaks = b; }, BREAKS);
const diag = await page.evaluate(async () => {
  const errors = [], diagrams = [];
  await document.fonts.ready;
  for (let i = 0; i < 50 && !window.__elk; i++) await new Promise(r => setTimeout(r, 100));
  if (!window.__elk) errors.push('the ELK layout engine did not load (run prepare_elk.mjs)');
  mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'strict',
    themeVariables: { fontFamily: 'Inter, DejaVu Sans, sans-serif', fontSize: '15px' },
    flowchart: { htmlLabels: true, useMaxWidth: true, nodeSpacing: 28, rankSpacing: 36, padding: 9, diagramPadding: 6, wrappingWidth: 170 },
    sequence: { useMaxWidth: true } });
  const vb = svg => { const m = svg.match(/viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"/); return m ? { w: +m[1], h: +m[2] } : null; };
  // placement boxes in CSS px: inline in the portrait text column, a full portrait page, or a landscape page
  const BOXES = { inline: [665, 830], fullpage: [710, 945], landscape: [994, 560] };
  // a subgraph title wider than its box is wrapped onto more lines, measured on the rendered SVG, then the diagram is re-rendered
  const probe = document.createElement('div'); probe.style.cssText = 'position:absolute;left:-10000px;top:0;width:4000px'; probe.className = 'mmd';
  document.body.appendChild(probe);
  const renderFitted = async (id, c) => {
    let src = c, out = await mermaid.render(id, src), wrapped = 0;
    for (let round = 0; round < 3; round++) {
      probe.innerHTML = out.svg;
      let changed = false;
      // Mermaid widens a box to its title after layout, around its centre: such a box can run into a neighbour
      const boxes = [...probe.querySelectorAll('g.cluster > rect, g.node')].map(e => ({ e, r: e.getBoundingClientRect() }));
      const inside = (a, b) => a.left >= b.left - 1 && a.right <= b.right + 1 && a.top >= b.top - 1 && a.bottom <= b.bottom + 1;
      const hits = (a, b) => a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 1 && b.top < a.bottom - 1;
      for (const g of probe.querySelectorAll('g.cluster')) {
        const rect = g.querySelector(':scope > rect'), fo = g.querySelector('g.cluster-label foreignObject');
        if (!rect || !fo) continue;
        const r = rect.getBoundingClientRect(), lw = fo.getBoundingClientRect().width;
        if (lw < r.width - 28) continue;                                     // the title has room inside its box: fine
        const sid = g.id.slice(id.length + 1);
        const re = new RegExp('^(\\s*subgraph\\s+' + sid.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\s*\\[\\s*)"([^"]+)"', 'm');
        const m = src.match(re); if (!m) continue;
        const title = m[2].replace(/<br\/?>/g, ' '), longest = Math.max(...m[2].split(/<br\/?>/).map(x => x.length));
        const max = Math.max(10, Math.min(Math.ceil(longest * 0.85), Math.floor(title.length * (r.width - 28) / Math.max(lw, 1))));
        const fill = (t, lim) => { const out = []; let cur = ''; for (const w of t.split(' ')) { if (cur && (cur + ' ' + w).length > lim) { out.push(cur); cur = w; } else cur = cur ? cur + ' ' + w : w; } out.push(cur); return out; };
        const greedy = t => { const n = fill(t, max).length; for (let lim = Math.ceil(t.length / n); lim < max; lim++) { const o = fill(t, lim); if (o.length <= n) return o; } return fill(t, max); };   // balanced lines
        const ci = title.indexOf(': '), pi = title.indexOf(' ('), di = title.indexOf(' · ');
        const lines = ci > 0 && ci + 1 <= max ? [title.slice(0, ci + 1), ...greedy(title.slice(ci + 2))]
          : pi > 0 && pi <= max && /\)\s*$/.test(title) ? [title.slice(0, pi), ...greedy(title.slice(pi + 1))]
          : di > 0 && di + 2 <= max && title.length - di - 3 <= max ? [title.slice(0, di + 2), title.slice(di + 3)] : greedy(title);
        const next = lines.join('<br/>');
        if (lines.length < 2 || next === m[2]) continue;
        src = src.replace(re, `$1"${next}"`); changed = true; wrapped++;
      }
      if (!changed) break;
      out = await mermaid.render(id + 'w' + round, src);
    }
    probe.innerHTML = '';
    return { svg: out.svg, wrapped };
  };
  let n = 0;
  for (const el of [...document.querySelectorAll('pre.mermaid-src')]) {
    // subgraph-heavy flowcharts: ELK routes edges around boxes and sizes boxes to their titles; dagre overlaps them
    // hyphenated words inside labels never split across label lines: use the non-breaking hyphen
    const raw = el.textContent.replace(/(?<!\()\(\("?([^"()]+?)"?\)\)(?!\))/g, (m, t) => `(("${t.split(/<br\s*\/?>/).map(x => `#nbsp;#nbsp;${x}#nbsp;#nbsp;`).join('<br/>')}"))`).replace(/"[^"\n]*"|\|[^|\n]*\|/g, q => q.replace(/(\w)-(?=\w)/g, '$1\u2011'));
    const useElk = !!window.__elk && /^\s*subgraph\b/m.test(raw) && /^\s*(flowchart|graph)\b/m.test(raw);
    // node labels the author already broke with <br/>: widen the wrapping width so Mermaid does not re-wrap those lines
    const ctx = (window.__mctx ||= document.createElement('canvas').getContext('2d')); ctx.font = '15px Inter';
    let widest = 0;
    for (const line of raw.split('\n')) {
      if (/^\s*subgraph\b/.test(line)) continue;
      for (const m of line.matchAll(/"([^"]*<br\s*\/?>[^"]*)"|[\[({]([^"\[\](){}]*<br\s*\/?>[^"\[\](){}]*)[\])}]/g))
        for (const seg of (m[1] || m[2]).split(/<br\s*\/?>/)) widest = Math.max(widest, ctx.measureText(seg.replace(/<[^>]+>/g, '').trim()).width);
    }
    const ww = widest + 8 > 170 ? Math.min(400, Math.ceil(widest + 8)) : 0;
    const conf = (useElk ? '  layout: elk\n' : '') + (ww ? `  flowchart:\n    wrappingWidth: ${ww}\n` : '');
    const src = conf && /^\s*(flowchart|graph)\b/m.test(raw) ? '---\nconfig:\n' + conf + '---\n' + raw : raw;
    const cands = [['as written', src]];
    if (/^\s*(flowchart|graph)\s+(LR|RL)\b/m.test(src)) cands.push(['top-to-bottom', src.replace(/^(\s*(?:flowchart|graph))\s+(LR|RL)\b/m, '$1 TB')]);
    const opts = [];
    for (const [orient, c] of cands) {
      try {
        const { svg, wrapped } = await renderFitted('mmd' + (n++), c); const d = vb(svg); if (!d) continue;
        for (const [box, [W, H]] of Object.entries(BOXES)) opts.push({ svg, d, orient, box, wrapped, s: Math.min(0.8, W / d.w, H / d.h) });
      } catch (e) { errors.push(String(e).slice(0, 200)); }
    }
    if (!opts.length) continue;
    opts.sort((a, b) => b.s - a.s);
    const bestAny = opts[0], inline = opts.filter(o => o.box === 'inline')[0];
    // stay inline when labels are already comfortable (>= 7 pt) or within 5% of the best alternative
    const pick = (12 * inline.s >= 7 || inline.s >= bestAny.s * 0.95) ? inline : bestAny;
    const wrap = document.createElement('div'); wrap.className = 'mmd'; wrap.innerHTML = pick.svg;
    const holder = el.closest('.diagram'); el.replaceWith(wrap);
    if (pick.box !== 'inline') {
      holder.classList.add(pick.box === 'landscape' ? 'wide' : 'fullpage');
      const ch = holder.closest('section').querySelector('h2');
      const chName = ch ? ch.textContent.split(/\s[·:]\s/)[0].trim() : '';
      const prev = holder.previousElementSibling;
      if (prev && /^H[1-6]$/.test(prev.tagName)) {
        // the heading introduces only this diagram: move it onto the diagram's page so it is not stranded
        holder.prepend(prev); prev.classList.add('with-diagram');
        const cap = document.createElement('div'); cap.className = 'figcap'; cap.textContent = chName; holder.prepend(cap);
      } else {
        let h = prev; while (h && !/^H[1-6]$/.test(h.tagName)) h = h.previousElementSibling;
        const cap = document.createElement('div'); cap.className = 'figcap';
        cap.textContent = chName;
        const ft = document.createElement('div'); ft.className = 'h2 with-diagram fig-h'; ft.textContent = h ? h.textContent.trim() : 'Diagram';
        holder.prepend(ft); holder.prepend(cap);
      }
    }
    const svgEl = wrap.querySelector('svg');
    // draw subgraph titles last, on the box colour, so neither a neighbouring box nor an edge can hide them
    let raised = 0;
    const top = svgEl.querySelector('g.root') || svgEl;
    for (const lab of [...svgEl.querySelectorAll('g.cluster > g.cluster-label')]) {
      const rect = lab.parentElement.querySelector(':scope > rect');
      const fill = rect ? getComputedStyle(rect).fill : '#fff';
      const m = top.getCTM().inverse().multiply(lab.getCTM());
      top.appendChild(lab);
      lab.setAttribute('transform', `matrix(${m.a} ${m.b} ${m.c} ${m.d} ${m.e} ${m.f})`);
      for (const d of lab.querySelectorAll('foreignObject > div')) { d.style.background = fill; d.style.boxShadow = `3px 0 0 ${fill}, -3px 0 0 ${fill}`; }
      raised++;
    }
    svgEl.setAttribute('width', Math.round(pick.d.w * pick.s)); svgEl.setAttribute('height', Math.round(pick.d.h * pick.s));
    svgEl.style.maxWidth = '100%'; svgEl.style.height = 'auto';
    diagrams.push({ elk: useElk, wrapped: pick.wrapped, raised, chapter: wrap.closest('section')?.id, orient: pick.orient, box: pick.box, labelPt: +(15 * 0.75 * pick.s).toFixed(1), w: Math.round(pick.d.w), h: Math.round(pick.d.h) });
  }
  probe.remove();
  // label paragraphs ("CI gates:", "**Interview questions.**") stay with what follows
  let leads = 0;
  for (const p of document.querySelectorAll('.chapter p')) {
    const kids = [...p.childNodes].filter(x => !(x.nodeType === 3 && !x.textContent.trim()));
    const t = p.textContent.trim();
    if ((kids.length === 1 && kids[0].nodeName === 'STRONG') || (t.length < 160 && /:$/.test(t))) { p.classList.add('lead'); leads++; }
  }
  // blocks of 2-5 lines cannot split without breaking orphans/widows 3, and Chromium then leaves a widow: move them whole
  const lineCount = el => {
    const r = document.createRange(); r.selectNodeContents(el);
    const cs = [...r.getClientRects()].filter(x => x.width > 0 && x.height > 0).map(x => (x.top + x.bottom) / 2).sort((a, b) => a - b);
    let n = 0, last = -1e9; for (const c of cs) if (c - last > 7) { n++; last = c; }
    return n;
  };
  for (const li of document.querySelectorAll('.chapter li')) {
    const sub = [...li.children].find(k => /^(UL|OL)$/.test(k.tagName)); if (!sub || li.querySelector(':scope > p')) continue;
    const lead = document.createElement('span'); lead.className = 'li-lead';
    while (li.firstChild && li.firstChild !== sub) lead.append(li.firstChild);
    if (lead.textContent.trim()) li.insertBefore(lead, sub); else sub.before(...lead.childNodes);
  }
  let kept = 0, afterHead = 0;
  for (const el of document.querySelectorAll('.chapter p, .chapter li, .chapter .li-lead')) {
    if (el.closest('td, th, blockquote, .diagram')) continue;
    if (el.querySelector('ul, ol, p, pre, table, blockquote, div')) continue;
    const n = lineCount(el);
    if (n >= 2 && n <= 5) { el.classList.add('keep'); kept++; }
    if (el.tagName === 'LI' && n <= 2) el.classList.add('short');
    const prev = el.previousElementSibling;
    const next = el.nextElementSibling;
    const introduces = next && (next.matches('pre.code, table, .diagram:not(.wide):not(.fullpage)') || (next.matches('ul, ol') && /:$/.test(el.textContent.trim())));
    if (el.tagName === 'P' && !el.classList.contains('lead') && next && ((n <= 2 && prev && /^H[1-6]$/.test(prev.tagName)) || (n <= 4 && introduces))) { el.classList.add('lead'); afterHead++; }
  }
  // detector input: first and last line of every multi-line block, as laid out at print width
  const blockLines = [];
  for (const el of document.querySelectorAll('.chapter p, .chapter li')) {
    if (el.closest('td, th, .diagram') || el.querySelector('ul, ol, p, pre, table, blockquote, div')) continue;
    const words = [], w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let tn;
    while ((tn = w.nextNode())) { const re = /\S+/g; let m; while ((m = re.exec(tn.data))) { const r = document.createRange(); r.setStart(tn, m.index); r.setEnd(tn, m.index + m[0].length); const b = [...r.getClientRects()].filter(x => x.width > 0).pop(); if (b) words.push([(b.top + b.bottom) / 2, m[0]]); } }
    const lines = []; for (const [b, t] of words) { if (!lines.length || Math.abs(lines[lines.length - 1][0] - b) > 7) lines.push([b, t]); else lines[lines.length - 1][1] += t; }
    if (lines.length >= 2) blockLines.push({ n: lines.length, first: lines[0][1], last: lines[lines.length - 1][1], keep: el.classList.contains('keep') });
  }
  let nwCode = 0;
  for (const c of document.querySelectorAll('code')) {
    if (c.closest('pre')) continue;
    const inCell = !!c.closest('td, th'), len = c.textContent.length;
    const alone = inCell && c.parentElement.matches('td, th') && c.parentElement.textContent.trim() === c.textContent.trim();
    if (len <= (inCell ? (alone ? 26 : 22) : 32) && !/\s/.test(c.textContent.trim()) || len <= (inCell ? 22 : 32)) { c.classList.add('nwc'); nwCode++; }
  }
  for (const pre of document.querySelectorAll('pre.code')) if (pre.querySelectorAll('.ln').length <= 10) pre.classList.add('keep');
  // forced page breaks for headings or lead-ins that an earlier pass left stranded at a page foot
  let forced = 0;
  const want = new Set((window.__breaks || []).map(t => t.replace(/\s+/g, ' ').trim()));
  if (want.size) for (const el of document.querySelectorAll('.chapter h2, .chapter h3, .chapter h4, .chapter h5, .chapter h6, .chapter p.lead')) {
    if (!want.has(el.textContent.replace(/\s+/g, ' ').trim())) continue;
    let t = el;
    for (let k = 0; k < 3; k++) { const pv = t.previousElementSibling; if (pv && (/^H[1-6]$/.test(pv.tagName) || pv.matches('p.lead'))) t = pv; else break; }
    if (!t.classList.contains('pbb')) { t.classList.add('pbb'); forced++; }
  }
  // a short bold label ("Real engagement:") never breaks inside
  for (const b of document.querySelectorAll('.chapter strong')) if (b.textContent.length <= 28 && /[:.]$/.test(b.textContent.trim())) {
    b.classList.add('nwl'); const nx = b.nextSibling;
    if (nx && nx.nodeType === 3 && /^ /.test(nx.data)) nx.data = '\u00a0' + nx.data.slice(1);
  }
  // fill-in tables: a column whose body cells are all empty keeps room to write
  for (const tb of document.querySelectorAll('.chapter table')) {
    const heads = [...tb.querySelectorAll('thead th')], rows = [...tb.querySelectorAll('tbody tr')];
    if (!rows.length) continue;
    heads.forEach((th, i) => { if (rows.every(r => !(r.children[i]?.textContent || '').trim())) th.classList.add('blank-col'); });
  }
  let numCells = 0;
  for (const c of document.querySelectorAll('td')) if (/^[~≈≤≥<>+±]?\s?[$€£₹]?\s?\d[\d.,]*\s?(%|×|x|k|K|M|B|ms|s|h|GB|TB|MB)?$/.test(c.textContent.trim())) { c.classList.add('num'); numCells++; }
  // headings wrap between words only: keep hyphenated compounds whole (balanced wrapping would otherwise split them)
  let headNw = 0;
  for (const h of document.querySelectorAll('h1, h2, h3, h4, h5, h6, .part-list .pl-t, .toc .t')) {
    const w = document.createTreeWalker(h, NodeFilter.SHOW_TEXT); const nodes = []; let tn;
    while ((tn = w.nextNode())) if (!tn.parentElement.closest('.nw, code') && /[\w’']-[\w’']/.test(tn.data)) nodes.push(tn);
    for (const node of nodes) {
      const frag = document.createDocumentFragment(); let last = 0; const re = /[\w’'.]+(?:-[\w’'.]+)+/g; let m;
      while ((m = re.exec(node.data))) {
        frag.append(node.data.slice(last, m.index)); const sp = document.createElement('span'); sp.className = 'nw'; sp.textContent = m[0]; frag.append(sp); last = m.index + m[0].length; headNw++;
      }
      frag.append(node.data.slice(last)); node.replaceWith(frag);
    }
  }
  // headings: short capitalised names (Claude Agent SDK, Microsoft Agent 365, US ADA Title II) stay on one line
  for (const h of document.querySelectorAll('.chapter h1, .chapter h2, .chapter h3, .chapter h4')) {
    const w = document.createTreeWalker(h, NodeFilter.SHOW_TEXT); const nodes = []; let tn;
    while ((tn = w.nextNode())) if (!tn.parentElement.closest('.nw, code, .h-meta')) nodes.push(tn);
    for (const node of nodes) {
      node.data = node.data.replace(/([A-Za-z]) ([A-Z]{2,4})\b/g, '$1\u00a0$2').replace(/(\S) \(([A-Z]{2,6})\)/g, '$1\u00a0($2)');
      const re = /\b[A-Z][\w.]*(?:[  ](?:[A-Z][\w.]*|\d[\w.]*)){1,3}\b/g; let m, last = 0; const frag = document.createDocumentFragment(); let hit = false;
      while ((m = re.exec(node.data))) {
        if (m[0].length > 24) continue;
        frag.append(node.data.slice(last, m.index)); const sp = document.createElement('span'); sp.className = 'nw'; sp.textContent = m[0]; frag.append(sp); last = m.index + m[0].length; hit = true;
      }
      if (hit) { frag.append(node.data.slice(last)); node.replaceWith(frag); }
    }
  }
  // headings that wrap: break after the colon, or before a closing parenthetical, when that costs no extra line
  let headBr = 0;
  for (const h of document.querySelectorAll('.chapter h1, .chapter h2, .chapter h3, .chapter h4')) {
    const before = lineCount(h); if (before < 2) continue;
    const cands = [], meta = h.querySelector('.h-meta'), full = h.textContent.slice(0, meta ? h.textContent.indexOf(meta.textContent) : undefined);
    const offset = (n, k) => { const r = document.createRange(); r.setStart(h, 0); r.setEnd(n, k); return r.toString().length; };
    const title = h.matches('.h1');
    const w = document.createTreeWalker(h, NodeFilter.SHOW_TEXT); let tn;
    while ((tn = w.nextNode())) {
      if (tn.parentNode !== h) continue;
      const d = tn.data.indexOf('· ');                                                  // 'P15 Starter Kit ·' / 'Distilled …'
      if (title && d >= 0 && offset(tn, d) >= 15) cands.push([tn, d + 2, 0]);
      const i = tn.data.indexOf(': ');                                                  // a colon after a label of 15+ characters
      if (i >= 0 && offset(tn, i) >= 15) cands.push([tn, i + 2, 1]);
      const j = tn.data.lastIndexOf(' (');                                              // only a parenthetical that closes the heading
      if (j >= 0) { const tail = full.slice(offset(tn, j + 1)); if (/^\([^()]*\)\s*$/.test(tail) && !/^\([A-Z]{2,6}\)/.test(tail)) cands.push([tn, j + 1, 2]); }
    }
    cands.sort((a, b) => a[2] - b[2]);
    for (const [node, at] of cands) {
      if (!node.parentNode || at >= node.data.length) continue;
      const rest = node.splitText(at), seg = document.createElement('span'); seg.className = 'hseg';
      h.insertBefore(seg, rest);
      for (let x = rest; x && !(x.nodeType === 1 && x.classList.contains('h-meta'));) { const nx = x.nextSibling; seg.appendChild(x); x = nx; }
      if (lineCount(h) <= before) { headBr++; break; }
      while (seg.firstChild) h.insertBefore(seg.firstChild, seg);
      seg.remove(); node.data += rest.data; rest.remove();
    }
  }
  // long code and URL-like tokens in table cells get break points at _ , / { ( = & and before dots
  const escH = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  let wbrs = 0;
  for (const el of document.querySelectorAll('td code, th code, td a, th a')) {
    const t = el.textContent;
    if (t.length <= 12 || el.children.length || el.matches('code.nwc') || el.querySelector('code.nwc') || (el.tagName === 'A' && /\s/.test(t))) continue;
    if (!t.split(/\s+/).some(r => r.length > 20)) continue;
    el.innerHTML = escH(t).split(/(\s+)/).map(r => r.length <= 20 ? r : r.replace(/([_,\/{=]|\((?!\))|&amp;)/g, '$1<wbr>').replace(/\.(?=[A-Za-z0-9])/g, '<wbr>.').replace(/^(.{0,2})<wbr>/, '$1').replace(/<wbr>(.{0,2})$/, '$1')).join(''); wbrs++;
  }
  // tables: keep short cells on one line unless that makes the table overflow; squeeze long tokens only in tables that still overflow
  const overflow = [];
  for (const tb of document.querySelectorAll('table')) {
    const cont = tb.parentElement.clientWidth;
    const hs = [...tb.querySelectorAll('thead th')].map(th => th.textContent.replace(/\s+/g, ' ').trim());
    if (hs.join('|') === 'Course week (real phase)|Build|Harness rows that should move') tb.classList.add('wybn');
    if (hs[0] === 'AC-ID' && hs[1] === 'Harness metric') tb.classList.add('kit-metrics');
    if (hs.join('|') === 'Turn|Title|How it is exercised') tb.classList.add('cmap');
    for (const c of tb.querySelectorAll('td, th')) {
      const w = document.createTreeWalker(c, NodeFilter.SHOW_TEXT); const nodes = []; let tn;
      while ((tn = w.nextNode())) if (!tn.parentElement.closest('.nw, code, a') && /[A-Za-z]-[A-Za-z]/.test(tn.data)) nodes.push(tn);
      for (const node of nodes) {
        const frag = document.createDocumentFragment(); let last = 0, m, hit = false; const re = /(?<![\w-])[A-Za-z]+(?:-[A-Za-z]+){1,2}(?![\w-])/g;
        while ((m = re.exec(node.data))) {
          if (m[0].length > 16) continue;
          frag.append(node.data.slice(last, m.index)); const sp = document.createElement('span'); sp.className = 'nw nwt'; sp.textContent = m[0]; frag.append(sp); last = m.index + m[0].length; hit = true;
        }
        if (hit) { frag.append(node.data.slice(last)); node.replaceWith(frag); }
      }
    }
    const phase = hs[0] === 'Phase (weeks)';
    const short = [...tb.querySelectorAll('th,td')].filter(c => {
      const t = c.textContent.trim(); if (!t.length) return false;
      if (t.length <= 12) return true;
      if (t.length <= 20 && /^[\d\s,–-]+$/.test(t)) return true;                    // turn lists such as '109, 110, 116'
      const a = c.children.length === 1 && c.firstElementChild.tagName === 'A' ? c.firstElementChild : null;
      if (a && a.textContent.trim() === t && t.length <= 45) return true;              // a link on its own
      return phase && c.cellIndex === 0 && t.length <= 24;                            // 'Production (10–11)'
    });
    short.forEach(c => c.classList.add('nowrap'));
    if (tb.scrollWidth > cont + 1) { short.forEach(c => c.classList.remove('nowrap')); tb.querySelectorAll('code.nwc').forEach(c => c.classList.remove('nwc')); tb.querySelectorAll('.nwt').forEach(c => c.classList.remove('nw')); }
    if (tb.scrollWidth > cont + 1) tb.classList.add('squeeze');
    if (tb.scrollWidth > cont + 1) overflow.push({ chapter: tb.closest('section')?.id, width: tb.scrollWidth, cont });
  }
  // detector: words in table cells that the layout splits across lines
  const brokenOrdinary = [], brokenLong = [], range = document.createRange();
  for (const c of document.querySelectorAll('td,th')) {
    const walker = document.createTreeWalker(c, NodeFilter.SHOW_TEXT); let node;
    while ((node = walker.nextNode())) {
      const re = /\S{3,}/g; let m;
      while ((m = re.exec(node.data))) {
        range.setStart(node, m.index); range.setEnd(node, m.index + m[0].length);
        const tops = new Set([...range.getClientRects()].filter(r => r.width > 0).map(r => Math.round(r.top)));
        if (tops.size > 1) {
          const w = m[0], item = { word: w.slice(0, 50), chapter: c.closest('section')?.id };
          (/[\/._:=?&]/.test(w) || w.length > 22 || /-/.test(w) ? brokenLong : brokenOrdinary).push(item);
        }
      }
    }
  }
  await document.fonts.ready;
  const clean = s => s.replace(/\s+/g, ' ').trim();
  return {
    headings: [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => clean(h.textContent)),
    blockLines,
    bookmarks: [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => { const c = h.cloneNode(true); c.querySelectorAll('.h-meta').forEach(m => m.remove()); return clean(c.textContent); }),
    leadsText: [...document.querySelectorAll('p.lead')].map(p => clean(p.textContent)),
    rendered: diagrams.length, errors,
    layout: { diagrams, leads, kept, afterHead, forced, numCells, headNw, nwCode, wbrs, tableOverflow: overflow, brokenOrdinary, brokenLong: brokenLong.length, brokenLongSamples: brokenLong.slice(0, 12) },
  };
});
await page.pdf({
  path: path.join(OUT, `main-pass${pass}.pdf`), preferCSSPageSize: true, printBackground: true, outline: true, tagged: true,
  displayHeaderFooter: false,
});
await browser.close();
fs.writeFileSync(path.join(OUT, `headings-pass${pass}.json`), JSON.stringify(diag.headings));
fs.writeFileSync(path.join(OUT, `leads-pass${pass}.json`), JSON.stringify(diag.leadsText));
fs.writeFileSync(path.join(OUT, `bookmarks-pass${pass}.json`), JSON.stringify(diag.bookmarks));
fs.writeFileSync(path.join(OUT, `blocklines-pass${pass}.json`), JSON.stringify(diag.blockLines));
fs.writeFileSync(path.join(OUT, 'build-report.json'), JSON.stringify({
  pass, files: ALL.length, chapters, parts: PARTS.map(p => ({ id: p.id, title: p.title, files: p.files.length })),
  mermaidInSource: mermaidCount, highlightedBlocks: highlighted, mermaidRendered: diag.rendered, mermaidErrors: diag.errors,
  internalLinks: internalLinks.length, escapedPipes, labelBreaks, metaHeadings, droppedRules, layout: diag.layout, problems, browser: browserVersion,
}, null, 2));
console.log(`pass ${pass}: ${ALL.length} files, mermaid ${diag.rendered}/${mermaidCount} (errors ${diag.errors.length}), internal links ${internalLinks.length}, problems ${problems.length}, label breaks ${labelBreaks}, leads ${diag.layout.leads}, overflowing tables ${diag.layout.tableOverflow.length}, broken ordinary words ${diag.layout.brokenOrdinary.length}, broken long tokens ${diag.layout.brokenLong}`);

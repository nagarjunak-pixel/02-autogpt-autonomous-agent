// Render selected Mermaid diagrams with the exact page code from build.mjs and screenshot them.
import { createRequire } from 'node:module'; const { chromium } = createRequire(import.meta.url)('playwright');
import fs from 'fs'; import path from 'path'; import { fileURLToPath, pathToFileURL } from 'node:url';
const HERE = path.dirname(fileURLToPath(import.meta.url)), REPO = path.resolve(HERE, '..', '..'), HERE_URL = pathToFileURL(HERE).href;
process.chdir(HERE);
const files = process.argv.slice(2);
const b = fs.readFileSync('build.mjs', 'utf8');
const s = b.indexOf('const diag = await page.evaluate(') + 'const diag = await page.evaluate('.length;
const e = b.indexOf('\nawait page.pdf(');
const fn = b.slice(s, e).trim().replace(/\);$/, '');
const esc = x => x.replace(/&/g, '&amp;').replace(/</g, '&lt;');
let body = '';
for (const f of files) {
  const src = fs.readFileSync(path.join(REPO, f), 'utf8');
  const m = [...src.matchAll(/```mermaid\n([\s\S]*?)```/g)];
  body += `<section class="chapter" id="${path.basename(f)}"><h2>${f}</h2>` + m.map(x => `<div class="diagram"><pre class="mermaid-src">${esc(x[1])}</pre></div>`).join('') + '</section>';
}
const html = fs.readFileSync('out/book-pass2.html', 'utf8');
const head = html.slice(0, html.indexOf('<body>') + 6); const cut = head.lastIndexOf('<style>');   // swap only the stylesheet; keep the font-face block before it
const headFixed = head.slice(0, cut) + `<style>${fs.readFileSync('style.css', 'utf8')}</style>` + head.slice(head.indexOf('</style>', cut) + 8);
fs.writeFileSync('out/diag-harness.html', `${headFixed}${body}<script src="${HERE_URL}/node_modules/mermaid/dist/mermaid.min.js"></script><script type="module">import elk from "${HERE_URL}/vendor/elk/mermaid-layout-elk.esm.min.mjs"; mermaid.registerLayoutLoaders(elk); window.__elk = true;</script></body></html>`);
const br = await chromium.launch({ ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : { channel: 'chromium' }), args: ['--allow-file-access-from-files'] });
const pg = await br.newPage({ viewport: { width: 665, height: 1100 }, deviceScaleFactor: 2 });
await pg.emulateMedia({ media: 'print' });
await pg.goto(pathToFileURL(path.join(HERE, 'out/diag-harness.html')).href, { waitUntil: 'load' });
const r = await pg.evaluate(`(${fn})()`.replace(/^\(async \(\) =>/, '(async () =>'));
console.log(JSON.stringify(r.layout.diagrams));
const els = await pg.$$('.mmd');
for (let i = 0; i < els.length; i++) await els[i].screenshot({ path: `out/dh-${i}.png` });
await br.close();

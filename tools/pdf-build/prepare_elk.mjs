// Copy the ELK layout engine for Mermaid into vendor/elk and tighten its base spacing (40 -> 24),
// so that diagrams with many nested boxes fit a page at a readable label size. Run by build.sh.
import fs from 'node:fs'; import path from 'node:path';
const HERE = path.dirname(new URL(import.meta.url).pathname);
const src = path.join(HERE, 'node_modules', '@mermaid-js', 'layout-elk', 'dist'), dst = path.join(HERE, 'vendor', 'elk');
if (!fs.existsSync(src)) { console.error('node_modules/@mermaid-js/layout-elk is missing: run npm ci first'); process.exit(1); }
fs.rmSync(dst, { recursive: true, force: true });
fs.cpSync(src, dst, { recursive: true });
const dir = path.join(dst, 'chunks', 'mermaid-layout-elk.esm.min');
const file = fs.readdirSync(dir).find(f => /^render-.*\.mjs$/.test(f) && fs.readFileSync(path.join(dir, f), 'utf8').includes('"spacing.baseValue":40'));
if (!file) { console.error('prepare_elk: "spacing.baseValue":40 not found; the layout-elk version changed, check the patch'); process.exit(1); }
const p = path.join(dir, file), s = fs.readFileSync(p, 'utf8');
if (s.split('"spacing.baseValue":40').length !== 2) { console.error('prepare_elk: expected exactly one spacing.baseValue'); process.exit(1); }
fs.writeFileSync(p, s.replace('"spacing.baseValue":40', '"spacing.baseValue":24'));
console.log('elk ok');

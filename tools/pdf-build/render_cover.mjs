// Render the cover page to out/cover.pdf, stamping the source repository, commit and today's date into cover.html.
import { createRequire } from 'node:module'; import fs from 'node:fs'; import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const { chromium } = createRequire(import.meta.url)('playwright');
const HERE = path.dirname(fileURLToPath(import.meta.url));
const repo = (process.env.REPO_URL || 'https://github.com/nagarjunak-pixel/02-autogpt-autonomous-agent').replace(/^https?:\/\//, '');
const today = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
const html = fs.readFileSync(path.join(HERE, 'cover.html'), 'utf8')
  .replaceAll('{{HERE}}', pathToFileURL(HERE).href).replaceAll('{{REPO}}', repo)
  .replaceAll('{{COMMIT}}', process.env.COMMIT || 'main').replaceAll('{{DIRTY}}', process.env.DIRTY ? ' (with uncommitted changes)' : '')
  .replaceAll('{{COMPILED}}', today);
const page = path.join(HERE, 'out', 'cover.html');
fs.writeFileSync(page, html);
const b = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : { channel: 'chromium' });
const p = await b.newPage(); await p.goto(pathToFileURL(page).href); await p.evaluate(() => document.fonts.ready);
await p.pdf({ path: path.join(HERE, 'out', 'cover.pdf'), format: 'A4', printBackground: true, margin: { top: 0, bottom: 0, left: 0, right: 0 } });
await b.close(); console.log('cover ok');

// Render the cover page to out/cover.pdf, stamping the source commit and today's date into cover.html.
import { createRequire } from 'node:module'; import fs from 'node:fs'; import path from 'node:path';
const { chromium } = createRequire(import.meta.url)('playwright');
const HERE = path.dirname(new URL(import.meta.url).pathname);
const today = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
const html = fs.readFileSync(path.join(HERE, 'cover.html'), 'utf8')
  .replaceAll('{{HERE}}', `file://${HERE}`).replaceAll('{{COMMIT}}', process.env.COMMIT || 'main').replaceAll('{{COMPILED}}', today);
fs.writeFileSync(path.join(HERE, 'out', 'cover.html'), html);
const b = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const p = await b.newPage(); await p.goto(`file://${HERE}/out/cover.html`); await p.evaluate(() => document.fonts.ready);
await p.pdf({ path: `${HERE}/out/cover.pdf`, format: 'A4', printBackground: true, margin: { top: 0, bottom: 0, left: 0, right: 0 } });
await b.close(); console.log('cover ok');

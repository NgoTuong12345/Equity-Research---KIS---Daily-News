const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');
const { getSourceFile } = require('./report-paths');

// --- CONFIG ---
const SESSION = process.argv[2] || 'morning'; // 'morning' or 'afternoon'
const SHEETS_URL = 'https://docs.google.com/spreadsheets/d/1PPjukC3surCnTBPAjfotk_gSckeWQY24UJCWwFuEVtw/edit';
const CHROME_USER_DATA = path.join(os.homedir(), 'AppData', 'Local', 'Google', 'Chrome', 'User Data');
const CHROME_EXE = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const LOG_FILE = path.join(__dirname, 'logs', 'upload.log');

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  try { fs.appendFileSync(LOG_FILE, line + '\n'); } catch (e) { /* ignore */ }
}

function getSheetName() {
  const now = new Date();
  const dd = String(now.getDate()).padStart(2, '0');
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const yyyy = now.getFullYear();
  const prefix = SESSION === 'morning' ? 'mor' : 'after';
  return `${prefix}_${dd}_${mm}_${yyyy}`;
}

function readClipboard() {
  const tmpScript = path.join(os.tmpdir(), `read_clip_${Date.now()}.ps1`);
  const tmpOut = path.join(os.tmpdir(), `clip_out_${Date.now()}.txt`);
  try {
    const script = `[System.IO.File]::WriteAllText('${tmpOut.replace(/\\/g, '\\\\')}', (Get-Clipboard -Raw), [System.Text.Encoding]::UTF8)`;
    fs.writeFileSync(tmpScript, script, 'utf8');
    execSync(`powershell -ExecutionPolicy Bypass -File "${tmpScript}"`, { stdio: 'pipe', timeout: 10000 });
    return fs.readFileSync(tmpOut, 'utf8');
  } finally {
    try { fs.unlinkSync(tmpScript); } catch (e) { /* ignore */ }
    try { fs.unlinkSync(tmpOut); } catch (e) { /* ignore */ }
  }
}

// Robust TSV parser that handles Google Sheets format
// Google Sheets uses \t between cells and \r\n between rows
// Cells containing \n, \t, or " are enclosed in double-quotes (RFC 4180 style)
function parseTsv(text) {
  const rows = [];
  let row = [];
  let cell = '';
  let inQuotes = false;
  let i = 0;

  while (i < text.length) {
    const ch = text[i];
    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') { cell += '"'; i += 2; continue; }
        inQuotes = false; i++; continue;
      }
      cell += ch; i++; continue;
    }
    if (ch === '"') { inQuotes = true; i++; continue; }
    if (ch === '\t') { row.push(cell); cell = ''; i++; continue; }
    if (ch === '\r' && text[i + 1] === '\n') {
      row.push(cell); rows.push(row); row = []; cell = ''; i += 2; continue;
    }
    if (ch === '\n') {
      row.push(cell); rows.push(row); row = []; cell = ''; i++; continue;
    }
    cell += ch; i++;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }

  return rows.filter(r => r.some(c => c.trim()));
}

function buildMarkdown(sheetName, rows) {
  const now = new Date();
  const dd   = String(now.getDate()).padStart(2, '0');
  const mm   = String(now.getMonth() + 1).padStart(2, '0');
  const yyyy = now.getFullYear();
  const hh   = String(now.getHours()).padStart(2, '0');
  const min  = String(now.getMinutes()).padStart(2, '0');
  const dateStr = `${dd}/${mm}/${yyyy}`;
  const timeStr = `${hh}:${min}`;

  // rows[0] = header, rows[1..] = data
  // Columns: A=news_date, B=news_time, C=news_source, D=news_category,
  //          E=news_corp_select, F=news_poli_select, G=news_titles, H=news_urls,
  //          I=corp_url, J=poli_url
  const dataRows = rows.slice(1); // skip header

  const corpRows    = dataRows.filter(r => (r[8] || '').trim()); // col I non-empty
  const poliRows    = dataRows.filter(r => (r[9] || '').trim()); // col J non-empty
  // Rows marked TAKE in col E or F but where the formula produced no URL
  const takenRows   = dataRows.filter(r =>
    ((r[4] || '').trim().toUpperCase() === 'TAKE' ||
     (r[5] || '').trim().toUpperCase() === 'TAKE') &&
    !(r[8] || '').trim() && !(r[9] || '').trim()
  );

  const lines = [
    `# News Report — ${sheetName}`,
    `> Generated: ${dateStr} ${timeStr}`,
    '',
  ];

  // Corporate section
  lines.push(`## Corporate News (${corpRows.length} articles)`);
  lines.push('');
  if (corpRows.length === 0) {
    lines.push('_No articles selected._');
  } else {
    for (const r of corpRows) {
      const title = (r[6] || '').trim();  // col G
      const url   = (r[8] || '').trim();  // col I
      const src   = (r[2] || '').trim();  // col C
      const cat   = (r[3] || '').trim();  // col D
      lines.push(`### ${title}`);
      lines.push(`- **Source:** ${src}  |  **Category:** ${cat}`);
      lines.push(`- **URL:** <${url}>`);
      lines.push('');
    }
  }

  // Political / Macro section
  lines.push(`## Political / Macro News (${poliRows.length} articles)`);
  lines.push('');
  if (poliRows.length === 0) {
    lines.push('_No articles selected._');
  } else {
    for (const r of poliRows) {
      const title = (r[6] || '').trim();  // col G
      const url   = (r[9] || '').trim();  // col J
      const src   = (r[2] || '').trim();  // col C
      const cat   = (r[3] || '').trim();  // col D
      lines.push(`### ${title}`);
      lines.push(`- **Source:** ${src}  |  **Category:** ${cat}`);
      lines.push(`- **URL:** <${url}>`);
      lines.push('');
    }
  }

  // ⚠️ Dropped section — TAKE rows where formula produced no URL
  if (takenRows.length > 0) {
    lines.push(`## ⚠️ DROPPED — TAKE rows with no URL formula output (${takenRows.length} articles)`);
    lines.push('> These rows had TAKE in col E or F but col I/J formula returned empty.');
    lines.push('> Check that H (news_urls) is populated and the formula in I/J is correct.');
    lines.push('');
    for (const r of takenRows) {
      const title = (r[6] || '').trim();
      const url   = (r[7] || '').trim();
      const src   = (r[2] || '').trim();
      const colE  = (r[4] || '').trim();
      const colF  = (r[5] || '').trim();
      lines.push(`### ${title || '(no title)'}`);
      lines.push(`- **Source:** ${src}  |  **E (corp):** ${colE}  |  **F (poli):** ${colF}`);
      lines.push(`- **H (raw url):** <${url}>`);
      lines.push('');
    }
  }

  return lines.join('\n');
}

async function navigateToCell(page, cell) {
  try {
    await page.click('.waffle-name-box', { timeout: 5000, force: true });
    await page.waitForTimeout(150);
    await page.keyboard.press('Control+A');
    await page.keyboard.type(cell, { delay: 40 });
    await page.keyboard.press('Enter');
    await page.waitForTimeout(300);
  } catch (err) {
    if (cell === 'A1') { await page.keyboard.press('Control+Home'); await page.waitForTimeout(300); }
    else log(`Warning: name box to ${cell} failed`);
  }
}

// --- MAIN ---
async function main() {
  fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });

  if (!['morning', 'afternoon'].includes(SESSION)) {
    throw new Error(`Invalid SESSION: ${SESSION}`);
  }

  const sheetName = getSheetName();
  log(`Generating report for sheet: "${sheetName}"`);

  // Launch Chrome with user profile
  log('Launching Chrome...');
  try { execSync('taskkill /F /IM chrome.exe /T', { stdio: 'pipe' }); } catch (e) { /* not running */ }
  await new Promise(resolve => setTimeout(resolve, 2000));
  for (const lockFile of ['SingletonLock', 'SingletonCookie', 'SingletonSocket']) {
    try { fs.unlinkSync(path.join(CHROME_USER_DATA, lockFile)); } catch (e) { /* ignore */ }
  }

  const CDP_PORT = 9222;
  const chromeArgs = [
    `--remote-debugging-port=${CDP_PORT}`,
    `--user-data-dir="${CHROME_USER_DATA}"`,
    '--profile-directory=Default',
    '--no-first-run',
    '--no-default-browser-check',
    '--window-size=1280,900',
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--disable-software-rasterizer',
    'about:blank',
  ].join(' ');
  execSync(
    `powershell -Command "Start-Process -FilePath '${CHROME_EXE}' -ArgumentList '${chromeArgs.replace(/'/g, "''")}'"`
    , { stdio: 'pipe' }
  );

  let browser;
  for (let i = 0; i < 20; i++) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    try { browser = await chromium.connectOverCDP(`http://127.0.0.1:${CDP_PORT}`); break; }
    catch (e) { if (i === 19) throw new Error(`Chrome CDP not ready: ${e.message}`); }
  }

  const context = browser.contexts()[0] || await browser.newContext();
  const page = await context.newPage();

  try {
    log('Navigating to Google Sheets...');
    await page.goto(SHEETS_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(5000);

    // Find and click the target sheet tab
    const tabs = await page.locator('.docs-sheet-tab-name').allTextContents();
    const match = tabs.find(t => t.trim().toLowerCase() === sheetName.toLowerCase());
    if (!match) throw new Error(`Sheet tab "${sheetName}" not found. Available: ${tabs.join(', ')}`);

    log(`Activating tab "${match}"...`);
    await page.locator('.docs-sheet-tab-name', { hasText: match }).first().click();
    await page.waitForTimeout(1000);

    // Find last row with data by pressing Ctrl+End
    await navigateToCell(page, 'A1');
    await page.keyboard.press('Control+End');
    await page.waitForTimeout(500);

    // Read the current cell address from the name box to know last row
    const lastCell = await page.inputValue('.waffle-name-box').catch(() => 'J100');
    const lastRowMatch = lastCell.match(/(\d+)$/);
    const lastRow = lastRowMatch ? parseInt(lastRowMatch[1]) : 100;
    log(`Last row detected: ${lastRow}`);

    // Select A1:J{lastRow} and copy to clipboard
    await navigateToCell(page, `A1:J${lastRow}`);
    await page.keyboard.press('Control+C');
    await page.waitForTimeout(1000);

    // Read clipboard content
    log('Reading clipboard...');
    const clipboardText = readClipboard();
    fs.writeFileSync(path.join(__dirname, 'logs', 'clipboard_dump.tsv'), clipboardText, 'utf8');
    const rows = parseTsv(clipboardText);
    log(`Parsed ${rows.length - 1} data rows`);

    // Build and save markdown
    const md = buildMarkdown(sheetName, rows);
    const outFile = getSourceFile(sheetName);
    fs.writeFileSync(outFile, md, 'utf8');
    log(`✅ Report saved to ${outFile}`);
    console.log('\n' + md);

  } catch (err) {
    log(`❌ Error: ${err.message}`);
    throw err;
  } finally {
    await page.waitForTimeout(500);
    try { await browser.close(); } catch (e) { /* ignore */ }
    try { execSync('taskkill /F /IM chrome.exe /T', { stdio: 'pipe' }); } catch (e) { /* ignore */ }
    log('Browser closed.');
  }
}

main().catch(err => {
  log(`FATAL: ${err.message}`);
  process.exit(1);
});

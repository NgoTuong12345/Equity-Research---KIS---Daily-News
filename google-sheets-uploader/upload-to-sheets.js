const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

// --- CONFIG ---
const SESSION = process.argv[2] || 'morning'; // 'morning' or 'afternoon'
const SHEETS_URL = 'https://docs.google.com/spreadsheets/d/1PPjukC3surCnTBPAjfotk_gSckeWQY24UJCWwFuEVtw/edit';
const CSV_DIR = path.join(__dirname, '..', 'vietnam_news_scraper');
const CHROME_USER_DATA = path.join(os.homedir(), 'AppData', 'Local', 'Google', 'Chrome', 'User Data');
const CHROME_EXE = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const LOG_FILE = path.join(__dirname, 'logs', 'upload.log');

// Sheet headers in order (10 columns: A–J)
// E and F are blank (manual TAKE columns); I and J get IF formulas after paste
const SHEET_HEADERS = [
  'news_date',       // A – from CSV col 1
  'news_time',       // B – from CSV col 2
  'news_source',     // C – from CSV col 3
  'news_category',   // D – from CSV col 4
  'news_corp_select',// E – blank (manual input)
  'news_poli_select',// F – blank (manual input)
  'news_titles',     // G – from CSV col 5
  'news_urls',       // H – from CSV col 6
  'corp_url',        // I – formula =IF(E2="TAKE",H2,"")
  'poli_url',        // J – formula =IF(F2="TAKE",H2,"")
];

// --- HELPERS ---
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

function getLatestCsv() {
  if (!fs.existsSync(CSV_DIR)) throw new Error(`CSV directory not found: ${CSV_DIR}`);
  const files = fs.readdirSync(CSV_DIR)
    .filter(f => f.startsWith('vietnam_financial_news_combined') && f.endsWith('.csv'))
    .map(f => ({ name: f, mtime: fs.statSync(path.join(CSV_DIR, f)).mtime }))
    .sort((a, b) => b.mtime - a.mtime);
  if (!files.length) throw new Error('No CSV files found in ' + CSV_DIR);
  return path.join(CSV_DIR, files[0].name);
}

function parseCsvLine(line) {
  const fields = [];
  let field = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') { field += '"'; i++; }
      else inQuotes = !inQuotes;
    } else if (ch === ',' && !inQuotes) {
      fields.push(field.trim());
      field = '';
    } else {
      field += ch;
    }
  }
  fields.push(field.trim());
  return fields;
}

// Remap CSV columns [date, time, source, category, title, link]
// to sheet columns [date, time, source, category, '', '', title, link]
// (cols I and J are formulas added separately, not pasted)
function buildTsvForPaste(csvPath) {
  const content = fs.readFileSync(csvPath, 'utf8').replace(/^﻿/, '');
  const lines = content.split(/\r?\n/).filter(l => l.trim());

  return lines.map((line, idx) => {
    const f = parseCsvLine(line);
    if (idx === 0) {
      // Header row: use canonical sheet column names A–H only (I and J added via formula)
      return ['news_date', 'news_time', 'news_source', 'news_category',
              'news_corp_select', 'news_poli_select', 'news_titles', 'news_urls'].join('\t');
    }
    // Data row: [date, time, source, category, '', '', title, link]
    return [f[0], f[1], f[2], f[3], '', '', f[4], f[5]].join('\t');
  }).join('\r\n');
}

function setWindowsClipboard(text) {
  const id = Date.now();
  const tmpData = path.join(os.tmpdir(), `sheets_data_${id}.tsv`);
  const tmpScript = path.join(os.tmpdir(), `sheets_clip_${id}.ps1`);
  try {
    fs.writeFileSync(tmpData, text, 'utf8');
    const script = `[System.IO.File]::ReadAllText('${tmpData.replace(/\\/g, '\\\\')}', [System.Text.Encoding]::UTF8) | Set-Clipboard`;
    fs.writeFileSync(tmpScript, script, 'utf8');
    execSync(`powershell -ExecutionPolicy Bypass -File "${tmpScript}"`, { stdio: 'pipe', timeout: 10000 });
  } catch (err) {
    throw new Error(`Failed to set clipboard: ${err.message}`);
  } finally {
    try { fs.unlinkSync(tmpData); } catch (e) { /* ignore */ }
    try { fs.unlinkSync(tmpScript); } catch (e) { /* ignore */ }
  }
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
    if (cell === 'A1') {
      await page.keyboard.press('Control+Home');
      await page.waitForTimeout(300);
    } else {
      log(`Warning: name box to ${cell} failed: ${err.message}`);
    }
  }
}

// --- MAIN ---
async function main() {
  fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });

  if (!['morning', 'afternoon'].includes(SESSION)) {
    throw new Error(`Invalid SESSION: ${SESSION}. Must be 'morning' or 'afternoon'`);
  }

  const sheetName = getSheetName();
  log(`Session: ${SESSION}, Sheet name: "${sheetName}"`);

  const csvPath = getLatestCsv();
  log(`Using CSV: ${csvPath}`);

  // Count data rows (excluding header) so we know formula range
  const csvLines = fs.readFileSync(csvPath, 'utf8').replace(/^﻿/, '').split(/\r?\n/).filter(l => l.trim());
  const dataRowCount = csvLines.length - 1; // minus header
  log(`Data rows: ${dataRowCount}`);

  const tsvData = buildTsvForPaste(csvPath);
  setWindowsClipboard(tsvData);
  log('Clipboard set with TSV data (columns A–H)');

  // Launch Chrome with user profile via CDP
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
    'about:blank',
  ].join(' ');
  execSync(
    `powershell -Command "Start-Process -FilePath '${CHROME_EXE}' -ArgumentList '${chromeArgs.replace(/'/g, "''")}'"`
    , { stdio: 'pipe' }
  );

  let browser;
  for (let i = 0; i < 20; i++) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    try {
      browser = await chromium.connectOverCDP(`http://127.0.0.1:${CDP_PORT}`);
      log(`Connected to Chrome (attempt ${i + 1})`);
      break;
    } catch (e) {
      if (i === 19) throw new Error(`Chrome CDP not ready: ${e.message}`);
    }
  }

  const context = browser.contexts()[0] || await browser.newContext();
  const page = await context.newPage();

  try {
    // Step 2: Navigate to the spreadsheet
    log('Navigating to Google Sheets...');
    await page.goto(SHEETS_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(5000);

    log(`Page: "${await page.title()}" | ${page.url()}`);

    // Dismiss any modal dialogs (error dialogs, overlays)
    try {
      // Click OK on any error dialog
      const okBtn = page.locator('button:has-text("OK"), button:has-text("Đồng ý")');
      if (await okBtn.count() > 0) {
        await okBtn.first().click();
        await page.waitForTimeout(500);
      }
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
    } catch (e) { /* ignore */ }

    // Step 3: Create or reuse sheet tab
    log(`Checking if tab "${sheetName}" already exists...`);

    // Check all existing tab names (case-insensitive match)
    const existingTabs = await page.locator('.docs-sheet-tab-name').allTextContents();
    const tabExists = existingTabs.some(t => t.trim().toLowerCase() === sheetName.toLowerCase());

    if (tabExists) {
      // Click the existing tab to activate it
      log(`Tab "${sheetName}" already exists — activating and clearing it...`);
      await page.locator('.docs-sheet-tab-name', { hasText: sheetName }).first().click();
      await page.waitForTimeout(800);
      // Click the select-all corner (top-left of grid) to select every cell, then delete
      try {
        await page.locator('.col-row-resize-overlay, .freezebar-handle-corner, [data-row-index="-1"][data-col-index="-1"]').first().click({ force: true, timeout: 2000 });
      } catch (e) {
        // Fallback: Ctrl+A twice (first selects data range, second selects all cells)
        await page.keyboard.press('Escape');
        await page.waitForTimeout(200);
        await page.keyboard.press('Control+A');
        await page.waitForTimeout(100);
        await page.keyboard.press('Control+A');
      }
      await page.waitForTimeout(200);
      await page.keyboard.press('Delete');
      await page.waitForTimeout(500);
    } else {
      // Create new tab
      log('Creating new sheet tab...');
      const addSheetSelectors = [
        '[aria-label="Thêm trang tính"]',
        '[aria-label="Add Sheet"]',
        '[title="Add Sheet"]',
        '.docs-sheet-tab-add',
        'button[aria-label*="Thêm"]',
        'button[aria-label*="Add"]',
      ];
      let clicked = false;
      for (const sel of addSheetSelectors) {
        try {
          await page.waitForSelector(sel, { timeout: 3000 });
          await page.click(sel);
          clicked = true;
          log(`Add Sheet clicked (${sel})`);
          break;
        } catch (e) { /* try next */ }
      }
      if (!clicked) throw new Error('Add Sheet button not found');
      await page.waitForTimeout(1000);

      // Rename by double-clicking the active tab
      log(`Renaming tab to "${sheetName}"...`);
      const activeTab = page.locator('.docs-sheet-active-tab');
      await activeTab.waitFor({ timeout: 5000 });
      await activeTab.dblclick();
      await page.waitForTimeout(400);
      await page.keyboard.press('Control+A');
      await page.keyboard.type(sheetName, { delay: 50 });
      await page.keyboard.press('Enter');
      await page.waitForTimeout(500);
      log(`Tab renamed to "${sheetName}"`);
    }

    // Step 3: Paste A–H data starting at A1
    await navigateToCell(page, 'A1');
    log('Pasting data (columns A–H)...');
    await page.keyboard.press('Control+V');
    await page.waitForTimeout(3000);

    // Step 4: Enter IF formulas in I2 and J2, then fill down
    if (dataRowCount > 0) {
      const lastRow = dataRowCount + 1; // +1 for header

      log('Entering corp_url formula in I2...');
      await navigateToCell(page, 'I2');
      await page.keyboard.type('=IF(E2="TAKE",H2,"")', { delay: 30 });
      await page.keyboard.press('Enter');

      log('Entering poli_url formula in J2...');
      await navigateToCell(page, 'J2');
      await page.keyboard.type('=IF(F2="TAKE",H2,"")', { delay: 30 });
      await page.keyboard.press('Enter');

      if (dataRowCount > 1) {
        // Select I2:J2 and fill down to cover all data rows
        await navigateToCell(page, `I2`);
        // Select I2:J{lastRow}
        await page.click('.waffle-name-box', { timeout: 5000 });
        await page.waitForTimeout(150);
        await page.keyboard.press('Control+A');
        await page.keyboard.type(`I2:J${lastRow}`, { delay: 40 });
        await page.keyboard.press('Enter');
        await page.waitForTimeout(300);
        await page.keyboard.press('Control+D'); // fill down
        await page.waitForTimeout(1000);
        log(`Formulas filled down to row ${lastRow}`);
      }
    }

    // Step 5: Bold header row 1
    log('Bolding header row...');
    try {
      await page.click('.waffle-name-box', { timeout: 5000, force: true });
      await page.waitForTimeout(150);
      await page.keyboard.press('Control+A');
      await page.keyboard.type('1:1', { delay: 40 });
      await page.keyboard.press('Enter');
      await page.waitForTimeout(300);
      await page.keyboard.press('Control+B');
      await page.waitForTimeout(500);
    } catch (err) {
      log(`Warning: bold header failed: ${err.message}`);
    }

    log('✅ Upload complete!');
  } catch (err) {
    log(`❌ Error: ${err.message}`);
    throw err;
  } finally {
    await page.waitForTimeout(1000);
    try { await browser.close(); } catch (e) { /* ignore */ }
    try { execSync('taskkill /F /IM chrome.exe /T', { stdio: 'pipe' }); } catch (e) { /* ignore */ }
    log('Browser closed.');
  }
}

main().catch(err => {
  log(`FATAL: ${err.message}`);
  process.exit(1);
});

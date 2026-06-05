const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');
const { getDataFile } = require('./report-paths');

const SHEETS_URL = 'https://docs.google.com/spreadsheets/d/1PPjukC3surCnTBPAjfotk_gSckeWQY24UJCWwFuEVtw/edit';
const CHROME_USER_DATA = path.join(os.homedir(), 'AppData', 'Local', 'Google', 'Chrome', 'User Data');
const CHROME_EXE = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const CDP_PORT = 9222;
const CLI_ARGS = process.argv.slice(2);
const SESSION_ALIASES = {
  morning: 'morning',
  mor: 'morning',
  afternoon: 'afternoon',
  after: 'afternoon',
};
const SESSION = SESSION_ALIASES[(CLI_ARGS[0] || '').toLowerCase()] || null;
const DATE_ARG = SESSION ? CLI_ARGS[1] : CLI_ARGS[0];
// Accept optional session and date args: [morning|afternoon] [DD/MM/YYYY].
const TODAY = DATE_ARG || (() => {
  const now = new Date();
  const dd = String(now.getDate()).padStart(2, '0');
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  return `${dd}/${mm}/${now.getFullYear()}`;
})();

function log(msg) {
  console.log(`[${new Date().toISOString()}] ${msg}`);
}

function dateParts(dateString) {
  const match = String(dateString || '').match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (match) return { dd: match[1], mm: match[2], yyyy: match[3] };
  const now = new Date();
  return {
    dd: String(now.getDate()).padStart(2, '0'),
    mm: String(now.getMonth() + 1).padStart(2, '0'),
    yyyy: String(now.getFullYear()),
  };
}

function reportBaseForSession(session) {
  const { dd, mm, yyyy } = dateParts(TODAY);
  const effectiveSession = session || (new Date().getHours() < 12 ? 'morning' : 'afternoon');
  const prefix = effectiveSession === 'morning' ? 'mor' : 'after';
  return { base: `${prefix}_${dd}_${mm}_${yyyy}`, dd, mm, yyyy, session: effectiveSession };
}

function writeEmptyAfternoonMacro(baseInfo) {
  const output = {
    source: 'macro_sheet',
    date: TODAY,
    extracted_at: new Date().toISOString(),
    item_count: 0,
    items: [],
    skipped: true,
    reason: 'Macro and vin_bank Google Sheet data are morning-only inputs.',
  };
  const outPath = getDataFile(baseInfo.base, `macro_sheet_${baseInfo.dd}_${baseInfo.mm}_${baseInfo.yyyy}.json`);
  fs.writeFileSync(outPath, JSON.stringify(output, null, 2), 'utf8');
  log(`Afternoon session detected. Skipped macro/vin_bank read and saved empty JSON: ${outPath}`);
  return output;
}

// Robust date match: the narrow column A causes clipboard to swap chars inside the date.
// We match by day (first 2 chars) and year (last 4 chars) to avoid the rendering artifact.
function matchesToday(cellValue) {
  const v = (cellValue || '').trim();
  if (!v) return false;
  const todayDay  = TODAY.slice(0, 2);  // '04'
  const todayYear = TODAY.slice(-4);    // '2026'
  return v.startsWith(todayDay) && v.includes(todayYear);
}

// Parse 'Macro: Title): Content' or 'Macro: Title: Content' format
function parseNewsTime(raw) {
  const text = (raw || '').trim();
  // Strip leading 'Macro: ' prefix
  const withoutPrefix = text.startsWith('Macro:') ? text.slice(6).trim() : text;
  // Split on first ': (' or ': ' to separate title from body
  const colonIdx = withoutPrefix.indexOf(': (');
  if (colonIdx > 0) {
    const title = withoutPrefix.slice(0, colonIdx).replace(/\)$/, '').trim();
    const body = withoutPrefix.slice(colonIdx + 2).trim(); // keep the '('
    return { title, body };
  }
  // Fallback: split on first ': '
  const simple = withoutPrefix.indexOf(': ');
  if (simple > 0) {
    return {
      title: withoutPrefix.slice(0, simple).trim(),
      body: withoutPrefix.slice(simple + 2).trim(),
    };
  }
  return { title: withoutPrefix.slice(0, 60), body: withoutPrefix };
}

async function scrapeTab(page, tabLocator, tabName) {
  log(`Switching to tab: ${tabName}`);
  await tabLocator.click();
  await page.waitForTimeout(4000);

  // Select A1:Z500 via name box and copy
  await page.click('.waffle-name-box', { timeout: 5000, force: true });
  await page.waitForTimeout(300);
  await page.keyboard.press('Control+A');
  await page.waitForTimeout(100);
  await page.keyboard.type('A1:Z500', { delay: 50 });
  await page.keyboard.press('Enter');
  await page.waitForTimeout(800);
  await page.keyboard.press('Control+C');
  await page.waitForTimeout(2000);

  // Read clipboard via Get-Clipboard -Raw (preserves exact bytes)
  const tmpOut = path.join(os.tmpdir(), `${tabName}_clip_${Date.now()}.txt`);
  const tmpScript = path.join(os.tmpdir(), `${tabName}_ps_${Date.now()}.ps1`);
  fs.writeFileSync(tmpScript,
    `[System.IO.File]::WriteAllText('${tmpOut.replace(/\\/g,'\\\\')}', (Get-Clipboard -Raw), [System.Text.Encoding]::UTF8)`,
    'utf8'
  );
  execSync(`powershell -ExecutionPolicy Bypass -File "${tmpScript}"`, { stdio: 'pipe', timeout: 10000 });
  const clipRaw = fs.readFileSync(tmpOut, 'utf8');
  try { fs.unlinkSync(tmpOut); } catch(e) {}
  try { fs.unlinkSync(tmpScript); } catch(e) {}

  log(`Clipboard bytes for ${tabName}: ${clipRaw.length}`);
  const rows = parseTsvRobust(clipRaw);
  log(`Parsed rows for ${tabName}: ${rows.length}`);
  return rows;
}

function processTabRows(rows, tabName) {
  if (rows.length < 2) {
    log(`WARNING: No data in tab ${tabName}`);
    return [];
  }

  const headers = rows[0].map(h => h.trim());
  log(`Headers for ${tabName}: ${JSON.stringify(headers)}`);

  // Filter rows matching today's date in column 0
  const todayRows = rows.slice(1).filter(cols => {
    const dateVal = (cols[0] || '').trim();
    return matchesToday(dateVal);
  });
  log(`Rows matching ${TODAY} in ${tabName}: ${todayRows.length}`);

  // If still 0, log all dates found for debugging
  if (todayRows.length === 0) {
    log(`WARNING: no rows matched in ${tabName}. Dates found:`);
    rows.slice(1).slice(0, 10).forEach((r, i) => log(`  Row ${i+1} col0: "${(r[0]||'').trim()}"`));
  }

  // Resolve column indices by header name (case-insensitive)
  const colIdx = (name) => headers.findIndex(h => h.toLowerCase() === name.toLowerCase());
  const idxDate  = colIdx('news_date');
  const idxCat   = colIdx('news_category');
  
  let idxEn  = colIdx('news_time_en') >= 0 ? colIdx('news_time_en') : colIdx('news_time');
  let idxVn  = colIdx('news_time_vn');

  // Robust fallback for duplicate or missing headers
  if (idxVn === -1 && headers.length > 3) {
    idxVn = 3;
  }
  if (idxEn === -1 && headers.length > 2) {
    idxEn = 2;
  }
  
  log(`Column indices for ${tabName} — date:${idxDate} cat:${idxCat} en:${idxEn} vn:${idxVn}`);

  // Build structured items
  return todayRows.map((cols, idx) => {
    const rawEn = (idxEn >= 0 && idxEn < cols.length ? cols[idxEn] : '').trim();
    const rawVn = (idxVn >= 0 && idxVn < cols.length ? cols[idxVn] : '').trim();
    const parsedEn = parseNewsTime(rawEn);
    const parsedVn = parseNewsTime(rawVn);
    
    // Determine category label:
    // - All Macro tab rows are economy/investment aggregates.
    // - vin_bank tab rows are Corporate UNLESS the news_category signals a
    //   non-ticker subject (Commodities, Macro, etc.).
    const newsCat = (idxCat >= 0 && idxCat < cols.length ? cols[idxCat] : '').trim();
    const NON_TICKER_CATEGORIES = new Set([
      'commodities', 'macro', 'policy', 'chính sách', 'hàng hóa', 'khác', 'others',
    ]);
    let catLabel = 'Economy & investments';
    if (tabName === 'vin_bank') {
      catLabel = NON_TICKER_CATEGORIES.has(newsCat.toLowerCase())
        ? 'Economy & investments'
        : 'Corporate';
    }

    return {
      source_tab: tabName.toLowerCase(),
      news_date:     (idxDate >= 0 && idxDate < cols.length ? cols[idxDate] : cols[0] || '').trim(),
      news_category: newsCat,
      title_en: parsedEn.title,
      body_en:  parsedEn.body,
      title_vn: parsedVn.title,
      body_vn:  parsedVn.body,
      raw_en: rawEn,
      raw_vn: rawVn,
      category_label: catLabel,
    };
  });
}

async function main() {
  const baseInfo = reportBaseForSession(SESSION);
  if (baseInfo.session === 'afternoon') {
    return writeEmptyAfternoonMacro(baseInfo);
  }

  log('Launching Chrome...');
  try { execSync('taskkill /F /IM chrome.exe /T', { stdio: 'pipe' }); } catch (e) { /* not running */ }
  await new Promise(r => setTimeout(r, 2000));

  for (const lockFile of ['SingletonLock', 'SingletonCookie', 'SingletonSocket']) {
    try { fs.unlinkSync(path.join(CHROME_USER_DATA, lockFile)); } catch (e) { /* ignore */ }
  }

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
    await new Promise(r => setTimeout(r, 1000));
    try {
      browser = await chromium.connectOverCDP(`http://127.0.0.1:${CDP_PORT}`);
      log(`Connected (attempt ${i + 1})`);
      break;
    } catch (e) {
      if (i === 19) throw new Error(`CDP not ready: ${e.message}`);
    }
  }

  const context = browser.contexts()[0] || await browser.newContext();
  const page = await context.newPage();

  try {
    log('Opening Google Sheets...');
    await page.goto(SHEETS_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(6000);

    // Locate both Macro and vin_bank tabs
    const tabs = page.locator('.docs-sheet-tab-name');
    const count = await tabs.count();
    let macroTab = null;
    let vinBankTab = null;
    for (let i = 0; i < count; i++) {
      const name = await tabs.nth(i).textContent();
      log(`Tab ${i}: "${name}"`);
      if (name) {
        const cleanName = name.toLowerCase().trim();
        if (cleanName === 'macro') macroTab = tabs.nth(i);
        if (cleanName === 'vin_bank') vinBankTab = tabs.nth(i);
      }
    }
    if (!macroTab) throw new Error('macro tab not found');

    const macroRows = await scrapeTab(page, macroTab, 'Macro');
    const macroItems = processTabRows(macroRows, 'Macro');

    let vinBankItems = [];
    if (vinBankTab) {
      const vinBankRows = await scrapeTab(page, vinBankTab, 'vin_bank');
      vinBankItems = processTabRows(vinBankRows, 'vin_bank');
    } else {
      log('WARNING: vin_bank tab not found on sheet.');
    }

    const allItems = [...macroItems, ...vinBankItems].map((item, idx) => {
      item.order = idx + 1;
      return item;
    });

    log(`Total combined items matching ${TODAY}: ${allItems.length}`);

    const now = new Date();
    const { dd, mm, yyyy } = baseInfo;

    const output = {
      source: 'macro_sheet',
      date: TODAY,
      extracted_at: now.toISOString(),
      item_count: allItems.length,
      items: allItems,
    };

    const outPath = getDataFile(baseInfo.base, `macro_sheet_${dd}_${mm}_${yyyy}.json`);
    fs.writeFileSync(outPath, JSON.stringify(output, null, 2), 'utf8');
    log(`Saved JSON: ${outPath}`);

    // Print each item for verification
    allItems.forEach(item => {
      log(`  Item ${item.order} (${item.source_tab}) EN: "${item.title_en}"`);
      log(`    EN body: ${item.body_en.slice(0, 100)}`);
      log(`  Item ${item.order} (${item.source_tab}) VN: "${item.title_vn}"`);
      log(`    VN body: ${item.body_vn.slice(0, 100)}`);
    });

    return output;

  } finally {
    await page.close();
    await browser.close();
  }
}

// Robust TSV parser that handles Google Sheets format
// Google Sheets uses \t between cells and \r\n between rows
// Cells containing \n, \t, or " are enclosed in double-quotes (RFC 4180 style)
function parseTsvRobust(text) {
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

main().catch(err => { console.error('ERROR:', err.message); process.exit(1); });

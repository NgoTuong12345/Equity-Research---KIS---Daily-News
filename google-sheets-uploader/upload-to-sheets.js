const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

// --- CONFIG ---
const SESSION = process.argv[2] || 'morning'; // 'morning' or 'afternoon'
const SHEETS_URL = 'https://docs.google.com/spreadsheets/d/11wp6NqYyRmUDcQhJ9NmDKoxX8d8bamC77WaXQg-ZTm4/edit';
const CSV_DIR = path.join(__dirname, '..', 'vietnam_news_scraper');
const CHROME_USER_DATA = path.join(os.homedir(), 'AppData', 'Local', 'Google', 'Chrome', 'User Data');
const CHROME_EXE = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const LOG_FILE = path.join(__dirname, 'logs', 'upload.log');

// --- HELPERS ---
function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  try {
    fs.appendFileSync(LOG_FILE, line + '\n');
  } catch (err) {
    console.error('Failed to write log:', err.message);
  }
}

function getSheetName() {
  const now = new Date();
  const day = String(now.getDate()).padStart(2, '0');
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const prefix = SESSION === 'morning' ? '[Mor]' : '[After]';
  return `${prefix} ${day}.${month}`;
}

function getLatestCsv() {
  if (!fs.existsSync(CSV_DIR)) {
    throw new Error(`CSV directory not found: ${CSV_DIR}`);
  }
  const files = fs.readdirSync(CSV_DIR)
    .filter(f => f.startsWith('vietnam_financial_news_combined') && f.endsWith('.csv'))
    .map(f => ({ name: f, mtime: fs.statSync(path.join(CSV_DIR, f)).mtime }))
    .sort((a, b) => b.mtime - a.mtime);
  if (!files.length) throw new Error('No CSV files found in ' + CSV_DIR);
  return path.join(CSV_DIR, files[0].name);
}

function parseCsvToTsv(csvPath) {
  const content = fs.readFileSync(csvPath, 'utf8').replace(/^﻿/, ''); // strip BOM
  const lines = content.split(/\r?\n/).filter(l => l.trim());

  return lines.map(line => {
    const fields = [];
    let field = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      const nextChar = line[i + 1];

      if (char === '"') {
        if (inQuotes && nextChar === '"') {
          // Escaped quote: "" becomes "
          field += '"';
          i++; // skip next quote
        } else {
          // Toggle quote state
          inQuotes = !inQuotes;
        }
      } else if (char === ',' && !inQuotes) {
        // End of field
        fields.push(field.trim());
        field = '';
      } else {
        field += char;
      }
    }
    fields.push(field.trim()); // Last field

    return fields.join('\t');
  }).join('\r\n');
}

function setWindowsClipboard(text) {
  const tmpDir = path.join(os.tmpdir(), 'sheets_' + Math.random().toString(36).substr(2, 9));
  const tmpFile = path.join(tmpDir, 'data.tsv');

  try {
    // Create temp directory
    fs.mkdirSync(tmpDir, { recursive: true });

    // Write TSV data
    fs.writeFileSync(tmpFile, text, 'utf8');

    // Use PowerShell to set clipboard with retry
    try {
      execSync(`powershell -Command "[System.IO.File]::ReadAllText('${tmpFile}') | Set-Clipboard"`, {
        stdio: 'pipe',
        timeout: 5000
      });
    } catch (err) {
      // Fallback: try without file, using here-string (for smaller data)
      if (text.length < 30000) {
        const escaped = text.replace(/'/g, "''");
        execSync(`powershell -Command "'${escaped}' | Set-Clipboard"`, { stdio: 'pipe', timeout: 5000 });
      } else {
        throw err;
      }
    }
  } catch (err) {
    throw new Error(`Failed to set clipboard: ${err.message}`);
  } finally {
    try {
      if (fs.existsSync(tmpFile)) fs.unlinkSync(tmpFile);
      if (fs.existsSync(tmpDir)) fs.rmdirSync(tmpDir);
    } catch (e) {
      // Ignore cleanup errors
    }
  }
}

// --- MAIN ---
async function main() {
  // Ensure logs directory exists
  fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });

  // Validate SESSION parameter
  if (!['morning', 'afternoon'].includes(SESSION)) {
    throw new Error(`Invalid SESSION: ${SESSION}. Must be 'morning' or 'afternoon'`);
  }

  const sheetName = getSheetName();
  log(`Session: ${SESSION}, Sheet name: "${sheetName}"`);

  const csvPath = getLatestCsv();
  log(`Using CSV: ${csvPath}`);

  const tsvData = parseCsvToTsv(csvPath);
  setWindowsClipboard(tsvData);
  log('Clipboard set with TSV data');

  // Launch fresh Chrome without authentication profile
  log('Launching Chrome...');
  const browser = await chromium.launch({
    executablePath: CHROME_EXE,
    headless: true,
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    log('Navigating to Google Sheets...');
    await page.goto(SHEETS_URL, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForLoadState('networkidle');

    // Click "+" button to add new sheet tab
    log('Creating new sheet tab...');
    try {
      await page.click('[aria-label="Add Sheet"]', { timeout: 5000 });
      await page.waitForSelector('.docs-sheet-active-tab', { timeout: 5000 });
    } catch (err) {
      throw new Error(`Failed to create sheet tab: ${err.message}`);
    }

    // Double-click the active (newly created) tab to rename it
    try {
      const activeTab = page.locator('.docs-sheet-active-tab .docs-sheet-tab-name');
      await activeTab.dblclick({ timeout: 5000 });
      await page.waitForTimeout(300);

      await page.keyboard.press('Control+A');
      await page.keyboard.type(sheetName, { delay: 50 });
      await page.keyboard.press('Enter');
      await page.waitForTimeout(500);
      log(`Sheet tab renamed to "${sheetName}"`);
    } catch (err) {
      throw new Error(`Failed to rename sheet tab: ${err.message}`);
    }

    // Navigate to cell A1 using the Name Box
    try {
      await page.click('.waffle-name-box', { timeout: 5000 });
      await page.waitForTimeout(200);
      await page.keyboard.press('Control+A');
      await page.keyboard.type('A1', { delay: 50 });
      await page.keyboard.press('Enter');
      await page.waitForTimeout(300);
    } catch (err) {
      log(`Warning: Name box navigation failed, trying direct approach: ${err.message}`);
      // Fallback: use Ctrl+Home to go to A1
      await page.keyboard.press('Control+Home');
    }

    // Paste TSV data (already in clipboard)
    log('Pasting data...');
    try {
      await page.keyboard.press('Control+V');
      await page.waitForTimeout(3000); // wait for paste to complete
    } catch (err) {
      throw new Error(`Failed to paste data: ${err.message}`);
    }

    // Select row 1 and bold it
    log('Applying bold to header row...');
    try {
      await page.click('.waffle-name-box', { timeout: 5000 });
      await page.waitForTimeout(200);
      await page.keyboard.press('Control+A');
      await page.keyboard.type('1:1', { delay: 50 });
      await page.keyboard.press('Enter');
      await page.waitForTimeout(300);
      await page.keyboard.press('Control+B');
      await page.waitForTimeout(500);
    } catch (err) {
      log(`Warning: Failed to bold header row: ${err.message}`);
    }

    log('✅ Upload complete!');
  } catch (err) {
    log(`❌ Error during automation: ${err.message}`);
    throw err;
  } finally {
    await page.waitForTimeout(1000);
    try {
      await context.close();
      await browser.close();
    } catch (e) {
      log(`Warning: Failed to close browser: ${e.message}`);
    }
    log('Browser closed.');
  }
}

main().catch(err => {
  log(`FATAL: ${err.message}`);
  process.exit(1);
});

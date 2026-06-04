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
  fs.appendFileSync(LOG_FILE, line + '\n');
}

function getSheetName() {
  const now = new Date();
  const day = String(now.getDate()).padStart(2, '0');
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const prefix = SESSION === 'morning' ? '[Mor]' : '[After]';
  return `${prefix} ${day}.${month}`;
}

function getLatestCsv() {
  const files = fs.readdirSync(CSV_DIR)
    .filter(f => f.startsWith('vietnam_financial_news_combined') && f.endsWith('.csv'))
    .map(f => ({ name: f, mtime: fs.statSync(path.join(CSV_DIR, f)).mtime }))
    .sort((a, b) => b.mtime - a.mtime);
  if (!files.length) throw new Error('No CSV files found in ' + CSV_DIR);
  return path.join(CSV_DIR, files[0].name);
}

function parseCsvToTsv(csvPath) {
  const content = fs.readFileSync(csvPath, 'utf8').replace(/^﻿/, ''); // strip BOM
  return content.trim().split('\n').map(line => {
    const fields = [];
    let inQuote = false, field = '';
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') { inQuote = !inQuote; continue; }
      if (ch === ',' && !inQuote) { fields.push(field); field = ''; continue; }
      field += ch;
    }
    fields.push(field);
    return fields.join('\t');
  }).join('\r\n');
}

function setWindowsClipboard(text) {
  const tmpFile = path.join(os.tmpdir(), 'gsheets_paste.tsv');
  fs.writeFileSync(tmpFile, text, 'utf8');
  // PowerShell reads the file and sets clipboard
  execSync(`powershell -Command "Get-Content -Path '${tmpFile}' -Raw | Set-Clipboard"`, { stdio: 'pipe' });
}

// --- MAIN ---
async function main() {
  const sheetName = getSheetName();
  log(`Session: ${SESSION}, Sheet name: "${sheetName}"`);

  const csvPath = getLatestCsv();
  log(`Using CSV: ${csvPath}`);

  const tsvData = parseCsvToTsv(csvPath);
  setWindowsClipboard(tsvData);
  log('Clipboard set with TSV data');

  const context = await chromium.launchPersistentContext(CHROME_USER_DATA, {
    executablePath: CHROME_EXE,
    headless: false,
    args: ['--profile-directory=Default', '--no-first-run', '--no-default-browser-check'],
    timeout: 30000,
  });

  const page = context.pages().length > 0 ? context.pages()[0] : await context.newPage();

  try {
    log('Navigating to Google Sheets...');
    await page.goto(SHEETS_URL, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(2000);

    // Click "+" button to add new sheet tab
    log('Creating new sheet tab...');
    await page.click('[aria-label="Add Sheet"]');
    await page.waitForTimeout(1500);

    // Double-click the active (newly created) tab to rename it
    const activeTab = page.locator('.docs-sheet-active-tab .docs-sheet-tab-name');
    await activeTab.dblclick();
    await page.waitForTimeout(500);
    await page.keyboard.press('Control+A');
    await page.keyboard.type(sheetName);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1500);
    log(`Sheet tab renamed to "${sheetName}"`);

    // Navigate to cell A1 using the Name Box
    await page.click('.waffle-name-box');
    await page.waitForTimeout(300);
    await page.keyboard.press('Control+A');
    await page.keyboard.type('A1');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(500);

    // Paste TSV data (already in clipboard)
    log('Pasting data...');
    await page.keyboard.press('Control+V');
    await page.waitForTimeout(5000); // wait for paste to complete

    // Select row 1 and bold it
    log('Applying bold to header row...');
    await page.click('.waffle-name-box');
    await page.waitForTimeout(300);
    await page.keyboard.press('Control+A');
    await page.keyboard.type('1:1');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(500);
    await page.keyboard.press('Control+B');
    await page.waitForTimeout(1000);

    log('✅ Upload complete!');
  } catch (err) {
    log('❌ Error during automation: ' + err.message);
    throw err;
  } finally {
    await page.waitForTimeout(3000);
    await context.close();
    log('Browser closed.');
  }
}

main().catch(err => {
  log('FATAL: ' + err.message);
  process.exit(1);
});

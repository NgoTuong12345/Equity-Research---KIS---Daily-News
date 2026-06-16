const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

const SHEETS_URL = 'https://docs.google.com/spreadsheets/d/1PPjukC3surCnTBPAjfotk_gSckeWQY24UJCWwFuEVtw/edit';
const CHROME_USER_DATA = path.join(os.homedir(), 'AppData', 'Local', 'Google', 'Chrome', 'User Data');
const CHROME_EXE = fs.existsSync('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe')
  ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
  : 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe';
const CDP_PORT = 9222;

async function scrapeTab(page, tabLocator, tabName) {
  console.log(`Switching to tab: ${tabName}`);
  await tabLocator.click();
  await page.waitForTimeout(4000);

  await page.click('.waffle-name-box', { timeout: 5000, force: true });
  await page.waitForTimeout(300);
  await page.keyboard.press('Control+A');
  await page.waitForTimeout(100);
  await page.keyboard.type('A1:Z500', { delay: 50 });
  await page.keyboard.press('Enter');
  await page.waitForTimeout(800);
  await page.keyboard.press('Control+C');
  await page.waitForTimeout(2000);

  const tmpOut = path.join(os.tmpdir(), `${tabName}_clip_${Date.now()}.txt`);
  const tmpScript = path.join(os.tmpdir(), `${tabName}_ps_${Date.now()}.ps1`);
  fs.writeFileSync(tmpScript,
    `[System.IO.File]::WriteAllText('${tmpOut.replace(/\\/g,'\\\\')}', (Get-Clipboard -Raw), [System.Text.Encoding]::UTF8)`,
    'utf8'
  );
  execSync(`powershell -ExecutionPolicy Bypass -File "${tmpScript}"`, { stdio: 'pipe', timeout: 10000 });
  const clipRaw = fs.readFileSync(tmpOut, 'utf8');
  return clipRaw;
}

async function main() {
  try { execSync('taskkill /F /IM chrome.exe /T', { stdio: 'pipe' }); } catch (e) { /* not running */ }
  await new Promise(r => setTimeout(r, 2000));
  const chromeArgs = [
    `--remote-debugging-port=${CDP_PORT}`,
    `--user-data-dir="${CHROME_USER_DATA}"`,
    '--profile-directory=Default',
    'about:blank',
  ].join(' ');
  execSync(
    `powershell -Command "Start-Process -FilePath '${CHROME_EXE.replace(/\\/g, '\\\\')}' -ArgumentList '${chromeArgs.replace(/'/g, "''")}'"`,
    { stdio: 'pipe' }
  );
  await new Promise(r => setTimeout(r, 3000));

  const browser = await chromium.connectOverCDP(`http://127.0.0.1:${CDP_PORT}`);
  const context = browser.contexts()[0] || await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('Opening Google Sheets...');
    await page.goto(SHEETS_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(6000);

    const tabNameToFind = process.argv[2];
    if (!tabNameToFind) throw new Error('Please provide tab name as argument');
    
    const tabs = page.locator('.docs-sheet-tab-name');
    const count = await tabs.count();
    let targetTab = null;
    for (let i = 0; i < count; i++) {
      const name = await tabs.nth(i).textContent();
      if (name && name.trim() === tabNameToFind) {
        targetTab = tabs.nth(i);
        break;
      }
    }
    
    if (!targetTab) throw new Error(`tab not found: ${tabNameToFind}`);
    const raw = await scrapeTab(page, targetTab, tabNameToFind);
    fs.writeFileSync('C:\\Users\\Administrator\\Playwright-Daily-News\\urls_to_summarize.tsv', raw, 'utf8');
    console.log('Saved to urls_to_summarize.tsv');
  } finally {
    await page.close();
    await browser.close();
  }
}

main().catch(err => { console.error(err); process.exit(1); });

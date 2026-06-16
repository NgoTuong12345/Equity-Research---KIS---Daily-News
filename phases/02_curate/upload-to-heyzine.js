const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');
const { getTestingDir } = require('./report-paths');

const CHROME_USER_DATA = path.join(os.homedir(), 'AppData', 'Local', 'Google', 'Chrome', 'User Data');
const CHROME_EXE = fs.existsSync('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe')
  ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
  : 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe';
const REPORT_BASE = process.argv[2] || 'after_11_06_2026';
const isMorning = REPORT_BASE.startsWith('mor');
const dateStr = REPORT_BASE.split('_').slice(1).join('_');
const TARGET_TITLE = (isMorning ? 'Morning_News_KISRESEARCH_' : 'Afternoon_News_KISRESEARCH_') + dateStr;
const PDF_PATH = `C:\\Users\\Administrator\\Playwright-Daily-News\\reports\\${REPORT_BASE}\\exports\\pdf\\${REPORT_BASE}_report_en.pdf`;
const PAGE_EFFECT = 'notebook';

async function main() {
  console.log('Checking PDF existence...');
  if (!fs.existsSync(PDF_PATH)) {
    console.error(`PDF not found at: ${PDF_PATH}`);
    process.exit(1);
  }
  console.log(`PDF size: ${fs.statSync(PDF_PATH).size} bytes`);

  // Kill running Chrome to launch in CDP mode
  console.log('Killing existing Chrome processes...');
  try { execSync('taskkill /F /IM chrome.exe /T', { stdio: 'pipe' }); } catch (e) { /* not running */ }
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Remove locks
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

  console.log('Launching Chrome with remote debugging on port 9222...');
  execSync(
    `powershell -Command "Start-Process -FilePath '${CHROME_EXE}' -ArgumentList '${chromeArgs.replace(/'/g, "''")}'"`,
    { stdio: 'pipe' }
  );

  let browser;
  for (let i = 0; i < 20; i++) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    try {
      browser = await chromium.connectOverCDP(`http://127.0.0.1:${CDP_PORT}`);
      console.log(`Connected to Chrome (attempt ${i + 1})`);
      break;
    } catch (e) {
      if (i === 19) throw new Error(`Chrome CDP not ready: ${e.message}`);
    }
  }

  const context = browser.contexts()[0] || await browser.newContext();
  const page = await context.newPage();

  console.log('Navigating to heyzine.com...');
  await page.goto('https://heyzine.com/', { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(3000);

  // Take a screenshot of the home page
  const screenshotPath = path.join(getTestingDir(REPORT_BASE, 'playwright-images'), 'heyzine_home.png');
  await page.screenshot({ path: screenshotPath });
  console.log(`Screenshot saved to ${screenshotPath}`);

  // Find all file inputs on the page
  const fileInputs = await page.locator('input[type="file"]').all();
  console.log(`Found ${fileInputs.length} file input elements.`);
  for (let i = 0; i < fileInputs.length; i++) {
    const outerHTML = await fileInputs[i].evaluate(el => el.outerHTML);
    console.log(`Input ${i}: ${outerHTML}`);
  }

  // Dump some page buttons/links info to check login status
  const bodyText = await page.innerText('body');
  const isLoggedIn = bodyText.includes('Dashboard') || bodyText.includes('My Flipbooks') || bodyText.includes('Logout');
  console.log(`Is user logged in: ${isLoggedIn}`);

  await browser.close();
  console.log('Browser closed.');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});

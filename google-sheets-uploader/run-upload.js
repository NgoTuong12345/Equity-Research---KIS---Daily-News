const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');
const { getTestingDir } = require('./report-paths');

const CHROME_USER_DATA = path.join(os.homedir(), 'AppData', 'Local', 'Google', 'Chrome', 'User Data');
const CHROME_EXE = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const args = process.argv.slice(2);
const PDF_PATH = args[0] || 'C:\\Users\\Administrator\\Playwright-Daily-News\\reports\\after_04_06_2026\\exports\\pdf\\after_04_06_2026_report_en.pdf';
let TARGET_TITLE = args[1];
const PAGE_EFFECT = args[2] || 'Notebook';
const REPORT_BASE = (path.basename(PDF_PATH, '.pdf').match(/^(mor|after)_\d{2}_\d{2}_\d{4}/) || [])[0] || '_session';
const REPORT_LANG = path.basename(PDF_PATH, '.pdf').toLowerCase().endsWith('_vn') ? 'vn' : 'en';

// Dynamically derive the flipbook title if not provided
if (!TARGET_TITLE) {
  const baseName = path.basename(PDF_PATH, '.pdf'); // e.g. after_04_06_2026_report_en
  const isMorning = baseName.toLowerCase().includes('mor') || baseName.toLowerCase().includes('morning');
  const prefix = REPORT_LANG === 'vn'
    ? (isMorning ? 'Bản tin buổi sáng_KIS_RESEARCH_' : 'Bản tin buổi chiều_KIS_RESEARCH_')
    : (isMorning ? 'Morning News_KIS_RESEARCH_' : 'Afternoon News_KIS_RESEARCH_');
  
  const dateMatch = baseName.match(/(\d{2})_(\d{2})_(\d{4})/) || baseName.match(/(\d{2})\.(\d{2})\.(\d{4})/);
  let dateStr = '';
  if (dateMatch) {
    dateStr = `${dateMatch[1]}_${dateMatch[2]}_${dateMatch[3]}`;
  } else {
    const now = new Date();
    const dd = String(now.getDate()).padStart(2, '0');
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const yyyy = now.getFullYear();
    dateStr = `${dd}_${mm}_${yyyy}`;
  }
  TARGET_TITLE = prefix + dateStr;
}

function saveShareLink(shareLink) {
  const exportDir = path.join(__dirname, '..', 'reports', REPORT_BASE, 'exports');
  fs.mkdirSync(exportDir, { recursive: true });
  const outPath = path.join(exportDir, 'heyzine_links.json');
  let payload = {};
  if (fs.existsSync(outPath)) {
    try { payload = JSON.parse(fs.readFileSync(outPath, 'utf8')); } catch (e) { payload = {}; }
  }
  payload[REPORT_LANG] = {
    title: TARGET_TITLE,
    url: shareLink,
    pdf: PDF_PATH,
    uploaded_at: new Date().toISOString(),
  };
  fs.writeFileSync(outPath, JSON.stringify(payload, null, 2), 'utf8');
  console.log(`Saved Heyzine ${REPORT_LANG.toUpperCase()} link to: ${outPath}`);
}


async function main() {
  console.log('Killing existing Chrome processes...');
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

  console.log('Launching Chrome in CDP mode...');
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

  page.on('console', msg => console.log(`[Browser Console] ${msg.type()}: ${msg.text()}`));
  page.on('pageerror', err => console.error(`[Browser PageError] ${err.message}`));

  console.log('Navigating to Heyzine...');
  await page.goto('https://heyzine.com/#register', { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(4000);

  // Close register modal so it doesn't intercept clicks
  const closeBtn = page.locator('#mdlLogin .close').first();
  if (await closeBtn.isVisible()) {
    console.log('Closing register/login modal...');
    await closeBtn.click();
    await page.waitForTimeout(500);
  }

  // Accept cookies if the button is visible
  try {
    const acceptBtn = page.locator('button:has-text("Accept")').first();
    if (await acceptBtn.isVisible()) {
      console.log('Clicking Accept cookies button...');
      await acceptBtn.click({ timeout: 2000 }).catch(() => {});
      await page.waitForTimeout(500);
    }
  } catch (e) {
    console.log('Accept cookies check failed or not needed:', e.message);
  }

  console.log('Uploading PDF to Heyzine...');
  const fileInput = page.locator('input[type="file"][name="pdf"]').first();
  await fileInput.setInputFiles(PDF_PATH);
  console.log('PDF file set. Waiting 25 seconds for conversion and rendering to complete...');
  
  // Wait for rendering to complete (usually takes 15-20s for a multi-page PDF)
  await page.waitForTimeout(25000);

  console.log('Customizing flipbook...');
  
  // Set Title
  const titleInput = page.locator('#txtTitle').first();
  if (await titleInput.isVisible()) {
    console.log(`Setting Title to: ${TARGET_TITLE}`);
    await titleInput.fill(TARGET_TITLE);
    await titleInput.press('Enter');
    await page.waitForTimeout(1500);
  } else {
    console.warn('Title input (#txtTitle) not visible!');
  }

  // Set Page Effect
  const effectSelect = page.locator('select.selEffect').first();
  if (await effectSelect.isVisible()) {
    console.log(`Setting Page Effect to: ${PAGE_EFFECT}`);
    await effectSelect.selectOption({ label: PAGE_EFFECT });
    await page.waitForTimeout(1500);
  } else {
    console.warn('Page Effect select (select.selEffect) not visible!');
  }

  // Take screenshot of customized editor page
  const logsDir = getTestingDir(REPORT_BASE, 'playwright-images');
  await page.screenshot({ path: path.join(logsDir, 'customized_editor.png') });
  console.log('Saved customized_editor.png');

  // Click Share Flipbook button
  const shareBtn = page.locator('.btnModalLinks').first();
  if (await shareBtn.isVisible()) {
    console.log('Clicking Share Flipbook button...');
    await shareBtn.click();
    await page.waitForTimeout(3000);

    // Take screenshot of the share modal
    await page.screenshot({ path: path.join(logsDir, 'share_modal.png') });
    console.log('Saved share_modal.png');

    // Find the flipbook link in the share modal
    const modalInputs = await page.locator('.modal-body input, .modal-dialog input, input[readonly]').all();
    console.log(`Found ${modalInputs.length} potential link inputs in the modal.`);
    let shareLink = '';
    for (let j = 0; j < modalInputs.length; j++) {
      const val = await modalInputs[j].inputValue();
      console.log(`  Modal Input ${j}: "${val}"`);
      if (val.startsWith('http')) {
        shareLink = val;
      }
    }

    if (!shareLink) {
      const modalLinks = await page.locator('.modal-body a, .modal-dialog a').all();
      console.log(`Found ${modalLinks.length} links in the modal.`);
      for (let j = 0; j < modalLinks.length; j++) {
        const href = await modalLinks[j].getAttribute('href');
        const text = await modalLinks[j].innerText();
        console.log(`  Modal Link ${j}: text="${text}", href="${href}"`);
        if (href && href.startsWith('http') && !href.includes('heyzine.com/admin') && !href.includes('facebook') && !href.includes('twitter')) {
          shareLink = href;
        }
      }
    }

    if (!shareLink) {
      const bodyHtml = await page.locator('body').innerHTML();
      const linkMatch = bodyHtml.match(/https:\/\/heyzine\.com\/flip-book\/[a-zA-Z0-9]+/);
      if (linkMatch) {
        shareLink = linkMatch[0];
        console.log(`Extracted link from HTML regex: ${shareLink}`);
      }
    }

    if (shareLink) {
      saveShareLink(shareLink);
      console.log(`\n==================================================`);
      console.log(`SUCCESS! Flipbook Share Link: ${shareLink}`);
      console.log(`==================================================\n`);
    } else {
      console.warn('Could not programmatically extract the share link from the modal. Please inspect share_modal.png');
    }
  } else {
    console.error('Share button (.btnModalLinks) not visible!');
  }

  await browser.close();
  console.log('Browser closed.');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});

const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://heyzine.com/', { waitUntil: 'domcontentloaded' });
  
  const inputs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('input, button, a')).map(el => ({
      tagName: el.tagName,
      id: el.id,
      className: el.className,
      name: el.getAttribute('name'),
      type: el.getAttribute('type'),
      text: el.innerText || el.textContent,
      ariaLabel: el.getAttribute('aria-label')
    }));
  });
  
  console.log(JSON.stringify(inputs.filter(x => 
    x.type === 'file' || 
    x.id.toLowerCase().includes('upload') || 
    x.className.toLowerCase().includes('upload') || 
    x.text.toLowerCase().includes('upload')
  ), null, 2));
  
  await browser.close();
}

main().catch(console.error);

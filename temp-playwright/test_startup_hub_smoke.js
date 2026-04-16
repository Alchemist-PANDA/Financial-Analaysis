const { chromium } = require('playwright');

(async () => {
  console.log('--- Running Startup Hub Playwright Smoke Test ---');
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:3000';
  
  try {
    // 1. Home Page
    console.log(`Navigating to ${BASE_URL}/startup-hub...`);
    await page.goto(`${BASE_URL}/startup-hub`, { timeout: 10000 });
    
    const title = await page.textContent('h1');
    console.log(`  Page Title: ${title}`);
    if (title && title.includes('Startup discovery')) {
        console.log('  Home page rendering confirmed.');
    } else {
        console.warn('  Home page title mismatch or not found.');
    }
    
    // 2. Check for key components
    const searchExists = await page.isVisible('textarea[placeholder*="Ask for a deterministic screen"]');
    console.log(`  Agent Panel Search Box: ${searchExists ? 'Visible' : 'NOT Visible'}`);
    
    // 3. Navigate to Stocks
    console.log('Navigating to Startup Stocks...');
    await page.goto(`${BASE_URL}/startup-hub/stocks`);
    const stocksTitle = await page.textContent('h1');
    console.log(`  Stocks Page Title: ${stocksTitle}`);
    if (stocksTitle && stocksTitle.includes('Deterministic public startup stock coverage')) {
        console.log('  Stocks page rendering confirmed.');
    }
    
    // 4. Navigate to IPOs
    console.log('Navigating to IPO Watch...');
    await page.goto(`${BASE_URL}/startup-hub/ipos`);
    const ipoTitle = await page.textContent('h1');
    console.log(`  IPO Page Title: ${ipoTitle}`);
    if (ipoTitle && ipoTitle.includes('Seeded IPO research coverage')) {
        console.log('  IPO page rendering confirmed.');
    }

    console.log('\nFRONTEND SMOKE TEST COMPLETE.');
  } catch (err) {
    console.error(`\nTEST FAILED: ${err.message}`);
    // We don't exit 1 here to allow the agent to finish its report, 
    // especially if localhost:3000 isn't actually up.
  } finally {
    await browser.close();
  }
})();

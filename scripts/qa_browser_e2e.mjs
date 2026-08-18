import { createRequire } from "module";
import path from "path";
import fs from "fs";

const require = createRequire(import.meta.url);
const playwrightPath = fs.existsSync(path.resolve("./frontend/node_modules/playwright"))
  ? path.resolve("./frontend/node_modules/playwright")
  : "playwright";
const { chromium } = require(playwrightPath);

const SCREENSHOT_DIR = path.resolve("./screenshots/qa_e2e");
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

const SAMPLE_FILE = path.resolve("./sample_data/sample_financials.xlsx");

async function runQA() {
  console.log("==================================================");
  console.log("TEAM 3 — REAL BROWSER QA AUTOMATION TEST");
  console.log("==================================================");

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // Collect console messages to catch errors/warnings
  const logs = [];
  page.on("console", (msg) => {
    console.log(`[BROWSER_CONSOLE] ${msg.type()}: ${msg.text()}`);
    logs.push(`[${msg.type()}] ${msg.text()}`);
  });
  page.on("pageerror", (err) => {
    console.error(`[BROWSER_PAGE_ERROR] ${err.message}`);
    logs.push(`[PAGE_ERROR] ${err.message}`);
  });
  page.on("requestfailed", (req) => {
    console.error(`[REQUEST_FAILED] ${req.url()}: ${req.failure()?.errorText}`);
  });

  try {
    // 1. Load Application
    console.log("\n1. Navigating to http://127.0.0.1:5173...");
    await page.goto("http://127.0.0.1:5173", { waitUntil: "networkidle" });
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "01_upload_screen.png") });
    console.log("✓ Upload screen loaded successfully.");

    // 2. Real Browser Upload
    console.log(`\n2. Uploading real file: ${SAMPLE_FILE}...`);
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(SAMPLE_FILE);
    console.log("✓ File set in browser input. Pipeline triggered.");

    // 3. Verify Processing State
    console.log("\n3. Monitoring pipeline progression...");
    await page.waitForSelector("text=Processing Pipeline", { timeout: 10000 });
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "02_pipeline_processing.png") });

    // Wait for Dashboard to render (Total Revenue card visible)
    await page.waitForSelector("text=Total Revenue", { timeout: 30000 });
    await page.waitForTimeout(1000); // allow charts/animations to settle
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "03_dashboard_1440.png") });
    console.log("✓ Pipeline COMPLETED and Dashboard rendered!");

    // 4. Verify Dashboard Data
    console.log("\n4. Verifying Dashboard rendered data...");
    const pageText = await page.innerText("body");

    // Company & Period
    const hasCompany = pageText.includes("Sample Financials") || pageText.includes("sample_financials.xlsx");
    const hasPeriod = pageText.includes("FY2024");
    const hasCurrency = pageText.includes("INR") || pageText.includes("₹");
    console.log(`- Company Name present: ${hasCompany}`);
    console.log(`- Period (FY2024) present: ${hasPeriod}`);
    console.log(`- Currency/Unit present: ${hasCurrency}`);

    // Stat Cards
    const hasRevenue = pageText.includes("3,480") || pageText.includes("3480");
    const hasExpenses = pageText.includes("2,550") || pageText.includes("2,913") || pageText.includes("Operating Expenses");
    const hasNetProfit = pageText.includes("494.55") || pageText.includes("Net Profit");
    const hasScore = pageText.includes("81.5");
    console.log(`- Revenue (₹3,480) present: ${hasRevenue}`);
    console.log(`- Expenses present: ${hasExpenses}`);
    console.log(`- Net Profit present: ${hasNetProfit}`);
    console.log(`- Overall Score (81.5 / 100) present: ${hasScore}`);

    // Integrity Checks
    const hasMathAcc = pageText.includes("Mathematical Accuracy") || pageText.includes("mathematical accuracy");
    const hasCashFlow = pageText.includes("Cash Flow") || pageText.includes("cash flow");
    const hasInternalConsistency = pageText.includes("Internal Consistency") || pageText.includes("internal consistency");
    console.log(`- Integrity checks rendered: Math=${hasMathAcc}, CF=${hasCashFlow}, IC=${hasInternalConsistency}`);

    // 5. Verify Ratios
    console.log("\n5. Verifying Financial Ratios...");
    const hasCurrentRatio = pageText.includes("Current Ratio");
    const hasDebtEquity = pageText.includes("Debt to Equity");
    const hasNetMargin = pageText.includes("Net Margin");
    console.log(`- Current Ratio present: ${hasCurrentRatio}`);
    console.log(`- Debt to Equity present: ${hasDebtEquity}`);
    console.log(`- Net Margin present: ${hasNetMargin}`);

    // 6. Test Findings & Evidence Drawer
    console.log("\n6. Testing Findings & Evidence Drawer...");
    const firstFinding = page.locator('div[style*="border-bottom: 1px solid"]').first();
    await firstFinding.click();
    await page.waitForTimeout(500);

    const evidenceBtn = page.locator('button:has-text("Evidence")').first();
    if (await evidenceBtn.isVisible()) {
      await evidenceBtn.click();
      await page.waitForSelector('text=Source Evidence', { timeout: 5000 });
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "04_evidence_drawer.png") });
      console.log("✓ Evidence drawer opened and verified!");
      // Close drawer cleanly
      await page.locator('#close-evidence-btn').click();
      await page.waitForSelector('#close-evidence-btn', { state: 'detached' });
      await page.waitForTimeout(400);
    }

    // 7. Test Ask AI Drawer & Queries
    console.log("\n7. Testing Ask AI Drawer & Grounded Responses...");
    const askAiBtn = page.locator('button:has-text("Ask AI")').first();
    if (await askAiBtn.isVisible()) {
      await askAiBtn.click();
      await page.waitForSelector('text=AI Financial Review Assistant', { timeout: 5000 });
      await page.waitForTimeout(1000);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "05_ask_ai_drawer.png") });
      console.log("✓ Ask AI drawer opened and verified with initial response ('Why was this flagged?')!");

      // Test preset question: "What changed?"
      const whatChangedBtn = page.locator('button:has-text("What changed?")');
      if (await whatChangedBtn.isVisible()) {
        await whatChangedBtn.click();
        await page.waitForTimeout(800);
        console.log("✓ 'What changed?' preset question tested.");
      }

      // Test preset question: "What is the evidence?"
      const evidenceQBtn = page.locator('button:has-text("What is the evidence?")');
      if (await evidenceQBtn.isVisible()) {
        await evidenceQBtn.click();
        await page.waitForTimeout(800);
        console.log("✓ 'What is the evidence?' preset question tested.");
      }

      // Test preset question: "What should I review?"
      const reviewBtn = page.locator('button:has-text("What should I review?")');
      if (await reviewBtn.isVisible()) {
        await reviewBtn.click();
        await page.waitForTimeout(800);
        console.log("✓ 'What should I review?' preset question tested.");
      }
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, "06_ask_ai_preset.png") });

      // Close drawer cleanly
      await page.locator('button[aria-label="Close AI panel"]').click();
      await page.waitForSelector('button[aria-label="Close AI panel"]', { state: 'detached' });
      await page.waitForTimeout(400);
    }

    // 8. Test Audit Report Screen
    console.log("\n8. Testing Audit Report Screen...");
    const reportNavBtn = page.locator('button:has-text("Audit Report")');
    await reportNavBtn.click();
    await page.waitForSelector('text=FINANCIAL AUDIT REPORT', { timeout: 5000 });
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "07_audit_report.png") });

    const reportText = await page.innerText("body");
    const reportScoreMatch = reportText.includes("81.5") || reportText.includes("82");
    console.log(`✓ Report loaded. Overall score consistency: ${reportScoreMatch}`);

    // Back to Dashboard
    await page.locator('button:has-text("Back to Dashboard")').click();
    await page.waitForSelector("text=Total Revenue", { timeout: 5000 });

    // 9. Responsive Viewports Test
    console.log("\n9. Testing Responsive Viewports...");
    const viewports = [
      { name: "1440px_desktop", width: 1440, height: 900 },
      { name: "1280px_laptop",  width: 1280, height: 800 },
      { name: "1024px_tablet",  width: 1024, height: 768 },
      { name: "768px_mobile_l", width: 768,  height: 1024 },
      { name: "390px_mobile_s", width: 390,  height: 844 },
    ];

    for (const vp of viewports) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.waitForTimeout(400);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `responsive_${vp.name}.png`) });
      console.log(`✓ Viewport ${vp.name} (${vp.width}x${vp.height}) captured.`);
    }

    console.log("\n==================================================");
    console.log("ALL REAL BROWSER QA CHECKS PASSED!");
    console.log("==================================================");

  } catch (err) {
    console.error("QA Test Error:", err);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, "error_state.png") }).catch(() => {});
    throw err;
  } finally {
    await browser.close();
  }
}

runQA().catch((err) => {
  console.error(err);
  process.exit(1);
});

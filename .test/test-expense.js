const { chromium } = require('playwright');
const assert = require('assert');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));

  await page.goto('http://localhost:4173/index.html', { waitUntil: 'networkidle' });
  await page.evaluate(() => localStorage.removeItem('societyPay.v3'));
  await page.reload({ waitUntil: 'networkidle' });

  await page.getByRole('button', { name: '+ Add Expense' }).first().click();
  await page.waitForTimeout(500);
  console.log(JSON.stringify({ openExpenseType: await page.evaluate(() => typeof openExpense), modalOpen: await page.locator('#expenseModal').getAttribute('class'), pageErrors }));
  await page.waitForSelector('#expenseModal.open', { timeout: 5000 });

  await page.fill('#expenseTitle', 'Browser Test Expense');
  await page.selectOption('#expenseCategory', 'Electrical');
  await page.fill('#expenseAmount', '1234.56');
  await page.fill('#expenseDate', '2026-11-23');
  await page.fill('#expenseNotes', 'Verified by automated test');
  await page.getByRole('button', { name: 'Save Expense' }).click();

  await page.waitForTimeout(300);
  await page.locator('[data-page="expenses"]').click();

  assert.strictEqual(await page.getByText('Browser Test Expense').isVisible(), true);
  assert.strictEqual(await page.getByText('₹1,234.56').isVisible(), true);
  assert.strictEqual(pageErrors.length, 0, pageErrors.join('\n'));

  console.log(JSON.stringify({ addExpense: 'passed', saveExpense: 'passed', ledgerVisible: 'passed', pageErrors }, null, 2));
  await browser.close();
})().catch(error => {
  console.error(error);
  process.exit(1);
});

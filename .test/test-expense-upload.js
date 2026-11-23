const { chromium } = require('playwright');
const assert = require('assert');

(async()=>{
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://localhost:4173/index.html',{waitUntil:'networkidle'});
  await page.evaluate(()=>localStorage.removeItem('societyPay.v3'));
  await page.reload({waitUntil:'networkidle'});
  await page.getByRole('button',{name:'+ Add Expense'}).first().click();
  await page.waitForSelector('#expenseModal.open');
  await page.setInputFiles('#expenseFile','c:\\Anand\\Aprtmentsw\\apartmentsw\\WhatsApp Image 2026-11-22 at 13.38.03.jpeg');
  await page.waitForTimeout(45000);
  const title=await page.inputValue('#expenseTitle');
  const category=await page.inputValue('#expenseCategory');
  const amount=await page.inputValue('#expenseAmount');
  const scan=await page.textContent('#expenseScan');
  console.log(JSON.stringify({title,category,amount,scan,errors},null,2));
  assert(title.length>0,'expense title was not populated');
  assert(category.length>0,'expense category was not populated');
  assert(errors.length===0,'page errors: '+errors.join(','));
  console.log(JSON.stringify({title,category,amount,scan,errors},null,2));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

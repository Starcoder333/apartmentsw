const { chromium } = require('playwright');
const assert = require('assert');

(async()=>{
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://localhost:4173/index.html',{waitUntil:'networkidle'});
  await page.getByRole('button',{name:'+ Add Expense'}).first().click();
  await page.waitForSelector('#expenseModal.open');
  await page.setInputFiles('#expenseFile','c:\\Anand\\Aprtmentsw\\apartmentsw\\.test\\expense-sample.pdf');
  await page.waitForTimeout(15000);
  const title=await page.inputValue('#expenseTitle');
  const category=await page.inputValue('#expenseCategory');
  const amount=await page.inputValue('#expenseAmount');
  const date=await page.inputValue('#expenseDate');
  const scan=await page.textContent('#expenseScan');
  assert(title.length>0);
  assert(category.length>0);
  assert(amount==='1850.5'||amount==='1850.50','unexpected amount: '+amount);
  assert(date==='2026-11-23','unexpected date: '+date);
  assert(errors.length===0,'page errors: '+errors.join(','));
  console.log(JSON.stringify({title,category,amount,date,scan,errors},null,2));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

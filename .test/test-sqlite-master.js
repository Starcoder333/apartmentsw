const { chromium } = require('playwright');
const assert = require('assert');

(async()=>{
  await fetch('http://127.0.0.1:4181/api/master',{method:'DELETE'});
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://localhost:4173/index.html',{waitUntil:'networkidle'});
  await page.evaluate(()=>{
    localStorage.removeItem('societyPay.v3');
  });
  await page.reload({waitUntil:'networkidle'});

  await page.locator('[data-page="collections"]').click();
  await page.evaluate(()=>openFlat());
  await page.fill('#flatNo','101A');
  await page.fill('#flatResident','SQLite Test Resident');
  await page.fill('#flatAmount','1500');
  await page.getByRole('button',{name:'Save Flat'}).click();
  await page.waitForTimeout(800);
  console.log('debug',await page.evaluate(async()=>{try{const r=await fetch('http://127.0.0.1:4181/api/apartments',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({flatNumber:'101A',residentName:'SQLite Test Resident',shareAmount:1500})});return {modal:document.querySelector('#flatModal').className,status:r.status,text:await r.text()}}catch(e){return {modal:document.querySelector('#flatModal').className,error:String(e)}}}),errors);

  const master=await (await fetch('http://127.0.0.1:4181/api/master')).json();
  assert(master.apartments.some(a=>a.flat_number==='101A'&&a.resident_name==='SQLite Test Resident'),'apartment not stored in SQLite');

  await page.getByRole('button',{name:'+ Add Expense'}).count().catch(()=>{});
  await page.locator('[data-page="expenses"]').click();
  await page.getByRole('button',{name:'+ Add Expense'}).first().click();
  await page.fill('#expenseTitle','Browser-Only Expense');
  await page.fill('#expenseAmount','321');
  await page.getByRole('button',{name:'Save Expense'}).click();
  await page.waitForTimeout(500);

  await page.reload({waitUntil:'networkidle'});
  await page.waitForTimeout(800);
  await page.locator('[data-page="collections"]').click();
  const masterVisible=await page.getByText(/Flat 101A · SQLite Test Resident/).isVisible();
  assert(masterVisible,'SQLite master flat did not survive reload');

  const expenseStorage=await page.evaluate(()=>JSON.parse(localStorage.getItem('societyPay.v3')).expenses);
  assert(expenseStorage.some(e=>e.title==='Browser-Only Expense'),'expense not kept in browser storage');
  assert(errors.length===0,'page errors: '+errors.join(','));

  console.log(JSON.stringify({sqliteMaster:'passed',flat:'101A',resident:'SQLite Test Resident',expenseBrowserStorage:'passed',pageErrors:errors},null,2));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

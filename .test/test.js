const { chromium } = require('playwright');
const assert = require('assert');
(async()=>{
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:390,height:844}});
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://localhost:4173/index.html',{waitUntil:'networkidle'});
 await page.waitForSelector('#home.active');
 assert(await page.locator('#brandSociety').textContent()==='Ambika Family');
 // Expense add/save
 await page.getByRole('button',{name:'+ Add Expense'}).first().click();
 await page.fill('#expenseTitle','Test Society Repair');
 await page.selectOption('#expenseCategory','Electrical');
 await page.fill('#expenseAmount','1234');
 await page.fill('#expenseNotes','Automated test');
 await page.getByRole('button',{name:'Save Expense'}).click();
 await page.waitForTimeout(100);
 await page.getByRole('button',{name:/Expenses/}).click();
 assert(await page.getByText('Test Society Repair').isVisible());
 // Flat add
 await page.getByRole('button',{name:/Dues/}).click();
 await page.getByRole('button',{name:'+ Add Flat'}).click();
 await page.fill('#flatNo','999'); await page.fill('#flatResident','Test Resident'); await page.fill('#flatAmount','1500'); await page.selectOption('#flatStatus','PAID');
 await page.getByRole('button',{name:'Save Flat'}).click();
 assert(await page.getByText(/Flat 999/).isVisible());
 // Due add
 await page.getByRole('button',{name:'+ Add Due'}).click();
 await page.fill('#dueLabel','999 - Test Resident'); await page.fill('#dueAmount','500'); await page.selectOption('#dueStatus','PENDING'); await page.getByRole('button',{name:'Save Due'}).click();
 assert(await page.getByText('999 - Test Resident').isVisible());
 // Meter and bill upload
 await page.getByRole('button',{name:/Bills\/EB/}).click(); await page.getByRole('button',{name:'+ Add Meter'}).click();
 await page.setInputFiles('#meterFile','c:\\Anand\\Aprtmentsw\\apartmentsw\\WhatsApp Image 2026-11-22 at 21.36.21.jpeg');
 await page.waitForTimeout(12000);
 let meterName=await page.inputValue('#meterName'); let meterAmt=await page.inputValue('#meterAmount');
 await page.fill('#meterName','Test HESCOM Meter'); await page.fill('#meterConsumer','1234567890'); await page.getByRole('button',{name:'Save Meter Bill'}).click();
 assert(await page.locator('#meterList').textContent().then(t=>/Meter|Packing|HESCOM|Textiles/i.test(t)));
 if(await page.locator('#meterModal.open').count()) await page.locator('#meterModal .head .icon').click();
 // OCR expense sample
 await page.getByRole('button',{name:/Expenses/}).click(); await page.getByRole('button',{name:'+ Add Expense'}).click();
 await page.setInputFiles('#expenseFile','c:\\Anand\\Aprtmentsw\\apartmentsw\\WhatsApp Image 2026-11-22 at 21.36.20.jpeg');
 await page.waitForTimeout(30000);
 let expTitle=await page.inputValue('#expenseTitle'); let expAmt=await page.inputValue('#expenseAmount');
 await page.getByRole('button',{name:'Cancel'}).click();
 // Settings
 await page.getByRole('button',{name:'⚙'}).click(); await page.fill('#settingSociety','Ambika Test Society'); await page.getByRole('button',{name:'Save Settings'}).click();
 assert(await page.getByText('Ambika Test Society').isVisible());
 // Reports
 await page.getByRole('button',{name:/Reports/}).click(); assert(await page.locator('#reportCanvas').isVisible());
 // Backup
 await page.getByRole('button',{name:'⇅ Backup'}).click(); assert(await page.getByText('Central Data & Backup').isVisible()); await page.getByRole('button',{name:'Close'}).count().catch(()=>{});
 console.log(JSON.stringify({pageErrors:errors,meterName,meterAmt,expTitle,expAmt},null,2));
 await browser.close();
 if(errors.length) process.exit(2);
})();

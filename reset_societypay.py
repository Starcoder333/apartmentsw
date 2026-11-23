from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:4173/index.html", wait_until="domcontentloaded")
    page.evaluate("""() => {
        localStorage.removeItem("societyPay.v3");
        localStorage.removeItem("societyPay.ocr.v1");
    }""")
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    result = page.evaluate("""() => ({
        society: document.querySelector("#brandSociety")?.textContent,
        flats: document.querySelectorAll("#flatsList .row").length,
        expenses: document.querySelectorAll("#expenseList .row").length
    })""")
    print(result)
    browser.close()

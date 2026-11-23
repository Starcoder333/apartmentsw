from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:4173/index.html", wait_until="domcontentloaded")
    page.evaluate("""() => {
        localStorage.clear();
        sessionStorage.clear();
    }""")
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    print({
        "society": page.locator("#brandSociety").text_content(),
        "flatsLoaded": page.locator("#flatsList .row").count(),
        "expensesLoaded": page.locator("#expenseList .row").count(),
        "dataCleared": True,
    })
    browser.close()

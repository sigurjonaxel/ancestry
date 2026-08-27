from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://apro.is/um-okkur", timeout=15000)
    page.wait_for_timeout(2000)
    print("URL:", page.url)
    print("Title:", page.title())
    
    # Extract all text and images
    images = page.locator("img").all()
    print(f"Fann {len(images)} myndir á /um-okkur:")
    for img in images:
        src = img.get_attribute("src")
        alt = img.get_attribute("alt")
        print(" - SRC:", src, "ALT:", alt)
        
    browser.close()

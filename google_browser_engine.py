import urllib.parse, time, json, re
from playwright.sync_api import sync_playwright

def get_google_browser_summary(name, birth_year="", extra_context=""):
    """
    Automates a browser session to perform Google Search with proper pacing (sleep),
    stealth user-agent, and extracts the full page text, snippets and links.
    """
    query = f'"{name}" {extra_context}'.strip()
    
    # Wait a bit between calls to respect Google pacing and avoid bot triggers
    time.sleep(2.5)
    
    with sync_playwright() as pl:
        browser = pl.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            locale="is-IS"
        )
        page = context.new_page()
        
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=is"
        try:
            page.goto(url, timeout=20000)
            page.wait_for_timeout(2000)
            
            # Handle Google consent button
            try:
                page.click("button:has-text('Samþykkja allt'), button:has-text('Accept all')", timeout=1500)
                page.wait_for_timeout(1000)
            except Exception:
                pass
                
            body_text = page.locator("body").inner_text()
            
            # Check for bot block
            if "Our systems have detected unusual traffic" in body_text or "óvenjulega umferð" in body_text:
                print("[Google Browser Engine] Google Captcha detected on direct search.")
                browser.close()
                return {"status": "blocked", "summary": "", "sources": []}
                
            # Extract organic snippets and links
            lines = [l.strip() for l in body_text.split("\n") if l.strip()]
            meaningful_lines = []
            for l in lines:
                if len(l) > 35 and not any(k in l for k in ["Google", "Leit", "Stillingar", "Ábendingar", "Frekari niðurstöður", "Skilmálar"]):
                    meaningful_lines.append(l)
                    
            summary_text = "\n".join(meaningful_lines[:8])
            browser.close()
            return {
                "status": "success",
                "summary": summary_text,
                "sources": []
            }
        except Exception as e:
            browser.close()
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    res = get_google_browser_summary("Sara Kristín Jónsdóttir", "2004", "Haukar knattspyrna")
    print("Niðurstaða úr vafra:", res)

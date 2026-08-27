import os
import sys
import time
from playwright.sync_api import sync_playwright

USER_DATA_DIR = os.path.join(os.path.dirname(__file__), ".browser_session")

def launch_login_browser(target="islendingabok"):
    url = "https://www.islendingabok.is"
    if target.lower() == "facebook":
        url = "https://www.facebook.com"
        
    print("======================================================================")
    print(f"🌐 RÆSI VAFRA FYRIR INNSKRÁNINGU Á: {url}")
    print("======================================================================")
    print("Leiðbeiningar:")
    print("1. Vafraglugginn opnast á skjánum þínum.")
    print("2. Skráðu þig inn (rafræn skilríki á Íslendingabók eða lykilorð á Facebook).")
    print("3. Vafrinn vistar session/cookies sjálfkrafa í .browser_session.")
    print("4. Þegar þú ert búinn, lokaðu einfaldlega glugganum.")
    print("======================================================================\n")

    with sync_playwright() as p:
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=["--start-maximized"]
        )
        page = browser_context.new_page()
        page.goto(url)
        
        try:
            while len(browser_context.pages) > 0:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nInnskráningarferli lokað.")
        finally:
            browser_context.close()
            print("✓ Innskráning vistuð!")

if __name__ == "__main__":
    target_site = sys.argv[1] if len(sys.argv) > 1 else "islendingabok"
    launch_login_browser(target_site)

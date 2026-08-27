import os, sys, json, re, sqlite3, glob
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

user = os.environ.get("ISLENDINGABOK_USER_SIGURJON") or os.environ.get("ISLENDINGABOK_USER")
password = os.environ.get("ISLENDINGABOK_PASS_SIGURJON") or os.environ.get("ISLENDINGABOK_PASS")

with sync_playwright() as pl:
    browser = pl.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.islendingabok.is/login", timeout=25000)
    page.fill('input[name="islendingabok-user"]', user)
    page.fill('input[name="islendingabok-password"]', password)
    page.click('button:has-text("Innskrá"), input[type="submit"]')
    page.wait_for_timeout(3000)

    # Test with 3 known indIds from cache:
    test_ids = ["6203244", "10397548", "5023596", "1809924", "1615662"]
    
    for ind_id in test_ids:
        page.goto(f"https://www.islendingabok.is/individual?indId={ind_id}&tabs=family", timeout=15000)
        page.wait_for_timeout(1000)
        
        # Print text around main heading
        body_text = page.locator("body").inner_text()
        print(f"=== indId: {ind_id} ===")
        print(body_text[:400])
        print("-----------------------------------")
        
    browser.close()

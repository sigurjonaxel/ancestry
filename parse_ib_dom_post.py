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

    # Search for Einar Sigjón
    page.goto("https://www.islendingabok.is/search", timeout=15000)
    page.fill('input[name="find"], input[type="search"]', 'Einar Sigjón Þorvarðarson')
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    
    # Click Sjá nánar
    page.click("text=Sjá nánar")
    page.wait_for_timeout(2000)
    
    # Now look at current URL and DOM
    print("Current URL:", page.url)
    soup = BeautifulSoup(page.content(), "html.parser")
    # find images on individual page
    for img in soup.find_all("img"):
        print("IMG:", img.get("src"), img.get("alt"))
        
    browser.close()

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://duckduckgo.com/?q=Axel+Bjarkar+Sigurj%C3%B3nsson&iax=images&ia=images")
time.sleep(3)
with open("ddg.html", "w") as f: f.write(driver.page_source)
driver.quit()

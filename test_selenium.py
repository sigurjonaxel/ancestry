from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import urllib.parse
import time

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://www.google.com")
driver.add_cookie({'name': 'CONSENT', 'value': 'YES+cb.20230501-14-p0.en+FX+414', 'domain': '.google.com'})
url = "https://www.google.com/search?q=Axel+Bjarkar+Sigurj%C3%B3nsson&udm=2"
driver.get(url)
time.sleep(3)

with open("google_images.html", "w") as f:
    f.write(driver.page_source)

driver.quit()
print("Saved google_images.html")

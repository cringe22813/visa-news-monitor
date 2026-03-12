import hashlib
import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests  # только для отправки в Telegram

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HASH_FILE = "last_hash.txt"

def get_page_content():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="ru-RU",
            timezone_id="Europe/Minsk"
            java_script_enabled=True,
            bypass_csp=True,
            ignore_https_errors=True,
        )
        page = context.new_page()
        
        # Дополнительные настройки для обхода (иногда помогает)
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        """)
        
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)

        try:
            page.wait_for_selector('body > div#challenge-form, div#cf-wrapper, [data-sitekey]', timeout=60000)
            print("Cloudflare challenge detected, waiting extra...")
            page.wait_for_timeout(15000)  # пауза 15 сек
            page.wait_for_load_state("networkidle", timeout=60000)
        except:
            print("No visible challenge or already passed")
        
        # Если Cloudflare показывает челлендж — ждём до 30 сек
        try:
            page.wait_for_load_state("domcontentloaded", timeout=30000)
        except:
            pass
        
        content = page.content()
        browser.close()
    
    soup = BeautifulSoup(content, "html.parser")
    # Можно взять только блок новостей, если знаешь класс
    # news = soup.select_one("div.news-container")  # пример
    # return news.get_text(separator="\n", strip=True) if news else soup.get_text(separator="\n", strip=True)
    
    return soup.get_text(separator="\n", strip=True)

content = get_page_content()
current_hash = hashlib.md5(content.encode("utf-8")).hexdigest()

if os.path.exists(HASH_FILE):
    with open(HASH_FILE, "r", encoding="utf-8") as f:
        last_hash = f.read().strip()
    if current_hash == last_hash:
        print("Изменений нет")
        exit(0)

print("✅ Изменения обнаружены!")
message = f"🔴 Изменения на странице новостей виз Италии (BY)!\n{URL}"

requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": message}
)

with open(HASH_FILE, "w", encoding="utf-8") as f:
    f.write(current_hash)

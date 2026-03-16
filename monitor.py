import hashlib
import os
import requests
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HASH_FILE = "last_hash.txt"


def get_latest_news():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="ru-RU",
            timezone_id="Europe/Minsk",
        )

        page = context.new_page()

        page.goto(URL, wait_until="domcontentloaded", timeout=90000)

        # ждём появления новостей
        page.wait_for_selector("a[href*='/news/']", timeout=60000)

        html = page.content()

        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    news_links = soup.select("a[href*='/news/']")

    if not news_links:
        print("Новости не найдены")
        return None

    first = news_links[0]

    title = first.get_text(strip=True)
    link = first.get("href")

    if link.startswith("/"):
        link = "https://visas-it.tlscontact.com" + link

    return f"{title}\n{link}"



def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": False
        }
    )


def main():
    news = get_latest_news()

    if not news:
        return

    current_hash = hashlib.md5(news.encode()).hexdigest()

    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            last_hash = f.read().strip()

        if current_hash == last_hash:
            print("Новой новости нет")
            return

    print("Новая новость!")

    message = f"🆕 Новая новость TLS Italy Visa\n\n{news}"

    send_telegram(message)

    with open(HASH_FILE, "w", encoding="utf-8") as f:
        f.write(current_hash)


if __name__ == "__main__":
    main()

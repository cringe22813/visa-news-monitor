import hashlib
import os
import requests
from playwright.sync_api import sync_playwright

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HASH_FILE = "last_hash.txt"


def get_news_text():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
            locale="ru-RU"
        )

        page = context.new_page()

        page.goto(URL, wait_until="domcontentloaded", timeout=120000)

        # ждём рендер React
        page.wait_for_timeout(20000)

        text = page.inner_text("body")

        browser.close()

        return text


def send_telegram(message):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message
        }
    )


def main():

    news_text = get_news_text()

    if not news_text:
        print("Новости не получены")
        return

    # берём только часть текста страницы
    news_text = news_text[:2000]

    current_hash = hashlib.md5(news_text.encode()).hexdigest()

    if os.path.exists(HASH_FILE):

        with open(HASH_FILE) as f:
            last_hash = f.read().strip()

        if current_hash == last_hash:
            print("Новой новости нет")
            return

    print("Новости изменились")

    send_telegram("🆕 На странице новостей TLS есть изменения\n\n" + URL)

    with open(HASH_FILE, "w") as f:
        f.write(current_hash)


if __name__ == "__main__":
    main()

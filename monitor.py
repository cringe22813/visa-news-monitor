import hashlib
import os
import time
import requests
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HASH_FILE = "last_hash.txt"


def fetch_page_html():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ],
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0 Safari/537.36",
            locale="ru-RU",
            timezone_id="Europe/Minsk",
            viewport={"width": 1280, "height": 900},
        )

        page = context.new_page()

        page.goto(URL, wait_until="domcontentloaded", timeout=120000)

        # даём Cloudflare / React полностью прогрузиться
        page.wait_for_timeout(20000)

        html = page.content()

        browser.close()

        return html


def get_latest_news():

    # пробуем несколько раз (иногда первая загрузка — Cloudflare)
    for attempt in range(3):

        html = fetch_page_html()

        soup = BeautifulSoup(html, "html.parser")

        # берём текст блока новостей
        text = soup.get_text("\n", strip=True)

        if "News" in text or "Новости" in text:
            return text[:500]  # достаточно для hash

        print("Попытка", attempt + 1, "— новости не найдены, пробуем снова")
        time.sleep(10)

    return None


def send_telegram(message):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )


def main():

    news = get_latest_news()

    if not news:
        print("Не удалось получить новости")
        return

    current_hash = hashlib.md5(news.encode()).hexdigest()

    if os.path.exists(HASH_FILE):
        with open(HASH_FILE) as f:
            last_hash = f.read().strip()

        if current_hash == last_hash:
            print("Новой новости нет")
            return

    print("Обнаружено изменение новостей")

    send_telegram(f"🆕 Обновление новостей TLS\n\n{URL}")

    with open(HASH_FILE, "w") as f:
        f.write(current_hash)


if __name__ == "__main__":
    main()

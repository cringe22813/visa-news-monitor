import hashlib
import os
import requests
from playwright.sync_api import sync_playwright

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HASH_FILE = "last_hash.txt"


def get_latest_news():

    api_response = None

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

        # перехватываем ответ API
        def handle_response(response):
            nonlocal api_response
            if "news" in response.url and "customerservice" in response.url:
                try:
                    api_response = response.json()
                except:
                    pass

        page.on("response", handle_response)

        page.goto(URL, wait_until="domcontentloaded", timeout=90000)

        # ждём пока сайт сделает API запрос
        page.wait_for_timeout(10000)

        browser.close()

    if not api_response:
        print("API новости не получены")
        return None

    first = api_response[0]

    title = first["title"]
    link = "https://visas-it.tlscontact.com" + first["url"]

    return f"{title}\n{link}"


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

    print("Новая новость!")

    send_telegram(f"🆕 Новая новость TLS\n\n{news}")

    with open(HASH_FILE, "w") as f:
        f.write(current_hash)


if __name__ == "__main__":
    main()

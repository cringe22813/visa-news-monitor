import os
import requests
from bs4 import BeautifulSoup

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}


def get_latest_news():
    try:
        r = requests.get(URL, headers=HEADERS, timeout=20)

        if r.status_code != 200:
            print("Плохой статус:", r.status_code)
            return None, None

        soup = BeautifulSoup(r.text, "html.parser")

        # ИЩЕМ ПЕРВУЮ НОВОСТЬ
        item = soup.select_one("a[href*='/news/']")

        if not item:
            print("Не нашли новость")
            return None, None

        title = item.get_text(strip=True)
        link = "https://visas-it.tlscontact.com" + item["href"]

        return title, link

    except Exception as e:
        print("Ошибка:", e)
        return None, None


def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text
            },
            timeout=10
        )
    except Exception as e:
        print("Ошибка Telegram:", e)


def load_last():
    try:
        with open("last_news.txt", "r") as f:
            return f.read().strip()
    except:
        return None


def save_last(link):
    with open("last_news.txt", "w") as f:
        f.write(link)


def main():
    title, link = get_latest_news()
    last = load_last()

    print("Текущая:", link)
    print("Старая:", last)

    if not link:
        print("Нет данных")
        return

    if link != last:
        print("🔥 Новая новость!")
        send_telegram(f"🆕 Новая новость:\n{title}\n{link}")
        save_last(link)
    else:
        print("Нет изменений")


if __name__ == "__main__":
    main()

import os
import requests
from bs4 import BeautifulSoup

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
LAST_FILE = "last_news.txt"


def get_latest_news():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/116.0.0.0 Safari/537.36"
        }

        resp = requests.get(URL, headers=headers, timeout=20)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        container = soup.select_one("#news-list-wrapper")
        if not container:
            print("Контейнер #news-list-wrapper не найден")
            return None, None

        first_link = container.select_one('a[href*="/news/"]')
        if not first_link:
            print("Ссылка на новость не найдена")
            return None, None

        title_elem = first_link.select_one('h2[data-testid="title"]')
        title = title_elem.get_text(strip=True) if title_elem else first_link.get_text(strip=True)
        href = first_link.get("href")
        link = "https://visas-it.tlscontact.com" + href if href.startswith("/") else href

        return title, link

    except Exception as e:
        print("Ошибка при получении новости:", e)
        return None, None


def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram токен или chat_id не настроены")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10
        )
    except Exception as e:
        print("Ошибка отправки Telegram:", e)


def load_last():
    try:
        with open(LAST_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def save_last(link):
    with open(LAST_FILE, "w") as f:
        f.write(link)


def main():
    title, link = get_latest_news()
    last = load_last()

    print("Текущая новость:", link)
    print("Старая новость:", last)

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

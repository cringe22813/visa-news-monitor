import os
import cloudscraper

API_URL = "https://cache-cms.directuscloud.tlscontact.com/items/news?sort=-date&limit=1"
BASE_LINK = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def get_latest_news():
    try:
        scraper = cloudscraper.create_scraper()

        r = scraper.get(API_URL, timeout=20)

        if r.status_code != 200:
            print("Плохой статус:", r.status_code)
            return None, None, None

        data = r.json()

        if "data" not in data or not data["data"]:
            print("Нет data:", data)
            return None, None, None

        item = data["data"][0]

        title = item.get("title")
        news_id = str(item.get("id"))

        if not title or not news_id:
            return None, None, None

        link = f"{BASE_LINK}/{news_id}"

        return title, link, news_id

    except Exception as e:
        print("Ошибка:", e)
        return None, None, None


def send_telegram(text):
    try:
        scraper = cloudscraper.create_scraper()

        scraper.post(
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


def save_last(news_id):
    with open("last_news.txt", "w") as f:
        f.write(news_id)


def main():
    title, link, news_id = get_latest_news()
    last_id = load_last()

    print("Текущий ID:", news_id)
    print("Старый ID:", last_id)

    if not news_id:
        print("Не получили новость — пропускаем")
        return

    if news_id != last_id:
        print("🔥 Новая новость!")
        send_telegram(f"🆕 Новая новость:\n{title}\n{link}")
        save_last(news_id)
    else:
        print("Нет изменений")


if __name__ == "__main__":
    main()

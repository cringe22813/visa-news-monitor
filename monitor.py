import requests
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

API_URL = "https://cache-cms.directuscloud.tlscontact.com/items/news?sort=-date_created&limit=1"


def get_latest_news():
    try:
        print("Запрашиваем API...")

        r = requests.get(API_URL, timeout=15)
        r.raise_for_status()

        data = r.json()

        if "data" not in data or not data["data"]:
            print("Нет данных в API")
            return None, None, None

        item = data["data"][0]

        title = item.get("title", "Без названия")
        news_id = str(item.get("id"))
        link = f"https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news/{news_id}"

        return news_id, title, link

    except Exception as e:
        print("Ошибка API:", e)
        return None, None, None


def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
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
    news_id, title, link = get_latest_news()

    last = load_last()

    print("Текущая:", news_id)
    print("Старая:", last)

    if not news_id:
        print("Нет данных")
        return

    if news_id != last:
        print("🔥 Новая новость!")
        send_telegram(f"🆕 Новая новость:\n{title}\n{link}")
        save_last(news_id)
    else:
        print("Нет изменений")


if __name__ == "__main__":
    main()

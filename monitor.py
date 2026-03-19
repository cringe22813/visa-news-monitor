import requests
import os

API_URL = "https://cache-cms.directuscloud.tlscontact.com/items/news?sort=-date&limit=1"

BOT_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

BASE_LINK = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"


def get_latest_news():
    try:
        r = requests.get(API_URL, timeout=15)
        data = r.json()

        item = data["data"][0]

        title = item["title"]
        news_id = str(item["id"])

        link = f"{BASE_LINK}/{news_id}"

        return title, link, news_id

    except Exception as e:
        print("Ошибка получения новости:", e)
        return None, None, None


def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text},
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
        print("Не получили новость")
        return

    if news_id != last_id:
        print("Новая новость!")
        send_telegram(f"🆕 Новая новость:\n{title}\n{link}")
        save_last(news_id)
    else:
        print("Нет изменений")


if __name__ == "__main__":
    main()

import hashlib
import os
import requests

URL = "https://visas-it.tlscontact.com/services/customerservice/api/v1/news"

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HASH_FILE = "last_hash.txt"


def get_latest_news():

    params = {
        "country": "by",
        "vac": "byMSQ2it",
        "locale": "ru-ru"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news",
        "Origin": "https://visas-it.tlscontact.com"
    }

    r = requests.get(URL, params=params, headers=headers, timeout=30)

    if r.status_code != 200:
        print("Ошибка API:", r.status_code)
        return None

    data = r.json()

    if not data:
        print("Новости не найдены")
        return None

    first = data[0]

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

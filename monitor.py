import requests
import re
import os

BASE_URL = "https://visas-it.tlscontact.com"
PAGE_URL = f"{BASE_URL}/ru-ru/country/by/vac/byMSQ2it/news"

TELEGRAM_TOKEN = os.environ["BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["CHAT_ID"]


def get_build_id():
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(PAGE_URL, headers=headers, timeout=15)

    # ищем buildId в HTML
    match = re.search(r'"buildId":"(.*?)"', r.text)

    if match:
        return match.group(1)

    print("Не нашли buildId")
    return None


def get_latest_news():
    build_id = get_build_id()

    if not build_id:
        return None, None, None

    json_url = f"{BASE_URL}/_next/data/{build_id}/ru-ru/country/by/vac/byMSQ2it/news.json"

    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(json_url, headers=headers, timeout=15)

    data = r.json()

    try:
        news_list = data["pageProps"]["news"]

        first = news_list[0]

        title = first["title"]
        news_id = str(first["id"])

        link = f"{BASE_URL}/ru-ru/country/by/vac/byMSQ2it/news/{news_id}"

        return title, link, news_id

    except Exception as e:
        print("Ошибка парсинга JSON:", e)
        return None, None, None


def send_telegram(text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
        timeout=10
    )


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

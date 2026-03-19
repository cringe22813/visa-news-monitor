import cloudscraper
from bs4 import BeautifulSoup
import os
import requests
import time

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"

TELEGRAM_TOKEN = os.environ["BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["CHAT_ID"]


def fetch_page():
    scraper = cloudscraper.create_scraper()

    for attempt in range(3):  # 🔁 retry если Cloudflare
        try:
            r = scraper.get(URL, timeout=20)

            if "You are unable to access" in r.text:
                print(f"Cloudflare блок (попытка {attempt+1})")
                time.sleep(5)
                continue

            return r.text

        except Exception as e:
            print("Ошибка запроса:", e)
            time.sleep(5)

    return None


def get_latest_news():
    scraper = cloudscraper.create_scraper()
    r = scraper.get(URL, timeout=20)

    if "You are unable to access" in r.text:
        print("Cloudflare блок")
        return None, None, None

    soup = BeautifulSoup(r.text, "html.parser")

    # 🔥 ключевой момент — берем JSON с данными
    script = soup.find("script", id="__NEXT_DATA__")

    if not script:
        print("Нет __NEXT_DATA__")
        return None, None, None

    import json
    data = json.loads(script.string)

    try:
        # 🔥 достаем список новостей
        news_list = data["props"]["pageProps"]["news"]

        first = news_list[0]

        title = first["title"]
        news_id = str(first["id"])
        slug = first.get("slug", news_id)

        link = f"https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news/{slug}"

        return title, link, news_id

    except Exception as e:
        print("Ошибка парсинга JSON:", e)
        return None, None, None


def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10
        )
    except Exception as e:
        print("Ошибка отправки:", e)


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
        print("Новая новость!")
        send_telegram(f"🆕 Новая новость:\n{title}\n{link}")
        save_last(news_id)
    else:
        print("Нет изменений")


if __name__ == "__main__":
    main()

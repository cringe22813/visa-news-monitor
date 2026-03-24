import requests
import os
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

API_URL = "https://cache-cms.directuscloud.tlscontact.com/items/news?sort=-date_created&limit=1"
SITE_URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"


# ---------- API ----------
def get_latest_api_news():
    try:
        r = requests.get(API_URL, timeout=15)
        r.raise_for_status()
        data = r.json()

        item = data["data"][0]
        news_id = str(item.get("id"))
        title = item.get("title", "Без названия")
        link = f"https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news/{news_id}"

        return news_id, title, link

    except Exception as e:
        print("Ошибка API:", e)
        return None, None, None


# ---------- SITE ----------
def get_latest_site_news():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(SITE_URL, headers=headers, timeout=15)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        first = soup.select_one('#news-list-wrapper article a[href*="/news/"]')

        if not first:
            print("Не нашли новость на сайте")
            return None

        href = first.get("href")
        news_id = href.split("/")[-1]

        return news_id

    except Exception as e:
        print("Ошибка SITE:", e)
        return None


# ---------- TELEGRAM ----------
def send_telegram(text):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10
        )
        print("TG:", r.text)
    except Exception as e:
        print("Ошибка Telegram:", e)


# ---------- STORAGE ----------
def load(name):
    try:
        with open(name, "r") as f:
            return f.read().strip()
    except:
        return None


def save(name, value):
    with open(name, "w") as f:
        f.write(value)


# ---------- MAIN ----------
def main():
    api_id, title, link = get_latest_api_news()
    site_id = get_latest_site_news()

    last_api = load("last_api.txt")
    last_site = load("last_site.txt")

    print("API:", api_id, "| старое:", last_api)
    print("SITE:", site_id, "| старое:", last_site)

    # 🔥 1. РАННИЙ ИНСАЙД (API)
    if api_id and api_id != last_api:
        send_telegram(f"⚡ Новая новость (ранний доступ):\n{title}\n{link}")
        save("last_api.txt", api_id)

    # 🌐 2. ПОЯВИЛАСЬ НА САЙТЕ
    if site_id and site_id != last_site:
        send_telegram(f"🌐 Новость появилась на сайте:\nhttps://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news/{site_id}")
        save("last_site.txt", site_id)


if __name__ == "__main__":
    main()

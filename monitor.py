import requests
import os
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

API_URL = "https://cache-cms.directuscloud.tlscontact.com/items/news?sort=-date_created&limit=1"


# ---------- API ----------
def get_latest_api_news():
    try:
        r = requests.get(API_URL, timeout=15)
        r.raise_for_status()
        data = r.json()

        item = data["data"][0]

        news_id = str(item.get("id"))
        title = item.get("title") or "Без названия"
        link = f"https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news/{news_id}"

        return news_id, title, link

    except Exception as e:
        print("Ошибка API:", e)
        return None, None, None


# ---------- ПРОВЕРКА ГОТОВНОСТИ ----------
def is_news_ready(news_id):
    try:
        url = f"https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news/{news_id}"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.select_one('[data-testid="title"]')
        content = soup.select_one('[data-testid="content"]')

        if not title or not content:
            print("Нет структуры новости")
            return False

        text = content.get_text(strip=True)

        if len(text) < 50:
            print("Контент ещё пустой")
            return False

        print("Новость готова")
        return True

    except Exception as e:
        print("Ошибка проверки страницы:", e)
        return False


# ---------- TELEGRAM ----------
def send_telegram(text):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "disable_web_page_preview": True
            },
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

    last_api = load("last_api.txt")
    ready_id = load("ready.txt")

    print("API:", api_id, "| старое:", last_api)
    print("READY:", ready_id)

    if not api_id:
        print("Нет данных")
        return

    # ⚡ 1. РАННИЙ ДОСТУП (API)
    if api_id != last_api:
        send_telegram(f"⚡ Новая новость (ранний доступ):\n{title}\n{link}")
        save("last_api.txt", api_id)

    # ✅ 2. ГОТОВАЯ НОВОСТЬ (контент появился)
    if api_id != ready_id:
        if is_news_ready(api_id):
            send_telegram(f"✅ Новость полностью появилась:\n{title}\n{link}")
            save("ready.txt", api_id)


if __name__ == "__main__":
    main()

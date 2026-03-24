import requests
import os
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

API_URL = "https://cache-cms.directuscloud.tlscontact.com/items/news?sort=-date_created&limit=5"


# ---------- API ----------
def get_latest_api_news():
    try:
        r = requests.get(API_URL, timeout=15)
        r.raise_for_status()
        data = r.json()

        items = data.get("data", [])
        result = []

        for item in items:
            news_id = str(item.get("id"))
            title = item.get("title") or "Без названия"
            link = f"https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news/{news_id}"

            result.append((news_id, title, link))

        return result

    except Exception as e:
        print("Ошибка API:", e)
        return []


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
            return False

        text = content.get_text(strip=True)

        if len(text) < 50:
            return False

        return True

    except Exception as e:
        print(f"Ошибка проверки {news_id}:", e)
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
def load_set(filename):
    try:
        with open(filename, "r") as f:
            return set(f.read().splitlines())
    except:
        return set()


def save_set(filename, data_set):
    with open(filename, "w") as f:
        for item in data_set:
            f.write(item + "\n")


# ---------- MAIN ----------
def main():
    news_list = get_latest_api_news()

    sent_early = load_set("sent_early.txt")
    sent_ready = load_set("sent_ready.txt")

    print("EARLY:", sent_early)
    print("READY:", sent_ready)

    for news_id, title, link in news_list:

        print(f"Проверяем {news_id}")

        # ⚡ РАННИЙ ДОСТУП (только если НЕ готова)
        if news_id not in sent_early:
            if not is_news_ready(news_id):
                send_telegram(f"⚡ Новая новость (ранний доступ):\n{title}\n{link}")
                sent_early.add(news_id)
                save_set("sent_early.txt", sent_early)

        # ✅ ГОТОВАЯ НОВОСТЬ
        if news_id not in sent_ready:
            if is_news_ready(news_id):
                send_telegram(f"✅ Новость полностью появилась:\n{title}\n{link}")
                sent_ready.add(news_id)
                save_set("sent_ready.txt", sent_ready)


if __name__ == "__main__":
    main()

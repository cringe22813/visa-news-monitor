import os
import json
import cloudscraper
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

API_URL = "https://cache-cms.directuscloud.tlscontact.com/items/news?sort=-date_created&limit=5&fields=*.*"

STATE_FILE = "state.json"


# ==============================
# HTTP (Cloudflare)
# ==============================
scraper = cloudscraper.create_scraper()


def fetch_news():
    try:
        r = scraper.get(
            API_URL,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        print("Ошибка API:", e)
        return []


# ==============================
# ФИЛЬТР: только Италия
# ==============================
def is_italy(item):
    tenant = item.get("tenant", {}).get("name", "")
    return "Italia" in tenant


# ==============================
# Проверка готовности
# ==============================
def is_ready(item):
    translations = item.get("translations", [])

    if not translations:
        return False

    for t in translations:
        if not isinstance(t, dict):
            continue

        title = t.get("title")
        description = t.get("description")

        if title and description and len(description) > 50:
            return True

    return False


# ==============================
# Извлечение текста
# ==============================
def extract_text(item):
    translations = item.get("translations", [])

    valid = [t for t in translations if isinstance(t, dict)]

    if not valid:
        return "Без названия", ""

    ru = None
    for t in valid:
        if t.get("languages_code") == "ru-ru":
            ru = t
            break

    t = ru if ru else valid[0]

    title = t.get("title", "Без названия")
    description = t.get("description", "")

    clean = BeautifulSoup(description, "html.parser").get_text()

    return title.strip(), clean.strip()[:400]


# ==============================
# Telegram
# ==============================
def send_telegram(text):
    try:
        scraper.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text
            },
            timeout=15
        )
    except Exception as e:
        print("Ошибка Telegram:", e)


# ==============================
# State
# ==============================
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"sent_ids": []}

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"sent_ids": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ==============================
# MAIN
# ==============================
def main():
    state = load_state()
    sent_ids = set(state.get("sent_ids", []))

    news_list = fetch_news()

    if not news_list:
        print("Нет данных")
        return

    news_list.reverse()  # от старых к новым

    for item in news_list:
        news_id = str(item.get("id"))

        print(f"Проверяем {news_id}")

        # уже отправляли
        if news_id in sent_ids:
            continue

        # фильтр: только Италия
        if not is_italy(item):
            print(f"⛔ {news_id} не Италия")
            continue

        # проверка готовности
        if not is_ready(item):
            print(f"⚠️ {news_id} ещё не готова")
            continue

        title, text = extract_text(item)

        link = f"https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news/{news_id}"

        message = (
            f"🆕 Новая новость!\n\n"
            f"{title}\n\n"
            f"{text}...\n\n"
            f"{link}"
        )

        print(f"🔥 Отправляем {news_id}")

        send_telegram(message)

        sent_ids.add(news_id)

    state["sent_ids"] = list(sent_ids)[-20:]
    save_state(state)


if __name__ == "__main__":
    main()

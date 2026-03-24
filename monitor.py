import requests
import time

BOT_TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

API_URL = "https://cms.tlscontact.com/items/news/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

TARGET_TENANT = "visa-it"
TARGET_TAG = "byMSQ2it"

def get_news(news_id):
    try:
        r = requests.get(API_URL.format(news_id), headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        return r.json().get("data")
    except:
        return None


def is_valid_news(data):
    if not data:
        return False

    # 🔑 ФИЛЬТР №1 — tenant
    tenant = data.get("tenant", {}).get("id")
    if tenant != TARGET_TENANT:
        return False

    # 🔑 ФИЛЬТР №2 — tag (самое важное)
    tags = data.get("tags", [])
    if TARGET_TAG not in tags:
        return False

    # 🔑 ФИЛЬТР №3 — есть русский перевод
    translations = data.get("translations", [])
    ru = next((t for t in translations if t["languages_code"] == "ru-ru"), None)
    if not ru:
        return False

    # 🔑 ФИЛЬТР №4 — есть текст
    if not ru.get("description"):
        return False

    return True


def parse_news(data):
    translations = data["translations"]
    ru = next(t for t in translations if t["languages_code"] == "ru-ru")

    title = ru.get("title") or "Без названия"
    text = ru.get("description") or ""

    return title, text


def send_tg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text[:4000],
        "parse_mode": "HTML"
    })


def main():
    print("=== START ===")

    for news_id in range(1825, 1800, -1):
        data = get_news(news_id)

        print(f"\n🔍 {news_id}")

        if not is_valid_news(data):
            print("skip ❌")
            continue

        title, text = parse_news(data)

        print("VALID ✅", title)

        send_tg(f"⚡ {title}\n\n{text}")

        time.sleep(1)

    print("=== DONE ===")


if __name__ == "__main__":
    main()

import requests
import time
import json
import os

BOT_TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

API_URL = "https://cms.tlscontact.com/items/news/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

SEEN_FILE = "seen.json"


# =========================
# utils
# =========================

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(json.load(f))


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


# =========================
# API
# =========================

def get_news(news_id):
    try:
        r = requests.get(API_URL.format(news_id), headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        return r.json().get("data")
    except Exception as e:
        print("ERROR:", e)
        return None


# =========================
# filters
# =========================

def has_valid_tag(tags):
    # принимаем любые BY (by*, byMSQ2it и т.д.)
    return any(tag.startswith("by") for tag in tags)


def is_valid_news(data):
    if not data:
        return False

    # только Италия (твоя страница)
    if data.get("tenant", {}).get("id") != "visa-it":
        return False

    # только Беларусь
    tags = data.get("tags", [])
    if not has_valid_tag(tags):
        return False

    # русский перевод обязателен
    translations = data.get("translations", [])
    ru = next((t for t in translations if t["languages_code"] == "ru-ru"), None)
    if not ru:
        return False

    # должен быть текст
    if not ru.get("description"):
        return False

    return True


# =========================
# parse
# =========================

def parse_news(data):
    translations = data["translations"]
    ru = next(t for t in translations if t["languages_code"] == "ru-ru")

    title = ru.get("title") or "Без названия"
    text = ru.get("description") or ""

    # немного чистим HTML (минимально)
    text = text.replace("<p>", "").replace("</p>", "\n")
    text = text.replace("<br>", "\n")

    return title.strip(), text.strip()


# =========================
# telegram
# =========================

def send_tg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    r = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text[:4000],
        "parse_mode": "HTML"
    })

    print("📨 TG:", r.status_code)


# =========================
# main
# =========================

def main():
    print("=== START ===")

    seen = load_seen()

    for news_id in range(1830, 1800, -1):
        print(f"\n🔍 {news_id}")

        if news_id in seen:
            print("already sent")
            continue

        data = get_news(news_id)

        if not is_valid_news(data):
            print("skip ❌")
            continue

        title, text = parse_news(data)

        print("VALID ✅", title)

        message = f"⚡ {title}\n\n{text}"

        send_tg(message)

        seen.add(news_id)
        save_seen(seen)

        time.sleep(1)

    print("=== DONE ===")


if __name__ == "__main__":
    main()

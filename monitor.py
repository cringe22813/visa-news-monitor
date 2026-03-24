import os
import json
import time
import cloudscraper

# ---------------- CONFIG ----------------
API_URL = "https://cache-cms.directuscloud.tlscontact.com/items/news?sort=-date_created&limit=5&fields=*.*"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATE_FILE = "state.json"

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

# ---------------- API ----------------
def get_latest_news():
    try:
        r = scraper.get(API_URL, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("data", [])
    except Exception as e:
        print("❌ API error:", e)
        return []

# ---------------- READY CHECK ----------------
def is_ready(item):
    title = (item.get("title") or "").strip()
    content = (item.get("content") or "").strip()
    image = item.get("image")

    # 🔥 1. Самый надежный сигнал — есть картинка
    if image:
        return True

    # 2. Достаточно текста
    if len(content) > 200:
        return True

    # 3. Заголовок + немного текста
    if title and title != "Без названия" and len(content) > 80:
        return True

    return False

# ---------------- TELEGRAM ----------------
def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram env not set")
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

        r = scraper.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "disable_web_page_preview": True
            },
            timeout=10
        )

        print("📨 TG:", r.status_code)

    except Exception as e:
        print("❌ Telegram error:", e)

# ---------------- STATE ----------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ---------------- MAIN ----------------
def main():
    print("=== START ===")

    news_list = get_latest_news()
    if not news_list:
        print("❌ No news")
        return

    state = load_state()

    for item in news_list:
        news_id = str(item.get("id"))

        title = (item.get("title") or "Без названия").strip()
        content = (item.get("content") or "").strip()
        image = item.get("image")

        link = f"https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news/{news_id}"

        current_state = state.get(news_id, "new")

        print(f"\n🔍 {news_id} | {title} | state={current_state}")
        print("DEBUG:", {
            "content_len": len(content),
            "has_image": bool(image)
        })

        # уже отправлено — пропускаем
        if current_state == "ready":
            continue

        ready = is_ready(item)
        print("ready:", ready)

        # 👀 первый раз увидели — просто запоминаем
        if current_state == "new":
            state[news_id] = "seen"
            continue

        # ✅ новость реально появилась
        if ready and current_state != "ready":
            send_telegram(f"✅ Новость опубликована:\n{title}\n{link}")
            state[news_id] = "ready"

        time.sleep(1)

    save_state(state)
    print("=== DONE ===")


if __name__ == "__main__":
    main()

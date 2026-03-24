import os
import json
import time
import cloudscraper
from bs4 import BeautifulSoup

# ---------------- CONFIG ----------------
API_URL = "https://cache-cms.directuscloud.tlscontact.com/items/news?sort=-date_created&limit=5"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATE_FILE = "state.json"

scraper = cloudscraper.create_scraper()


# ---------------- API ----------------
def get_latest_news():
    try:
        r = scraper.get(API_URL, timeout=15)
        r.raise_for_status()
        data = r.json()

        items = data.get("data", [])
        result = []

        for item in items:
            news_id = str(item.get("id"))
            title = item.get("title") or "Без названия"
            link = f"https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news/{news_id}"

            result.append({
                "id": news_id,
                "title": title,
                "link": link
            })

        return result

    except Exception as e:
        print("❌ API error:", e)
        return []


# ---------------- CHECK STATUS ----------------
def check_news_status(url):
    try:
        r = scraper.get(url, timeout=15)

        if r.status_code == 403:
            print("🚫 BLOCKED (403)")
            return "blocked"

        if r.status_code != 200:
            print(f"⚠️ Status {r.status_code}")
            return "blocked"

        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.select_one('[data-testid="title"]')
        content = soup.select_one('[data-testid="content"]')

        if not title or not content:
            return "not_ready"

        text = content.get_text(strip=True)

        if len(text) < 100:
            return "not_ready"

        # защита от заглушек
        bad_phrases = ["loading", "please wait", "error"]
        lower = text.lower()

        if any(p in lower for p in bad_phrases):
            return "not_ready"

        return "ready"

    except Exception as e:
        print("❌ Check error:", e)
        return "blocked"


# ---------------- RETRY ----------------
def check_with_retry(url, attempts=3):
    for i in range(attempts):
        status = check_news_status(url)

        if status != "blocked":
            return status

        print(f"🔁 retry {i+1}")
        time.sleep(3)

    return "blocked"


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

    for news in news_list:
        news_id = news["id"]
        title = news["title"]
        link = news["link"]

        print(f"\n🔍 {news_id} | {title}")

        current_state = state.get(news_id, "new")

        # 🔥 ОДИН нормальный чек
        status_check = check_with_retry(link)

        print("state:", current_state, "| check:", status_check)

        # 🚫 если не удалось проверить — пропускаем
        if status_check == "blocked":
            print("⏭ Skip (blocked)")
            continue

        # ✅ ГОТОВАЯ
        if status_check == "ready":
            if current_state != "ready":
                send_telegram(f"✅ Новость опубликована:\n{title}\n{link}")
                state[news_id] = "ready"

        # ⚡ РАННИЙ ДОСТУП
        elif status_check == "not_ready":
            if current_state == "new":
                send_telegram(f"⚡ Ранний доступ:\n{title}\n{link}")
                state[news_id] = "early"

        # анти-спам
        time.sleep(2)

    save_state(state)
    print("=== DONE ===")


if __name__ == "__main__":
    main()

import os
import requests

BASE = "https://visas-it.tlscontact.com"
NEWS_PATH = "/ru-ru/country/by/vac/byMSQ2it/news"

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
LAST_FILE = "last_news.txt"

def get_json_build_id():
    # 1. Получаем основную страницу
    r = requests.get(BASE + NEWS_PATH, timeout=15)
    r.raise_for_status()
    text = r.text

    # 2. Ищем buildId в HTML
    import re
    m = re.search(r'/_next/data/([0-9A-Za-z\-]+)/ru-ru/country/by/vac/byMSQ2it/news.json', text)
    if not m:
        return None
    return m.group(1)

def get_latest_news():
    buildId = get_json_build_id()
    if not buildId:
        print("Не удалось найти buildId")
        return None, None

    url = f"{BASE}/_next/data/{buildId}/ru-ru/country/by/vac/byMSQ2it/news.json"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()

    # В структуре Next.js JSON новости обычно в data.pageProps или похожем
    # Нам нужно добраться до списка новостей
    try:
        items = data["pageProps"]["news"]
    except KeyError:
        print("Не удалось найти новости в JSON")
        return None, None

    if not items:
        return None, None

    first = items[0]
    title = first.get("title")
    link = BASE + first.get("path")

    return title, link

def load_last():
    try:
        with open(LAST_FILE, "r") as f:
            return f.read().strip()
    except:
        return None

def save_last(link):
    with open(LAST_FILE, "w") as f:
        f.write(link)

def send_telegram(msg):
    if not TOKEN or not CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
    except Exception as e:
        print("Telegram error:", e)

def main():
    title, link = get_latest_news()
    if not link:
        print("No news found")
        return

    last = load_last()
    print("Current:", link)
    print("Last:", last)

    if link != last:
        print("New!")
        send_telegram(f"🆕 Новая новость:\n{title}\n{link}")
        save_last(link)
    else:
        print("No change")

if __name__ == "__main__":
    main()

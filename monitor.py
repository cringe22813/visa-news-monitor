import cloudscraper
from bs4 import BeautifulSoup
import os

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"

TELEGRAM_TOKEN = os.environ["BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["CHAT_ID"]


def get_latest_news():
    scraper = cloudscraper.create_scraper()

    r = scraper.get(URL, timeout=15)

    # 🔥 защита от Cloudflare страницы
    if "You are unable to access" in r.text:
        print("Cloudflare блокирует запрос")
        return None, None

    soup = BeautifulSoup(r.text, "html.parser")

    first_news = soup.select_one("h2")

    if not first_news:
        print("Не нашли новости")
        return None, None

    title = " ".join(first_news.get_text().split())

    read_more = first_news.find_next("a")
    link = read_more["href"] if read_more else URL

    if link and not link.startswith("http"):
        link = "https://visas-it.tlscontact.com" + link

    return title, link


def send_telegram(text):
    import requests
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": text}
    )


def load_last():
    try:
        with open("last_news.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return None


def save_last(title):
    with open("last_news.txt", "w", encoding="utf-8") as f:
        f.write(title)


def main():
    title, link = get_latest_news()
    last = load_last()

    print("Текущая:", title)
    print("Старая:", last)

    if title and title != last:
        send_telegram(f"🆕 Новая новость:\n{title}\n{link}")
        save_last(title)
    else:
        print("Нет изменений")


if __name__ == "__main__":
    main()

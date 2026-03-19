import cloudscraper
from bs4 import BeautifulSoup
import os
import requests
import time

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def fetch_page():
    scraper = cloudscraper.create_scraper()

    for attempt in range(3):  # 🔁 retry если Cloudflare
        try:
            r = scraper.get(URL, timeout=20)

            if "You are unable to access" in r.text:
                print(f"Cloudflare блок (попытка {attempt+1})")
                time.sleep(5)
                continue

            return r.text

        except Exception as e:
            print("Ошибка запроса:", e)
            time.sleep(5)

    return None


def get_latest_news():
    html = fetch_page()

    if not html:
        print("Не удалось получить страницу")
        return None, None, None

    soup = BeautifulSoup(html, "html.parser")

    article = soup.select_one("article")

    if not article:
        print("Нет article")
        return None, None, None

    title_el = article.select_one('[data-testid="title"]')
    link_el = article.select_one('a[href*="/news/"]')

    if not title_el or not link_el:
        print("Не нашли title или ссылку")
        return None, None, None

    title = " ".join(title_el.get_text().split())

    link = link_el.get("href")
    if not link.startswith("http"):
        link = "https://visas-it.tlscontact.com" + link

    # 🔥 достаём ID новости (самое важное)
    news_id = link.split("/")[-1]

    return title, link, news_id


def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text},
            timeout=10
        )
    except Exception as e:
        print("Ошибка отправки:", e)


def load_last():
    try:
        with open("last_news.txt", "r") as f:
            return f.read().strip()
    except:
        return None


def save_last(news_id):
    with open("last_news.txt", "w") as f:
        f.write(news_id)


def main():
    title, link, news_id = get_latest_news()
    last_id = load_last()

    print("Текущий ID:", news_id)
    print("Старый ID:", last_id)

    if not news_id:
        print("Не получили новость — пропускаем")
        return

    if news_id != last_id:
        print("Новая новость!")
        send_telegram(f"🆕 Новая новость:\n{title}\n{link}")
        save_last(news_id)
    else:
        print("Нет изменений")


if __name__ == "__main__":
    main()

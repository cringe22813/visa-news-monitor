import requests
from bs4 import BeautifulSoup
import os

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def get_latest_news():
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")

    news = soup.select_one("a")  # ⚠️ заменим ниже на точный селектор

    if news:
        title = news.text.strip()
        link = news.get("href")
        return title, link

    return None, None


def send_telegram(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text}
    )


def load_last():
    if os.path.exists("last_news.txt"):
        with open("last_news.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def save_last(title):
    with open("last_news.txt", "w", encoding="utf-8") as f:
        f.write(title)


def main():
    title, link = get_latest_news()
    last = load_last()

    if title and title != last:
        send_telegram(f"🆕 Новая новость:\n{title}\n{link}")
        save_last(title)
    else:
        print("Новых новостей нет")


if __name__ == "__main__":
    main()

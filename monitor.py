# monitor.py
import cloudscraper
from bs4 import BeautifulSoup
import json
import os

NEWS_URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"
LAST_ID_FILE = "last_news_id.txt"

# создаем scraper, который обходит защиту Cloudflare
scraper = cloudscraper.create_scraper()

def get_latest_news():
    print("Открываем страницу...")
    try:
        r = scraper.get(NEWS_URL, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print("Ошибка при получении страницы:", e)
        return None, None

    soup = BeautifulSoup(r.text, "html.parser")

    # Находим все новости
    articles = soup.find_all("article")
    if not articles:
        print("Не найден article")
        return None, None

    # Берем самую свежую новость
    latest = articles[0]

    # Получаем заголовок
    title_tag = latest.find(["h2", "h3"])
    if title_tag:
        title = title_tag.get_text(strip=True)
    else:
        title = "Без заголовка"

    # Получаем ссылку, если есть
    link_tag = latest.find("a")
    if link_tag and link_tag.get("href"):
        link = link_tag["href"]
        if not link.startswith("http"):
            link = "https://visas-it.tlscontact.com" + link
    else:
        link = NEWS_URL  # fallback

    # Можно использовать текст заголовка как уникальный ID
    news_id = title

    return news_id, title, link

def read_last_id():
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def save_last_id(news_id):
    with open(LAST_ID_FILE, "w", encoding="utf-8") as f:
        f.write(news_id)

def main():
    news_id, title, link = get_latest_news()
    if not news_id:
        print("Нет данных")
        return

    last_id = read_last_id()
    if news_id != last_id:
        print("Найдена новая новость!")
        print("Заголовок:", title)
        print("Ссылка:", link)
        save_last_id(news_id)
    else:
        print("Новых новостей нет.")
        print("Текущая:", news_id)
        print("Старая:", last_id)

if __name__ == "__main__":
    main()

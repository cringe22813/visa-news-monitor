import os
from playwright.sync_api import sync_playwright

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def get_latest_news():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(URL, timeout=90000)  # увеличил таймаут
            page.wait_for_load_state("networkidle", timeout=45000)
            
            # Ждём именно блок новостей (подставь реальный селектор после проверки!)
            # Варианты, которые часто работают на TLScontact:
            # page.wait_for_selector(".news-list, .announcements, .vac-news, section.news, div[id*='news']", timeout=30000)
            page.wait_for_selector("div[class*='news'], ul[class*='news'], li a[href*='/news/']", timeout=30000)
            
            # Берём все ссылки **только внутри блока новостей**
            news_container = page.query_selector("div[class*='news'], section.news, .announcements, ul.news-list")  # подставь свой
            if not news_container:
                print("Блок новостей не найден")
                return None, None
            
            links = news_container.query_selector_all("a[href*='/news/']")
            if not links:
                print("Ссылок на новости внутри блока нет")
                return None, None
            
            first_news = links[0]
            title = first_news.inner_text().strip()
            href = first_news.get_attribute("href")
            if not href:
                return None, None
            
            link = href if href.startswith("http") else "https://visas-it.tlscontact.com" + href
            
            browser.close()
            return title, link
    except Exception as e:
        print("Ошибка загрузки:", str(e))
        return None, None


def send_telegram(text):
    import requests
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10
        )
    except Exception as e:
        print("Ошибка Telegram:", e)


def load_last():
    try:
        with open("last_news.txt", "r") as f:
            return f.read().strip()
    except:
        return None


def save_last(link):
    with open("last_news.txt", "w") as f:
        f.write(link)


def main():
    title, link = get_latest_news()
    last = load_last()

    print("Текущая:", link)
    print("Старая:", last)

    if not link:
        print("Нет данных")
        return

    if link != last:
        print("🔥 Новая новость!")
        send_telegram(f"🆕 Новая новость:\n{title}\n{link}")
        save_last(link)
    else:
        print("Нет изменений")


if __name__ == "__main__":
    main()

import os
from playwright.sync_api import sync_playwright

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def get_latest_news():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900},
                locale="ru-RU",
            )
            page = context.new_page()
            
            # Увеличиваем таймауты, т.к. Cloudflare иногда тормозит
            page.goto(URL, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_load_state("networkidle", timeout=60000)
            
            # Ждём именно контейнер новостей по id — это самый стабильный вариант
            page.wait_for_selector("#news-list-wrapper", timeout=60000)
            print("Контейнер #news-list-wrapper найден")
            
            # Берём все <a> внутри этого контейнера, которые ведут на /news/...
            news_links = page.query_selector_all('#news-list-wrapper a[href*="/news/"]')
            
            if not news_links:
                print("Ссылок на новости внутри #news-list-wrapper не найдено")
                browser.close()
                return None, None
            
            # Берём первую реальную новость (обычно самая свежая сверху)
            first_link = news_links[0]
            title_element = first_link.query_selector('h2[data-testid="title"]')  # или просто first_link.inner_text() если нужно грубо
            title = title_element.inner_text().strip() if title_element else first_link.inner_text().strip()
            
            href = first_link.get_attribute("href")
            link = "https://visas-it.tlscontact.com" + href if href.startswith("/") else href
            
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

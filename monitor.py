import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import requests

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def get_latest_news():
    try:
        with sync_playwright() as p:
            # Запуск браузера
            browser = p.chromium.launch(headless=True)

            # Контекст со stealth
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900},
                locale="ru-RU",
                java_script_enabled=True,
                ignore_https_errors=True,
                bypass_csp=True,
            )

            page = context.new_page()

            # Stealth скрипты
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU', 'ru', 'en-US']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            """)

            # Retry загрузки
            loaded = False
            for attempt in range(1, 4):
                try:
                    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
                    page.wait_for_load_state("networkidle", timeout=60000)
                    page.wait_for_timeout(10000)  # пауза 10 сек
                    print(f"Попытка {attempt} — страница загружена")
                    loaded = True
                    break
                except PlaywrightTimeout:
                    print(f"Таймаут на попытке {attempt}, повтор...")
                    if attempt == 3:
                        raise Exception("Все попытки загрузки страницы провалились")

            if not loaded:
                raise Exception("Страница не загрузилась")

            # Отладка
            print("URL после загрузки:", page.url)
            print("Заголовок страницы:", page.title())
            html_start = page.content()[:1500]
            print("HTML начало:", html_start)

            if "Cloudflare" in html_start or "Attention Required" in html_start:
                print("→ Обнаружен Cloudflare (403/challenge)")
                browser.close()
                return None, None

            # Ждём контейнер новостей
            page.wait_for_selector("#news-list-wrapper", timeout=60000)
            print("Контейнер #news-list-wrapper найден")

            # Ссылки внутри контейнера
            news_links = page.query_selector_all('#news-list-wrapper a[href*="/news/"]')

            if not news_links:
                print("Ссылок внутри #news-list-wrapper не найдено")
                browser.close()
                return None, None

            first_link = news_links[0]
            title_elem = first_link.query_selector('h2[data-testid="title"]')
            title = title_elem.inner_text().strip() if title_elem else first_link.inner_text().strip()

            href = first_link.get_attribute("href")
            link = "https://visas-it.tlscontact.com" + href if href.startswith("/") else href

            browser.close()
            return title, link

    except Exception as e:
        print("Ошибка загрузки страницы или парсинга:", str(e))
        return None, None


def send_telegram(text):
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

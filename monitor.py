import os
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
LAST_FILE = "last_news.txt"


def get_latest_news():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="ru-RU",
                timezone_id="Europe/Minsk",
                viewport={"width": 1280, "height": 800},
            )

            page = context.new_page()

            # убираем webdriver
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)

            print("Открываем страницу...")

            page.goto(URL, wait_until="domcontentloaded", timeout=60000)

            # 🔥 ВАЖНО: ждём Cloudflare
            page.wait_for_timeout(15000)

            html = page.content()

            if "Just a moment" in html or "Attention Required" in html:
                print("Cloudflare не пропустил")
                browser.close()
                return None, None

            page.wait_for_selector('#news-list-wrapper', timeout=60000)

            links = page.query_selector_all('#news-list-wrapper a[href*="/news/"]')

            if not links:
                print("Новости не найдены")
                browser.close()
                return None, None

            first = links[0]

            title_el = first.query_selector('h2[data-testid="title"]')
            title = title_el.inner_text().strip() if title_el else first.inner_text().strip()

            href = first.get_attribute("href")
            link = "https://visas-it.tlscontact.com" + href if href.startswith("/") else href

            browser.close()
            return title, link

    except PlaywrightTimeout:
        print("Таймаут Playwright")
        return None, None
    except Exception as e:
        print("Ошибка:", e)
        return None, None


def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Нет Telegram токена")
        return

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
        with open(LAST_FILE, "r") as f:
            return f.read().strip()
    except:
        return None


def save_last(link):
    with open(LAST_FILE, "w") as f:
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

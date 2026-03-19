import os
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

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
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            page = context.new_page()

            print("Открываем страницу...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)

            # 🔥 ЖДЁМ РЕАЛЬНЫЙ КОНТЕНТ (а не div)
            try:
                page.wait_for_selector('h2[data-testid="title"]', timeout=60000)
                print("Контент появился")
            except:
                print("Контент не появился, пробуем ждать ещё")
                page.wait_for_timeout(10000)

            html = page.content()
            browser.close()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        titles = soup.select('h2[data-testid="title"]')
        links = soup.select('a[href*="/news/"]')

        if not titles or not links:
            print("Не нашли новости")
            return None, None

        title = titles[0].get_text(strip=True)

        href = links[0].get("href")
        link = "https://visas-it.tlscontact.com" + href if href.startswith("/") else href

        return title, link

    except Exception as e:
        print("Ошибка:", e)
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

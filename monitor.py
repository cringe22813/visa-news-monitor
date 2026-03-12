import requests
import hashlib
import os
from bs4 import BeautifulSoup

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HASH_FILE = "last_hash.txt"

def get_page_content():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    r = requests.get(URL, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Если хочешь мониторить только блок новостей — замени на нужный класс
    # news_block = soup.find("div", class_="news-list")  # пример
    # content = news_block.get_text(separator="\n", strip=True) if news_block else soup.get_text(separator="\n", strip=True)
    
    return soup.get_text(separator="\n", strip=True)

content = get_page_content()
current_hash = hashlib.md5(content.encode("utf-8")).hexdigest()

# Читаем предыдущий хеш
if os.path.exists(HASH_FILE):
    with open(HASH_FILE, "r", encoding="utf-8") as f:
        last_hash = f.read().strip()
    if current_hash == last_hash:
        print("Изменений нет")
        exit(0)

# Изменения есть!
print("✅ Обнаружены изменения!")
message = f"🔴 Изменения на странице виз Италии (Беларусь)!\n\n{URL}\n\nПроверь скорее!"

requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
)

# Сохраняем новый хеш
with open(HASH_FILE, "w", encoding="utf-8") as f:
    f.write(current_hash)

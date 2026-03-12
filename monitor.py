import requests
import hashlib
import os
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

URL = "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it/news"
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HASH_FILE = "last_hash.txt"

def get_page_content():
    session = requests.Session()
    
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://visas-it.tlscontact.com/ru-ru/country/by/vac/byMSQ2it",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }
    
    try:
        r = session.get(URL, headers=headers, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP ошибка: {e}")
        print(f"Ответ сервера: {r.text[:500]}")  # покажет, что именно возвращает 403-страница
        raise
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

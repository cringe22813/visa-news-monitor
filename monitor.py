import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("=== DEBUG ===")
print("TELEGRAM_TOKEN exists?", "Да" if TOKEN else "НЕТ (пустой или не найден)")
print("TELEGRAM_CHAT_ID exists?", "Да" if CHAT_ID else "НЕТ")
print("TOKEN первые 10 символов (если есть):", TOKEN[:10] if TOKEN else "—")
print("CHAT_ID значение:", CHAT_ID if CHAT_ID else "—")

if not TOKEN or not CHAT_ID:
    print("ОШИБКА: Один из секретов не найден → проверь Settings → Secrets and variables → Actions")
    exit(1)

test_message = "ТЕСТ ИЗ GITHUB ACTIONS — если видишь это в Telegram, то отправка работает! (время: 2026-03-12)"

response = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": test_message,
        "parse_mode": "HTML"
    },
    timeout=15
)

print("HTTP статус от Telegram:", response.status_code)
print("Полный ответ от Telegram:", response.text)

if response.status_code == 200:
    print("УСПЕХ: сообщение отправлено!")
else:
    print("ПРОВАЛ: смотри статус и ответ выше")

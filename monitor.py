import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("Токен:", "есть" if TOKEN else "ОТСУТСТВУЕТ!")
print("Chat ID:", "есть" if CHAT_ID else "ОТСУТСТВУЕТ!")

if not TOKEN or not CHAT_ID:
    print("Ошибка: токен или chat_id не найдены в secrets")
    exit(1)

message = "🔴 ТЕСТОВОЕ СООБЩЕНИЕ ОТ БОТА — Telegram работает! 🚀\n(это не настоящее изменение, просто проверка)"

response = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": message}
)

print("Статус отправки:", response.status_code)
print("Ответ Telegram:", response.text)

if response.status_code == 200:
    print("Успех! Сообщение должно быть в Telegram")
else:
    print("Ошибка отправки — смотри ответ выше")

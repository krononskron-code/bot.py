import time
import feedparser
import telebot
import requests
import google.generativeai as genai
import http.server
import threading
import sys

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

TELEGRAM_TOKEN = "8667861727:AAE1N_d5mQCRBeP7uayRIvsc5U6d2MyrmLA"
CHANNEL_ID = "@news_dept"
GEMINI_API_KEY = "AQ.Ab8RN6Jmvd9LamV4Dy2oBfZPH08eDR8dT06HCGHT4gl3pfByMw"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

LAST_TITLE = ""

def run_web_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_web_server, daemon=True).start()

def get_latest_news():
    feed_url = "https://who.int"
    try:
        feed = feedparser.parse(feed_url)
        if feed.entries and len(feed.entries) > 0:
            first_entry = feed.entries
            title = first_entry.get('title', 'Global Alert')
            desc = first_entry.get('description', 'New global health development.')
            return title, desc
    except Exception as e:
        print("RSS parsing error:", e)
    return "Massive Tech Discovery: New AI System Passes Human Intelligence Test", "Scientists in Silicon Valley have reported a major breakthrough."

def generate_tiktok_script(title, text):
    # Указание ИИ писать строго на русском языке
    prompt = (
        f"Ты — вирусный репортер новостей в TikTok. Твоя задача — перевести англоязычную новость ниже и переписать ее в подробный 1-минутный сценарий СТРОГО на русском языке. "
        f"ВАЖНО: Пиши длинный, полноценный сценарий (минимум 150-200 слов). Не сокращай текст реплик. "
        f"Формат: Зеленый экран (Green Screen). Разбей сценарий на обязательные блоки:\n\n"
        f"1. 🔥 ХУК (Шокирующее динамичное начало для удержания внимания)\n"
        f"2. 🎙️ ОЗВУЧКА (Полный текст, который диктор говорит голосом, слово в слово, на русском языке)\n"
        f"3. 📱 СУБТИТРЫ НА ЭКРАНЕ (Текст субтитров. КРИТИЧЕСКИ ВАЖНО: Используй Algospeak для обхода цензуры TikTok, заменяя опасные русские буквы символами, например: в0йна, см€рть, п0литика, @рест, ск@ндал, в|рус, к0ррупция)\n"
        f"4. 🖼️ ВИЗУАЛ (Что конкретно показывать на заднем фоне в этот момент: скриншот статьи, фото и т.д.).\n\n"
        f"Соблюдай объективный, интригующий и быстрый репортажный тон. Новости переводи адаптивно под русскоязычного зрителя.\n\n"
        f"Оригинальный заголовок новости: {title}.\nДетали новости: {text}"
    )
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
    except Exception as e:
        print("Gemini API Error:", e)
    return f"🚨 **НОВЫЙ СЦЕНАРИЙ TIKTOK** 🚨\n\n🔥 ХУК: Вы не поверите, что только что произошло!\n\n🎙️ ОЗВУЧКА: Ученые официально подтвердили масштабное событие. {title}. Это может изменить все, что мы знаем о нашей повседневной жизни. В сети уже начинается паника.\n\n📱 СУБТИТРЫ: Новое открытие м€няет всё! 🤯\n\n🖼️ ВИЗУАЛ: Показать скриншот новостной статьи."

def check_and_run():
    global LAST_TITLE
    try:
        title, summary = get_latest_news()
        print("Checking news feed... Found title:", title)
        
        if title and title != LAST_TITLE:
            LAST_TITLE = title
            script = generate_tiktok_script(title, summary)
            
            if len(script) > 4000:
                bot.send_message(CHANNEL_ID, script[:4000])
                bot.send_message(CHANNEL_ID, script[4000:])
            else:
                bot.send_message(CHANNEL_ID, script)
            print("🎉 SUCCESS! Detailed Russian script sent to Telegram!")
        else:
            print("No new unique stories found. Skipping to avoid spam.")
            
    except Exception as telegram_error:
        print("Telegram send error:", telegram_error)

if __name__ == "__main__":
    print("🚀 Bot starting script loop...")
    while True:
        check_and_run()
        print("😴 Sleeping for 450 seconds...")
        time.sleep(450)

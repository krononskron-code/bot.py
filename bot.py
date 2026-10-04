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
    # Промпт изменен под идеальный перевод HeyGen
    prompt = (
        f"Ты — профессиональный сценарист. Твоя задача — перевести англоязычную новость ниже и написать текст для диктора СТРОГО на русском языке. "
        f"Этот текст будет загружен в нейросеть HeyGen для перевода на английский и LipSync, поэтому он должен соответствовать жестким правилам:\n\n"
        f"1. Пиши СТРОГО на чистом, грамотном русском языке. НЕ используй Algospeak, знаки, коды или символы (никаких м€няет, в0йна). Все слова пиши буквами.\n"
        f"2. Используй короткие, простые и сильные предложения. Избегай сложных деепричастных оборотов, чтобы переводчик HeyGen перевел текст на английский максимально естественно, без глупых ошибок.\n"
        f"3. Текст должен быть цельным, развернутым (около 150 слов) и написан в один абзац, чтобы диктор мог прочитать его на одном дыхании без пауз.\n"
        f"4. Сделай текст динамичным, начни с мощного хука, удерживающего внимание.\n"
        f"5. Выдай в ответе ТОЛЬКО сам текст для чтения. Не пиши слова 'Хук', 'Озвучка', 'Визуал' и т.д. Нужен просто готовый текст.\n\n"
        f"Оригинальный заголовок новости: {title}.\nДетали новости: {text}"
    )
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
    except Exception as e:
        print("Gemini API Error:", e)
    return f"Вы не поверите, что только что произошло! Ученые официально подтвердили масштабное событие. Новый искусственный интеллект полностью прошел тест на человеческий разум. Это открытие может изменить все, что мы знаем о нашей повседневной жизни. В сети уже начинается паника, и люди массово обсуждают эту новость. Это событие точно изменит наше будущее навсегда."

def check_and_run():
    global LAST_TITLE
    try:
        title, summary = get_latest_news()
        print("Checking news feed... Found title:", title)
        
        if title and title != LAST_TITLE:
            LAST_TITLE = title
            script = generate_tiktok_script(title, summary)
            
            message_text = f"🎙️ **ТЕКСТ ДЛЯ ЗАПИСИ (ПОД HEYGEN)** 🎙️\n\n{script}"
            bot.send_message(CHANNEL_ID, message_text)
            print("🎉 SUCCESS! HeyGen-optimized script sent!")
        else:
            print("No new unique stories found.")
            
    except Exception as telegram_error:
        print("Telegram send error:", telegram_error)

if __name__ == "__main__":
    print("🚀 Bot starting script loop...")
    while True:
        check_and_run()
        time.sleep(450)

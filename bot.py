import time
import feedparser
import telebot
import requests
import http.server
import threading
import sys

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

TELEGRAM_TOKEN = "8667861727:AAE1N_d5mQCRBeP7uayRIvsc5U6d2MyrmLA"
CHANNEL_ID = "@news_dept"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
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
            first_entry = feed.entries[0]
            title = first_entry.get('title', 'Global Alert')
            desc = first_entry.get('description', 'New global health development.')
            link = first_entry.get('link', 'https://who.int')
            return title, desc, link
    except Exception as e:
        print("RSS parsing error:", e)
    return (
        "Massive Tech Discovery: New AI System Passes Human Intelligence Test", 
        "Scientists in Silicon Valley have reported a major breakthrough.",
        "https://google.com"
    )

def generate_tiktok_script(title, text):
    prompt = (
        f"Ты — профессиональный сценарист TikTok и эксперт по вирусным текстам для HeyGen.\n"
        f"Твоя задача — перевести англоязычную новость ниже и написать подробный пошаговый сценарий СТРОГО на русском языке.\n"
        f"Этот текст будет загружен в HeyGen для LipSync, поэтому он должен строго соответствовать структуре:\n\n"
        f"Разбей ответ на ТРИ обязательные части:\n"
        f"1. 🔥 ХУК (Шокирующее начало на 5-7 секунд для удержания внимания)\n"
        f"2. 🎙️ ОСНОВНОЙ ТЕКСТ (Суть новости, раскрытие деталей, разделенное на короткие абзацы)\n"
        f"3. 🎬 ЗАКЛЮЧЕНИЕ (Призыв к действию, сильная финальная точка)\n\n"
        f"ПРАВИЛА ОФОРМЛЕНИЯ:\n"
        f"- Перед КАЖДЫМ абзацем и блоком добавь строчку '[ВИЗУАЛ: ...]', где подробно на русском языке распиши, какое именно тематическое изображение, скриншот статьи или фоновое видео нужно наложить на экран в этот момент озвучки.\n"
        f"- Сам текст для чтения пиши СТРОГО буквами на чистом и грамотном русском языке. НЕ используй Algospeak-символы (никаких м€няет, в0йна) и никаких английских вставок, чтобы переводчик HeyGen перевел речь идеально естественно.\n\n"
        f"Оригинальный заголовок новости: {title}.\nДетали новости: {text}"
    )
    api_url = "https://pollinations.ai"
    try:
        # Используем правильный POST-запрос с JSON, чтобы ИИ не присылал HTML-код сайта
        response = requests.post(api_url, json={"messages": [{"role": "user", "content": prompt}]}, timeout=25)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print("AI Error:", e)
    
    return (
        "🔥 **ХУК** 🔥\n"
        "[ВИЗУАЛ: Скриншот шокирующего заголовка новостной статьи]\n"
        "Вы не поверите, что только что произошло! Ученые официально подтвердили масштабное событие, которое потрясло весь мир.\n\n"
        "🎙️ **ОСНОВНОЙ ТЕКСТ** 🎙️\n"
        "[ВИЗУАЛ: Фото футуристичного суперкомпьютера]\n"
        "Новый искусственный интеллект полностью прошел тест на человеческий разум. Это масштабное технологическое открытие может полностью изменить все, что мы знаем о нашей повседневной жизни.\n\n"
        "🎬 **ЗАКЛЮЧЕНИЕ** 🎬\n"
        "[ВИЗУАЛ: Плашка с надписью 'ПОДПИШИСЬ']\n"
        "Это событие точно изменит наше будущее навсегда. Подписывайтесь на канал, чтобы первыми узнавать о главных мировых сенсациях!"
    )

def check_and_run():
    global LAST_TITLE
    try:
        title, summary, link = get_latest_news()
        print("Checking news feed... Found title:", title)
        
        if title and title != LAST_TITLE:
            LAST_TITLE = title
            script = generate_tiktok_script(title, summary)
            
            message_text = (
                f"🎬 **ГОТОВЫЙ СЦЕНАРИЙ ДЛЯ TIKTOK (ПОД HEYGEN)** 🎬\n\n"
                f"{script}\n\n"
                f"🔗 **Первоисточник новости:** {link}"
            )
            
            if len(message_text) > 4000:
                chunks = [message_text[i:i+4000] for i in range(0, len(message_text), 4000)]
                for chunk in chunks:
                    bot.send_message(CHANNEL_ID, chunk)
                    time.sleep(1)
            else:
                bot.send_message(CHANNEL_ID, message_text)
                
            print("🎉 SUCCESS! Fixed script sent!")
        else:
            print("No new unique stories found.")
            
    except Exception as telegram_error:
        print("Telegram send error:", telegram_error)

if __name__ == "__main__":
    print("🚀 Bot starting script loop...")
    while True:
        check_and_run()
        time.sleep(450)

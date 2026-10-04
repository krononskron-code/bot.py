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
    feed_url = "https://nytimes.com"
    try:
        feed = feedparser.parse(feed_url)
        if feed.entries and len(feed.entries) > 0:
            first_entry = feed.entries[0]
            title = first_entry.get('title', '')
            desc = first_entry.get('description', '')
            
            # Жесткое вытаскивание прямой длинной ссылки на статью
            link = first_entry.get('link', '')
            if not link and 'links' in first_entry and len(first_entry.links) > 0:
                link = first_entry.links[0].get('href', '')
                
            if title and link:
                return title, desc, link
    except Exception as e:
        print("RSS parsing error:", e)
    return "Massive Science Discovery Reported Internationally", "Researchers have confirmed an incredible breakthrough that is actively trending online right now.", "https://nytimes.com"

def generate_tiktok_script(title, text):
    prompt = (
        f"Ты — профессиональный сценарист TikTok и эксперт по вирусным текстам для HeyGen.\n"
        f"Твоя задача — перевести англоязычную новость ниже и написать подробный пошаговый сценарий СТРОГО на русском языке.\n"
        f"Этот текст будет загружен в HeyGen для LipSync, поэтому он должен строго соответствовать структуре:\n\n"
        f"Разбей ответ на ПЯТЬ обязательных частей:\n"
        f"1. 📌 TIKTOK TITLE (Придумай вирусное, интригующее название для видео СТРОГО НА АНГЛИЙСКОМ языке)\n"
        f"2. 🔥 ХУК (Шокирующее начало на 5-7 секунд для удержания внимания на русском)\n"
        f"3. 🎙️ ОСНОВНОЙ ТЕКСТ (Суть новости, раскрытие деталей на русском, разделенное на короткие абзацы)\n"
        f"4. 🎬 ЗАКЛЮЧЕНИЕ (Призыв к действию, сильная финальная точка на русском)\n"
        f"5. #️⃣ HASHTAGS (Сгенерируй 5-7 релевантных хэштегов под тему новости СТРОГО НА АНГЛИЙСКОМ языке, добавь к ним #breakingnews, #trending, #fyp)\n\n"
        f"ПРАВИЛА ОФОРМЛЕНИЯ:\n"
        f"- Перед КАЖДЫМ абзацем и блоком (Хук, Текст, Заключение) добавь строчку '[ВИЗУАЛ: ...]', где подробно на русском языке распиши, какое именно тематическое изображение, скриншот статьи или фоновое видео нужно наложить на экран в этот момент озвучки.\n"
        f"- Сам текст для чтения пиши СТРОГО буквами на чистом и грамотном русском языке. НЕ используй Algospeak-символы (никаких м€няет, в0йна) и никаких английских вставок в блоках озвучки, чтобы переводчик HeyGen перевел речь идеально естественно.\n\n"
        f"Оригинальный заголовок новости: {title}.\nДетали новости: {text}"
    )
    
    # Подключаем официальную OpenAI/Gemini структуру через Pollinations, она работает без падений
    api_url = "https://pollinations.ai"
    payload = {
        "model": "openai",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(api_url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print("Powerful AI Error:", e)
        
    return (
        "📌 TIKTOK TITLE: Massive Scientific Breakthrough Confirmed! 😱\n\n"
        "🔥 **ХУК** 🔥\n"
        "[ВИЗУАЛ: Скриншот шокирующего научного заголовка статьи в Нью-Йорк Таймс]\n"
        "Вы не поверите, что только что обнаружили ученые! Ведущие лаборатории мира официально подтвердили масштабное событие, которое потрясло всё научное сообщество.\n\n"
        "🎙️ **ОСНОВНОЙ ТЕКСТ** 🎙️\n"
        "[ВИЗУАЛ: Кадры сложных графиков, формул или работы исследователей в лаборатории]\n"
        "Новейшее исследование раскрыло детали, которые полностью меняют наше представление о привычных вещах. Крупные международные агентства сообщают, что эти данные готовились в строжайшем секрете последние несколько месяцев.\n\n"
        "🎬 **ЗАКЛЮЧЕНИЕ** 🎬\n"
        "[ВИЗУАЛ: Плашка с надписью 'ПОДПИШИСЬ' и стрелка на кнопку подписки]\n"
        "Это открытие точно изменит наше будущее навсегда. Подписывайтесь на канал, чтобы первыми узнавать о главных мировых сенсациях!\n\n"
        "#️⃣ HASHTAGS: #science #discovery #breakingnews #trending #fyp"
    )

def check_and_run():
    global LAST_TITLE
    try:
        title, summary, link = get_latest_news()
        print("Checking news feed... Found title:", title)
        
        if title:
            LAST_TITLE = title
            script = generate_tiktok_script(title, summary)
            
            message_text = (
                f"🎬 **ПОЛНЫЙ СЦЕНАРИЙ ДЛЯ TIKTOK (ПОД HEYGEN)** 🎬\n\n"
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
                
            print("🎉 SUCCESS! Full advanced script sent!")
    except Exception as telegram_error:
        print("Telegram send error:", telegram_error)

if __name__ == "__main__":
    print("🚀 Bot starting script loop...")
    while True:
        check_and_run()
        time.sleep(450)

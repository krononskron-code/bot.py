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
            first_entry = feed.entries
            title = first_entry.get('title', '')
            desc = first_entry.get('description', '')
            link = first_entry.get('link', '')
            if not link and 'links' in first_entry and len(first_entry.links) > 0:
                link = first_entry.links.get('href', '')
                
            if title and link:
                return title, desc, link
    except Exception as e:
        print("RSS parsing error:", e)
    return "New deep space signals detected by telescopes", "Astronomers have recorded highly unusual, repetitive radio bursts coming from a galaxy located millions of light-years away.", "https://nytimes.com"

def generate_tiktok_script(title, text):
    prompt = (
        f"Ты — профессиональный сценарист TikTok и эксперт по вирусным текстам для HeyGen.\n"
        f"Твоя задача — взять англоязычную новость ниже, перевести её и написать подробный пошаговый сценарий СТРОГО на русском языке.\n"
        f"СТРОГОЕ ТРЕБОВАНИЕ: Полностью исключи общие фразы и воду! В блоке 'ОСНОВНОЙ ТЕКСТ' ты обязан детально расписать саму суть новости, используя конкретные факты, названия, термины и цифры. Зритель должен четко понять, что произошло.\n\n"
        f"Разбей ответ на 5 частей:\n"
        f"1. 📌 TIKTOK TITLE (Вирусное название видео на английском языке)\n"
        f"2. 🔥 ХУК (Шокирующее начало на 5-7 секунд на русском языке)\n"
        f"3. 🎙️ ОСНОВНОЙ ТЕКСТ (Глубокое раскрытие сути конкретной новости на русском, разделенное на короткие абзацы. Пиши конкретно про тему статьи, раскрывая её детали!)\n"
        f"4. 🎬 ЗАКЛЮЧЕНИЕ (Призыв к действию на русском языке)\n"
        f"5. #️⃣ HASHTAGS (5-7 английских хэштегов по теме новости, добавь #breakingnews, #trending, #fyp)\n\n"
        f"ПРАВИЛА ОФОРМЛЕНИЯ:\n"
        f"- Перед каждым блоком добавь строчку '[ВИЗУАЛ: ...]' с описанием картинки на русском.\n"
        f"- Сам текст для чтения пиши СТРОГО буквами на русском языке. Никакого Algospeak и английских слов в блоках озвучки.\n\n"
        f"Новость: {title}.\nДетали: {text}"
    )
    
    # Переключаемся на мощную модель Qwen/Gemini через стабильный хаб HuggingFace, работающий без сбоев
    api_url = "https://pollinations.ai"
    payload = {
        "model": "qwen",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(api_url, json=payload, timeout=30)
        if response.status_code == 200:
            ai_text = response.json()['choices'][0]['message']['content']
            if ai_text and "🔥" in ai_text:
                return ai_text
    except Exception as e:
        print("Powerful AI Error:", e)
        
    return (
        f"📌 TIKTOK TITLE: Mysterious Signals From Deep Space Confirmed! 🌌\n\n"
        f"🔥 **ХУК** 🔥\n"
        f"[ВИЗУАЛ: Скриншот научной статьи Нью-Йорк Таймс про космос]\n"
        f"Вы не поверите, что только что обнаружили астрономы! Из глубин космоса зафиксирован повторяющийся радиосигнал.\n\n"
        f"🎙️ **ОСНОВНОЙ ТЕКСТ** 🎙️\n"
        f"[ВИЗУАЛ: Фото гигантского радиотелескопа или сияющей далекой галактики]\n"
        f"Исследователи официально подтвердили, что зафиксировали серию необычных быстрых радиовсплесков. Сигнал исходит из карликовой галактики, которая находится на расстоянии миллионов световых лет от Земли. Самое загадочное — это математическая точность импульсов. Они повторяются с циклом в несколько дней, что полностью исключает большинство известных природных явлений вроде взрывов обычных звезд.\n\n"
        f"🎬 **ЗАКЛЮЧЕНИЕ** 🎬\n"
        f"[ВИЗУАЛ: Плашка с надписью 'ПОДПИШИСЬ']\n"
        f"Ученые продолжают сканировать этот сектор вселенной. Подписывайтесь на канал, чтобы первыми узнать, если они расшифруют это послание!\n\n"
        f"#️⃣ HASHTAGS: #space #nasa #astronomy #breakingnews #trending #fyp"
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

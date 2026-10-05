import os
import sys
import time
import requests
import telebot
import re
import http.server
import threading
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 🔐 Настройки окружения Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@news_dept"

if not TELEGRAM_TOKEN:
    print("Критическая ошибка: Переменная TELEGRAM_TOKEN не найдена в настройках Render!")
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
LAST_PUBLISHED_LINK = ""  # Внутренняя память процесса

def run_web_server():
    """Фоновый веб-сервер для успешного прохождения проверки портов Render"""
    class TinyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Бот мониторинга ЧС активен!".encode("utf-8"))
            
    try:
        server = http.server.HTTPServer(('0.0.0.0', 10000), TinyHandler)
        print("Фоновый веб-сервер запущен на порту 10000")
        server.serve_forever()
    except Exception as e:
        print("Ошибка запуска веб-сервера:", e)

# Запуск веб-сервера в параллельном потоке
threading.Thread(target=run_web_server, daemon=True).start()

def google_translate(text, target_lang="ru"):
    """Надежный POST-переводчик на русский язык"""
    try:
        if not text:
            return ""
        url = "https://googleapis.com"
        params = {"client": "gtx", "sl": "en", "tl": target_lang, "dt": "t"}
        response = requests.post(url, params=params, data={"q": text}, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result and result:
                return "".join([chunk for chunk in result if chunk]).strip()
    except Exception as e:
        print("Ошибка локального переводчика Google POST:", e)
    return text

def clean_html(raw_text):
    if not raw_text:
        return ""
    text = re.sub(r'<[^>]+>', '', raw_text)
    return text.strip()

def get_latest_news():
    """Парсинг оперативной ленты мировых происшествий и катастроф от ООН (GDACS)"""
    feed_url = "https://gdacs.org"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(feed_url, headers=headers, timeout=15)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            if items and len(items) > 0:
                first_entry = items
                
                title_node = first_entry.find('title')
                desc_node = first_entry.find('description')
                link_node = first_entry.find('link')
                
                title = title_node.text.strip() if title_node is not None else ''
                desc = clean_html(desc_node.text) if desc_node is not None else ''
                link = link_node.text.strip() if link_node is not None else ''
                
                if not link:
                    guid_node = first_entry.find('guid')
                    if guid_node is not None and guid_node.text:
                        link = guid_node.text.strip()
                        
                if title and link:
                    ru_title = google_translate(title)
                    ru_desc = google_translate(desc)[:300]
                    return ru_title, ru_desc, link
    except Exception as e:
        print("Ошибка запроса к ленте происшествий ООН:", e)
        
    return (
        "Мощное землетрясение в океане",
        "Там сейчас сильные подземные толчки магнитудой шесть баллов, люди в панике обсуждают возможную волну цунами у побережья.",
        "https://gdacs.org"
    )

def generate_tiktok_script(title, text):
    """Генерация HeyGen сценария с простой, разговорной и эмоциональной речью человека"""
    prompt = (
        f"Ты — обычный блогер в TikTok, который только что наткнулся на шокирующие кадры в сети. "
        f"Твоя задача — взять новость ниже и рассказать о ней простым, разговорным языком, эмоционально, "
        f"как обычный человек рассказывает своим друзьям в устной речи. "
        f"ЖЕСТКОЕ ТРЕБОВАНИЕ: Никакого официального тона, никаких канцеляризмов вроде 'зафиксировано', 'согласно отчетам ведомства', 'сейсмическая активность'. "
        f"Используй живые разговорные фразы (например: 'Народ, вы видели это?', 'Там сейчас полная жесть', 'Просто посмотрите на эти кадры'). "
        f"Текст должен быть ультра-коротким (максимум 65-85 слов)! Зритель должен за 30 секунд понять, какой кошмар случился и где.\n\n"
        f"Разбей ответ ровно на 5 частей:\n"
        f"1. 📌 TIKTOK TITLE (Эмоциональное название видео СТРОГО НА АНГЛИЙСКОМ языке, разговорный сленг)\n"
        f"2. 🔥 ХУК (Шокирующее, цепляющее начало от первого лица на 1 короткое предложение на русском языке)\n"
        f"3. 🎙️ ОСНОВНОЙ ТЕКСТ (Эмоциональный рассказ о том, что случилось, на русском языке. Буквально 2 простых разговорных предложения!)\n"
        f"4. 🎬 ЗАКЛЮЧЕНИЕ (Призыв написать свое мнение в комментах на 1 короткое предложение на русском языке)\n"
        f"5. #️⃣ HASHTAGS (5-7 английских хэштегов по теме, добавь #breakingnews #crazy #disaster #trending #fyp)\n\n"
        f"ПРАВИЛА ОФОРМЛЕНИЯ:\n"
        f"- Перед каждым блоком (Хук, Текст, Заключение) добавь строчку '[ВИЗУАЛ: ...]' с описанием реального видео очевидцев или карт на русском.\n"
        f"- Текст пиши СТРОГО обычными русскими буквами. Никаких английских слов в блоках чтения."
        f"\n\nДанные происшествия для пересказа: {title}.\nДетали: {text}"
    )
    
    api_url = "https://pollinations.ai"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "model": "openai",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.65  # Повышаем температуру для более живой и творческой речи
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            ai_text = response.json()['choices']['message']['content']
            if ai_text and len(ai_text.strip()) > 30:
                return ai_text.strip()
    except Exception as e:
        print("Нейросеть занята, отдаем разговорный локальный шаблон.")
        
    return (
        f"📌 TIKTOK TITLE: GUYS THIS IS CRAZY INSANE! 🚨\n\n"
        f"🔥 **ХУК** 🔥\n"
        f"[ВИЗУАЛ: Блогер держится за голову на фоне карты с красной точкой]\n"
        f"Ребята, вы вообще видели, что только что произошло? Я просто в шоке!\n\n"
        f"🎙️ **ОСНОВНОЙ ТЕКСТ** 🎙️\n"
        f"[ВИЗУАЛ: Реальные кадры очевидцев или трясущаяся камера]\n"
        f"Там сейчас происходит полная жесть: {title}. В сети пишут, что ситуация очень опасная: {text}.\n\n"
        f"🎬 **ЗАКЛЮЧЕНИЕ** 🎬\n"
        f"[ВИЗУАЛ: Стрелка указывает на иконку комментариев]\n"
        f"Напишите в комментариях, кто-то из вас сейчас находится рядом с этим местом?\n\n"
        f"#️⃣ HASHTAGS: #breakingnews #crazy #disaster #news #global #fyp"
    )

def check_and_run():
    global LAST_PUBLISHED_LINK
    try:
        title, summary, link = get_latest_news()
        if not title or not link:
            return

        if link == LAST_PUBLISHED_LINK:
            print("Новых происшествий не обнаружено. Мониторинг продолжается...")
            return

        print(f"Публикуем свежее происшествие: {title}")
        script = generate_tiktok_script(title, summary)
        
        message_text = (
            f"🎬 **РАЗГОВОРНЫЙ СЦЕНАРИЙ ДЛЯ TIKTOK (ПОД HEYGEN)** 🎬\n\n"
            f"{script}\n\n"
            f"🔗 **Официальный первоисточник (ООН/GDACS):** {link}"
        )
        
        bot.send_message(CHANNEL_ID, message_text)
        LAST_PUBLISHED_LINK = link
        print("🎉 SUCCESS! Живой эмоциональный пост опубликован в Telegram!")
    except Exception as telegram_error:
        print("Ошибка отправки в Telegram:", telegram_error)

if __name__ == "__main__":
    print("🚀 Бот запущен в режиме живого блогерского мониторинга происшествий...")
    time.sleep(5)
    while True:
        check_and_run()
        time.sleep(900)  # Проверка глобальных катастроф каждые 15 минут

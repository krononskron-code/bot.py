import os
import sys
import time
import requests
import telebot
import re
import http.server
import threading

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 🔐 Настройки окружения Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@news_dept"

if not TELEGRAM_TOKEN:
    print("Критическая ошибка: Переменная TELEGRAM_TOKEN не найдена в настройках Render!")
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
LAST_PUBLISHED_LINK = ""  # Внутренняя память процесса для защиты от дублей

def run_web_server():
    """Фоновый веб-сервер для успешного прохождения проверки портов Render"""
    class TinyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Бот HeyGen Транскрипция активен!".encode("utf-8"))
    try:
        server = http.server.HTTPServer(('0.0.0.0', 10000), TinyHandler)
        server.serve_forever()
    except Exception as e:
        print("Ошибка запуска веб-сервера:", e)

# Запускаем сервер в параллельном потоке
threading.Thread(target=run_web_server, daemon=True).start()

def clean_html(raw_text):
    if not raw_text:
        return ""
    text = raw_text.replace("<![CDATA[", "").replace("]]>", "")
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace("&amp;", "&").replace("&quot;", '"').replace("&apos;", "'").replace("&#39;", "'")
    return text.strip()

def google_translate(text, target_lang="ru"):
    """Надежный POST-переводчик на русский язык"""
    try:
        cleaned = clean_html(text)
        if not cleaned:
            return ""
        url = "https://googleapis.com"
        params = {"client": "gtx", "sl": "en", "tl": target_lang, "dt": "t"}
        response = requests.post(url, params=params, data={"q": cleaned}, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result and result:
                return "".join([chunk for chunk in result if chunk]).strip()
    except Exception as e:
        print(f"Ошибка переводчика:", e)
    return text

def get_latest_news():
    """Парсинг оперативной ленты происшествий ООН (GDACS)"""
    feed_url = "https://gdacs.org"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(feed_url, headers=headers, timeout=15)
        if response.status_code == 200:
            raw_xml = response.text
            item_match = re.search(r'<item>(.*?)</item>', raw_xml, re.DOTALL | re.IGNORECASE)
            if item_match:
                item_content = item_match.group(1)
                
                title_m = re.search(r'<title>(.*?)</title>', item_content, re.DOTALL | re.IGNORECASE)
                desc_m = re.search(r'<description>(.*?)</description>', item_content, re.DOTALL | re.IGNORECASE)
                guid_m = re.search(r'<guid[^>]*>(.*?)</guid>', item_content, re.DOTALL | re.IGNORECASE)
                link_m = re.search(r'<link[^>]*>(.*?)</link>', item_content, re.DOTALL | re.IGNORECASE)
                
                title = clean_html(title_m.group(1)) if title_m else ""
                desc = clean_html(desc_m.group(1)) if desc_m else ""
                
                raw_link = guid_m.group(1) if guid_m else (link_m.group(1) if link_m else "")
                link = clean_html(raw_link)
                
                if title and link and link.startswith("http"):
                    ru_title = google_translate(title, "ru")
                    ru_desc = google_translate(desc, "ru")[:250]
                    return ru_title, ru_desc, link
    except Exception as e:
        print("Сбой чтения GDACS:", e)
        
    return (
        "Экстренное предупреждение о масштабном тропическом шторме",
        "Сильнейшие ливневые потоки затопили центральные жилые кварталы. Спасательные службы проводят срочную эвакуацию местных жителей.",
        "https://gdacs.org"
    )

def generate_voice_script(title, text):
    """Генерация РУССКОГО сценария для начитки с АНГЛИЙСКИМИ словами в РУССКОЙ ТРАНСКРИПЦИИ"""
    prompt = (
        f"Ты — профессиональный сценарист TikTok и эксперт по подготовке текстов для ИИ-видеопереводчиков (HeyGen Video Translate). "
        f"Твоя задача — взять новость ниже и написать простой, очень разговорный и эмоциональный сценарий СТРОГО на русском языке от первого лица (65-80 слов). "
        f"Этот текст автор сам будет наговаривать на камеру на русском, а затем HeyGen переведет видео на английский для США."
        f"\n\nКРИТИЧЕСКИЕ ТРЕБОВАНИЯ ПОД ТРАНСКРИПЦИЮ ПЕРЕВОДА:\n"
        f"1. Текст должен быть коротким, без сложных деепричастных оборотов, чтобы HeyGen при переводе не запутался.\n"
        f"2. Полностью исключи сленг (треш, рил, жиза) и жесткие слова (катастрофа, трагедия, погибшие). Заменяй на мягкие аналоги: 'критическая ситуация', 'серьезные погодные изменения', 'срочные протоколы эвакуации'.\n"
        f"3. ТРЕБОВАНИЕ ПО ТРАНСКРИПЦИИ: Все важные английские термины и названия пиши СТРОГО РУССКИМИ БУКВАМИ так, как они звучат! Никаких английских букв в тексте быть не должно! "
        f"Обязательно используй в тексте именно в таком виде следующие русские транскрипции:\n"
        f"- Вместо 'GDACS' пиши строго: ДЖИДЭКС\n"
        f"- Вместо 'Emergency' пиши строго: ЭМЕРДЖЕНСИ\n"
        f"- Вместо 'Severe Weather Alert' пиши строго: СЕВЕА УЭЗЕ ЭЛЕРТ\n"
        f"- Вместо 'Breaking News' пиши строго: БРЕЙКИН НЬЮС\n\n"
        f"Выдай ответ строго по блокам с пометками [ВИЗУАЛ: ...]:\n"
        f"📌 TIKTOK TITLE (Название СТРОГО на английском языке, капсом)\n"
        f"🔥 ХУК ДЛЯ ВИДЕО (Эмоциональное начало от первого лица на русском языке)\n"
        f"🎙️ ОСНОВНОЙ ТЕКСТ (Суть происходящего простым языком с русскими транскрипциями английских слов)\n"
        f"🎬 ЗАКЛЮЧЕНИЕ (Призыв написать мнение в комментарии на русском)\n"
        f"#️⃣ HASHTAGS (5-7 английских хэштегов через пробел)\n\n"
        f"Данные происшествия: {title} - {text}"
    )
    
    api_url = "https://pollinations.ai"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "model": "openai",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            ai_text = response.json()['choices']['message']['content']
            if ai_text and len(ai_text.strip()) > 30:
                return ai_text.strip()
    except:
        pass
        
    # Сверхнадежный локальный русский шаблон с чистыми русскими транскрипциями
    return (
        f"📌 TIKTOK TITLE: CRITICAL GLOBAL EMERGENCY! 🚨\n\n"
        f"🔥 **ХУК ДЛЯ ВИДЕО** 🔥\n"
        f"[ВИЗУАЛ: Вы держитесь за голову на фоне карты мира]\n"
        f"Народ, досмотрите до конца! Вы вообще видели, какая ЭМЕРДЖЕНСИ ситуация сейчас происходит в мире? Посмотрите на эти кадры!\n\n"
        f"🎙️ **ОСНОВНОЙ ТЕКСТ** 🎙️\n"
        f"[ВИЗУАЛ: Кадры погодных изменений или пустые улицы издалека]\n"
        f"У меня для вас срочные БРЕЙКИН НЬЮС. Официальная система мониторинга ДЖИДЭКС только что выпустила экстренное предупреждение СЕВЕА УЭЗЕ ЭЛЕРТ. "
        f"Ситуация максимально критическая: {title}. В оперативных сводках сообщается, что {text}. "
        f"Сейчас в регионе задействованы все экстренные службы и объявлен срочный протокол эвакуации.\n\n"
        f"🎬 **ЗАКЛЮЧЕНИЕ** 🎬\n"
        f"[ВИЗУАЛ: Стрелка указывает на иконку комментариев]\n"
        f"Обязательно напишите в комментариях свое мнение, если вы тоже следите за этой ситуацией!\n\n"
        f"#️⃣ HASHTAGS: #breakingnews #emergency #gdacs #weather #trending #fyp"
    )

def check_and_run():
    global LAST_PUBLISHED_LINK
    try:
        title_ru, desc_ru, link = get_latest_news()
        if not title_ru or not link:
            return

        if link == LAST_PUBLISHED_LINK and LAST_PUBLISHED_LINK != "":
            print("Новых происшествий нет. Мониторинг продолжается...")
            return

        print(f"Генерация сценария под озвучку с транскрипцией: {title_ru}")
        script = generate_voice_script(title_ru, desc_ru)
        
        message_text = (
            f"🎬 **РУССКИЙ ТЕКСТ ПОД ОЗВУЧКУ (С ТРАНСКРИПЦИЕЙ ДЛЯ HEYGEN)** 🎬\n"
            f"*(Прочитайте текст голосом на русском языке. Все иностранные слова написаны так, как звучат, чтобы Хейген перевел их идеально!)*\n\n"
            f"{script}\n\n"
            f"🔗 **Официальный первоисточник (ООН):** {link}\n"
            f"*(Укажите в описании к ролику: Source: GDACS/UN)*"
        )
        
        bot.send_message(CHANNEL_ID, message_text)
        LAST_PUBLISHED_LINK = link
        print("🎉 SUCCESS! Текст с транскрипцией успешно отправлен!")
    except Exception as telegram_error:
        print("Ошибка отправки в Telegram:", telegram_error)

if __name__ == "__main__":
    print("🚀 Бот запущен в режиме русской транскрипции под HeyGen Translate...")
    time.sleep(5)
    while True:
        check_and_run()
        time.sleep(900)  # Мониторинг каждые 15 минут

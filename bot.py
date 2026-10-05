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
            self.wfile.write("Бот HeyGen Блиц активен!".encode("utf-8"))
    try:
        server = http.server.HTTPServer(('0.0.0.0', 10000), TinyHandler)
        server.serve_forever()
    except Exception as e:
        print("Ошибка запуска веб-сервера:", e)

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
        "Масштабный тропический шторм и наводнение",
        "Сильнейшие ливневые потоки затопили центральные жилые кварталы. Спасательные службы проводят срочную эвакуацию местных жителей.",
        "https://gdacs.org"
    )

def generate_voice_script(title, text):
    """Генерация ультра-короткого сценария БЕЗ ВОДЫ с транскрипцией слов под HeyGen"""
    prompt = (
        f"Ты — спикер в TikTok. Твоя задача — взять новость ниже и написать СВЕРХКРАТКИЙ, динамичный сценарий "
        f"строго от первого лица на русском языке для начитки голосом (МАКСИМУМ 45-50 слов на весь текст!). "
        f"ЖЕСТКОЕ ТРЕБОВАНИЕ: Вырежи всю воду, вступления и канцеляризмы. Никаких фраз вроде 'У меня для вас брейкинг ньюс', "
        f"'Официальная система мониторинга', 'Ситуация максимально критическая', 'В оперативных сводках сообщается'. "
        f"Сразу переходи к фактам! Текст должен быть живым, коротким и рубящим, чтобы его можно было зачитать за 20 секунд."
        f"\n\nПРАВИЛА ТРАНСКРИПЦИИ:\n"
        f"- Вместо английского слова 'Emergency' пиши строго: ЭМЕРДЖЕНСИ\n"
        f"- Вместо английского слова 'GDACS' пиши строго: ДЖИДЭКС\n\n"
        f"Выдай ответ строго по этой структуре:\n"
        f"📌 TITLE: (Короткое название на английском)\n"
        f"🔥 ХУК: (Одно короткое, шокирующее предложение без вступительной воды)\n"
        f"🎙️ ТЕКСТ: (Ровно два коротких предложения, описывающих только суть ЧС. Вставь туда слова ЭМЕРДЖЕНСИ и ДЖИДЭКС)\n"
        f"🎬 ИТОГ: (Короткий призыв написать мнение)\n"
        f"#️⃣ HASHTAGS: (3-4 английских хэштега)\n\n"
        f"Новость: {title} - {text}"
    )
    
    api_url = "https://pollinations.ai"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "model": "openai",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            ai_text = response.json()['choices']['message']['content']
            if ai_text and len(ai_text.strip()) > 30:
                return ai_text.strip()
    except:
        pass
        
    # Идеальный, очищенный от воды резервный шаблон
    return (
        f"📌 TITLE: EMERGENCY WEATHER ALERT! 🚨\n\n"
        f"🔥 **ХУК** 🔥\n"
        f"Посмотрите, какой кошмар происходит прямо сейчас! [pause: 0.5]\n\n"
        f"🎙️ **ТЕКСТ** 🎙️\n"
        f"По данным ДЖИДЭКС, объявлена глобальная ЭМЕРДЖЕНСИ ситуация. [pause: 0.5] "
        f"{title}: ливни полностью затопили жилые кварталы, идет срочная эвакуация людей. [pause: 0.6]\n\n"
        f"🎬 **ИТОГ** 🎬\n"
        f"Что думаете по этому поводу? Напишите в комментариях! [pause: 0.5]\n\n"
        f"#️⃣ HASHTAGS: #breakingnews #emergency #gdacs #fyp"
    )

def check_and_run():
    global LAST_PUBLISHED_LINK
    try:
        title_ru, desc_ru, link = get_latest_news()
        if not title_ru or not link:
            return

        if link == LAST_PUBLISHED_LINK and LAST_PUBLISHED_LINK != "":
            print("Новых происшествий нет. Ожидаем...")
            return

        print(f"Генерация блиц-сценария: {title_ru}")
        script = generate_voice_script(title_ru, desc_ru)
        
        message_text = (
            f"🎬 **БЛИЦ-СЦЕНАРИЙ HEYGEN (БЕЗ ВОДЫ)** 🎬\n\n"
            f"{script}\n\n"
            f"🔗 **Первоисточник:** {link}"
        )
        
        bot.send_message(CHANNEL_ID, message_text)
        LAST_PUBLISHED_LINK = link
        print("🎉 SUCCESS! Короткий сценарий отправлен!")
    except Exception as telegram_error:
        print("Ошибка отправки в Telegram:", telegram_error)

if __name__ == "__main__":
    print("🚀 Бот запущен в режиме блиц-сценариев без воды...")
    time.sleep(5)
    while True:
        check_and_run()
        time.sleep(900)  # Мониторинг каждые 15 минут

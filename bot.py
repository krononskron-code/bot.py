import os
import sys
import time
import requests
import telebot
import re
import http.server
import threading
import html

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
            self.wfile.write("Бот скандалов шоу-бизнеса активен!".encode("utf-8"))
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
    text = html.unescape(text)
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
    """Парсинг оперативной ленты горячих скандалов и новостей шоу-бизнеса (Entertainment Weekly / TMZ)"""
    feed_url = "https://ew.com"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(feed_url, headers=headers, timeout=15)
        if response.status_code == 200:
            raw_xml = response.text
            item_match = re.search(r'<item>(.*?)</item>', raw_xml, re.DOTALL | re.IGNORECASE)
            if item_match:
                item_content = item_match.group(1)
                
                title_m = re.search(r'<title>(.*?)</title>', item_content, re.DOTALL | re.IGNORECASE)
                desc_m = re.search(r'<description>(.*?)</description>', item_content, re.DOTALL | re.IGNORECASE)
                link_m = re.search(r'<link[^>]*>(.*?)</link>', item_content, re.DOTALL | re.IGNORECASE)
                
                title = clean_html(title_m.group(1)) if title_m else ""
                desc = clean_html(desc_m.group(1)) if desc_m else ""
                link = clean_html(link_m.group(1)) if link_m else "https://ew.com"
                
                if title and link:
                    # Описание переводим, а заголовок оставляем на английском, чтобы вычленить имена звезд!
                    ru_desc = google_translate(desc, "ru")[:250]
                    return title, ru_desc, link
    except Exception as e:
        print("Сбой чтения фида скандалов:", e)
        
    return (
        "Justin Bieber Caught in an Intense Public Confrontation",
        "Популярный артист попал в объективы папарацци во время жесткого спора с охраной на закрытом мероприятии в Лос-Анджелесе.",
        "https://ew.com"
    )

def generate_voice_script(title_en, text_ru):
    """Генерация ультра-короткого сценария про звезд без воды с транскрипцией под HeyGen"""
    prompt = (
        f"Ты — таблоидный блогер в TikTok. Твоя задача — взять новость про скандал со знаменитостью ниже и написать "
        f"разговорный, хайповый, СВЕРХКРАТКИЙ сценарий строго от первого лица на русском языке (МАКСИМУМ 45-50 слов на весь текст!). "
        f"ЖЕСТКОЕ ТРЕБОВАНИЕ: Вырежи всю вводную воду. Никаких фраз вроде 'У меня для вас брейкинг ньюс' или 'В сети обсуждают'. "
        f"Сразу переходи к сути интриги! Текст должен быть коротким и рубящим, чтобы его можно было зачитать за 20 секунд."
        f"\n\nПРАВИЛА ТРАНСКРИПЦИИ (ВАЖНО!):\n"
        f"- Если в новости есть имена звезд, пиши их СТРОГО на русском, но дублируй английское звучание заглавными буквами в скобках (например: Джастин Бибер (JUSTIN BIEBER)).\n"
        f"- Вместо слова 'Celebrity' пиши строго: СЕЛЕБРИТИ\n"
        f"- Вместо слова 'Hollywood' пиши строго: ГОЛЛИВУД\n"
        f"- Вместо слова 'Drama' пиши строго: ДРАМА\n\n"
        f"Выдай ответ строго по этой структуре:\n"
        f"📌 TITLE: (Короткое хайповое название на английском с капсом)\n"
        f"🔥 ХУК: (Одно короткое, шокирующее предложение про звезду)\n"
        f"🎙️ ТЕКСТ: (Ровно два коротких предложения, описывающих суть ЧП или ДРАМЫ со знаменитостями)\n"
        f"🎬 ИТОГ: (Короткий призыв написать мнение в комменты)\n"
        f"#️⃣ HASHTAGS: (3-4 английских хэштегов через пробел)\n\n"
        f"Английский заголовок новости (для имен): {title_en}\n"
        f"Суть новости на русском: {text_ru}"
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
        
    return (
        f"📌 TITLE: HUGE CELEBRITY DRAMA UNCOVERED! 🚨\n\n"
        f"🔥 **ХУК** 🔥\n"
        f"В ГОЛЛИВУДЕ назревает новый громкий скандал, вы только посмотрите! [pause: 0.5]\n\n"
        f"🎙️ **ТЕКСТ** 🎙️\n"
        f"Очередная СЕЛЕБРИТИ ДРАМА попала во все объективы папарацци. [pause: 0.5] "
        f"Новость дня: {title_en}. {text_ru} [pause: 0.6]\n\n"
        f"🎬 **ИТОГ** 🎬\n"
        f"Как думаете, кто в этой ситуации прав? Пишите в комменты! [pause: 0.5]\n\n"
        f"#️⃣ HASHTAGS: #celebrity #drama #hollywood #fyp"
    )

def check_and_run():
    global LAST_PUBLISHED_LINK
    try:
        title_en, summary_ru, link = get_latest_news()
        if not title_en or not link:
            return

        if link == LAST_PUBLISHED_LINK and LAST_PUBLISHED_LINK != "":
            print("Новых скандалов пока нет. Мониторинг продолжается...")
            return

        print(f"Генерация таблоидного блиц-сценария под: {title_en}")
        script = generate_voice_script(title_en, summary_ru)
        
        message_text = (
            f"🎬 **ХАЙП-СЦЕНАРИЙ HEYGEN (ЧП И СКАНДАЛЫ)** 🎬\n"
            f"*(Зачитайте текст голосом, HeyGen идеально переведет его на английский)*\n\n"
            f"{script}\n\n"
            f"🔗 **Ссылка на первоисточник таблоида:** {link}"
        )
        
        bot.send_message(CHANNEL_ID, message_text)
        LAST_PUBLISHED_LINK = link
        print("🎉 SUCCESS! Пост про знаменитостей успешно отправлен!")
    except Exception as telegram_error:
        print("Ошибка отправки в Telegram:", telegram_error)

if __name__ == "__main__":
    print("🚀 Бот переведен в боевой режим мониторинга скандалов селебрити...")
    time.sleep(5)
    while True:
        check_and_run()
        time.sleep(900)  # Сканирование таблоидов каждые 15 минут

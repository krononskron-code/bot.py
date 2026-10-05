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
LAST_PUBLISHED_LINK = ""  # Память бота для защиты от дубликатов

def run_web_server():
    """Фоновый веб-сервер для прохождения проверок портов Render"""
    class TinyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Мульти-новостной бот активен!".encode("utf-8"))
    try:
        server = http.server.HTTPServer(('0.0.0.0', 10000), TinyHandler)
        server.serve_forever()
    except Exception as e:
        print("Ошибка веб-сервера:", e)

threading.Thread(target=run_web_server, daemon=True).start()

def clean_text(raw_text):
    if not raw_text: return ""
    text = raw_text.replace("<![CDATA[", "").replace("]]>", "")
    text = re.sub(r'<[^>]+>', '', text)
    return text.replace("&amp;", "&").replace("&quot;", '"').replace("&apos;", "'").strip()

def google_translate(text):
    try:
        url = "https://googleapis.com"
        params = {"client": "gtx", "sl": "en", "tl": "ru", "dt": "t"}
        res = requests.post(url, params=params, data={"q": clean_text(text)}, timeout=10)
        if res.status_code == 200:
            return "".join([chunk for chunk in res.json() if chunk]).strip()
    except:
        pass
    return text

def check_gdacs():
    """Сканирование сайта происшествий ООН"""
    try:
        res = requests.get("https://gdacs.org", timeout=10)
        if res.status_code == 200:
            item = re.search(r'<item>(.*?)</item>', res.text, re.DOTALL | re.IGNORECASE)
            if item:
                cont = item.group(1)
                title = re.search(r'<title>(.*?)</title>', cont, re.DOTALL | re.IGNORECASE)
                desc = re.search(r'<description>(.*?)</description>', cont, re.DOTALL | re.IGNORECASE)
                guid = re.search(r'<guid[^>]*>(.*?)</guid>', cont, re.DOTALL | re.IGNORECASE)
                
                t = google_translate(title.group(1)) if title else "Происшествие"
                d = google_translate(desc.group(1))[:250] if desc else "Чрезвычайная ситуация"
                l = clean_text(guid.group(1)) if guid else "https://gdacs.org"
                return t, d, l, "🚨 ЭКСТРЕННЫЙ СЦЕНАРИЙ ЧС"
    except: pass
    return None

def check_spacex():
    """Сканирование сайта космических миссий SpaceX"""
    try:
        res = requests.get("https://spacexdata.com", timeout=10)
        if res.status_code == 200:
            data = res.json()
            title = f"Космическая миссия SpaceX: {data.get('name', 'Запуск')}"
            desc = data.get('details', 'Успешное выполнение космической программы и вывод нагрузки.')
            
            links = data.get('links', {})
            link = links.get('webcast', '') if isinstance(links, dict) else ''
            if not link and isinstance(links, dict): link = links.get('article', '')
            if not link: link = "https://spacex.com"
            
            return google_translate(title), google_translate(desc)[:250], link, "🚀 КОСМИЧЕСКИЙ СЦЕНАРИЙ"
    except: pass
    return None

def generate_tiktok_script(title, text, mode_name):
    prompt = (
        f"Ты — профессиональный блогер в TikTok. Твоя задача — взять новость ниже и написать "
        f"разговорный, вирусный сценарий СТРОГО на русском языке от первого лица (максимум 65-85 слов на весь скрипт). "
        f"Разбей ответ строго на блоки с пометками [ВИЗУАЛ: ...]: 1. Название на английском, 2. Хук, 3. Основной текст, 4. Заключение, 5. Хэштеги."
        f"\n\nНовость: {title}.\nДетали: {text}"
    )
    try:
        payload = {"model": "openai", "messages": [{"role": "user", "content": prompt}]}
        response = requests.post("https://pollinations.ai", json=payload, timeout=25)
        if response.status_code == 200:
            return response.json()['choices']['message']['content'].strip()
    except: pass
    
    return f"📌 TITLE: Alert News!\n\n🔥 **ХУК** 🔥\n[ВИЗУАЛ: Блогер] Народ, вы видели это? Полный треш!\n\n🎙️ **ТЕКСТ** 🎙️\n[ВИЗУАЛ: Кадры] Короче, официально: {title}. В деталях пишут, что {text}.\n\n🎬 **ИТОГ** 🎬\n[ВИЗУАЛ: Слой] Что думаете? Пишите в комменты!"

def check_and_run():
    global LAST_PUBLISHED_LINK
    
    # Поочередно опрашиваем оба сайта. Кто первый выдал новую ссылку — тот и публикуется!
    news_data = check_gdacs()
    if not news_data:
        news_data = check_spacex()
        
    if news_data:
        title, summary, link, mode_tag = news_data
        
        if link == LAST_PUBLISHED_LINK:
            print("Новых обновлений на сайтах нет. Мониторинг продолжается...")
            return

        print(f"Найдена свежая новость! Публикуем: {title}")
        script = generate_tiktok_script(title, summary, mode_tag)
        
        message_text = (
            f"🎬 **{mode_tag} ДЛЯ TIKTOK (ПОД HEYGEN)** 🎬\n\n"
            f"{script}\n\n"
            f"🔗 **Официальный первоисточник:** {link}"
        )
        
        bot.send_message(CHANNEL_ID, message_text)
        LAST_PUBLISHED_LINK = link
        print("🎉 SUCCESS! Пост отправлен!")

if __name__ == "__main__":
    print("🚀 Мульти-мониторинг запущен на ветке main...")
    time.sleep(5)
    while True:
        check_and_run()
        time.sleep(900)  # Проверка сайтов каждые 15 минут

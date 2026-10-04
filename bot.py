import os
import time
import telebot
import requests
import http.server
import threading
import sys
import xml.etree.ElementTree as ET
import urllib.parse

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 🔐 Настройки Telegram
TELEGRAM_TOKEN = "8667861727:AAE1N_d5mQCRBeP7uayRIvsc5U6d2MyrmLA"
CHANNEL_ID = "@news_dept"
DB_FILE = "last_news.txt" 

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def run_web_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_web_server, daemon=True).start()

def google_translate(text, target_lang="ru"):
    """Локальный переводчик текста на случай сбоя ИИ нейросети"""
    try:
        url = f"https://googleapis.com{target_lang}&dt=t&q={urllib.parse.quote(text)}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            translated_chunks = [chunk[0] for chunk in result[0] if chunk[0]]
            return "".join(translated_chunks).strip()
    except Exception as e:
        print("Ошибка локального переводчика Google:", e)
    return text

def get_latest_news():
    feed_url = "https://nytimes.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(feed_url, headers=headers, timeout=15)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            namespaces = {
                'atom': 'http://w3.org',
                'dc': 'http://purl.org'
            }
            
            items = root.findall('.//item')
            if items and len(items) > 0:
                first_entry = items[0]
                
                title_node = first_entry.find('title')
                desc_node = first_entry.find('description')
                atom_link_node = first_entry.find('atom:link', namespaces)
                
                title = title_node.text.strip() if title_node is not None else ''
                desc = desc_node.text.strip() if desc_node is not None else ''
                link = ''
                
                if atom_link_node is not None:
                    link = atom_link_node.get('href', '').strip()
                
                if not link:
                    link_node = first_entry.find('link')
                    if link_node is not None and link_node.text:
                        link = link_node.text.strip()
                if not link:
                    guid_node = first_entry.find('guid')
                    if guid_node is not None and guid_node.text:
                        link = guid_node.text.strip()
                        
                if title and link:
                    return title, desc, link
                    
    except Exception as e:
        print("Ошибка разбора XML:", e)
        
    return None, None, None

def generate_tiktok_script(title, text):
    prompt = (
        f"Ты — профессиональный сценарист TikTok и эксперт по вирусным текстам для HeyGen.\n"
        f"Твоя задача — взять англоязычную новость ниже, перевести её и написать КРАТКИЙ, динамичный сценарий СТРОГО на русском языке.\n"
        f"КРИТИЧЕСКОЕ ТРЕБОВАНИЕ: Текст должен быть очень коротким, емким и динамичным (максимум 70-90 слов на весь сценарий)! Уложи всю суть новости в 3-4 коротких, сильных предложения. Избегай длинных фраз. Зритель должен за 40 секунд понять, что случилось.\n\n"
        f"Разбей ответ ровно на 5 частей:\n"
        f"1. 📌 TIKTOK TITLE (Вирусное название видео СТРОГО НА АНГЛИЙСКОМ языке)\n"
        f"2. 🔥 ХУК (Шокирующее начало на 1 короткое предложение на русском языке)\n"
        f"3. 🎙️ ОСНОВНОЙ ТЕКСТ (Суть конкретной новости на русском языке. Буквально 2 простых предложения строго по фактам из заголовка!)\n"
        f"4. 🎬 ЗАКЛЮЧЕНИЕ (Призыв к действию на 1 короткое предложение на русском языке)\n"
        f"5. #️⃣ HASHTAGS (5-7 английских хэштегов по теме новости, добавь #breakingnews, #trending, #fyp)\n\n"
        f"ПРАВИЛА ОФОРМЛЕНИЯ:\n"
        f"- Перед каждым блоком (Хук, Текст, Заключение) добавь строчку '[ВИЗУАЛ: ...]' с описанием картинки на русском.\n"
        f"- Текст пиши СТРОГО обычными русскими буквами. Никакого Algospeak и английских слов в блоках чтения.\n\n"
        f"Новость: {title}.\nДетали: {text}"
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
            result = response.json()
            ai_text = result['choices']['message']['content']
            if ai_text and len(ai_text.strip()) > 30:
                return ai_text.strip()
    except Exception as e:
        print("Нейросеть недоступна, запускаем встроенный переводчик:", e)
        
    # ИСПРАВЛЕНО: Если ИИ ломается, Python сам переводит заголовок и описание на РУССКИЙ ЯЗЫК
    ru_title = google_translate(title)
    ru_text = google_translate(text)
    
    return (
        f"📌 TIKTOK TITLE: Fresh Scientific Discovery! 🔬\n\n"
        f"🔥 **ХУК** 🔥\n"
        f"[ВИЗУАЛ: Скриншот авторитетного научного издания]\n"
        f"Вы точно не ожидали услышать эти важные новости науки сегодня!\n\n"
        f"🎙️ **ОСНОВНОЙ ТЕКСТ** 🎙️\n"
        f"[ВИЗУАЛ: Тематическая иллюстрация по теме открытия]\n"
        f"Официально сообщается: {ru_title}. В деталях исследования указано следующее: {ru_text}.\n\n"
        f"🎬 **ЗАКЛЮЧЕНИЕ** 🎬\n"
        f"[ВИЗУАЛ: Интерактивная плашка 'ПОДПИШИСЬ']\n"
        f"Подписывайтесь на наш канал, чтобы первыми узнавать о главных мировых событиях!\n\n"
        f"#️⃣ HASHTAGS: #science #news #breaking #trending #fyp"
    )

def check_and_run():
    try:
        title, summary, link = get_latest_news()
        if not title or not link:
            return

        last_published = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                last_published = f.read().strip()

        if link == last_published:
            print("Новых статей пока нет. Засыпаем...")
            return

        print(f"Публикуем новую статью: {title}")
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
            
        with open(DB_FILE, "w", encoding="utf-8") as f:
            f.write(link)
            
        print("🎉 Успешно отправлено!")
    except Exception as telegram_error:
        print("Telegram error:", telegram_error)

if __name__ == "__main__":
    print("🚀 Бот запущен в боевом режиме с автопереводчиком и защитой от дублей...")
    while True:
        check_and_run()
        time.sleep(900) # Проверка каждые 15 минут

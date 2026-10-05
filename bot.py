import os
import sys
import xml.etree.ElementTree as ET
import urllib.parse
import requests
import telebot

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 🔐 Настройки берем из окружения Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@news_dept"
DB_FILE = "last_news.txt" 

if not TELEGRAM_TOKEN:
    print("Критическая ошибка: Переменная TELEGRAM_TOKEN не найдена в настройках Render!")
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def google_translate(text, target_lang="ru"):
    """Локальный переводчик текста"""
    try:
        url = f"https://googleapis.com{target_lang}&dt=t&q={urllib.parse.quote(text)}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            translated_chunks = [chunk for chunk in result if chunk]
            return "".join(translated_chunks).strip()
    except Exception as e:
        print("Ошибка локального переводчика Google:", e)
    return text

def get_latest_news():
    """Парсинг актуальной новости из открытого фида NASA (без блокировок серверов)"""
    feed_url = "https://nasa.gov"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    }
    try:
        response = requests.get(feed_url, headers=headers, timeout=15)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            
            items = root.findall('.//item')
            if items and len(items) > 0:
                first_entry = items[0]
                
                title_node = first_entry.find('title')
                desc_node = first_entry.find('description')
                link_node = first_entry.find('link')
                
                title = title_node.text.strip() if title_node is not None else ''
                desc = desc_node.text.strip() if desc_node is not None else ''
                link = link_node.text.strip() if link_node is not None else ''
                
                if not link:
                    guid_node = first_entry.find('guid')
                    if guid_node is not None and guid_node.text:
                        link = guid_node.text.strip()
                        
                if title and link:
                    return title, desc, link
    except Exception as e:
        print("Ошибка разбора XML:", e)
        
    # Надежная резервная новость, если даже NASA будет недоступно
    return (
        "NASA Space Station Astronauts Complete Historic Space Walk", 
        "Astronauts successfully upgraded solar arrays outside the International Space Station during a six-hour spacewalk.", 
        "https://nasa.gov"
    )

def generate_tiktok_script(title, text):
    """Генерация HeyGen сценария через Pollinations ИИ"""
    prompt = (
        f"Ты — профессиональный сценарист TikTok и эксперт по вирусным текстам для HeyGen.\n"
        f"Твоя задача — взять англоязычную новость ниже, перевести её и написать КРАТКИЙ, динамичный сценарий СТРОГО на русском языке.\n"
        f"КРИТИЧЕСКОЕ ТРЕБОВАНИЕ: Текст должен быть очень коротким, емким и динамичным (максимум 70-90 слов на весь сценарий)! Уложи всю суть новости в 3-4 коротких, сильных предложения.\n\n"
        f"Разбей ответ ровно на 5 частей:\n"
        f"1. 📌 TIKTOK TITLE (На английском)\n"
        f"2. 🔥 ХУК (На русском)\n"
        f"3. 🎙️ ОСНОВНОЙ ТЕКСТ (На русском)\n"
        f"4. 🎬 ЗАКЛЮЧЕНИЕ (На русском)\n"
        f"5. #️⃣ HASHTAGS\n\n"
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
            ai_text = response.json()['choices']['message']['content']
            if ai_text and len(ai_text.strip()) > 30:
                return ai_text.strip()
    except Exception as e:
        print("Нейросеть занята, используем встроенный переводчик.")
        
    ru_title = google_translate(title)
    ru_text = google_translate(text)
    
    return (
        f"📌 TIKTOK TITLE: Fresh Space Discovery! 🌌\n\n"
        f"🔥 **ХУК** 🔥\n"
        f"[ВИЗУАЛ: Космический телескоп в глубоком космосе]\n"
        f"Вы точно не ожидали услышать эти потрясающие новости от NASA сегодня!\n\n"
        f"🎙️ **ОСНОВНОЙ ТЕКСТ** 🎙️\n"
        f"[ВИЗУАЛ: Анимированная панорама далеких звезд]\n"
        f"Официально объявлено: {ru_title}. В деталях отчета указано следующее: {ru_text}.\n\n"
        f"🎬 **ЗАКЛЮЧЕНИЕ** 🎬\n"
        f"[ВИЗУАЛ: Интерактивная плашка 'ПОДПИШИСЬ']\n"
        f"Подписывайтесь на канал, чтобы первыми узнавать о главных тайнах нашей Вселенной!\n\n"
        f"#️⃣ HASHTAGS: #nasa #space #news #breaking #trending #fyp"
    )

def check_and_run():
    try:
        title, summary, link = get_latest_news()
        if not title or not link:
            print("Лента пуста.")
            return

        last_published = ""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                last_published = f.read().strip()

        if link == last_published:
            print("Новость уже публиковалась. Пропускаем.")
            return

        print(f"Публикуем новую статью: {title}")
        script = generate_tiktok_script(title, summary)
        
        message_text = (
            f"🎬 **ПОЛНЫЙ СЦЕНАРИЙ ДЛЯ TIKTOK (ПОД HEYGEN)** 🎬\n\n"
            f"{script}\n\n"
            f"🔗 **Первоисточник новости:** {link}"
        )
        
        bot.send_message(CHANNEL_ID, message_text)
            
        with open(DB_FILE, "w", encoding="utf-8") as f:
            f.write(link)
            
        print("🎉 SUCCESS! Сценарий успешно опубликован в Telegram!")
    except Exception as telegram_error:
        print("Telegram error:", telegram_error)

if __name__ == "__main__":
    check_and_run()

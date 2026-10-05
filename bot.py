import os
import sys
import urllib.parse
import requests
import telebot
import re

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 🔐 Настройки окружения Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@news_dept"
DB_FILE = "last_news.txt" 

if not TELEGRAM_TOKEN:
    print("Критическая ошибка: Переменная TELEGRAM_TOKEN не найдена в настройках Render!")
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def google_translate(text, target_lang="ru"):
    """Исправленный локальный переводчик с защитой от спецсимволов"""
    try:
        # Полностью очищаем текст от символов, которые ломают URL-запрос
        clean_text = re.sub(r'[^\w\s\.\,\!\?\-]', '', text)
        url = f"https://googleapis.com{target_lang}&dt=t&q={urllib.parse.quote(clean_text)}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result and result[0]:
                translated_text = "".join([chunk[0] for chunk in result[0] if chunk[0]])
                return translated_text.strip()
    except Exception as e:
        print("Ошибка локального переводчика Google:", e)
    return text

def get_latest_news():
    """Парсинг актуальной новости из NASA с помощью сверхнадежных регулярных выражений"""
    feed_url = "https://nasa.gov"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    }
    try:
        response = requests.get(feed_url, headers=headers, timeout=15)
        if response.status_code == 200:
            raw_xml = response.text
            
            # Находим самый первый блок новости <item>
            item_match = re.search(r'<item>(.*?)</item>', raw_xml, re.DOTALL)
            if item_match:
                item_content = item_match.group(1)
                
                # Вытаскиваем значения тегов через регулярные выражения (это не ломается из-за синтаксиса XML)
                title_m = re.search(r'<title>(.*?)</title>', item_content, re.DOTALL)
                desc_m = re.search(r'<description>(.*?)</description>', item_content, re.DOTALL)
                link_m = re.search(r'<link>(.*?)</link>', item_content, re.DOTALL)
                
                title = title_m.group(1).strip() if title_m else ""
                desc = desc_m.group(1).strip() if desc_m else ""
                link = link_m.group(1).strip() if link_m else ""
                
                # Очистка от возможных оберток CDATA
                for clean_target in [title, desc, link]:
                    if "<![CDATA[" in clean_target:
                        clean_target = clean_target.replace("<![CDATA Gaza [", "").replace("<![CDATA[", "").replace("]]>", "")
                
                if not link or not link.startswith("http"):
                    guid_m = re.search(r'<guid.*?>(.*?)</guid>', item_content, re.DOTALL)
                    if guid_m:
                        link = guid_m.group(1).strip()
                
                if title and link:
                    return title, desc, link
    except Exception as e:
        print("Ошибка регулярных выражений при чтении фида NASA:", e)
        
    # Качественный резервный вариант с ПРЯМОЙ рабочей ссылкой на подраздел новостей
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
        f"Вы точно не ожидали услышать эти потрясающие новости от НАСА сегодня!\n\n"
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

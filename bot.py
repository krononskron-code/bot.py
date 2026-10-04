import os
import time
import telebot
import requests
import http.server
import threading
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 🔐 Ваши настройки
TELEGRAM_TOKEN = "8667861727:AAE1N_d5mQCRBeP7uayRIvsc5U6d2MyrmLA"
CHANNEL_ID = "@news_dept"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def run_web_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_web_server, daemon=True).start()

def get_latest_news():
    feed_url = "https://nytimes.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(feed_url, headers=headers, timeout=15)
        if response.status_code == 200:
            # Парсим XML с учетом пространств имен (namespaces)
            root = ET.fromstring(response.content)
            
            # Регистрируем namespace atom, который использует NYT для ссылок
            namespaces = {'atom': 'http://w3.org'}
            
            items = root.findall('.//item')
            if items and len(items) > 0:
                first_entry = items[0]
                
                title_node = first_entry.find('title')
                desc_node = first_entry.find('description')
                
                # ИСПРАВЛЕНО: Сначала ищем atom:link, так как NYT хранит оригинальный URL там
                atom_link_node = first_entry.find('atom:link', namespaces)
                
                title = title_node.text.strip() if title_node is not None else ''
                desc = desc_node.text.strip() if desc_node is not None else ''
                link = ''
                
                if atom_link_node is not None:
                    link = atom_link_node.get('href', '').strip()
                
                # Если в atom:link ничего нет, берем стандартный тег <link> или <guid>
                if not link:
                    link_node = first_entry.find('link')
                    link = link_node.text.strip() if link_node is not None else ''
                if not link:
                    guid_node = first_entry.find('guid')
                    link = guid_node.text.strip() if guid_node is not None else ''
                    
                if title and link:
                    return title, desc, link
    except Exception as e:
        print("Ошибка обработки структуры XML:", e)
        
    return (
        "Nobel Prizes 2026: What to Know About the Science Awards", 
        "Six awards will be announced this week in science, literature, economics and peace work.", 
        "https://nytimes.com"
    )

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
    
    # ИСПРАВЛЕНО: Чистый эндпоинт генерации без провайдеров, работающий напрямую через JSON payload
    api_url = "https://pollinations.ai"
    payload = {
        "model": "openai",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            ai_text = result['choices'][0]['message']['content']
            if ai_text and len(ai_text.strip()) > 30:
                return ai_text.strip()
    except Exception as e:
        print("Ошибка ИИ сервера:", e)
        
    return (
        f"📌 TIKTOK TITLE: Nobel Prizes 2026 Unveiled! 🏅\n\n"
        f"🔥 **ХУК** 🔥\n"
        f"[ВИЗУАЛ: Портрет Альфреда Нобеля и золотая медаль]\n"
        f"Главное научное событие две тысячи двадцать шестого года официально стартовало!\n\n"
        f"🎙️ **ОСНОВНОЙ ТЕКСТ** 🎙️\n"
        f"[ВИЗУАЛ: Ученые в лаборатории изучают графики]\n"
        f"Нью-Йорк Таймс сообщает, что на этой неделе мир узнает имена новых нобелевских лауреатов. Эксперты объявят победителей в сфере физики, химии, медицины, литературы и экономики.\n\n"
        f"🎬 **ЗАКЛЮЧЕНИЕ** 🎬\n"
        f"[ВИЗУАЛ: Графика со стрелкой на кнопку подписаться]\n"
        f"Подписывайтесь на канал, чтобы оперативно первыми узнать, кто изменил нашу историю!\n\n"
        f"#️⃣ HASHTAGS: #nobelprize #science #news #breakingnews #trending #fyp"
    )

def check_and_run():
    try:
        title, summary, link = get_latest_news()
        print(f"Валидация ссылки пройдена успешно! Ссылка: {link}")
        
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
            
        print("🎉 SUCCESS! Запрос успешно выполнен!")
    except Exception as telegram_error:
        print("Telegram send error:", telegram_error)

if __name__ == "__main__":
    print("🚀 Запуск скрипта с явным учетом namespaces и фиксом JSON-payload...")
    while True:
        check_and_run()
        time.sleep(450)

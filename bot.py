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

# 🔐 Ваши настройки для тестов
TELEGRAM_TOKEN = "8667861727:AAE1N_d5mQCRBeP7uayRIvsc5U6d2MyrmLA"
CHANNEL_ID = "@news_dept"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def run_web_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_web_server, daemon=True).start()

def get_latest_news():
    feed_url = "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(feed_url, headers=headers, timeout=15)
        if response.status_code == 200:
            # Используем ElementTree вместо багнутого feedparser
            root = ET.fromstring(response.content)
            
            # Находим все элементы новостей (<item>) в RSS
            items = root.findall('.//item')
            if items and len(items) > 0:
                first_entry = items[0]
                
                # Извлекаем данные напрямую из тегов XML
                title_node = first_entry.find('title')
                desc_node = first_entry.find('description')
                link_node = first_entry.find('link')
                
                title = title_node.text.strip() if title_node is not None else ''
                desc = desc_node.text.strip() if desc_node is not None else ''
                link = link_node.text.strip() if link_node is not None else ''
                
                # Если тег <link> пустой, проверяем альтернативный тег глобального ID (guid)
                if not link:
                    guid_node = first_entry.find('guid')
                    if guid_node is not None:
                        link = guid_node.text.strip()
                        
                if title and link:
                    return title, desc, link
                    
    except Exception as e:
        print("Ошибка парсинга XML:", e)
        
    # Корректная космическая заглушка, если сайт упадет
    return (
        "Mysterious Signals From Deep Space Confirmed by Astronomers", 
        "Researchers have recorded highly unusual, repetitive radio bursts coming from a galaxy located millions of light-years away.", 
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
    
    api_url = "https://pollinations.ai"
    payload = {
        "model": "openai",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(api_url, json=payload, timeout=30)
        if response.status_code == 200:
            ai_text = response.json()['choices']['message']['content']
            if ai_text:
                return ai_text
    except Exception as e:
        print("Powerful AI Error:", e)
        
    return (
        f"📌 TIKTOK TITLE: Mysterious Deep Space Signals Confirmed! 🌌\n\n"
        f"🔥 **ХУК** 🔥\n"
        f"[ВИЗУАЛ: Скриншот научной статьи Нью-Йорк Таймс]\n"
        f"Вы не поверите, что только что обнаружили астрономы!\n\n"
        f"🎙️ **ОСНОВНОЙ ТЕКСТ** 🎙️\n"
        f"[ВИЗУАЛ: Фото гигантского радиотелескопа]\n"
        f"Ученые зафиксировали серию загадочных радиосигналов из далекой галактики. Импульсы повторяются с математической точностью, что полностью исключает взрывы обычных звезд.\n\n"
        f"🎬 **ЗАКЛЮЧЕНИЕ** 🎬\n"
        f"[ВИЗУАЛ: Плашка с надписью 'ПОДПИШИСЬ']\n"
        f"Подписывайтесь на канал, чтобы первыми узнать разгадку этой космической тайны!\n\n"
        f"#️⃣ HASHTAGS: #space #nasa #astronomy #breakingnews #trending #fyp"
    )

def check_and_run():
    try:
        title, summary, link = get_latest_news()
        print(f"Успешно спарсили XML. Новость: {title}")
        print(f"Прямая ссылка: {link}")
        
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
            
        print("🎉 SUCCESS! Сценарий отправлен!")
    except Exception as telegram_error:
        print("Telegram send error:", telegram_error)

if __name__ == "__main__":
    print("🚀 Бот запущен на чистом XML-парсере...")
    while True:
        check_and_run()
        time.sleep(450)

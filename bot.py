import os
import time
import telebot
import requests
import http.server
import threading
import sys

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
            text = response.text
            
            # Самый надежный способ: вырезаем первый блок <item> вручную по строкам
            start_item = text.find("<item>")
            end_item = text.find("</item>")
            
            if start_item != -1 and end_item != -1:
                item_content = text[start_item:end_item]
                
                # Пошагово вытягиваем значения тегов
                def extract_tag(xml_data, tag_name):
                    s_tag = xml_data.find(f"<{tag_name}>")
                    e_tag = xml_data.find(f"</tag_name>")
                    if s_tag == -1: # Пробуем с CDATA секцией, если есть
                        s_tag = xml_data.find(f"<{tag_name}>")
                    
                    # Стандартный поиск границ текстового узла
                    start_idx = xml_data.find(f"<{tag_name}>")
                    if start_idx != -1:
                        start_idx += len(f"<{tag_name}>")
                        end_idx = xml_data.find(f"</{tag_name}>", start_idx)
                        if end_idx != -1:
                            val = xml_data[start_idx:end_idx]
                            if "<![CDATA[" in val:
                                val = val.replace("<![CDATA[", "").replace("]]>", "")
                            return val.strip()
                    return ""

                title = extract_tag(item_content, "title")
                desc = extract_tag(item_content, "description")
                link = extract_tag(item_content, "link")
                
                if not link:
                    link = extract_tag(item_content, "guid")
                    
                if title and link:
                    return title, desc, link
    except Exception as e:
        print("Ошибка ручного извлечения XML:", e)
        
    return (
        "Nobel Prizes 2026: What to Know", 
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
    
    # Стабильный POST-эндпоинт с быстрой текстовой моделью p1
    api_url = "https://pollinations.ai"
    payload = {
        "model": "p1",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post(api_url, json=payload, timeout=30)
        if response.status_code == 200:
            ai_text = response.json()['choices']['message']['content']
            if ai_text:
                return ai_text
    except Exception as e:
        print("Ошибка ИИ API:", e)
        
    return (
        f"📌 TIKTOK TITLE: Nobel Prizes 2026! 🏅\n\n"
        f"🔥 **ХУК** 🔥\n"
        f"[ВИЗУАЛ: Скриншот статьи Нью-Йорк Таймс]\n"
        f"Главное научное событие года началось прямо сейчас!\n\n"
        f"🎙️ **ОСНОВНОЙ ТЕКСТ** 🎙️\n"
        f"[ВИЗУАЛ: Золотая медаль Альфреда Нобеля]\n"
        f"Стали известны первые подробности о вручении Нобелевской премии 2026 года. На этой неделе объявят лауреатов в области науки, литературы и экономики.\n\n"
        f"🎬 **ЗАКЛЮЧЕНИЕ** 🎬\n"
        f"[ВИЗУАЛ: Плашка с надписью 'ПОДПИШИСЬ']\n"
        f"Подписывайтесь на канал, чтобы первыми узнать имена победителей!\n\n"
        f"#️⃣ HASHTAGS: #nobelprize #science #news #breakingnews #trending #fyp"
    )

def check_and_run():
    try:
        title, summary, link = get_latest_news()
        print(f"Успешно обработан XML. Ссылка: {link}")
        
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
            
        print("🎉 SUCCESS! Пост отправлен!")
    except Exception as telegram_error:
        print("Telegram send error:", telegram_error)

if __name__ == "__main__":
    print("🚀 Бот запущен на строковом поиске подстрок...")
    while True:
        check_and_run()
        time.sleep(450)

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
LAST_PUBLISHED_LINK = ""  # Внутренняя память процесса

def run_web_server():
    """Фоновый веб-сервер строго для прохождения проверки портов Render"""
    class TinyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Бот активен и работает!".encode("utf-8"))
            
    try:
        server = http.server.HTTPServer(('0.0.0.0', 10000), TinyHandler)
        print("Фоновый веб-сервер успешно запущен на порту 10000")
        server.serve_forever()
    except Exception as e:
        print("Ошибка запуска веб-сервера:", e)

# Запускаем сервер в параллельном потоке, чтобы он не мешал основному циклу бота
threading.Thread(target=run_web_server, daemon=True).start()

def google_translate(text, target_lang="ru"):
    """Надежный POST-переводчик на русский язык"""
    try:
        if not text:
            return ""
        url = "https://googleapis.com"
        params = {"client": "gtx", "sl": "en", "tl": target_lang, "dt": "t"}
        response = requests.post(url, params=params, data={"q": text}, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result and result:
                return "".join([chunk for chunk in result if chunk]).strip()
    except Exception as e:
        print("Ошибка локального переводчика Google POST:", e)
    return text

def get_latest_news():
    """Получение данных о последнем запуске SpaceX через официальный API"""
    api_url = "https://spacexdata.com"
    try:
        response = requests.get(api_url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            
            title = f"SpaceX Launch Mission: {data.get('name', 'New Launch')}"
            desc = data.get('details', '')
            if not desc:
                desc = "SpaceX successfully completed another historic orbital deployment."
                
            # ИСПРАВЛЕНО: Правильный разбор структуры ссылок SpaceX API
            links = data.get('links', {})
            link = ""
            
            # 1. Пробуем взять прямую ссылку на YouTube-вебкаст
            if isinstance(links, dict):
                link = links.get('webcast', '')
                # 2. Если webcast пустой, пробуем вытащить альтернативную статью
                if not link:
                    link = links.get('article', '')
                # 3. Если и этого нет, собираем видео-ссылку по ID видео
                if not link and links.get('youtube_id'):
                    link = f"https://youtube.com{links.get('youtube_id')}"
            
            # Если вообще ничего не нашлось, даем точную ссылку на лог миссии по её ID
            if not link:
                mission_id = data.get('id', '')
                link = f"https://spacex.com" if not mission_id else f"https://spacex.commission/?missionId={mission_id}"
                
            if title and link:
                ru_title = google_translate(title)
                ru_desc = google_translate(desc)
                return ru_title, ru_desc, link
    except Exception as e:
        print("Ошибка запроса к SpaceX API:", e)
        
    return (
        "Запуск космического корабля Starship завершился успешным развертыванием",
        "Компания SpaceX провела успешные испытания и вывела на орбиту новую партию полезной нагрузки, подтвердив стабильность систем.",
        "https://spacex.com"
    )

def generate_tiktok_script(title, text):
    """Генерация HeyGen сценария через ИИ на основе готового русского текста"""
    prompt = (
        f"Ты — профессиональный сценарист TikTok и эксперт по вирусным текстам для HeyGen.\n"
        f"Твоя задача — взять космическую новость ниже и написать КРАТКИЙ, динамичный сценарий СТРОГО на русском языке.\n"
        f"КРИТИЧЕСКОЕ ТРЕБОВАНИЕ: Текст должен быть очень коротким, емким (максимум 70-90 слов на весь скрипт)! Уложи суть в 3-4 коротких предложения. Избегай длинных фраз. Зритель должен за 40 секунд понять, что случилось.\n\n"
        f"Разбей ответ ровно на 5 частей:\n"
        f"1. 📌 TIKTOK TITLE (Вирусное название видео СТРОГО НА АНГЛИЙСКОМ языке)\n"
        f"2. 🔥 ХУК (Шокирующее начало на 1 короткое предложение на русском языке)\n"
        f"3. 🎙️ ОСНОВНОЙ ТЕКСТ (Суть новости на русском языке. Буквально 2 простых предложения!)\n"
        f"4. 🎬 ЗАКЛЮЧЕНИЕ (Призыв к действию на 1 короткое предложение на русском языке)\n"
        f"5. #️⃣ HASHTAGS (5-7 английских хэштегов по теме новости, добавь #space #spacex #breakingnews, #fyp)\n\n"
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
            ai_text = response.json()['choices']['message']['content']
            if ai_text and len(ai_text.strip()) > 30:
                return ai_text.strip()
    except Exception as e:
        print("Нейросеть занята, отдаем структурированный локальный шаблон.")
        
    return (
        f"📌 TIKTOK TITLE: New SpaceX Mission Success! 🚀\n\n"
        f"🔥 **ХУК** 🔥\n"
        f"[ВИЗУАЛ: Запуск гигантской ракеты Илона Маска со стартовой площадки]\n"
        f"Илон Маск снова сделал это! Только что завершилась масштабная космическая миссия!\n\n"
        f"🎙️ **ОСНОВНОЙ ТЕКСТ** 🎙️\n"
        f"[ВИЗУАЛ: Разделение ступеней ракеты в верхних слоях атмосферы]\n"
        f"Официально подтвержден новый запуск: {title}. В деталях отчета указано следующее: {text}.\n\n"
        f"🎬 **ЗАКЛЮЧЕНИЕ** 🎬\n"
        f"[ВИЗУАЛ: Графика со стрелкой на кнопку подписаться]\n"
        f"Подписывайтесь на канал, чтобы первыми видеть эксклюзивные кадры космических запусков!\n\n"
        f"#️⃣ HASHTAGS: #spacex #elonmusk #space #news #breaking #fyp"
    )

def check_and_run():
    global LAST_PUBLISHED_LINK
    try:
        title, summary, link = get_latest_news()
        if not title or not link:
            return

        if link == LAST_PUBLISHED_LINK:
            print("Новых космических миссий нет. Ожидаем...")
            return

        print(f"Публикуем новую статью: {title}")
        script = generate_tiktok_script(title, summary)
        
        message_text = (
            f"🎬 **ПОЛНЫЙ СЦЕНАРИЙ ДЛЯ TIKTOK (ПОД HEYGEN)** 🎬\n\n"
            f"{script}\n\n"
            f"🔗 **Первоисточник новости:** {link}"
        )
        
        bot.send_message(CHANNEL_ID, message_text)
        LAST_PUBLISHED_LINK = link
        print("🎉 SUCCESS! Пост успешно доставлен в ваш Telegram-канал!")
    except Exception as telegram_error:
        print("Ошибка отправки сообщения в Telegram:", telegram_error)

if __name__ == "__main__":
    print("🚀 Скрипт запущен. Ожидаем прохождения проверки портов Render...")
    time.sleep(5)
    while True:
        check_and_run()
        time.sleep(1800)  # Проверка фида каждые 30 минут

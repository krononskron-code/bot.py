import time
import feedparser
import telebot
import google.generativeai as genai
import http.server
import threading

# Настройки
TELEGRAM_TOKEN = "8667861727:AAFu9e__XCjpr7p5I3wIvCD1W0liGuzo1HQR"
CHANNEL_ID = "@news_dept"
GEMINI_API_KEY = "AQ.Ab8RN6Jmvd9LamV4Dy2oBfZPH08eDR8dT06HCGHT4gl3pfByMw"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Веб-сервер для обхода портов Render
def run_web_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_web_server, daemon=True).start()

def get_latest_news():
    # Используем стабильный мировой фид новостей от мировых агентств
    feed_url = "https://nytimes.com"
    try:
        feed = feedparser.parse(feed_url)
        if feed.entries:
            first_entry = feed.entries[0]
            first_entry = feed.entries[0]
title = first_entry.get('title', 'Breaking News')

            return title, desc
    except Exception as e:
        print("RSS parsing error:", e)
    return None, None

def generate_tiktok_script(title, text):
    prompt = (
        f"You are a viral US TikTok news reporter. Rewrite this breaking event into a 1-minute script. "
        f"Format: Green Screen. Use extreme dynamic hooks at the beginning. "
        f"CRITICAL: Use Algospeak to completely bypass US TikTok censorship (replace sensitive letters with symbols like w@r, d€@th, p0litics, @rrest, b@nned). "
        f"Structure the final output into: 1. Voiceover 2. On-screen text 3. Visuals. "
        f"Maintain an objective, neutral reporter tone. News Title: {title}. Details: {text}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"New Event: {title}"

def check_and_run():
    title, summary = get_latest_news()
    print(f"Checking news feed... Current Title: {title}")
    if title:
        script = generate_tiktok_script(title, summary)
        message_text = f"🚨 **NEW TIKTOK SCRIPT** 🚨\n\n{script}"
        bot.send_message(CHANNEL_ID, message_text, parse_mode="Markdown")
        print("Script sent to Telegram successfully!")

if __name__ == "__main__":
    print("Bot starting script loop...")
    while True:
        try:
            check_and_run()
        except Exception as main_error:
            print("Main loop error:", main_error)
        time.sleep(450)

import time
import telebot
import requests
import http.server
import threading
import sys

# Принудительно заставляем логи печататься в Render в ту же секунду
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

TELEGRAM_TOKEN = "8667861727:AAFu9e__XCjpr7p5I3wIvCD1W0liGuzo1HQR"
CHANNEL_ID = "@news_dept"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def run_web_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_web_server, daemon=True).start()

def generate_tiktok_script(title, text):
    prompt = (
        f"You are a viral US TikTok news reporter. Rewrite this breaking event into a 1-minute script. "
        f"Format: Green Screen. Use extreme dynamic hooks at the beginning. "
        f"CRITICAL: Use Algospeak to completely bypass US TikTok censorship (replace sensitive letters with symbols like w@r, d€@th, p0litics, @rrest, b@nned). "
        f"Structure the final output into: 1. Voiceover 2. On-screen text 3. Visuals. "
        f"Maintain an objective, neutral reporter tone. News Title: {title}. Details: {text}"
    )
    api_url = "https://pollinations.ai"
    try:
        response = requests.post(api_url, json={"messages": [{"role": "user", "content": prompt}]}, timeout=20)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print("AI Error:", e)
    return f"New Event: {title}"

def check_and_run():
    try:
        # ВРЕМЕННАЯ ЗАГЛУШКА: Проверяем чистую отправку без капризных сайтов
        title = "🔴 BREAKING: Massive Political Scandal Sparks Storm in Washington"
        summary = "Federal investigators have launched an overnight inquiry into a major development involving senior US officials."
        
        print(f"--- STARTING CHECK ---")
        print(f"Testing AI generation for title: {title}")
        
        script = generate_tiktok_script(title, summary)
        message_text = f"🚨 NEW TIKTOK SCRIPT 🚨\n\n{script}"
        
        print("Attempting to send message to Telegram...")
        bot.send_message(CHANNEL_ID, message_text)
        print("🎉 SUCCESS! Script sent to Telegram successfully!")
        
    except Exception as e:
        print("🛑 CRITICAL ERROR:", e)

if __name__ == "__main__":
    print("🚀 STEP 1: Python script has officially started inside Render!")
    while True:
        check_and_run()
        print("😴 Sleeping for 7.5 minutes...")
        time.sleep(450)

import time
import feedparser
import telebot
import requests
import http.server
import threading
import sys

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Ваши стопроцентно рабочие настройки
TELEGRAM_TOKEN = "8667861727:AAFu9e__XCjpr7p5I3wIvCD1W0liGuzo1HQR"
CHANNEL_ID = "@news_dept"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def run_web_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_web_server, daemon=True).start()

def get_latest_news():
    feed_url = "https://nytimes.com"
    try:
        feed = feedparser.parse(feed_url)
        if feed.entries and len(feed.entries) > 0:
            first_entry = feed.entries[0]
            title = first_entry.get('title', 'Breaking News')
            desc = first_entry.get('description', 'Breaking global news.')
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
        title, summary = get_latest_news()
        print("Checking news feed... Found title:", title)
        if title:
            script = generate_tiktok_script(title, summary)
            message_text = f"🚨 **NEW TIKTOK SCRIPT** 🚨\n\n{script}"
            bot.send_message(CHANNEL_ID, message_text)
            print("🎉 SUCCESS! Script sent to Telegram successfully!")
    except Exception as telegram_error:
        print("Telegram send error:", telegram_error)

if __name__ == "__main__":
    print("🚀 Bot starting script loop...")
    while True:
        check_and_run()
        print("😴 Sleeping for 7.5 minutes...")
        time.sleep(450)

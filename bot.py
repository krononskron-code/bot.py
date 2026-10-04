import time
import feedparser
import telebot
import requests
import google.generativeai as genai
import http.server
import threading
import sys

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Вставлен ваш новый рабочий токен и ключи
TELEGRAM_TOKEN = "8667861727:AAE1N_d5mQCRBeP7uayRIvsc5U6d2MyrmLA"
CHANNEL_ID = "@news_dept"
GEMINI_API_KEY = "AQ.Ab8RN6Jmvd9LamV4Dy2oBfZPH08eDR8dT06HCGHT4gl3pfByMw"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def run_web_server():
    server = http.server.HTTPServer(('0.0.0.0', 10000), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()
threading.Thread(target=run_web_server, daemon=True).start()

def get_latest_news():
    feed_url = "https://who.int"
    try:
        feed = feedparser.parse(feed_url)
        if feed.entries and len(feed.entries) > 0:
            first_entry = feed.entries[0]
            title = first_entry.get('title', 'Global Alert')
            desc = first_entry.get('description', 'New global health development.')
            return title, desc
    except Exception as e:
        print("RSS parsing error:", e)
    return "Massive Tech Discovery: New AI System Passes Human Intelligence Test", "Scientists in Silicon Valley have reported a major breakthrough."

def generate_tiktok_script(title, text):
    prompt = (
        f"You are a viral US TikTok news reporter. Rewrite this breaking event into a detailed 1-minute script. "
        f"CRITICAL: Write a long, full script. Do NOT just summarize. Write at least 200 words. "
        f"Format: Green Screen. You MUST include detailed sections:\n\n"
        f"1. 🔥 HOOK (Extreme dynamic beginning to grab attention)\n"
        f"2. 🎙️ VOICEOVER (Exactly what the speaker says, line by line, full text)\n"
        f"3. 📱 ON-SCREEN TEXT (Subtitles for each line using Algospeak to bypass TikTok censorship: w@r, d€@th, p0litics, @rrest, b@nned, sc@ndal, v|rus)\n"
        f"4. 🖼️ VISUALS (What specific image or screenshot to show on the background for each part).\n\n"
        f"Maintain an objective, shocking, and fast-paced reporter tone.\n\n"
        f"News Title: {title}.\nDetails: {text}"
    )
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
    except Exception as e:
        print("Gemini API Error:", e)
    return f"🚨 NEW TIKTOK SCRIPT 🚨\n\nHOOK: You won't believe what just happened!\n\nVOICEOVER: Scientists have just confirmed a massive development. {title}. This could change everything we know about our daily lives. People are already panicking online.\n\nON-SCREEN TEXT: New discovery ch@nges everything! 🤯\n\nVISUALS: Show a screenshot of a breaking news article headline."

def check_and_run():
    try:
        title, summary = get_latest_news()
        print("Checking news feed... Found title:", title)
        if title:
            script = generate_tiktok_script(title, summary)
            
            if len(script) > 4000:
                bot.send_message(CHANNEL_ID, script[:4000])
                bot.send_message(CHANNEL_ID, script[4000:])
            else:
                bot.send_message(CHANNEL_ID, script)
            print("🎉 SUCCESS! Detailed script sent to Telegram successfully!")
    except Exception as telegram_error:
        print("Telegram send error:", telegram_error)

if __name__ == "__main__":
    print("🚀 Bot starting script loop...")
    while True:
        check_and_run()
        print("😴 Sleeping for 7.5 minutes...")
        time.sleep(450)

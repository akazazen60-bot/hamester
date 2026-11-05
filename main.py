import sqlite3
import time
import random
import secrets
import threading
import os
import requests

TOKEN = os.getenv("BALE_BOT_TOKEN", "").strip()
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}/"
ALLOWED_CHAT_ID = None
ADMIN_UID = 818566532  # پنل فقط برای این شناسه؛ در راهنما نمایش داده نمی‌شود.
admin_pending = {}
MISSION_RESET_SECONDS = 24 * 60 * 60
SHOP_OTP_TTL = 26
pending_shop_purchases = {}
pending_shop_lock = threading.Lock()

ANGOSHT_COOLDOWN = 90
BANK_PROFIT_COOLDOWN = 86400
DAILY_COOLDOWN = 86400
ROB_COOLDOWN = 600
DOOZ_TURN_TIMEOUT = 60
HAMSTER_HUNGER_LIMIT = 3600

CARROT_CONFIG = {
    "معمولی": {"cooldown": 900, "cost": 10, "yield": 2, "feed_xp": 1},
    "طلایی": {"cooldown": 3000, "cost": 29, "yield": 1, "feed_xp": 3},
    "الماسی": {"cooldown": 9000, "cost": 50, "yield": 1, "feed_xp": 10},
}

HAMSTER_INCOME = {1: 5, 2: 69, 3: 439}

TREASURE_STAGES = {
    1: [
        {"q": "اگر ۳ ماشین در ۳ دقیقه، ۳ قطعه بسازند؛ ۹ ماشین در ۹ دقیقه چند قطعه می‌سازند؟", "a": "27"},
        {"q": "عدد بعدی دنباله چیست؟ ۲، ۶، ۱۲، ۲۰، ۳۰، ؟", "a": "42"},
        {"q": "کدام سیاره به‌خاطر چرخش تقریباً خوابیده‌اش معروف است؟", "a": "اورانوس"},
        {"q": "حاصل ۱۵ به توان ۲ منهای ۱۰۰ چیست؟", "a": "125"},
        {"q": "در شطرنج کدام مهره می‌تواند از روی مهره‌ها بپرد؟", "a": "اسب"},
        {"q": "اگر امروز سه‌شنبه باشد، ۱۰۰ روز دیگر چه روزی است؟", "a": "پنجشنبه"},
        {"q": "نماد شیمیایی عنصر نقره چیست؟", "a": "ag"},
        {"q": "کدام اقیانوس بزرگ‌ترین اقیانوس زمین است؟", "a": "آرام"},
    ],
    2: [
        {"q": "عدد اول بعد از ۴۰ چیست؟", "a": "41"},
        {"q": "کدام دانشمند قانون جاذبه عمومی را صورت‌بندی کرد؟", "a": "نیوتن"},
        {"q": "اگر x+7=3x-9 باشد، x چند است؟", "a": "8"},
        {"q": "پایتخت کشور کانادا چیست؟", "a": "اتاوا"},
        {"q": "کدام گاز بیشترین سهم جو زمین را دارد؟", "a": "نیتروژن"},
        {"q": "حاصل جذر ۲۰۲۵ چیست؟", "a": "45"},
        {"q": "کدام بخش سلول بیشتر انرژی تولید می‌کند؟", "a": "میتوکندری"},
        {"q": "نام طولانی‌ترین رود آفریقا چیست؟", "a": "نیل"},
    ],
    3: [
        {"q": "در یک ساعت چند درجه زاویه بین عقربه‌های ساعت‌شمار و دقیقه‌شمار طی می‌شود؟ (حرکت نسبی در ۶۰ دقیقه)", "a": "330"},
        {"q": "کوچک‌ترین عددی که بر ۲، ۳، ۴، ۵ و ۶ بخش‌پذیر است چیست؟", "a": "60"},
        {"q": "عنصر با عدد اتمی ۷۹ چیست؟", "a": "طلا"},
        {"q": "کدام لایه جو زمین بیشتر شهاب‌سنگ‌ها را می‌سوزاند؟", "a": "مزوسفر"},
        {"q": "اگر دو تاس سالم بیندازیم، احتمال مجموع ۷ چند حالت از ۳۶ حالت است؟", "a": "6"},
        {"q": "نام فرایندی که گیاهان با نور، غذا می‌سازند چیست؟", "a": "فتوسنتز"},
        {"q": "کدام فلز در دمای اتاق مایع است؟", "a": "جیوه"},
        {"q": "عدد رومی XL چه عددی است؟", "a": "40"},
    ],
    4: [
        {"q": "حاصل ۲۳ به توان ۲ منهای ۱۷۶ چیست؟", "a": "353"},
        {"q": "اگر ۵ کارگر در ۱۲ روز کاری را تمام کنند، ۱۰ کارگر با همان سرعت چند روز نیاز دارند؟", "a": "6"},
        {"q": "عدد بعدی دنباله ۳، ۸، ۱۸، ۳۸، ۷۸ چیست؟", "a": "158"},
        {"q": "کوچک‌ترین عدد سه‌رقمی که بر ۷ و ۹ بخش‌پذیر است چیست؟", "a": "126"},
    ],
    5: [
        {"q": "حاصل ۲ به توان ۱۰ به‌علاوه ۳ به توان ۵ چیست؟", "a": "1267"},
        {"q": "اگر مجموع سه عدد صحیح متوالی ۲۴۶ باشد، عدد میانی چیست؟", "a": "82"},
        {"q": "عدد بعدی دنباله ۲، ۳، ۵، ۹، ۱۷، ۳۳ چیست؟", "a": "65"},
        {"q": "کمترین مضرب مشترک ۱۸ و ۲۸ چند است؟", "a": "252"},
    ]
}

db_lock = threading.Lock()
conn = sqlite3.connect("hamester_ttf.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    coins INTEGER DEFAULT 0,
    bank_coins INTEGER DEFAULT 0,
    last_angosht REAL DEFAULT 0,
    last_bank_profit REAL DEFAULT 0,
    last_daily REAL DEFAULT 0,
    last_rob REAL DEFAULT 0,
    carrot_normal INTEGER DEFAULT 0,
    carrot_gold INTEGER DEFAULT 0,
    carrot_diamond INTEGER DEFAULT 0,
    farm_type TEXT DEFAULT NULL,
    farm_time REAL DEFAULT 0,
    hamster_name TEXT DEFAULT 'همستر بی‌نام',
    hamster_level INTEGER DEFAULT 0,
    hamster_xp INTEGER DEFAULT 0,
    hamster_last_fed REAL DEFAULT 0,
    hamster_last_claim REAL DEFAULT 0,
    treasure_stage INTEGER DEFAULT 0,
    treasure_q_idx INTEGER DEFAULT -1,
    last_treasure REAL DEFAULT 0,
    player_xp INTEGER DEFAULT 0,
    player_level INTEGER DEFAULT 1,
    daily_streak INTEGER DEFAULT 0,
    last_streak_day INTEGER DEFAULT 0,
    last_wheel REAL DEFAULT 0
)
""")
conn.commit()

# Migration: safely add new fields to databases created by older bot versions.
with db_lock:
    existing_cols = {row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()}
    migrations = {
        "last_treasure": "REAL DEFAULT 0", "player_xp": "INTEGER DEFAULT 0",
        "player_level": "INTEGER DEFAULT 1", "daily_streak": "INTEGER DEFAULT 0",
        "last_streak_day": "INTEGER DEFAULT 0", "last_wheel": "REAL DEFAULT 0"
    }
    for col, definition in migrations.items():
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
    cursor.execute("CREATE TABLE IF NOT EXISTS owned_items (user_id INTEGER NOT NULL, item_id TEXT NOT NULL, bought_at REAL NOT NULL, PRIMARY KEY(user_id, item_id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS active_abilities (user_id INTEGER NOT NULL, item_id TEXT NOT NULL, activated_at REAL NOT NULL, PRIMARY KEY(user_id, item_id))")
    # Replace the previous decorative shop catalog with the new ability catalog.
    cursor.execute("DELETE FROM owned_items WHERE item_id IN ('naruto_headband','goku_badge','luffy_hat','tanjiro_earrings','totoro_plush','pikachu_plush','spider_badge','kungfu_scroll')")
    cursor.execute("DELETE FROM active_abilities WHERE item_id NOT IN ('voldemort_wand','batman_cape','krypton','spiderman_mask','batmobile','dragon_ball')")
    cursor.execute("CREATE TABLE IF NOT EXISTS player_materials (user_id INTEGER NOT NULL, material TEXT NOT NULL, quantity INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(user_id, material))")
    # Remove legacy Forge and Auction House data/features from older databases.
    cursor.execute("DROP TABLE IF EXISTS forge_collection")
    cursor.execute("DROP TABLE IF EXISTS forge_catalog")
    cursor.execute("DROP TABLE IF EXISTS forge_jobs")
    cursor.execute("DROP TABLE IF EXISTS auction_listings")

    cursor.execute("CREATE TABLE IF NOT EXISTS purchase_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, item_name TEXT NOT NULL, toman_price INTEGER NOT NULL, coin_price INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at REAL NOT NULL)")
    conn.commit()

with db_lock:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_missions (
        user_id INTEGER PRIMARY KEY,
        reset_at REAL NOT NULL,
        angosht_count INTEGER DEFAULT 0,
        harvest_count INTEGER DEFAULT 0,
        treasure_count INTEGER DEFAULT 0,
        claimed_angosht INTEGER DEFAULT 0,
        claimed_harvest INTEGER DEFAULT 0,
        claimed_treasure INTEGER DEFAULT 0
    )
    """)
    conn.commit()

active_dooz = None
dooz_lock = threading.Lock()

def fa_to_en(text):
    fa_digits = "۰۱۲۳۴۵۶۷۸۹"
    en_digits = "0123456789"
    for f, e in zip(fa_digits, en_digits):
        text = text.replace(f, e)
    return text

def send_message(chat_id, text, reply_to=None, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    nav_row = [{"text": "🏠 منو", "callback_data": "quick_menu"}, {"text": "🫧 🛍️ فروشگاه", "callback_data": "menu_shop"}, {"text": "🫧 👤 پروفایل", "callback_data": "menu_profile"}]
    if reply_markup:
        payload["reply_markup"] = reply_markup
        if isinstance(reply_markup, dict) and "inline_keyboard" in reply_markup:
            reply_markup["inline_keyboard"].append(nav_row)
    else:
        payload["reply_markup"] = {"inline_keyboard": [nav_row]}
    try:
        return requests.post(BASE_URL + "sendMessage", json=payload, timeout=10).json()
    except Exception as e:
        print(f"Error send_message: {e}")
        return None

def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(BASE_URL + "editMessageText", json=payload, timeout=10)
    except Exception as e:
        print(f"Error edit_message: {e}")

def answer_callback(callback_id, text=""):
    payload = {"callback_query_id": callback_id, "text": text}
    try:
        requests.post(BASE_URL + "answerCallbackQuery", json=payload, timeout=5)
    except:
        pass

def get_or_create_user(user_id, username, first_name):
    username = username.lower() if username else ""
    with db_lock:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                (user_id, username, first_name)
            )
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
        else:
            cursor.execute("UPDATE users SET username = ?, first_name = ? WHERE user_id = ?", (username, first_name, user_id))
            conn.commit()
        return row

def get_user_dict(user_id):
    with db_lock:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None
        cols = [col[0] for col in cursor.description]
        return dict(zip(cols, row))

def find_user_by_username(username):
    username = username.lstrip("@").lower()
    with db_lock:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if not row:
            return None
        cols = [col[0] for col in cursor.description]
        return dict(zip(cols, row))

PLAYER_LEVEL_XP = {1: 0, 2: 100, 3: 250, 4: 500, 5: 900, 6: 1400, 7: 2100, 8: 3000, 9: 4200, 10: 5700, 11: 7500}

def calculate_player_level(xp):
    level = 1
    for candidate, needed in PLAYER_LEVEL_XP.items():
        if xp >= needed:
            level = candidate
    return level

def award_player_xp(user_id, amount):
    if amount <= 0:
        return
    with db_lock:
        cursor.execute("UPDATE users SET player_xp = player_xp + ? WHERE user_id = ?", (amount, user_id))
        cursor.execute("SELECT player_xp FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        xp = row[0] if row else 0
        level = calculate_player_level(xp)
        cursor.execute("UPDATE users SET player_level = ? WHERE user_id = ?", (level, user_id))
        conn.commit()

def sync_hamster(user_id):
    u = get_user_dict(user_id)
    if not u or u["hamster_level"] == 0:
        return 0, None

    now = time.time()
    h_lvl = u["hamster_level"]
    last_fed = u["hamster_last_fed"]
    last_claim = u["hamster_last_claim"]
    msg = None

    if now - last_fed > HAMSTER_HUNGER_LIMIT:
        effective_end = last_fed + HAMSTER_HUNGER_LIMIT
        minutes = max(0, int((effective_end - last_claim) // 60))
        earned = minutes * HAMSTER_INCOME.get(h_lvl, 5)

        new_lvl = max(1, h_lvl - 1)
        with db_lock:
            cursor.execute("""
                UPDATE users 
                SET coins = coins + ?, hamster_level = ?, hamster_last_fed = ?, hamster_last_claim = ?, hamster_xp = 0
                WHERE user_id = ?
            """, (earned, new_lvl, now, now, user_id))
            conn.commit()
        if new_lvl < h_lvl:
            msg = f"⚠️ همسترت از گشنگی تلف شد و لولش افتاد روی {new_lvl}! زود بهش هویج بده!"
        else:
            msg = "⚠️ همسترت شدیداً گشنه‌ست! بهش هویج بده تا کوین جمع کنه."
        return earned, msg
    else:
        minutes = int((now - last_claim) // 60)
        if minutes > 0:
            earned = minutes * HAMSTER_INCOME.get(h_lvl, 5)
            new_claim_time = last_claim + (minutes * 60)
            with db_lock:
                cursor.execute("""
                    UPDATE users SET coins = coins + ?, hamster_last_claim = ? WHERE user_id = ?
                """, (earned, new_claim_time, user_id))
                conn.commit()
            return earned, None
        return 0, None

def get_dooz_keyboard(board):
    symbols = {" ": "⬜", "X": "❌", "O": "⭕"}
    inline_kb = []
    for row in range(3):
        btn_row = []
        for col in range(3):
            idx = row * 3 + col
            btn_row.append({
                "text": symbols[board[idx]],
                "callback_data": f"dooz_move_{idx}"
            })
        inline_kb.append(btn_row)
    return {"inline_keyboard": inline_kb}

def check_dooz_winner(b):
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for x, y, z in wins:
        if b[x] != " " and b[x] == b[y] == b[z]:
            return b[x]
    if " " not in b:
        return "DRAW"
    return None

def dooz_timeout_watcher():
    global active_dooz
    while True:
        time.sleep(3)
        with dooz_lock:
            if not active_dooz or active_dooz["status"] != "playing":
                continue
            now = time.time()
            if now - active_dooz["turn_time"] > DOOZ_TURN_TIMEOUT:
                loser_id = active_dooz["turn_user"]
                winner_id = active_dooz["p1"] if loser_id == active_dooz["p2"] else active_dooz["p2"]
                loser_name = active_dooz["p1_name"] if loser_id == active_dooz["p1"] else active_dooz["p2_name"]
                winner_name = active_dooz["p2_name"] if loser_id == active_dooz["p1"] else active_dooz["p1_name"]
                
                entry = active_dooz["entry"]
                penalty = entry * 2

                with db_lock:
                    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (loser_id,))
                    loser_row = cursor.fetchone()
                    loser_coins = loser_row[0] if loser_row else 0
                    actual_penalty = min(max(0, loser_coins - 2), penalty)
                    cursor.execute(
                        "UPDATE users SET coins = coins - ? WHERE user_id = ?",
                        (actual_penalty, loser_id)
                    )
                    cursor.execute(
                        "UPDATE users SET coins = coins + ? WHERE user_id = ?",
                        (actual_penalty, winner_id)
                    )
                    conn.commit()
                wallet_auto_topup(loser_id)

                send_message(
                    active_dooz["chat_id"],
                    f"⏰ وقت تموم شد!\\n"
                    f"کاربر {loser_name} نوبتشو نزد!\\n"
                    f"{actual_penalty} کوین به {winner_name} رسید. 💸"
                )
                active_dooz = None

threading.Thread(target=dooz_timeout_watcher, daemon=True).start()

def ensure_missions(user_id):
    now = time.time()
    with db_lock:
        cursor.execute("SELECT reset_at FROM daily_missions WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            cursor.execute("INSERT INTO daily_missions (user_id, reset_at) VALUES (?, ?)", (user_id, now))
        elif now - row[0] >= MISSION_RESET_SECONDS:
            cursor.execute("""UPDATE daily_missions SET reset_at = ?, angosht_count = 0,
                harvest_count = 0, treasure_count = 0, claimed_angosht = 0,
                claimed_harvest = 0, claimed_treasure = 0 WHERE user_id = ?""", (now, user_id))
        conn.commit()
        cursor.execute("SELECT * FROM daily_missions WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))


def progress_mission(user_id, field):
    if field not in {"angosht_count", "harvest_count", "treasure_count"}:
        return
    ensure_missions(user_id)
    with db_lock:
        cursor.execute(f"UPDATE daily_missions SET {field} = {field} + 1 WHERE user_id = ?", (user_id,))
        conn.commit()


def missions_message(user_id):
    m = ensure_missions(user_id)
    remain = max(0, int(MISSION_RESET_SECONDS - (time.time() - m["reset_at"])))
    hh, rem = divmod(remain, 3600)
    mm = rem // 60
    lines = [
        "🎯 *ماموریت‌های روزانه*",
        "━━━━━━━━━━━━━━━",
        f"{'✅' if m['angosht_count'] >= 3 else '▫️'} انگشت‌زن حرفه‌ای: {min(m['angosht_count'], 3)}/3 (جایزه: ۱۰ کوین)",
        f"{'✅' if m['harvest_count'] >= 1 else '▫️'} کشاورز: {min(m['harvest_count'], 1)}/1 برداشت (جایزه: ۱۵ کوین)",
        f"{'✅' if m['treasure_count'] >= 1 else '▫️'} گنج‌یاب: {min(m['treasure_count'], 1)}/1 تکمیل گنج (جایزه: ۲۵ کوین)",
        "",
        "برای گرفتن جایزه، دکمه‌ی دریافت را بزن. هر ماموریت فقط یک‌بار در هر دوره جایزه دارد.",
        f"⏳ بازنشانی ماموریت‌ها تا {hh} ساعت و {mm} دقیقه دیگر",
    ]
    buttons = [[{"text": "🎁 جایزه انگشت", "callback_data": "mission_claim_angosht"}],
               [{"text": "🎁 جایزه برداشت", "callback_data": "mission_claim_harvest"}],
               [{"text": "🎁 جایزه گنج", "callback_data": "mission_claim_treasure"}],
               [{"text": "🔄 بروزرسانی", "callback_data": "mission_refresh"}]]
    return "\n".join(lines), {"inline_keyboard": buttons}


def admin_panel_text():
    return ("🛡️ *پنل مدیریت*\n━━━━━━━━━━━━━━━\n"
            "یکی از عملیات را انتخاب کن. سطح پلیر از ۱ تا ۱۱ قابل افزایش و کاهش است.")


def admin_panel_keyboard():
    return {"inline_keyboard": [
        [{"text": "➕ دادن کوین", "callback_data": "admin_give"}],
        [{"text": "➖ کم کردن کوین", "callback_data": "admin_take"}],
        [{"text": "⭐ افزایش لول پلیر", "callback_data": "admin_level"}],
        [{"text": "⬇️ کاهش لول پلیر", "callback_data": "admin_level_down"}],
        [{"text": "✖️ بستن پنل", "callback_data": "admin_close"}],
    ]}



SHOP_ITEMS = {
    "voldemort_wand": {
        "name": "چوب جادویی لرد ولدمورت 🪄", "price": 420, "category": "ability",
        "description": "جادوی تاریک گنج‌ها را تقویت می‌کند؛ جایزه نهایی گنج ۲۰٪ بیشتر می‌شود.",
        "effect": "افزایش ۲۰٪ جایزه نهایی گنج"
    },
    "batman_cape": {
        "name": "شنل بتمن 🦇", "price": 500, "category": "ability",
        "description": "با شنل بتمن در تاریکی پنهان می‌شوی و احتمال موفقیت سرقتت بیشتر می‌شود.",
        "effect": "افزایش شانس موفقیت سرقت از ۵۰٪ به ۶۰٪"
    },
    "krypton": {
        "name": "Krypton (کریپتونِ سوپرمن) 🦹‍♀️", "price": 650, "category": "ability",
        "description": "قدرت کریپتونی سرعت رشد محصولات مزرعه را بیشتر می‌کند.",
        "effect": "کاهش ۱۵٪ زمان انتظار رشد هویج"
    },
    "spiderman_mask": {
        "name": "ماسک مرد عنکبوتی 🕷️", "price": 460, "category": "ability",
        "description": "حس عنکبوتی شانس و مهارتت را در بازی انگشت تقویت می‌کند.",
        "effect": "افزایش ۱۰٪ جایزه دستور انگشت"
    },
    "batmobile": {
        "name": "بت‌موبیل (ماشین بتمن) 🏎️", "price": 580, "category": "ability",
        "description": "با بت‌موبیل سریع‌تر به مأموریت بعدی می‌رسی.",
        "effect": "کاهش ۲۰٪ زمان انتظار بین دو سرقت"
    },
    "dragon_ball": {
        "name": "گوی اژدها (Dragon Ball) 🟠", "price": 700, "category": "ability",
        "description": "گوی اژدها انرژی جایزه روزانه‌ات را افزایش می‌دهد.",
        "effect": "افزایش ۱۵٪ جایزه روزانه"
    },
}


def ability_slots(level):
    """تعداد توانایی‌های قابل فعال‌سازی با توجه به لول بازیکن."""
    return min(6, 1 + max(0, level - 1) // 2)


def get_active_abilities(user_id):
    with db_lock:
        cursor.execute("SELECT item_id FROM active_abilities WHERE user_id = ?", (user_id,))
        return {row[0] for row in cursor.fetchall()}


def ability_is_active(user_id, item_id):
    return item_id in get_active_abilities(user_id)


def shop_keyboard():
    rows = []
    for item_id, item in SHOP_ITEMS.items():
        rows.append([{"text": f"🫧 توضیحات {item['name']}", "callback_data": f"shop_info_{item_id}"}])
        rows.append([{"text": f"🪙 خرید با جیب | {item['price']}", "callback_data": f"shop_buy_{item_id}"},
                     {"text": f"🏦 خرید از بانک | {item['price']}", "callback_data": f"shop_buy_bank_{item_id}"}])
    rows.append([{"text": "🎒 کلکسیون و توانایی‌ها", "callback_data": "shop_collection"}, {"text": "🏠 منو", "callback_data": "quick_menu"}])
    return {"inline_keyboard": rows}


def shop_text():
    lines = ["🛍️ *فروشگاه توانایی‌های TTF*", "هر آیتم را یک‌بار بخر؛ بعد از کلکسیون می‌توانی توانایی‌اش را فعال یا غیرفعال کنی.", ""]
    for item in SHOP_ITEMS.values():
        lines.append(f"• *{item['name']}* — {item['price']} کوین\n  ✨ {item['effect']}")
    return "\n".join(lines)


def collection_text(user_id):
    u = get_user_dict(user_id)
    level = calculate_player_level((u or {}).get("player_xp", 0))
    slots = ability_slots(level)
    active = get_active_abilities(user_id)
    with db_lock:
        cursor.execute("SELECT item_id FROM owned_items WHERE user_id = ? ORDER BY bought_at", (user_id,))
        owned = [row[0] for row in cursor.fetchall()]
    owned = [item_id for item_id in owned if item_id in SHOP_ITEMS]
    if not owned:
        return f"🎒 کلکسیونت هنوز خالیه؛ از فروشگاه یک آیتم بخر.\nلول {level}: ظرفیت فعال‌سازی {slots} توانایی."
    lines = [
        "🎒 *کلکسیون و توانایی‌های من*",
        f"⭐ لول پلیر: {level}",
        f"⚡ توانایی‌های فعال: {len(active)} از {slots}",
        "برای هر آیتم دکمه توضیحات یا فعال/غیرفعال را بزن."
    ]
    for item_id in owned:
        item = SHOP_ITEMS[item_id]
        status = "🟢 فعال" if item_id in active else "⚪ غیرفعال"
        lines.append(f"• {item['name']} — {status}")
    return "\n".join(lines)


def collection_keyboard(user_id):
    with db_lock:
        cursor.execute("SELECT item_id FROM owned_items WHERE user_id = ? ORDER BY bought_at", (user_id,))
        owned = [row[0] for row in cursor.fetchall()]
    rows = []
    for item_id in owned:
        if item_id not in SHOP_ITEMS:
            continue
        active = ability_is_active(user_id, item_id)
        rows.append([
            {"text": f"🫧 توضیحات {SHOP_ITEMS[item_id]['name']}", "callback_data": f"ability_info_{item_id}"},
            {"text": "🔴 غیرفعال کن" if active else "🟢 فعال کن", "callback_data": f"ability_toggle_{item_id}"}
        ])
    rows.append([{"text": "🛍️ فروشگاه", "callback_data": "menu_shop"}, {"text": "🏠 منو", "callback_data": "quick_menu"}])
    return {"inline_keyboard": rows}


def ability_info_text(item_id):
    item = SHOP_ITEMS[item_id]
    return (
        f"✨ *{item['name']}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{item['description']}\n\n"
        f"🎯 اثر توانایی: *{item['effect']}*\n"
        "این توانایی فقط وقتی اثر دارد که از کلکسیون فعالش کرده باشی."
    )


def main_menu_keyboard():
    return {"inline_keyboard": [
        [{"text": "🫧 👤 پروفایل", "callback_data": "menu_profile"}, {"text": "🫧 🎯 ماموریت‌ها", "callback_data": "menu_missions"}],
        [{"text": "🫧 💰 انگشت", "callback_data": "menu_angosht"}, {"text": "🫧 🎁 روزانه", "callback_data": "menu_daily"}],
        [{"text": "🫧 🗺️ گنج", "callback_data": "menu_treasure"}, {"text": "🫧 🛍️ فروشگاه", "callback_data": "menu_shop"}],
        [{"text": "🫧 🚜 مزرعه", "callback_data": "menu_farm"}, {"text": "🫧 🏦 بانک", "callback_data": "menu_bank"}],
        [{"text": "🫧 🐹 همستر", "callback_data": "menu_hamster"}, {"text": "🫧 🏆 رتبه‌ها", "callback_data": "menu_leaderboard"}],
        [{"text": "🫧 🎮 دوز", "callback_data": "menu_dooz"}, {"text": "🫧 ❓ راهنما", "callback_data": "menu_help"}],
        [{"text": "🫧 🎡 گردونه شانس", "callback_data": "menu_wheel"}, {"text": "🫧 🔥 استریک", "callback_data": "menu_streak"}],
        [{"text": "🫧 ⚙️ دستورات بیشتر", "callback_data": "menu_more"}],
    ]}



def action_keyboard(rows):
    return {"inline_keyboard": rows + [[{"text": "🏠 منو", "callback_data": "quick_menu"}]]}


def handle_message(msg):
    global active_dooz
    chat_id = msg["chat"]["id"]
    if ALLOWED_CHAT_ID and chat_id != ALLOWED_CHAT_ID:
        return

    if "text" not in msg or "from" not in msg:
        return

    user_id = msg["from"]["id"]
    username = msg["from"].get("username", "")
    first_name = msg["from"].get("first_name", "کاربر")
    msg_id = msg["message_id"]
    text = fa_to_en(msg["text"].strip())

    # Private-message OTP verification for purchases paid from the in-game bank.
    with pending_shop_lock:
        pending = pending_shop_purchases.get(user_id) if msg["chat"].get("type") == "private" else None
        if pending:
            if time.time() > pending["expires_at"]:
                pending_shop_purchases.pop(user_id, None)
                send_message(chat_id, "⌛ کد خرید منقضی شد؛ هیچ کوینی کم نشد. دوباره از فروشگاه درخواست خرید بده.")
                return
            if not text.isdigit() or len(text) != 4:
                send_message(chat_id, "🔐 کد تأیید باید دقیقاً ۴ رقم باشد. تا پایان مهلت کد را بفرست.")
                return
            if not secrets.compare_digest(text, pending["code"]):
                pending["attempts"] += 1
                if pending["attempts"] >= 3:
                    pending_shop_purchases.pop(user_id, None)
                    send_message(chat_id, "❌ سه بار کد اشتباه وارد شد؛ خرید لغو شد و هیچ کوینی کم نشد.")
                else:
                    send_message(chat_id, f"❌ کد اشتباه است. {3-pending['attempts']} فرصت باقی مانده.")
                return
            item_id = pending["item_id"]
            item = SHOP_ITEMS.get(item_id)
            pending_shop_purchases.pop(user_id, None)
        else:
            item = None
    if item is not None:
        with db_lock:
            cursor.execute("SELECT bank_coins FROM users WHERE user_id=?", (user_id,))
            row = cursor.fetchone()
            balance = int(row[0] or 0) if row else 0
            cursor.execute("SELECT 1 FROM owned_items WHERE user_id=? AND item_id=?", (user_id, item_id))
            already_owned = cursor.fetchone() is not None
            if already_owned:
                conn.rollback()
                send_message(chat_id, "این آیتم را قبلاً خریدی؛ مبلغی کسر نشد.")
                return
            if balance < item["price"]:
                conn.rollback()
                send_message(chat_id, "موجودی بانک برای این خرید کافی نیست؛ مبلغی کسر نشد.")
                return
            cursor.execute("UPDATE users SET bank_coins=bank_coins-? WHERE user_id=? AND bank_coins>=?", (item["price"], user_id, item["price"]))
            if cursor.rowcount != 1:
                conn.rollback()
                send_message(chat_id, "موجودی بانک تغییر کرده و کافی نیست؛ خرید انجام نشد.")
                return
            cursor.execute("INSERT INTO owned_items (user_id,item_id,bought_at) VALUES (?,?,?)", (user_id,item_id,time.time()))
            conn.commit()
        award_player_xp(user_id, 15)
        send_message(chat_id, f"✅ خرید *{item['name']}* با موفقیت از بانک داخل بازی انجام شد.\n💰 {item['price']} کوین کسر شد و آیتم به کلکسیونت اضافه شد.")
        return

    get_or_create_user(user_id, username, first_name)
    wallet_auto_topup(user_id)
    sync_hamster(user_id)
    u = get_user_dict(user_id)
    p_level = calculate_player_level(u.get("player_xp", 0))


    # Digikala live search (read-only; checkout is completed on Digikala itself).
    if text.startswith("دیجی کالا ") or text.startswith("جستجوی دیجی کالا "):
        query = text.split(" ", 2)[-1].strip()
        if not query:
            send_message(chat_id, "نام محصول را بعد از «دیجی کالا» بنویس.", reply_to=msg_id); return
        try:
            products = digikala_search(query)
            if not products:
                send_message(chat_id, "محصولی از جست‌وجوی زنده دریافت نشد. می‌توانی درخواست خرید برای ادمین ثبت کنی:\n`درخواست خرید نام محصول | قیمت به تومان`", reply_to=msg_id); return
            rows=[]; lines=[f"🔎 نتایج دیجی‌کالا برای: {query}", "قیمت‌ها ممکن است تغییر کنند؛ خرید در خود سایت انجام می‌شود.", ""]
            for title, price, url in products:
                lines.append(f"• {title}" + (f" — {price:,} تومان" if price else ""))
                rows.append([{"text": title[:48], "url": url}])
            rows.append([{"text":"📨 درخواست خرید از ادمین", "callback_data":"shop_request_help"}])
            send_message(chat_id, "\n".join(lines), reply_to=msg_id, reply_markup={"inline_keyboard":rows}); return
        except Exception as e:
            print("Digikala search error:", e)
            send_message(chat_id, "فعلاً جست‌وجوی زنده دیجی‌کالا در دسترس نیست. از دستور درخواست خرید استفاده کن:\n`درخواست خرید نام محصول | قیمت به تومان`", reply_to=msg_id); return

    if text.startswith("درخواست خرید "):
        raw=text[len("درخواست خرید "):].strip()
        try:
            name, toman = [x.strip() for x in raw.split("|",1)]
            toman=int(fa_to_en(toman).replace(",",""))
            if not name or toman <= 0: raise ValueError
            coins=toman_to_coins(toman)
            with db_lock:
                cursor.execute("INSERT INTO purchase_requests(user_id,item_name,toman_price,coin_price,created_at) VALUES(?,?,?,?,?)", (user_id,name,toman,coins,time.time()))
                req_id=cursor.lastrowid; conn.commit()
            notify_admin(f"📨 درخواست خرید جدید #{req_id}\nکاربر: {user_id} ({first_name})\nآیتم: {name}\nقیمت اعلامی: {toman:,} تومان\nمعادل طبق قانون: {coins} کوین\nپس از بررسی پرداخت، برای تحویل از دستور ادمین استفاده کن: آیتم بده {user_id} | {name} | 1\nتأیید درخواست: درخواست تایید {req_id}")
            send_message(chat_id, f"✅ درخواست #{req_id} برای ادمین فرستاده شد. قیمت اعلامی {toman:,} تومان است و معادل محاسباتی آن {coins} کوین می‌شود. تحویل پس از بررسی و تأیید ادمین انجام می‌شود.", reply_to=msg_id); return
        except Exception:
            send_message(chat_id, "قالب درست نیست. نمونه:\n`درخواست خرید هدفون بی‌سیم | 850000`", reply_to=msg_id); return

    if text.startswith("آیتم بده ") and str(user_id)==str(ADMIN_UID):
        try:
            raw=text[len("آیتم بده "):].strip(); uid,name,qty=raw.split("|",2)
            uid=int(fa_to_en(uid.strip())); name=name.strip(); qty=int(fa_to_en(qty.strip()))
            if not name or qty<1 or not get_user_dict(uid): raise ValueError
            with db_lock:
                cursor.execute("INSERT INTO player_materials(user_id,material,quantity) VALUES(?,?,?) ON CONFLICT(user_id,material) DO UPDATE SET quantity=quantity+excluded.quantity", (uid,name,qty)); conn.commit()
            send_message(chat_id, f"✅ {qty} عدد «{name}» به موجودی کاربر {uid} اضافه شد.")
            send_message(uid, f"🎁 ادمین {qty} عدد «{name}» به موجودی تو اضافه کرد.")
        except Exception:
            send_message(chat_id, "قالب: `آیتم بده شناسه کاربر | نام آیتم | تعداد`")
        return

    if text.startswith("درخواست تایید ") and str(user_id)==str(ADMIN_UID):
        try:
            rid=int(fa_to_en(text.split()[-1]))
            with db_lock:
                cursor.execute("SELECT user_id,item_name,status FROM purchase_requests WHERE id=?",(rid,)); req=cursor.fetchone()
                if not req or req[2] != 'pending': raise ValueError
                cursor.execute("UPDATE purchase_requests SET status='approved' WHERE id=?",(rid,)); conn.commit()
            send_message(req[0], f"✅ درخواست خرید #{rid} توسط ادمین تأیید شد. برای دریافت آیتم، ادمین موجودی‌ات را ثبت می‌کند.")
            send_message(chat_id, f"درخواست #{rid} تأیید شد. برای تحویل: آیتم بده {req[0]} | {req[1]} | 1")
        except Exception:
            send_message(chat_id,"شناسه درخواست نامعتبر است یا قبلاً بررسی شده.")
        return


    if text in ["منو", "منوی اصلی", "دکمه ها", "دکمه‌ها"]:
        kb = main_menu_keyboard()
        send_message(chat_id, "✨ *منوی بازی*\nاز دکمه‌های زیر برای دسترسی سریع استفاده کن:", reply_to=msg_id, reply_markup=kb)
        return

    if text == "دستورات بیشتر":
        more_kb = {"inline_keyboard": [
            [{"text": "🥷 سرقت از کاربر", "callback_data": "prompt_rob"}, {"text": "💸 پرداخت کوین", "callback_data": "prompt_pay"}],
            [{"text": "🏦 واریز کوین", "callback_data": "prompt_deposit"}, {"text": "🏦 برداشت از بانک", "callback_data": "prompt_withdraw"}],
            [{"text": "🐹 تغییر اسم همستر", "callback_data": "prompt_rename"}, {"text": "🎮 شروع دوز", "callback_data": "prompt_dooz"}],
            [{"text": "🏠 منوی اصلی", "callback_data": "quick_menu"}]
        ]}
        send_message(chat_id, "⚙️ *دستورات بیشتر*\nیکی را انتخاب کن تا روش استفاده‌اش را ببینی:", reply_to=msg_id, reply_markup=more_kb)
        return

    if text in ["ماموریت", "ماموریت ها", "ماموریت‌ها", "missions"]:
        body, kb = missions_message(user_id)
        send_message(chat_id, body, reply_to=msg_id, reply_markup=kb)
        return

    # پنل مخفی فقط برای شناسه مدیر پاسخ می‌دهد؛ بررسی شناسه در پیام و callback انجام می‌شود.
    if text in ["پنل مخفی", "admin panel", "/admin"]:
        if str(user_id) == str(ADMIN_UID):
            send_message(chat_id, admin_panel_text(), reply_to=msg_id, reply_markup=admin_panel_keyboard())
        return

    if str(user_id) == str(ADMIN_UID) and user_id in admin_pending:
        mode = admin_pending[user_id]
        parts = text.split()
        try:
            if mode in ("give", "take") and len(parts) == 2:
                target_id, amount = int(parts[0]), int(parts[1])
                if amount <= 0:
                    raise ValueError
                if not get_user_dict(target_id):
                    send_message(chat_id, "❌ این کاربر هنوز در دیتابیس بات ثبت نشده است.", reply_to=msg_id)
                    return
                target = get_user_dict(target_id)
                with db_lock:
                    if mode == "take":
                        amount = min(amount, max(0, target["coins"] - 2))
                    delta = amount if mode == "give" else -amount
                    cursor.execute("UPDATE users SET coins = MAX(2, coins + ?) WHERE user_id = ?", (delta, target_id))
                    conn.commit()
                if mode == "take":
                    wallet_auto_topup(target_id)
                verb = "اضافه شد به" if mode == "give" else "از حسابش کم شد"
                send_message(chat_id, f"✅ {amount} کوین {verb} کاربر {target_id}.", reply_to=msg_id)
                admin_pending.pop(user_id, None)
                return
            if mode in ("level", "level_down") and len(parts) == 2:
                target_id, level = int(parts[0]), int(parts[1])
                target = get_user_dict(target_id)
                if not target or level not in PLAYER_LEVEL_XP or (mode == "level_down" and level >= target.get("player_level", calculate_player_level(target.get("player_xp", 0)))):
                    raise ValueError
                with db_lock:
                    cursor.execute("UPDATE users SET player_xp = ?, player_level = ? WHERE user_id = ?", (PLAYER_LEVEL_XP[level], level, target_id))
                    conn.commit()
                send_message(chat_id, f"✅ لول پلیر کاربر {target_id} روی سطح {level} تنظیم شد.", reply_to=msg_id)
                admin_pending.pop(user_id, None)
                return
        except (ValueError, TypeError):
            send_message(chat_id, "❌ قالب ورودی درست نیست. شناسه و مقدار را با فاصله بفرست؛ برای لول: شناسه و عدد ۱ تا ۱۱.", reply_to=msg_id)
            return

    if text in ["راهنمایی", "راهنما", "کمک"]:
        help_text = (
            "🐹 *راهنمای سریع TTF*\n"
            "از دکمه‌های منو استفاده کن؛ دستورها هم بدون / هستند.\n\n"
            "💰 انگشت | روزانه | پروفایل | لیدربرد\n"
            "🗺️ گنج پنج‌مرحله‌ای (روزی یک‌بار) | ماموریت‌ها\n"
            "🚜 مزرعه: معمولی ۱۰ کوین/۱۵ دقیقه، طلایی ۲۹ کوین/۵۰ دقیقه، الماسی ۵۰ کوین/۱۵۰ دقیقه؛ برداشت با دکمه\n"
            "🏦 بانک: واریز عدد، برداشت بانک عدد، سود بانک؛ هدف جیب ۱۰ و کف اضطراری ۲ کوین\n"
            "🐹 همستر: ساخت همستر، همستر، غذا دادن نوع\n"
            "🛍️ فروشگاه: خرید نام آیتم | کلکسیون\n"
            "🎮 دوز عدد شرط | سرقت (با ریپلای) | پرداخت @آیدی عدد\n"
            "⭐ فعالیت‌ها XP می‌دهند؛ لول پلیر از ۱ تا ۱۱ بالا می‌رود.\n"
             "🎡 گردونه و 🔥 استریک هرکدام روزی یک‌بار جایزه دارند.\\n"
        )
        send_message(chat_id, help_text, reply_to=msg_id)
        return

    if text == "انگشت":
        now = time.time()
        elapsed = now - u["last_angosht"]
        if elapsed < ANGOSHT_COOLDOWN:
            rem = int(ANGOSHT_COOLDOWN - elapsed)
            m, s = divmod(rem, 60)
            send_message(chat_id, f"⏳ عجله نکن ستون! {m} دقیقه و {s} ثانیه دیگه می‌تونی انگشت کنی.", reply_to=msg_id)
            return

        reward = random.randint(1, 50)
        if ability_is_active(user_id, "spiderman_mask"):
            reward = max(1, int(round(reward * 1.10)))
        with db_lock:
            cursor.execute("UPDATE users SET coins = coins + ?, last_angosht = ? WHERE user_id = ?", (reward, now, user_id))
            conn.commit()
        award_player_xp(user_id, 8)
        progress_mission(user_id, "angosht_count")
        send_message(chat_id, f"🎉 شانست گرفت! *{reward} کوین* بردی.\n⭐ +۸ XP پلیر | انگشت بعدی ۹۰ ثانیه دیگر.", reply_to=msg_id)
        return

    if text in ["فروشگاه", "shop"]:
        send_message(chat_id, shop_text(), reply_to=msg_id, reply_markup=shop_keyboard())
        return

    if text in ["کلکسیون", "آیتم‌های من"]:
        send_message(chat_id, collection_text(user_id), reply_to=msg_id, reply_markup=collection_keyboard(user_id))
        return

    if text == "گردونه":
        now = time.time()
        if now - u.get("last_wheel", 0) < DAILY_COOLDOWN:
            remain = int(DAILY_COOLDOWN - (now - u.get("last_wheel", 0)))
            hours, rem = divmod(remain, 3600)
            send_message(chat_id, f"🎡 گردونه را چرخاندی؛ {hours} ساعت و {rem // 60} دقیقه دیگر برگرد.", reply_to=msg_id)
            return
        prize = random.choice([10, 20, 35, 50, 75, 100, 150, 250])
        with db_lock:
            cursor.execute("UPDATE users SET coins = coins + ?, last_wheel = ? WHERE user_id = ?", (prize, now, user_id))
            conn.commit()
        award_player_xp(user_id, 12)
        send_message(chat_id, f"🎡 گردونه چرخید و *{prize} کوین* بردی! (+۱۲ XP)", reply_to=msg_id)
        return

    if text == "استریک":
        today = int(time.time() // 86400)
        last_day = u.get("last_streak_day", 0)
        if last_day == today:
            send_message(chat_id, f"🔥 استریک فعلی تو: {u.get('daily_streak', 0)} روز. جایزه امروز را قبلاً گرفتی.", reply_to=msg_id)
            return
        streak = (u.get("daily_streak", 0) + 1) if last_day == today - 1 else 1
        reward = min(20 + streak * 5, 100)
        with db_lock:
            cursor.execute("UPDATE users SET daily_streak = ?, last_streak_day = ?, coins = coins + ? WHERE user_id = ?", (streak, today, reward, user_id))
            conn.commit()
        award_player_xp(user_id, 10)
        send_message(chat_id, f"🔥 استریک {streak} روزه! *{reward} کوین* گرفتی. هر روز سر بزن تا زنجیره حفظ بشه.", reply_to=msg_id)
        return

    if text in ["لیدربرد", "برترین ها", "رتبه"]:
        with db_lock:
            cursor.execute("""
                SELECT first_name, coins, bank_coins, hamster_level, player_xp
                FROM users
                ORDER BY (coins + bank_coins) DESC LIMIT 10
            """)
            rows = cursor.fetchall()

        lb_text = "🏆 *لیدربرد سلاطین گپ TTF* 🏆\n━━━━━━━━━━━━━━━\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for idx, r in enumerate(rows):
            fname, c, bc, hlvl, xp = r
            tot = c + bc
            lvl = calculate_player_level(xp)
            h_tag = f" | 🐹 لول {hlvl}" if hlvl > 0 else ""
            lb_text += f"{medals[idx]} *{fname}* ⬅️ `{tot}` کوین (لول {lvl}{h_tag})\n"

        send_message(chat_id, lb_text, reply_to=msg_id)
        return

    if text in ["پروفایل", "موجودی"]:
        h_status = "نداری (لول ۳ شو و بزن: ساخت همستر)" if u["hamster_level"] == 0 else f"{u['hamster_name']} (لول {u['hamster_level']})"
        prof_text = (
            f"👤 *پروفایل {first_name}*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⭐ لول پلیر: *{p_level}* | XP: *{u.get('player_xp', 0)}* / {PLAYER_LEVEL_XP.get(min(p_level + 1, 11), 7500)}\n"
            f"💰 کوین جیب: *{u['coins']}*\n"
            f"🏦 کوین بانک: *{u['bank_coins']}*\n"
            f"🐹 همستر: *{h_status}*\n"
            f"🥕 هویج‌ها: معمولی ({u['carrot_normal']}) | طلایی ({u['carrot_gold']}) | الماسی ({u['carrot_diamond']})"
        )
        send_message(chat_id, prof_text, reply_to=msg_id)
        return

    if text == "روزانه":
        now = time.time()
        if now - u["last_daily"] < DAILY_COOLDOWN:
            rem = int(DAILY_COOLDOWN - (now - u["last_daily"]))
            h, rem = divmod(rem, 3600)
            m, _ = divmod(rem, 60)
            send_message(chat_id, f"⏳ جایزه روزانه‌تو گرفتی! {h} ساعت و {m} دقیقه دیگه بیا.", reply_to=msg_id)
            return

        daily_rewards = {1: 5, 2: 10, 3: 18, 4: 30, 5: 50, 6: 80, 7: 120}
        reward = daily_rewards.get(p_level, 5)
        if ability_is_active(user_id, "dragon_ball"):
            reward = int(round(reward * 1.15))
        with db_lock:
            cursor.execute("UPDATE users SET coins = coins + ?, last_daily = ? WHERE user_id = ?", (reward, now, user_id))
            conn.commit()
        wallet_auto_topup(user_id)
        award_player_xp(user_id, 15)
        send_message(chat_id, f"🎁 به خاطر اینکه *لول {p_level}* هستی، جایزه روزانه‌ت *{reward} کوین* به حسابت نشست!", reply_to=msg_id)
        return

    if text == "مزرعه":
        farm_info = "خالی (آماده کاشت)"
        if u["farm_type"]:
            cfg = CARROT_CONFIG[u["farm_type"]]
            rem = int(cfg["cooldown"] - (time.time() - u["farm_time"]))
            if rem <= 0:
                farm_info = f"✅ هویج *{u['farm_type']}* رسیده! بزن `برداشت`"
            else:
                m, s = divmod(rem, 60)
                farm_info = f"🌱 هویج *{u['farm_type']}* در حال رشد ({m} دقیقه و {s} ثانیه مونده)"

        msg_farm = (
            f"🚜 *مزرعه اختصاصی {first_name}*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"وضعیت زمین: {farm_info}\n\n"
            f"📦 *انبار هویج‌های تو:*\n"
            f"🥕 معمولی: `{u['carrot_normal']}`\n"
            f"🥕 طلایی: `{u['carrot_gold']}`\n"
            f"💎 الماسی: `{u['carrot_diamond']}`\n\n"
            f"برای کاشت بنویس:\n"
            f"`کاشت معمولی` (۱۰ کوین - ۱۵ دقیقه)\n"
            f"`کاشت طلایی` (۲۹ کوین - ۵۰ دقیقه)\n"
            f"`کاشت الماسی` (۵۰ کوین - ۱۵۰ دقیقه)"
        )
        send_message(chat_id, msg_farm, reply_to=msg_id, reply_markup=action_keyboard([
            [{"text": "🌱 کاشت معمولی", "callback_data": "action_plant_normal"}, {"text": "🌾 کاشت طلایی", "callback_data": "action_plant_gold"}],
            [{"text": "💎 کاشت الماسی", "callback_data": "action_plant_diamond"}, {"text": "🧺 برداشت", "callback_data": "action_harvest"}],
            [{"text": "🔄 بروزرسانی مزرعه", "callback_data": "action_farm_refresh"}]
        ]))
        return

    if text.startswith("کاشت "):
        c_type = text.replace("کاشت ", "").strip()
        if c_type not in CARROT_CONFIG:
            send_message(chat_id, "❌ نوع هویج نامعتبره! بنویس: `کاشت معمولی`، `کاشت طلایی` یا `کاشت الماسی`", reply_to=msg_id)
            return
        if u["farm_type"] is not None:
            send_message(chat_id, "⚠️ زمینت پره! اول قبلی رو `برداشت` کن.", reply_to=msg_id)
            return

        cfg = CARROT_CONFIG[c_type]
        if u["coins"] - cfg["cost"] < 2:
            send_message(chat_id, f"❌ برای کاشت باید بعد از پرداخت حداقل ۲ کوین در جیبت بماند؛ هزینه هویج {c_type} برابر {cfg['cost']} کوین است.", reply_to=msg_id)
            return

        planted_at = time.time()
        if ability_is_active(user_id, "krypton"):
            planted_at -= cfg["cooldown"] * 0.15
        with db_lock:
            cursor.execute("""
                UPDATE users SET coins = coins - ?, farm_type = ?, farm_time = ? WHERE user_id = ?
            """, (cfg["cost"], c_type, planted_at, user_id))
            conn.commit()
        wallet_auto_topup(user_id)

        send_message(chat_id, f"🌱 بذر هویج *{c_type}* کاشته شد! {cfg['cooldown']//60} دقیقه دیگه بیا بزن `برداشت`.", reply_to=msg_id)
        return

    if text == "برداشت":
        if not u["farm_type"]:
            send_message(chat_id, "❌ چیزی تو مزرعه نکاشتی که بخوای برداشت کنی!", reply_to=msg_id)
            return

        c_type = u["farm_type"]
        cfg = CARROT_CONFIG[c_type]
        elapsed = time.time() - u["farm_time"]
        if elapsed < cfg["cooldown"]:
            rem = int(cfg["cooldown"] - elapsed)
            m, s = divmod(rem, 60)
            send_message(chat_id, f"⏳ هنوز نرسیده! {m} دقیقه و {s} ثانیه دیگه صبر کن.", reply_to=msg_id)
            return

        col_map = {"معمولی": "carrot_normal", "طلایی": "carrot_gold", "الماسی": "carrot_diamond"}
        col = col_map[c_type]
        with db_lock:
            cursor.execute(f"""
                UPDATE users SET {col} = {col} + ?, farm_type = NULL, farm_time = 0 WHERE user_id = ?
            """, (cfg["yield"], user_id))
            conn.commit()

        progress_mission(user_id, "harvest_count")
        award_player_xp(user_id, 20)
        send_message(chat_id, f"🎉 ایول! تعداد *{cfg['yield']} هویج {c_type}* برداشت کردی و رفت تو انبارت!", reply_to=msg_id)
        return

    if text == "بانک":
        send_message(
            chat_id,
            f"🏦 *بانک مرکزی TTF*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 موجودی بانک تو: *{u['bank_coins']} کوین*\n"
            f"👛 موجودی جیبت: *{u['coins']} کوین*\n\n"
            f"• `واریز [عدد]`\n"
            f"• `برداشت بانک [عدد]`\n"
            f"• `سود بانک` (دریافت سود رندوم روزانه)\n\nهدف موجودی جیب ۱۰ کوین است و اگر کمتر شود از بانک تا ۱۰ شارژ می‌شود؛ اگر بانک کافی نباشد، ۲ کوین کف اضطراری و غیرقابل‌خرج است.",
            reply_to=msg_id,
            reply_markup=action_keyboard([[{"text": "📈 سود بانک", "callback_data": "action_bank_profit"}, {"text": "➕ واریز ۱۰", "callback_data": "action_deposit_10"}, {"text": "➖ برداشت ۱۰", "callback_data": "action_withdraw_10"}]])
        )
        return

    if text.startswith("واریز "):
        amt_str = text.replace("واریز ", "").strip()
        if not amt_str.isdigit() or int(amt_str) <= 0:
            send_message(chat_id, "❌ یه عدد درست وارد کن! مثال: `واریز 20`", reply_to=msg_id)
            return
        amt = int(amt_str)
        if u["coins"] - amt < 10:
            send_message(chat_id, "❌ باید حداقل ۱۰ کوین در جیبت بماند؛ این مقدار قابل واریز نیست.", reply_to=msg_id)
            return
        with db_lock:
            cursor.execute("UPDATE users SET coins = coins - ?, bank_coins = bank_coins + ? WHERE user_id = ?", (amt, amt, user_id))
            conn.commit()
        send_message(chat_id, f"✅ مقدار *{amt} کوین* با موفقیت رفت تو بانک!", reply_to=msg_id)
        return

    if text.startswith("برداشت بانک "):
        amt_str = text.replace("برداشت بانک ", "").strip()
        if not amt_str.isdigit() or int(amt_str) <= 0:
            send_message(chat_id, "❌ عدد درست بزن! مثال: `برداشت بانک 20`", reply_to=msg_id)
            return
        amt = int(amt_str)
        if u["bank_coins"] < amt:
            send_message(chat_id, "❌ اینقدر کوین تو بانکت نداری!", reply_to=msg_id)
            return
        with db_lock:
            cursor.execute("UPDATE users SET bank_coins = bank_coins - ?, coins = coins + ? WHERE user_id = ?", (amt, amt, user_id))
            conn.commit()
        send_message(chat_id, f"✅ مقدار *{amt} کوین* از بانک کشیدی بیرون و اومد تو جیبت!", reply_to=msg_id)
        return

    if text == "سود بانک":
        if u["bank_coins"] <= 0:
            send_message(chat_id, "❌ اول باید کوین بذاری تو بانک تا سود بگیری!", reply_to=msg_id)
            return
        now = time.time()
        if now - u["last_bank_profit"] < BANK_PROFIT_COOLDOWN:
            rem = int(BANK_PROFIT_COOLDOWN - (now - u["last_bank_profit"]))
            h, rem = divmod(rem, 3600)
            m, _ = divmod(rem, 60)
            send_message(chat_id, f"⏳ سود امروزتو گرفتی! {h} ساعت و {m} دقیقه دیگه بیا.", reply_to=msg_id)
            return

        percent = random.randint(5, 25)
        profit = max(1, (u["bank_coins"] * percent) // 100)
        with db_lock:
            cursor.execute("UPDATE users SET bank_coins = bank_coins + ?, last_bank_profit = ? WHERE user_id = ?", (profit, now, user_id))
            conn.commit()
        send_message(chat_id, f"📈 شانست باهات یار بود! امروز *{percent}%* سود بهت خورد و *{profit} کوین* رفت رو حساب بانکت!", reply_to=msg_id)
        return

    if text == "ساخت همستر":
        if p_level < 3:
            send_message(chat_id, f"❌ برای تولید همستر باید حداقل *لول ۳* باشی (۲۵۰ XP داشته باشی). الان لول {p_level} هستی!", reply_to=msg_id)
            return
        if u["hamster_level"] > 0:
            send_message(chat_id, "🐹 تو که همستر داری ستون! بزن `همستر` تا وضعیتشو ببینی.", reply_to=msg_id)
            return
        now = time.time()
        with db_lock:
            cursor.execute("""
                UPDATE users SET hamster_level = 1, hamster_last_fed = ?, hamster_last_claim = ? WHERE user_id = ?
            """, (now, now, user_id))
            conn.commit()
        send_message(
            chat_id,
            "🎉 *مبارکه! همسترت متولد شد!* 🐹\n"
            "الان *لول ۱* هست و دقیقه‌ای *۵ کوین* برات استخراج می‌کنه.\n"
            "• برای تغییر اسمش بزن: `اسم همستر [نام]`\n"
            "• یادت نره با هویج‌های مزرعه بهش غذا بدی (`غذا دادن معمولی`) وگرنه گشنه میمونه و لولش میفته!",
            reply_to=msg_id
        )
        return

    if text == "همستر":
        if u["hamster_level"] == 0:
            send_message(chat_id, "❌ هنوز همستر نداری! وقتی رسیدی به *لول ۳*، بنویس `ساخت همستر`.", reply_to=msg_id)
            return
        earned, hunger_msg = sync_hamster(user_id)
        u = get_user_dict(user_id)
        hlvl = u["hamster_level"]
        inc = HAMSTER_INCOME[hlvl]
        rem_hunger = max(0, int(HAMSTER_HUNGER_LIMIT - (time.time() - u["hamster_last_fed"])))
        m_h, s_h = divmod(rem_hunger, 60)

        status_txt = (
            f"🐹 *وضعیت همستر: {u['hamster_name']}*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🔼 لول همستر: *{hlvl}* (نهایت لول ۳)\n"
            f"⚡ درآمد فعلی: *دقیقه‌ای {inc} کوین*\n"
            f"🍖 تایمر گرسنگی: *{m_h} دقیقه و {s_h} ثانیه*\n"
            f"📊 امتیاز غذا برای لول بعد: `{u['hamster_xp']} / {hlvl * 5}`\n"
        )
        if earned > 0:
            status_txt += f"\n💰 همین الان *{earned} کوین* از درآمد همسترت رفت تو جیبت!"
        if hunger_msg:
            status_txt += f"\n\n{hunger_msg}"

        send_message(chat_id, status_txt, reply_to=msg_id, reply_markup=action_keyboard([
            [{"text": "🥕 غذای معمولی", "callback_data": "action_feed_normal"}, {"text": "🥇 غذای طلایی", "callback_data": "action_feed_gold"}],
            [{"text": "💎 غذای الماسی", "callback_data": "action_feed_diamond"}],
            [{"text": "✏️ تغییر نام همستر", "callback_data": "prompt_rename"}, {"text": "🔄 بروزرسانی", "callback_data": "action_hamster_refresh"}]
        ]))
        return

    if text.startswith("اسم همستر "):
        if u["hamster_level"] == 0:
            send_message(chat_id, "❌ اول همستر بساز بعد براش اسم بذار!", reply_to=msg_id)
            return
        new_name = text.replace("اسم همستر ", "").strip()[:25]
        with db_lock:
            cursor.execute("UPDATE users SET hamster_name = ? WHERE user_id = ?", (new_name, user_id))
            conn.commit()
        send_message(chat_id, f"✅ اسم همسترت عوض شد به: *{new_name}* 🐹", reply_to=msg_id)
        return

    if text.startswith("غذا دادن "):
        if u["hamster_level"] == 0:
            send_message(chat_id, "❌ تو هنوز همستر نداری!", reply_to=msg_id)
            return
        c_type = text.replace("غذا دادن ", "").strip()
        col_map = {"معمولی": "carrot_normal", "طلایی": "carrot_gold", "الماسی": "carrot_diamond"}
        if c_type not in col_map:
            send_message(chat_id, "❌ بنویس: `غذا دادن معمولی`، `غذا دادن طلایی` یا `غذا دادن الماسی`", reply_to=msg_id)
            return

        col = col_map[c_type]
        if u[col] <= 0:
            send_message(chat_id, f"❌ هویج *{c_type}* تو انبارت نداری! برو تو `مزرعه` بکار.", reply_to=msg_id)
            return

        xp_gain = CARROT_CONFIG[c_type]["feed_xp"]
        hlvl = u["hamster_level"]
        new_xp = u["hamster_xp"] + xp_gain
        needed_xp = hlvl * 5
        lvl_up_msg = ""

        if hlvl < 3 and new_xp >= needed_xp:
            hlvl += 1
            new_xp = 0
            lvl_up_msg = f"\n🔥 *ایول! همسترت لول‌آپ شد به لول {hlvl}!* الان دقیقه‌ای *{HAMSTER_INCOME[hlvl]} کوین* میده!"

        now = time.time()
        with db_lock:
            cursor.execute(f"""
                UPDATE users 
                SET {col} = {col} - 1, hamster_level = ?, hamster_xp = ?, hamster_last_fed = ?
                WHERE user_id = ?
            """, (hlvl, new_xp, now, user_id))
            conn.commit()

        send_message(chat_id, f"🥕 یه هویج *{c_type}* دادی به *{u['hamster_name']}* و سیر شد! (+{xp_gain} XP){lvl_up_msg}", reply_to=msg_id)
        return

    if text.startswith("پرداخت "):
        parts = text.split()
        if "reply_to_message" in msg and len(parts) == 2 and parts[1].isdigit():
            amt = int(parts[1])
            target_msg = msg["reply_to_message"]["from"]
            target_id = target_msg["id"]
            target_name = target_msg.get("first_name", "کاربر")
            get_or_create_user(target_id, target_msg.get("username", ""), target_name)
        elif len(parts) >= 3 and parts[-1].isdigit():
            amt = int(parts[-1])
            target_username = parts[1]
            target_user = find_user_by_username(target_username)
            if not target_user:
                send_message(chat_id, "❌ این یوزرنیم تو دیتابیس پیدا نشد! (طرف باید حداقل یه پیام تو گپ داده باشه یا روش ریپلای کنی)", reply_to=msg_id)
                return
            target_id = target_user["user_id"]
            target_name = target_user["first_name"]
        else:
            send_message(chat_id, "❌ فرمت درست:\n`پرداخت @username 100`\nیا روی پیام طرف ریپلای کن بنویس: `پرداخت 100`", reply_to=msg_id)
            return

        if amt <= 0:
            send_message(chat_id, "❌ عدد باید بیشتر از صفر باشه!", reply_to=msg_id)
            return
        if target_id == user_id:
            send_message(chat_id, "😐 به خودت میخوای پول بدی؟!", reply_to=msg_id)
            return
        if u["coins"] - amt < 2:
            send_message(chat_id, "❌ باید حداقل ۲ کوین در جیبت بماند؛ این پرداخت ممکن نیست.", reply_to=msg_id)
            return

        with db_lock:
            cursor.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (amt, user_id))
            cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amt, target_id))
            conn.commit()
        wallet_auto_topup(user_id)

        send_message(chat_id, f"💸 انتقال موفق!\n*{amt} کوین* از طرف {first_name} واریز شد به حساب *{target_name}*.", reply_to=msg_id)
        return

    if text == "گنج":
        now = time.time()
        stage = u["treasure_stage"]
        if stage == 0:
            if now - u.get("last_treasure", 0) < DAILY_COOLDOWN:
                remaining = int(DAILY_COOLDOWN - (now - u.get("last_treasure", 0)))
                hours, rem = divmod(remaining, 3600)
                minutes = rem // 60
                send_message(chat_id, f"🗺️ گنج را امروز باز کردی؛ {hours} ساعت و {minutes} دقیقه دیگر برگرد.", reply_to=msg_id)
                return
            stage = 1
            q_idx = random.randrange(len(TREASURE_STAGES[1]))
            with db_lock:
                cursor.execute("UPDATE users SET treasure_stage = 1, treasure_q_idx = ?, last_treasure = ? WHERE user_id = ?", (q_idx, now, user_id))
                conn.commit()
        else:
            q_idx = u["treasure_q_idx"]

        question = TREASURE_STAGES[stage][q_idx]["q"]
        send_message(
            chat_id,
            f"🗺️ *گنجینه TTF - مرحله {stage} از 5*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"❓ سوال: *{question}*\n\n"
            f"برای پاسخ بنویس: `جواب [پاسخ تو]`",
            reply_to=msg_id
        )
        return

    if text.startswith("جواب "):
        if u["treasure_stage"] == 0:
            send_message(chat_id, "❌ هنوز وارد بازی گنج نشدی! اول بنویس `گنج`.", reply_to=msg_id)
            return

        ans = text.replace("جواب ", "").strip().lower()
        stage = u["treasure_stage"]
        q_idx = u["treasure_q_idx"]
        correct_ans = TREASURE_STAGES[stage][q_idx]["a"].lower()

        if ans == correct_ans:
            if stage < 5:
                next_stage = stage + 1
                next_q_idx = random.randrange(len(TREASURE_STAGES[next_stage]))
                with db_lock:
                    cursor.execute("UPDATE users SET treasure_stage = ?, treasure_q_idx = ? WHERE user_id = ?", (next_stage, next_q_idx, user_id))
                    conn.commit()
                next_q = TREASURE_STAGES[next_stage][next_q_idx]["q"]
                send_message(
                    chat_id,
                    f"✅ *درسته باریکلا! رفتی مرحله {next_stage}!*\n\n"
                    f"❓ سوال مرحله {next_stage}: *{next_q}*\n"
                    f"بنویس: `جواب [پاسخ]`",
                    reply_to=msg_id
                )
            else:
                prize = random.randint(20, 80)
                if ability_is_active(user_id, "voldemort_wand"):
                    prize = int(round(prize * 1.20))

                with db_lock:
                    cursor.execute("UPDATE users SET coins = coins + ?, treasure_stage = 0, treasure_q_idx = -1 WHERE user_id = ?", (prize, user_id))
                    conn.commit()
                progress_mission(user_id, "treasure_count")
                award_player_xp(user_id, 100)
                send_message(chat_id, f"👑 *صندوق گنج رو باز کردی!* 👑\nهر ۵ مرحله رو ترکوندی و *{prize} کوین* جایزه رندوم از دل گنج کشیدی بیرون!", reply_to=msg_id)
        else:
            send_message(chat_id, "❌ جوابت اشتباهه! دوباره فکر کن.", reply_to=msg_id)
        return

    if text.startswith("سرقت"):
        now = time.time()
        effective_rob_cooldown = ROB_COOLDOWN * (0.8 if ability_is_active(user_id, "batmobile") else 1.0)
        if now - u["last_rob"] < effective_rob_cooldown:
            rem = int(effective_rob_cooldown - (now - u["last_rob"]))
            m, s = divmod(rem, 60)
            send_message(chat_id, f"🚓 پلیس دنبالته! {m} دقیقه و {s} ثانیه دیگه می‌تونی دوباره سرقت کنی.", reply_to=msg_id)
            return

        target_id = None
        target_name = None
        parts = text.split()
        if "reply_to_message" in msg:
            t_from = msg["reply_to_message"]["from"]
            target_id = t_from["id"]
            target_name = t_from.get("first_name", "کاربر")
            get_or_create_user(target_id, t_from.get("username", ""), target_name)
        elif len(parts) >= 2:
            t_user = find_user_by_username(parts[1])
            if t_user:
                target_id = t_user["user_id"]
                target_name = t_user["first_name"]

        if not target_id or target_id == user_id:
            send_message(chat_id, "❌ روی پیام قربانی ریپلای کن بنویس `سرقت` یا بنویس `سرقت @username`", reply_to=msg_id)
            return

        t_data = get_user_dict(target_id)
        if not t_data or t_data["coins"] <= 2:
            send_message(chat_id, "😂 جیب این بازیکن فقط موجودی اضطراری دارد و قابل سرقت نیست!", reply_to=msg_id)
            return

        with db_lock:
            cursor.execute("UPDATE users SET last_rob = ? WHERE user_id = ?", (now, user_id))
            conn.commit()

        success_chance = 0.60 if ability_is_active(user_id, "batman_cape") else 0.50
        if random.random() < success_chance:
            stolen = random.randint(1, max(1, (t_data["coins"] - 2) // 3))
            stolen = min(stolen, t_data["coins"] - 2)
            with db_lock:
                cursor.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (stolen, target_id))
                cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (stolen, user_id))
                conn.commit()
            wallet_auto_topup(target_id)
            wallet_auto_topup(user_id)
            send_message(chat_id, f"🥷 *سرقت موفق!*\nدزدکی دست کردی تو جیب {target_name} و *{stolen} کوین* کش رفتی!", reply_to=msg_id)
        else:
            fine = min(max(0, u["coins"] - 2), random.randint(2, 10))
            with db_lock:
                cursor.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (fine, user_id))
                cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (fine, target_id))
                conn.commit()
            wallet_auto_topup(user_id)
            wallet_auto_topup(target_id)
            send_message(chat_id, f"🚨 *گیر افتادی!*\nموقع دزدی از {target_name} لو رفتی و *{fine} کوین* غرامت دادی بهش!", reply_to=msg_id)
        return

    if text == "دوز راهنما":
        send_message(chat_id, "🎮 برای شروع بازی، مقدار کل جایزه را بفرست؛ مثال: *دوز 100* (ورودی هر نفر ۵۰ کوین است).", reply_to=msg_id)
        return

    if text.startswith("دوز "):
        bet_str = text.replace("دوز ", "").strip()
        if not bet_str.isdigit() or int(bet_str) < 2:
            send_message(chat_id, "❌ عدد شرط باید حداقل ۲ باشه! مثال: `دوز 100` (ورودی میشه ۵۰)", reply_to=msg_id)
            return

        bet = int(bet_str)
        entry = bet // 2

        with dooz_lock:
            if active_dooz is not None:
                send_message(chat_id, "⚠️ یه بازی دوز همین الان بازه! تا اون تموم نشه نمیشه بازی جدید باز کرد.", reply_to=msg_id)
                return

            if u["coins"] - entry < 2:
                send_message(chat_id, f"❌ برای باز کردن `دوز {bet}` باید حداقل ورودی یعنی *{entry} کوین* تو جیبت داشته باشی!", reply_to=msg_id)
                return

            active_dooz = {
                "chat_id": chat_id,
                "status": "waiting",
                "bet": bet,
                "entry": entry,
                "p1": user_id,
                "p1_name": first_name,
                "p2": None,
                "p2_name": None,
                "board": [" "] * 9,
                "turn_user": user_id,
                "turn_time": time.time(),
            }

            kb = {
                "inline_keyboard": [
                    [{"text": f"⚔️ قبول شرط (ورودی: {entry} کوین)", "callback_data": "dooz_join"}],
                    [{"text": "❌ انصراف سازنده", "callback_data": "dooz_cancel"}]
                ]
            }
            send_message(
                chat_id,
                f"🎲 *چالش بازی دوز باز شد!*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"👤 سازنده: *{first_name}*\n"
                f"💰 کل جایزه میز: *{bet} کوین*\n"
                f"🎟️ ورودی هر نفر: *{entry} کوین*\n"
                f"⚠️ جریمه نزدن نوبت (۶۰ ثانیه): کسر ۲ برابر ورودی ({entry*2} کوین)!\n\n"
                f"کی جرات داره بیاد وسط؟ رو دکمه زیر بزن!",
                reply_to=msg_id,
                reply_markup=kb
            )
        return

def handle_callback(cb):
    global active_dooz
    cb_id = cb["id"]
    user_id = cb["from"]["id"]
    first_name = cb["from"].get("first_name", "کاربر")
    username = cb["from"].get("username", "")
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]
    data = cb["data"]

    get_or_create_user(user_id, username, first_name)
    wallet_auto_topup(user_id)

    if data.startswith("admin_"):
        if str(user_id) != str(ADMIN_UID):
            answer_callback(cb_id, "دسترسی ندارید.")
            return
        actions = {"admin_give": ("give", "شناسه عددی کاربر و مقدار کوین را بفرست. مثال: 123456 50"),
                   "admin_take": ("take", "شناسه عددی کاربر و مقدار کوین برای کسر را بفرست. مثال: 123456 20"),
                   "admin_level": ("level", "شناسه کاربر و لول موردنظر (۱ تا ۱۱) را بفرست. مثال: 123456 4"),
                   "admin_level_down": ("level_down", "شناسه کاربر و لول جدید (۱ تا ۱۱، کمتر از لول فعلی) را بفرست. مثال: 123456 2")}
        if data == "admin_close":
            edit_message(chat_id, msg_id, "پنل مدیریت بسته شد.")
        elif data in actions:
            admin_pending[user_id] = actions[data][0]
            send_message(chat_id, actions[data][1])
        answer_callback(cb_id)
        return

    if data.startswith("action_"):
        action_map = {
            "action_plant_normal": "کاشت معمولی", "action_plant_gold": "کاشت طلایی",
            "action_plant_diamond": "کاشت الماسی", "action_harvest": "برداشت",
            "action_bank_profit": "سود بانک", "action_deposit_10": "واریز 10",
            "action_withdraw_10": "برداشت بانک 10", "action_feed_normal": "غذا دادن معمولی",
            "action_feed_gold": "غذا دادن طلایی", "action_feed_diamond": "غذا دادن الماسی",
            "action_farm_refresh": "مزرعه", "action_hamster_refresh": "همستر"
        }
        command = action_map.get(data)
        answer_callback(cb_id)
        if command:
            synthetic = {"message_id": msg_id, "chat": {"id": chat_id},
                         "from": {"id": user_id, "username": username, "first_name": first_name}, "text": command}
            handle_message(synthetic)
        return

    if data.startswith("prompt_"):
        prompts = {
            "prompt_rob": "🥷 برای سرقت، روی پیام کاربر ریپلای کن و بنویس: *سرقت* (هر ۱۰ دقیقه یک‌بار).",
            "prompt_pay": "💸 برای پرداخت بنویس: *پرداخت @username 50* یا روی پیام کاربر ریپلای کن و بنویس: *پرداخت 50*.",
            "prompt_deposit": "🏦 برای واریز بنویس: *واریز 50* (به‌جای ۵۰ عدد دلخواهت را بگذار).",
            "prompt_withdraw": "🏦 برای برداشت بنویس: *برداشت بانک 50*.",
            "prompt_rename": "🐹 برای تغییر اسم بنویس: *اسم همستر اسم‌جدید*.",
            "prompt_dooz": "🎮 برای شروع دوز بنویس: *دوز 100*؛ ورودی هر نفر نصف مبلغ است."
        }
        answer_callback(cb_id)
        send_message(chat_id, prompts.get(data, "دستور پیدا نشد."), reply_markup={"inline_keyboard": [[{"text": "🫧 ⚙️ دستورات بیشتر", "callback_data": "menu_more"}, {"text": "🏠 منو", "callback_data": "quick_menu"}]]})
        return

    if data == "quick_menu":
        edit_message(chat_id, msg_id, "✨ *منوی اصلی بازی*\nیکی از بخش‌ها را انتخاب کن:", reply_markup=main_menu_keyboard())
        answer_callback(cb_id)
        return

    if data == "shop_collection":
        edit_message(chat_id, msg_id, collection_text(user_id), reply_markup=collection_keyboard(user_id))
        answer_callback(cb_id)
        return

    if data.startswith("shop_info_"):
        item_id = data.replace("shop_info_", "", 1)
        if item_id not in SHOP_ITEMS:
            answer_callback(cb_id, "این آیتم وجود ندارد.")
            return
        edit_message(chat_id, msg_id, ability_info_text(item_id), reply_markup={"inline_keyboard": [[{"text": "🛍️ بازگشت به فروشگاه", "callback_data": "menu_shop"}], [{"text": "🎒 کلکسیون", "callback_data": "shop_collection"}]]})
        answer_callback(cb_id)
        return

    if data.startswith("ability_info_"):
        item_id = data.replace("ability_info_", "", 1)
        if item_id not in SHOP_ITEMS:
            answer_callback(cb_id, "این توانایی وجود ندارد.")
            return
        with db_lock:
            cursor.execute("SELECT 1 FROM owned_items WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            owned = cursor.fetchone() is not None
        if not owned:
            answer_callback(cb_id, "اول باید این آیتم را از فروشگاه بخری.")
            return
        edit_message(chat_id, msg_id, ability_info_text(item_id), reply_markup=collection_keyboard(user_id))
        answer_callback(cb_id)
        return

    if data.startswith("ability_toggle_"):
        item_id = data.replace("ability_toggle_", "", 1)
        if item_id not in SHOP_ITEMS:
            answer_callback(cb_id, "این توانایی وجود ندارد.")
            return
        with db_lock:
            cursor.execute("SELECT 1 FROM owned_items WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            owned = cursor.fetchone() is not None
            if not owned:
                answer_callback(cb_id, "اول باید این آیتم را از فروشگاه بخری.")
                return
            cursor.execute("SELECT 1 FROM active_abilities WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            is_active = cursor.fetchone() is not None
            if is_active:
                cursor.execute("DELETE FROM active_abilities WHERE user_id = ? AND item_id = ?", (user_id, item_id))
                notice = "توانایی غیرفعال شد."
            else:
                cursor.execute("SELECT player_xp FROM users WHERE user_id = ?", (user_id,))
                player_row = cursor.fetchone()
                level = calculate_player_level(player_row[0] if player_row else 0)
                limit = ability_slots(level)
                cursor.execute("SELECT COUNT(*) FROM active_abilities WHERE user_id = ?", (user_id,))
                active_count = cursor.fetchone()[0]
                if active_count >= limit:
                    answer_callback(cb_id, f"ظرفیتت پره! لول {level} فقط {limit} توانایی هم‌زمان می‌تونه فعال داشته باشه.")
                    return
                cursor.execute("INSERT OR IGNORE INTO active_abilities (user_id, item_id, activated_at) VALUES (?, ?, ?)", (user_id, item_id, time.time()))
                notice = "توانایی فعال شد!"
            conn.commit()
        edit_message(chat_id, msg_id, collection_text(user_id), reply_markup=collection_keyboard(user_id))
        answer_callback(cb_id, notice)
        return

    if data.startswith("shop_buy_bank_"):
        item_id = data.replace("shop_buy_bank_", "", 1)
        item = SHOP_ITEMS.get(item_id)
        if not item:
            answer_callback(cb_id, "این آیتم وجود ندارد.")
            return
        with db_lock:
            cursor.execute("SELECT bank_coins FROM users WHERE user_id=?", (user_id,))
            row = cursor.fetchone()
            balance = int(row[0] or 0) if row else 0
            cursor.execute("SELECT 1 FROM owned_items WHERE user_id=? AND item_id=?", (user_id,item_id))
            owned = cursor.fetchone() is not None
        if owned:
            answer_callback(cb_id, "این آیتم را قبلاً خریدی.")
            return
        if balance < item["price"]:
            answer_callback(cb_id, "موجودی بانک داخل بازی کافی نیست.")
            return
        code = f"{secrets.randbelow(10000):04d}"
        with pending_shop_lock:
            pending_shop_purchases[user_id] = {"item_id":item_id,"code":code,"expires_at":time.time()+SHOP_OTP_TTL,"attempts":0}
        dm = send_message(user_id, f"🔐 تأیید خرید\nآیتم: {item['name']}\nمبلغ: {item['price']} کوین از بانک داخل بازی\n\nکد ۴ رقمی: {code}\n⏳ اعتبار کد: ۲۶ ثانیه\nکد را در همین گفت‌وگوی خصوصی برای ربات بفرست.")
        if not dm or not dm.get("ok"):
            with pending_shop_lock:
                pending_shop_purchases.pop(user_id, None)
            answer_callback(cb_id, "ارسال پیام خصوصی ناموفق بود. ابتدا ربات را در خصوصی Start کن.")
            return
        answer_callback(cb_id, "کد ۴ رقمی به خصوصی ربات فرستاده شد؛ ۲۶ ثانیه فرصت داری.")
        return

    if data.startswith("shop_buy_"):
        item_id = data.replace("shop_buy_", "", 1)
        item = SHOP_ITEMS.get(item_id)
        buyer = get_user_dict(user_id)
        if not item:
            answer_callback(cb_id, "این آیتم وجود ندارد.")
            return
        with db_lock:
            cursor.execute("SELECT 1 FROM owned_items WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            already_owned = cursor.fetchone() is not None
            if already_owned:
                answer_callback(cb_id, "این آیتم را قبلاً خریدی.")
                return
            if buyer["coins"] - item["price"] < 2:
                answer_callback(cb_id, "باید بعد از خرید حداقل ۲ کوین در جیبت بماند.")
                return
            cursor.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (item["price"], user_id))
            cursor.execute("INSERT INTO owned_items (user_id, item_id, bought_at) VALUES (?, ?, ?)", (user_id, item_id, time.time()))
            conn.commit()
        wallet_auto_topup(user_id)
        award_player_xp(user_id, 15)
        answer_callback(cb_id, "خرید انجام شد! +۱۵ XP")
        edit_message(chat_id, msg_id, shop_text() + f"\n\n✅ *{item['name']}* به کلکسیونت اضافه شد.", reply_markup=shop_keyboard())
        return

    if data.startswith("mission_"):
        ensure_missions(user_id)
        if data == "mission_refresh":
            body, kb = missions_message(user_id)
            edit_message(chat_id, msg_id, body, reply_markup=kb)
            answer_callback(cb_id, "بروزرسانی شد.")
            return
        mission = data.replace("mission_claim_", "")
        specs = {"angosht": ("angosht_count", "claimed_angosht", 3, 10),
                 "harvest": ("harvest_count", "claimed_harvest", 1, 15),
                 "treasure": ("treasure_count", "claimed_treasure", 1, 25)}
        if mission not in specs:
            answer_callback(cb_id)
            return
        count_col, claim_col, goal, reward = specs[mission]
        with db_lock:
            cursor.execute(f"SELECT {count_col}, {claim_col} FROM daily_missions WHERE user_id = ?", (user_id,))
            progress, claimed = cursor.fetchone()
            if progress < goal:
                answer_callback(cb_id, "هنوز این ماموریت کامل نشده!")
                return
            if claimed:
                answer_callback(cb_id, "جایزه این ماموریت را قبلاً گرفتی.")
                return
            cursor.execute(f"UPDATE daily_missions SET {claim_col} = 1 WHERE user_id = ?", (user_id,))
            cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (reward, user_id))
            conn.commit()
        body, kb = missions_message(user_id)
        edit_message(chat_id, msg_id, body + f"\n\n🎉 {reward} کوین به حسابت اضافه شد!", reply_markup=kb)
        answer_callback(cb_id, "جایزه دریافت شد!")
        return

    if data == "shop_request_help":
        answer_callback(cb_id)
        send_message(chat_id,"برای درخواست محصول بنویس:\n`درخواست خرید نام محصول | قیمت به تومان`\nدرخواست برای ادمین ارسال می‌شود؛ تحویل پس از بررسی و تأیید دستی انجام خواهد شد.")
        return

    if data.startswith("menu_"):
        actions = {"menu_profile": "پروفایل", "menu_missions": "ماموریت‌ها", "menu_angosht": "انگشت",
                   "menu_daily": "روزانه", "menu_farm": "مزرعه", "menu_bank": "بانک",
                   "menu_hamster": "همستر", "menu_help": "راهنما", "menu_treasure": "گنج",
                   "menu_shop": "فروشگاه", "menu_leaderboard": "لیدربرد", "menu_wheel": "گردونه",
                   "menu_streak": "استریک", "menu_dooz": "دوز راهنما", "menu_more": "دستورات بیشتر"}
        command = actions.get(data)
        answer_callback(cb_id)
        if command:
            synthetic = {"message_id": msg_id, "chat": {"id": chat_id},
                         "from": {"id": user_id, "username": username, "first_name": first_name}, "text": command}
            handle_message(synthetic)
        return

    with dooz_lock:
        if not active_dooz:
            answer_callback(cb_id, "این بازی دیگه تموم شده!")
            return

        if data == "dooz_cancel":
            if user_id != active_dooz["p1"] or active_dooz["status"] != "waiting":
                answer_callback(cb_id, "فقط سازنده قبل از شروع میتونه لغو کنه!")
                return
            active_dooz = None
            edit_message(chat_id, msg_id, "❌ بازی دوز توسط سازنده لغو شد.")
            return

        if data == "dooz_join":
            if active_dooz["status"] != "waiting":
                answer_callback(cb_id, "بازی قبلاً شروع شده!")
                return
            if user_id == active_dooz["p1"]:
                answer_callback(cb_id, "با خودت که نمیتونی بازی کنی ستون!")
                return

            p1_data = get_user_dict(active_dooz["p1"])
            p2_data = get_user_dict(user_id)
            entry = active_dooz["entry"]

            if p1_data["coins"] - entry < 2:
                active_dooz = None
                edit_message(chat_id, msg_id, "❌ سازنده بازی کوینش کم شد و بازی لغو شد!")
                return
            if p2_data["coins"] - entry < 2:
                answer_callback(cb_id, f"کوینت کمه! {entry} کوین ورودی میخواد.")
                return

            with db_lock:
                cursor.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (entry, active_dooz["p1"]))
                cursor.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (entry, user_id))
                conn.commit()
            wallet_auto_topup(active_dooz["p1"])
            wallet_auto_topup(user_id)

            active_dooz["status"] = "playing"
            active_dooz["p2"] = user_id
            active_dooz["p2_name"] = first_name
            active_dooz["turn_user"] = active_dooz["p1"]
            active_dooz["turn_time"] = time.time()

            edit_message(
                chat_id,
                msg_id,
                f"⚔️ *بازی دوز شروع شد!* (جایزه: {active_dooz['bet']} کوین)\n"
                f"❌ {active_dooz['p1_name']}\n"
                f"⭕ {active_dooz['p2_name']}\n\n"
                f"👈 نوبت: *{active_dooz['p1_name']}* (۶۰ ثانیه وقت داری)",
                reply_markup=get_dooz_keyboard(active_dooz["board"])
            )
            return

        if data.startswith("dooz_move_"):
            if active_dooz["status"] != "playing":
                return
            if user_id != active_dooz["turn_user"]:
                answer_callback(cb_id, "نوبت تو نیست!")
                return

            try:
                idx = int(data.split("_")[-1])
            except (ValueError, IndexError):
                answer_callback(cb_id, "حرکت نامعتبره!")
                return
            if not 0 <= idx < 9:
                answer_callback(cb_id, "حرکت نامعتبره!")
                return
            if active_dooz["board"][idx] != " ":
                answer_callback(cb_id, "این خونه پره!")
                return

            symbol = "X" if user_id == active_dooz["p1"] else "O"
            active_dooz["board"][idx] = symbol
            winner = check_dooz_winner(active_dooz["board"])

            if winner in ["X", "O"]:
                win_id = active_dooz["p1"] if winner == "X" else active_dooz["p2"]
                win_name = active_dooz["p1_name"] if winner == "X" else active_dooz["p2_name"]
                pot = active_dooz["bet"]
                with db_lock:
                    cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (pot, win_id))
                    conn.commit()
                award_player_xp(win_id, 30)
                edit_message(
                    chat_id,
                    msg_id,
                    f"🏆 *پایان بازی دوز!*\n"
                    f"برنده میدان: *{win_name}* 🎉\n"
                    f"مقدار *{pot} کوین* رفت تو جیبش!",
                    reply_markup=get_dooz_keyboard(active_dooz["board"])
                )
                active_dooz = None
                return

            elif winner == "DRAW":
                entry = active_dooz["entry"]
                with db_lock:
                    cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (entry, active_dooz["p1"]))
                    cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (entry, active_dooz["p2"]))
                    conn.commit()
                edit_message(
                    chat_id,
                    msg_id,
                    f"🤝 *بازی مساوی شد!*\nورودی هر دو نفر ({entry} کوین) برگشت به جیبشون.",
                    reply_markup=get_dooz_keyboard(active_dooz["board"])
                )
                active_dooz = None
                return

            else:
                next_user = active_dooz["p2"] if user_id == active_dooz["p1"] else active_dooz["p1"]
                next_name = active_dooz["p2_name"] if user_id == active_dooz["p1"] else active_dooz["p1_name"]
                active_dooz["turn_user"] = next_user
                active_dooz["turn_time"] = time.time()

                edit_message(
                    chat_id,
                    msg_id,
                    f"⚔️ *بازی دوز در جریانه!* (جایزه: {active_dooz['bet']} کوین)\n"
                    f"❌ {active_dooz['p1_name']}\n"
                    f"⭕ {active_dooz['p2_name']}\n\n"
                    f"👈 نوبت: *{next_name}* (۶۰ ثانیه وقت داری)",
                    reply_markup=get_dooz_keyboard(active_dooz["board"])
                )


# --- Digikala requests and wallet rules ---
MIN_PLAY_WALLET = 2
NORMAL_WALLET_TARGET = 10


def toman_to_coins(toman):
    """Rule 2: below 100k, each started 1k = 1 coin; from 100k upward, each started 100k = 5 coins."""
    toman = max(0, int(toman))
    if toman == 0:
        return 0
    if toman < 100_000:
        return (toman + 999) // 1000
    return ((toman + 99_999) // 100_000) * 5


def wallet_auto_topup(user_id):
    """Keep the wallet at 10 when possible by transferring available bank coins."""
    with db_lock:
        cursor.execute("SELECT coins, bank_coins FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return 0, 0
        wallet, bank = int(row[0] or 0), int(row[1] or 0)
        if wallet < NORMAL_WALLET_TARGET and bank > 0:
            transfer = min(bank, NORMAL_WALLET_TARGET - wallet)
            cursor.execute("UPDATE users SET coins=coins+?, bank_coins=bank_coins-? WHERE user_id=?", (transfer, transfer, user_id))
            conn.commit()
            wallet += transfer
            bank -= transfer
        return wallet, bank


def has_play_wallet(user_id, chat_id):
    wallet, _ = wallet_auto_topup(user_id)
    if wallet < MIN_PLAY_WALLET:
        send_message(chat_id, f"موجودی قابل استفاده نداری. کف اضطراری کیف پول ۲ کوین است؛ بانک هم موجودی ندارد. موجودی فعلی: {wallet} کوین.")
        return False
    return True


def digikala_search(query):
    """Read-only search against Digikala's public web search endpoint; no checkout/payment."""
    from urllib.parse import quote
    url = "https://api.digikala.com/v1/search/?q=" + quote(query)
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
    response.raise_for_status()
    payload = response.json()
    found = []
    def walk(obj):
        if isinstance(obj, dict):
            title = obj.get("title_fa") or obj.get("title") or obj.get("name")
            pid = obj.get("id")
            price = obj.get("selling_price") or obj.get("price") or obj.get("selling_price_toman")
            if title and pid and ("product" in str(obj.get("url", "")) or "selling_price" in obj or "price" in obj):
                try:
                    price = int(price or 0)
                except (ValueError, TypeError):
                    price = 0
                # Digikala API commonly reports price in Rial; convert to Toman when clearly Rial.
                if price >= 10000:
                    price //= 10
                product_url = obj.get("url") or f"https://www.digikala.com/product/dkp-{pid}/"
                if product_url.startswith("/"):
                    product_url = "https://www.digikala.com" + product_url
                found.append((str(title)[:90], price, product_url))
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)
    walk(payload)
    unique=[]; seen=set()
    for item in found:
        if item[2] not in seen:
            unique.append(item); seen.add(item[2])
        if len(unique) >= 8:
            break
    return unique


def notify_admin(text):
    try:
        send_message(ADMIN_UID, text)
    except Exception:
        pass



def main():
    if not TOKEN:
        raise SystemExit("خطا: متغیر محیطی BALE_BOT_TOKEN تنظیم نشده است.")
    print("Hamster Bot (TTF Edition) is running...")
    offset = 0
    while True:
        try:
            resp = requests.get(
                BASE_URL + "getUpdates",
                params={"offset": offset, "timeout": 20},
                timeout=25
            ).json()

            if resp.get("ok"):
                for update in resp.get("result", []):
                    offset = update["update_id"] + 1
                    if "message" in update:
                        handle_message(update["message"])
                    elif "callback_query" in update:
                        handle_callback(update["callback_query"])
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()

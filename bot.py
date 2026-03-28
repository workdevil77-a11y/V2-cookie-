import telebot
from telebot import types
import sqlite3
import time
import random

# --- CONFIGURATION ---
API_TOKEN = '8216719604:AAEpBL7bwpF5qEnBbB4D_D3UKqzzcutWgxE' 
ADMIN_ID = 6806787718  # Apni Numerical ID yahan daalein

bot = telebot.TeleBot(API_TOKEN)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('cookie_premium_v9.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
                      (id INTEGER PRIMARY KEY, min_qty INTEGER, price INTEGER, qr_file_id TEXT, stock INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings VALUES (1, 30, 5, 'None', 600)")
    conn.commit()
    conn.close()

def get_settings():
    conn = sqlite3.connect('cookie_premium_v9.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT min_qty, price, qr_file_id, stock FROM settings WHERE id=1")
    data = cursor.fetchone()
    conn.close()
    return {"min_qty": data[0], "price": data[1], "qr_file_id": data[2], "stock": data[3]}

def update_db(column, value):
    conn = sqlite3.connect('cookie_premium_v9.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE settings SET {column} = ? WHERE id=1", (value,))
    conn.commit()
    conn.close()

# --- CLASSIC ANIMATION ---
def old_style_anim(chat_id, text):
    msg = bot.send_message(chat_id, "✨")
    frames = ["🔍 Searching...", "📡 Connecting...", "⚙️ Processing...", "✅ Done!"]
    for f in frames:
        time.sleep(0.4)
        try: bot.edit_message_text(f"{text}\n{f}", chat_id, msg.message_id, parse_mode="Markdown")
        except: pass
    return msg.message_id

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.chat.id
    name = message.from_user.first_name
    
    try: bot.set_message_reaction(user_id, message.message_id, [types.ReactionTypeEmoji("🔥")], is_big=False)
    except: pass

    conn = sqlite3.connect('cookie_premium_v9.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users VALUES (?)", (user_id,))
        conn.commit()
        alert = (f"🚀 *NEW PREMIUM USER*\n"
                 f"━━━━━━━━━━━━━━━━━━━━━\n"
                 f"👤 Name: {name}\n"
                 f"🆔 ID: `{user_id}`")
        bot.send_message(ADMIN_ID, alert, parse_mode="Markdown")
    conn.close()

    aid = old_style_anim(user_id, f"WELCOME {name.upper()}")
    time.sleep(0.3)
    bot.delete_message(user_id, aid)

    if user_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🖼️ SET QR", callback_data="adm_qr"),
            types.InlineKeyboardButton("📦 ADD STOCK", callback_data="adm_stock"),
            types.InlineKeyboardButton("💰 SET PRICE", callback_data="adm_price"),
            types.InlineKeyboardButton("🔢 SET MIN QTY", callback_data="adm_min"),
            types.InlineKeyboardButton("📊 STATS", callback_data="adm_stats")
        )
        bot.send_message(user_id, "🤴 *BOSS ADMIN PANEL*\nManage your premium store:", reply_markup=markup, parse_mode="Markdown")
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛒 OPEN STORE & BUY NOW", callback_data="user_buy"))
        
        welcome_text = (f"💞 HELLO {name.upper()}! 💞\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n"
                        f"✨ *Premium Instagram Cookies*\n"
                        f"✨ *Instant Delivery | 24/7 Support*\n\n"
                        f"Store open karne ke liye niche click karein 👇")
        bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode="Markdown")

# --- ADMIN UPDATES ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_callbacks(call):
    if call.data == "adm_qr":
        msg = bot.send_message(ADMIN_ID, "📸 Send QR Photo:")
        bot.register_next_step_handler(msg, lambda m: [update_db('qr_file_id', m.photo[-1].file_id), bot.send_message(ADMIN_ID, "✅ New QR Saved!")])
    elif call.data == "adm_stock":
        msg = bot.send_message(ADMIN_ID, "➕ How much stock to add?")
        bot.register_next_step_handler(msg, lambda m: [update_db('stock', get_settings()['stock'] + int(m.text)), bot.send_message(ADMIN_ID, "✅ New Stock Saved!")])
    elif call.data == "adm_price":
        msg = bot.send_message(ADMIN_ID, "💰 Enter New Price:")
        bot.register_next_step_handler(msg, lambda m: [update_db('price', int(m.text)), bot.send_message(ADMIN_ID, "✅ New Price Saved!")])
    elif call.data == "adm_min":
        msg = bot.send_message(ADMIN_ID, "🔢 Enter New Minimum Quantity:")
        bot.register_next_step_handler(msg, lambda m: [update_db('min_qty', int(m.text)), bot.send_message(ADMIN_ID, "✅ New Min Qty Saved!")])
    elif call.data == "adm_stats":
        s = get_settings()
        bot.send_message(ADMIN_ID, f"📊 LIVE STATS\nStock: {s['stock']}\nPrice: {s['price']}₹\nMin: {s['min_qty']}")

# --- PREMIUM BUYING FLOW ---
@bot.callback_query_handler(func=lambda call: call.data == "user_buy")
def user_buy(call):
    config = get_settings()
    if config['qr_file_id'] == 'None':
        bot.answer_callback_query(call.id, "❌ Admin QR not set!", show_alert=True)
        return
    
    aid = old_style_anim(call.message.chat.id, "LOADING PREMIUM STORE")
    bot.delete_message(call.message.chat.id, aid)

    store_text = (f"🏪 STORE STATUS: ONLINE\n"
                  f"━━━━━━━━━━━━━━━━━━━━━\n"
                  f"📂 Item: Instagram Cookie\n"
                  f"📊 Available: {config['stock']}\n"
                  f"💰 Rate: {config['price']}₹ per pc\n"
                  f"⚠️ Min Order: {config['min_qty']}\n\n"
                  f"💞 How many do you want to buy?\n"
                  f"Type the quantity now:")
    
    msg = bot.send_message(call.message.chat.id, store_text, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_order)

def process_order(message):
    config = get_settings()
    try:
        qty = int(message.text)
        if qty < config['min_qty']:
            bot.reply_to(message, f"❌ Minimum order {config['min_qty']} pieces ka hai.")
        elif qty > config['stock']:
            bot.reply_to(message, "❌ Utna stock available nahi hai!")
        else:
            total = qty * config['price']
            oid = random.randint(1000, 9999)
            
            caption = (f"🧾 PREMIUM INVOICE 💞\n"
                       f"━━━━━━━━━━━━━━━━━━━━━\n"
                       f"🆔 ORDER ID: #{oid}\n"
                       f"🔢 Qty: {qty}\n"
                       f"💵 Total: {total}₹\n"
                       f"━━━━━━━━━━━━━━━━━━━━━\n"
                       f"📸 Payment ka screenshot bhejein.")
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ I HAVE PAID", callback_data=f"paid_{qty}_{oid}"))
            bot.send_photo(message.chat.id, config['qr_file_id'], caption=caption, reply_markup=markup, parse_mode="Markdown")
    except: bot.reply_to(message, "⚠️ Sirf number likhein!")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("paid_", "dec_")))
def handle_callbacks(call):
    if call.data.startswith("paid_"):
        bot.send_message(call.message.chat.id, "📸 Screenshot upload karein:")
        bot.register_next_step_handler(call.message, admin_review, call.data.split("_")[1], call.data.split("_")[2])
    elif call.data.startswith("dec_ok"):
        _, _, uid, qty = call.data.split("_")
        update_db('stock', get_settings()['stock'] - int(qty))
        bot.send_message(uid, "✅ *ORDER APPROVED!*\nAdmin will contact you soon for delivery.", parse_mode="Markdown")
        bot.edit_message_caption("PROCESSED ✅", ADMIN_ID, call.message.message_id)

def admin_review(message, qty, oid):
    if message.content_type == 'photo':
        # --- SCREENSHOT ANIMATION ---
        user_id = message.chat.id
        status_msg = bot.send_message(user_id, "⏳")
        
        frames = [
            "📂 *Processing Proof...*",
            "📡 *Connecting to Admin...*",
            "📨 *Sending Order Details...*",
            "✅ *Order Sent to Admin!*"
        ]
        
        for frame in frames:
            time.sleep(0.5)
            try: bot.edit_message_text(frame, user_id, status_msg.message_id, parse_mode="Markdown")
            except: pass
        
        time.sleep(1)
        bot.delete_message(user_id, status_msg.message_id)
        bot.send_message(user_id, f"🔥 *ORDER #{oid} SUBMITTED!*\nVerification ke baad delivery mil jayegi.", parse_mode="Markdown")

        # Admin Notification
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ APPROVE", callback_data=f"dec_ok_{user_id}_{qty}"),
                   types.InlineKeyboardButton("❌ REJECT", callback_data=f"dec_no_{user_id}"))
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                       caption=f"🚀 *NEW ORDER RECEIVED*\n━━━━━━━━━━━━━━━━━━━━━\n🆔 Order ID: #{oid}\n👤 User ID: `{user_id}`\n🔢 Qty: {qty}", 
                       reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Photo bhejein!")

if __name__ == "__main__":
    init_db()
    print("💎 VIP Premium Store is Running...")
    bot.infinity_polling()
  

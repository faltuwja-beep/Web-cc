import time
import requests
import telebot
from flask import Flask
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8765709173:AAHaDmKQzPnQv1nLkpYlvN8KNALxpPMEstA"
ADMIN_ID = 7161571409
REQUIRED_CHANNEL = "@eraningwithask"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is Active!"

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        if member.status in ["member", "creator", "administrator"]:
            return True
    except:
        pass
    return False

def get_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🛒 Buy Likes Plan"),
        KeyboardButton("💰 Add Money"),
        KeyboardButton("💼 My Wallet"),
        KeyboardButton("🔍 FF UID Info"),
        KeyboardButton("👥 Refer & Earn"),
        KeyboardButton("📜 History"),
        KeyboardButton("🤖 AI Support")
    )
    if user_id == ADMIN_ID:
        markup.add(KeyboardButton("👑 Admin Panel"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Join Channel", url="https://t.me/eraningwithask"))
        markup.add(InlineKeyboardButton("✅ Verify", callback_data="check"))
        bot.send_message(message.chat.id, "Pehle channel join karein:", reply_markup=markup)
        return
    bot.send_message(message.chat.id, "Swagat hai! Menu niche hai:", reply_markup=get_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "check":
        if check_subscription(call.from_user.id):
            bot.answer_callback_query(call.id, "Verified!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "Unlock ho gaya!", reply_markup=get_keyboard(call.from_user.id))
        else:
            bot.answer_callback_query(call.id, "Pehle join karo!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def text_handler(message):
    text = message.text
    if text == "🛒 Buy Likes Plan":
        bot.reply_to(message, "Plans: \n1. ₹59 - 15 Days\n2. ₹99 - 30 Days")
    elif text == "💼 My Wallet":
        bot.reply_to(message, "Aapka balance: ₹0")
    elif text == "🤖 AI Support":
        bot.reply_to(message, "AI Support active hai. Sawal puchein ya @Xenon_ask9 par sampark karein.")
    else:
        bot.reply_to(message, "Sahi option chunein.")

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    

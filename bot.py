import os
import threading
import time
import requests
import telebot
from flask import Flask
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# Configuration & Credentials
TOKEN = "8765709173:AAHaDmKQzPnQv1nLkpYlvN8KNALxpPMEstA"
ADMIN_ID = 7161571409
REQUIRED_CHANNEL = "@eraningwithask"
AI_API_KEY = "AQ.Ab8RN6JGzoIesCfV8RONnPq3ySr5TMzDx7vm8dGAVDeNpFIOhg"

CURRENT_UPI_ID = "sima6241@ptaxis"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)


@app.route("/")
def home():
  return "⚡ Prime Tips Bot is Online & Running Smoothly! 🚀"


user_balances = {}
user_state = {}
user_timers = {}
active_users = set()
user_history = {}
user_referrals = {}


def check_subscription(user_id):
  try:
    member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
    if member.status in ["member", "creator", "administrator"]:
      return True
  except Exception:
    pass
  return False


def get_main_keyboard(user_id):
  markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(
      KeyboardButton("🛒 Buy Plans (Likes) 💎"),
      KeyboardButton("💰 Add Money (Wallet) 💳"),
      KeyboardButton("💼 My Wallet 📊"),
      KeyboardButton("🔍 Free Fire UID Info 🎮"),
      KeyboardButton("👥 Refer & Earn 🎁"),
      KeyboardButton("📜 History 📜"),
      KeyboardButton("🤖 AI Support Assistant 🧠"),
  )
  if user_id == ADMIN_ID:
    markup.add(KeyboardButton("👑 Admin Panel ⚡"))
  return markup


def add_history(user_id, action_text):
  if user_id not in user_history:
    user_history[user_id] = []
  user_history[user_id].insert(0, action_text)
  if len(user_history[user_id]) > 5:
    user_history[user_id].pop()


def format_countdown(expiry_timestamp):
  remaining = int(expiry_timestamp - time.time())
  if remaining <= 0:
    return "⏰ Plan Expired!"
  days = remaining // 86400
  hours = (remaining % 86400) // 3600
  minutes = (remaining % 3600) // 60
  seconds = remaining % 60
  return "⏳ " + str(days) + " Din " + str(hours) + " Ghante baaki hain 🔥"


def get_ai_response(prompt_text):
  try:
    time.sleep(0.5)
    query = prompt_text.lower()
    if "like" in query:
      return (
          "🤖 *Prime Tips AI Assistant:*\n\n🔥 Free Fire profile me likes"
          " badhane ke liye aap hamare 15 Days (₹59) ya 30 Days (₹99) wale VIP"
          " plans kharid sakte hain! ⚡"
      )
    elif "wallet" in query or "paisa" in query:
      return (
          "💳 *Prime Tips AI Assistant:*\n\nApne wallet me balance add karne ke"
          " liye 'Add Money (Wallet)' par click karein aur di gayi UPI ID par"
          " payment karein. 💰"
      )
    else:
      return (
          "🤖 *Prime Tips AI Assistant:*\n\nAapka swagat hai! Free Fire plans"
          " ya likes ke liye niche diye gaye buttons ka use karein. 🌟"
      )
  except Exception:
    return "🤖 Namaste! Main aapki kya sahayta kar sakta hoon? ✨"


@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.from_user.id
  active_users.add(user_id)

  args = message.text.split()
  if len(args) > 1 and args[1].startswith("ref_"):
    try:
      referrer_id = int(args[1].split("_")[1])
      if referrer_id != user_id:
        user_balances[referrer_id] = user_balances.get(referrer_id, 0) + 5
        bot.send_message(
            referrer_id,
            "🎉 Referral Reward Mil Gaya! Aapke wallet me ₹5 add kar diye gaye"
            " hain! 💰",
        )
    except Exception:
      pass

  if not check_subscription(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            "📢 Join Official Channel 🚀", url="https://t.me/eraningwithask"
        ),
        InlineKeyboardButton(
            "🔄 Verify Subscription ✅", callback_data="check_join"
        ),
    )
    bot.send_message(
        message.chat.id,
        "⚠️ *Access Restricted!*\n\nPehle hamara official channel join karein"
        " aur phir 'Verify Subscription' par click karein.",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  bot.send_message(
      message.chat.id,
      "🌟 *Swagat hai Prime Tips Bot me!* Neeche diye gaye options se chunein"
      " 👇",
      reply_markup=get_main_keyboard(user_id),
      parse_mode="Markdown",
  )


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
  chat_id = call.message.chat.id
  user_id = call.from_user.id

  if call.data == "check_join":
    if check_subscription(user_id):
      bot.answer_callback_query(call.id, "✅ Verification Successful!")
      bot.delete_message(chat_id, call.message.message_id)
      bot.send_message(
          chat_id,
          "✨ *Hub Unlock Ho Gaya!* 🚀",
          reply_markup=get_main_keyboard(user_id),
          parse_mode="Markdown",
      )
    else:
      bot.answer_callback_query(
          call.id, "❌ Kripya pehle channel join karein!", show_alert=True
      )

  elif call.data in ["buy_59", "buy_99"]:
    plan_cost = 59 if call.data == "buy_59" else 99
    days = 15 if call.data == "buy_59" else 30
    current_bal = user_balances.get(user_id, 0)

    if current_bal < plan_cost:
      bot.answer_callback_query(
          call.id,
          "❌ Wallet me balance kam hai! Required: ₹" + str(plan_cost),
          show_alert=True,
      )
      return

    user_balances[user_id] -= plan_cost
    user_state[user_id] = "waiting_for_plan_uid_" + str(days)

    bot.send_message(
        chat_id,
        "✅ *Payment Successful!*\nAb apna target Free Fire UID bhejein:",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )

  elif call.data.startswith("approve_"):
    if user_id != ADMIN_ID:
      return
    _, target_user_id, amount = call.data.split("_")
    target_user_id, amount = int(target_user_id), int(amount)
    user_balances[target_user_id] = (
        user_balances.get(target_user_id, 0) + amount
    )
    add_history(target_user_id, "Added ₹" + str(amount) + " via Admin approval")
    bot.answer_callback_query(call.id, "Approved!")
    bot.edit_message_text(
        "✅ Deposit Approved! User ID: "
        + str(target_user_id)
        + " | Added: ₹"
        + str(amount),
        chat_id=chat_id,
        message_id=call.message.message_id,
    )
    bot.send_message(
        target_user_id,
        "🎉 Deposit Confirmed! Aapka ₹"
        + str(amount)
        + " approve ho gaya hai. 💰",
    )

  elif call.data.startswith("reject_"):
    if user_id != ADMIN_ID:
      return
    _, target_user_id, amount = call.data.split("_")
    target_user_id = int(target_user_id)
    bot.answer_callback_query(call.id, "Rejected.")
    bot.edit_message_text(
        "❌ Deposit Rejected for User ID: " + str(target_user_id),
        chat_id=chat_id,
        message_id=call.message.message_id,
    )
    bot.send_message(target_user_id, "❌ Aapka deposit proof reject ho gaya hai.")


@bot.message_handler(func=lambda message: True)
def handle_text(message):
  global CURRENT_UPI_ID
  user_id = message.from_user.id
  text = message.text.strip()
  state = user_state.get(user_id)
  username = (
      ("@" + message.from_user.username)
      if message.from_user.username
      else message.from_user.first_name
  )

  if state == "waiting_for_broadcast" and user_id == ADMIN_ID:
    user_state.pop(user_id, None)
    for uid in active_users:
      try:
        bot.send_message(uid, "📢 *Announcement:*\n\n" + text, parse_mode="Markdown")
      except Exception:
        pass
    bot.reply_to(
        message,
        "✅ Broadcast bhej diya gaya hai!",
        reply_markup=get_main_keyboard(user_id),
    )
    return

  if state == "waiting_for_new_upi" and user_id == ADMIN_ID:
    user_state.pop(user_id, None)
    CURRENT_UPI_ID = text
    bot.reply_to(
        message,
        "✅ UPI ID update ho gayi hai: " + CURRENT_UPI_ID,
        reply_markup=get_main_keyboard(user_id),
    )
    return

  if state == "ai_support_chat":
    if text == "🔙 Exit AI Support":
      user_state.pop(user_id, None)
      bot.send_message(
          message.chat.id,
          "🤖 AI Support band kar diya gaya hai.",
          reply_markup=get_main_keyboard(user_id),
      )
      return
    bot.send_message(
        message.chat.id, get_ai_response(text), parse_mode="Markdown"
    )
    return

  if text.startswith("🛒 Buy Plans"):
    user_state.pop(user_id, None)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            "💎 15 Days Plan (₹59)", callback_data="buy_59"
        ),
        InlineKeyboardButton(
            "💎 30 Days Plan (₹99)", callback_data="buy_99"
        ),
    )
    bot.send_message(
        message.chat.id,
        "📦 *Plans:*\n• ₹59: 15 Days (220 Likes/Day)\n• ₹99: 30 Days (220"
        " Likes/Day)",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  elif text.startswith("💰 Add Money"):
    user_state[user_id] = "waiting_for_amount"
    bot.send_message(
        message.chat.id,
        "💰 Kitna amount add karna chahte hain? (Jaise: 59 ya 99):",
        reply_markup=get_main_keyboard(user_id),
    )
    return

  elif text.startswith("💼 My Wallet"):
    user_state.pop(user_id, None)
    bal = user_balances.get(user_id, 0)
    bot.send_message(
        message.chat.id,
        "💼 Available Balance: ₹" + str(bal),
        reply_markup=get_main_keyboard(user_id),
    )
    return

  elif text.startswith("🔍 Free Fire UID Info"):
    user_state[user_id] = "waiting_for_info_uid"
    bot.send_message(
        message.chat.id,
        "🔍 Kripya target player ka UID bhejein:",
        reply_markup=get_main_keyboard(user_id),
    )
    return

  elif text.startswith("👥 Refer & Earn"):
    user_state.pop(user_id, None)
    bot_info = bot.get_me()
    ref_link = "https://t.me/" + bot_info.username + "?start=ref_" + str(user_id)
    bot.send_message(
        message.chat.id,
        "👥 Refer & Earn\nHar referral par ₹5 paye!\n🔗 Link: " + ref_link,
        reply_markup=get_main_keyboard(user_id),
    )
    return

  elif text.startswith("📜 History"):
    user_state.pop(user_id, None)
    history_list = user_history.get(user_id, [])
    history_text = (
        "\n".join(history_list)
        if history_list
        else "Koi history nahi hai."
    )
    bot.send_message(
        message.chat.id,
        "📜 History:\n\n" + history_text,
        reply_markup=get_main_keyboard(user_id),
    )
    return

  elif text.startswith("🤖 AI Support Assistant"):
    user_state[user_id] = "ai_support_chat"
    ai_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    ai_markup.add(KeyboardButton("🔙 Exit AI Support"))
    bot.send_message(
        message.chat.id,
        "🤖 AI Support Active. Apna sawal puchein:",
        reply_markup=ai_markup,
    )
    return

  elif text.startswith("👑 Admin Panel") and user_id == ADMIN_ID:
    user_state.pop(user_id, None)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📊 Analytics", callback_data="admin_stats"),
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_bc"),
        InlineKeyboardButton("⚙️ Change UPI", callback_data="admin_change_upi"),
    )
    bot.send_message(
        message.chat.id, "👑 Admin Command Center", reply_markup=markup
    )
    return

  if state == "waiting_for_amount":
    if not text.isdigit():
      bot.reply_to(message, "❌ Sirf numbers enter karein.")
      return
    user_state[user_id] = "waiting_for_ss_" + text
    bot.reply_to(
        message,
        "💳 UPI ID: "
        + CURRENT_UPI_ID
        + "\nAmount: ₹"
        + text
        + "\n\nPayment karne ke baad UTR / Transaction detail yahan bhejein:",
    )

  elif state and state.startswith("waiting_for_ss_"):
    amount = state.split("_")[3]
    user_state.pop(user_id, None)
    bot.reply_to(
        message,
        "⏳ Verification Pending. Admin ko request bhej di gayi hai.",
        reply_markup=get_main_keyboard(user_id),
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(
            "✅ Approve", callback_data="approve_" + str(user_id) + "_" + amount
        ),
        InlineKeyboardButton(
            "❌ Reject", callback_data="reject_" + str(user_id) + "_" + amount
        ),
    )
    bot.send_message(
        ADMIN_ID,
        "🔔 New Deposit!\nUser: "
        + username
        + " (`"
        + str(user_id)
        + "`)\nAmount: ₹"
        + amount
        + "\nProof: "
        + text,
        reply_markup=markup,
        parse_mode="Markdown",
    )

  elif state and state.startswith("waiting_for_plan_uid_"):
    days = int(state.split("_")[4])
    uid = text
    user_state.pop(user_id, None)
    if not uid.isdigit():
      bot.reply_to(message, "❌ Sahi UID dalein.")
      return

    add_history(
        user_id, "Plan: " + str(days) + " Days for UID: " + uid
    )
    bot.reply_to(
        message,
        "🎉 Plan Successfully Deployed! UID: " + uid,
        reply_markup=get_main_keyboard(user_id),
    )

  elif state == "waiting_for_info_uid":
    uid = text
    user_state.pop(user_id, None)
    if not uid.isdigit():
      bot.reply_to(message, "❌ Invalid UID!")
      return
    try:
      api_url = "https://ff-info-ro45.vercel.app/api?uid=" + uid + "&key=Anurag"
      res = requests.get(api_url, timeout=15).json()
      basic = res.get("basicInfo", {})
      info_text = (
          "🎮 *PROFILE*\nName: "
          + str(basic.get("nickname", "N/A"))
          + "\nUID: "
          + uid
          + "\nLikes: "
          + str(basic.get("liked", "N/A"))
      )
      bot.reply_to(message, info_text, parse_mode="Markdown")
    except Exception as e:
      bot.reply_to(message, "❌ Error: " + str(e))


@bot.callback_query_handler(
    func=lambda call: call.data in [
        "admin_stats",
        "admin_bc",
        "admin_change_upi",
        "main_menu",
    ]
)
def handle_admin_inline(call):
  chat_id = call.message.chat.id
  user_id = call.from_user.id

  if call.data == "main_menu":
    bot.delete_message(chat_id, call.message.message_id)
    bot.send_message(
        chat_id,
        "🌟 Menu",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  if user_id != ADMIN_ID:
    bot.answer_callback_query(call.id, "❌ Unauthorized", show_alert=True)
    return

  if call.data == "admin_stats":
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔙 Return to Main", callback_data="main_menu")
    )
    bot.edit_message_text(
        "📊 Total Users: " + str(len(active_users)),
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup,
    )
  elif call.data == "admin_bc":
    user_state[user_id] = "waiting_for_broadcast"
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔙 Return to Main", callback_data="main_menu")
    )
    bot.edit_message_text(
        "📢 Broadcast message enter karein:",
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup,
    )
  elif call.data == "admin_change_upi":
    user_state[user_id] = "waiting_for_new_upi"
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔙 Return to Main", callback_data="main_menu")
    )
    bot.edit_message_text(
        "⚙️ Current UPI: " + CURRENT_UPI_ID + "\nNayi UPI ID bhejein:",
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup,
    )


def run_bot():
  bot.infinity_polling(none_stop=True, interval=0)


if __name__ == "__main__":
  print("🚀 Prime Tips Bot Running!")
  threading.Thread(target=run_bot, daemon=True).start()
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
      

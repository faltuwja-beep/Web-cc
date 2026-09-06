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
  return "Prime Tips Bot is Online and Running!"


# In-Memory Storage
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
  except:
    pass
  return False


def get_main_keyboard(user_id):
  markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  markup.add(
      KeyboardButton("🛒 Buy Plans (Likes)"),
      KeyboardButton("💰 Add Money (Wallet)"),
      KeyboardButton("💼 My Wallet"),
      KeyboardButton("🔍 Free Fire UID Info"),
      KeyboardButton("👥 Refer & Earn"),
      KeyboardButton("📜 History"),
      KeyboardButton("🤖 AI Support Assistant"),
  )
  if user_id == ADMIN_ID:
    markup.add(KeyboardButton("👑 Admin Panel"))
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
  return f"{days}d {hours}h {minutes}m {seconds}s baaki hain ⏳"


def get_ai_response(prompt_text):
  try:
    time.sleep(1)
    query = prompt_text.lower()
    if "like" in query or "likes" in query:
      return (
          "🤖 *Prime Tips AI (Hindi):*\n\nFree Fire mein likes badhane ke liye"
          " aap hamare 15 Days (₹59) ya 30 Days (₹99) wale plans kharid sakte"
          " hain jisme daily 220 likes milte hain!"
      )
    elif "wallet" in query or "paisa" in query or "balance" in query:
      return (
          f"🤖 *Prime Tips AI (Hindi):*\n\nWallet mein paise add karne ke liye"
          f" 'Add Money (Wallet)' button par click karein aur `{CURRENT_UPI_ID}`"
          " par payment karke screenshot/UTR bhej dein."
      )
    else:
      return (
          f"🤖 *Prime Tips AI (Hindi):*\n\nAapne pucha: '{prompt_text}'.\nMain"
          " Prime Tips ka smart assistant hoon. Madad ke liye @Xenon_ask9 par"
          " sampark karein."
      )
  except Exception:
    return "🤖 Namaste! Aapka sandesh mil gaya hai."


@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.from_user.id
  active_users.add(user_id)

  args = message.text.split()
  if len(args) > 1 and args[1].startswith("ref_"):
    try:
      referrer_id = int(args[1].split("_")[1])
      if referrer_id != user_id and referrer_id not in user_referrals.get(
          user_id, []
      ):
        if "referred_users" not in user_referrals:
          user_referrals["referred_users"] = []
        user_referrals["referred_users"].append(user_id)
        user_balances[referrer_id] = user_balances.get(referrer_id, 0) + 5
        bot.send_message(
            referrer_id,
            "🎉 *Referral Reward Mil Gaya!*\n🎁 Naye user ke judne par **₹5**"
            " add ho gaye hain!",
            parse_mode="Markdown",
        )
    except:
      pass

  if not check_subscription(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            "📢 Join Official Channel", url="https://t.me/eraningwithask"
        ),
        InlineKeyboardButton(
            "🔄 Verify Subscription", callback_data="check_join"
        ),
    )
    bot.send_message(
        message.chat.id,
        "⚠️ *Access Restricted!*\n\nPehle hamara official channel join karein"
        " phir 'Verify Subscription' dabayein.",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  bot.send_message(
      message.chat.id,
      "🌟 *Prime Tips Free Fire Utility Bot me Swagat hai!*",
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
          "✨ *Prime Tips Hub Unlock Ho Gaya!* 🚀",
          reply_markup=get_main_keyboard(user_id),
          parse_mode="Markdown",
      )
    else:
      bot.answer_callback_query(
          call.id,
          "❌ Kripya pehle official channel join karein!",
          show_alert=True,
      )

  elif call.data in ["buy_59", "buy_99"]:
    plan_cost = 59 if call.data == "buy_59" else 99
    days = 15 if call.data == "buy_59" else 30
    current_bal = user_balances.get(user_id, 0)

    if current_bal < plan_cost:
      bot.answer_callback_query(
          call.id,
          f"❌ Wallet me balance kam hai! Required: ₹{plan_cost}",
          show_alert=True,
      )
      return

    user_balances[user_id] -= plan_cost
    user_state[user_id] = f"waiting_for_plan_uid_{days}"
    bot.send_message(
        chat_id,
        f"✅ *Payment Deducted (₹{plan_cost})*\n\nEnter target **Free Fire"
        " UID**:",
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
    add_history(target_user_id, f"Added ₹{amount} via Admin approval")
    bot.answer_callback_query(call.id, f"Approved! ₹{amount} added.")
    bot.edit_message_text(
        f"✅ *Deposit Approved!*\nUser ID: `{target_user_id}` | Added:"
        f" `₹{amount}`",
        chat_id=chat_id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )
    bot.send_message(
        target_user_id,
        f"🎉 *Deposit Confirmed!*\nAdmin ne aapka ₹{amount} approve kar diya"
        " hai.",
    )

  elif call.data.startswith("reject_"):
    if user_id != ADMIN_ID:
      return
    _, target_user_id, amount = call.data.split("_")
    target_user_id, amount = int(target_user_id), int(amount)
    bot.answer_callback_query(call.id, f"Deposit rejected.")
    bot.edit_message_text(
        f"❌ *Deposit Rejected!*\nUser ID: `{target_user_id}`",
        chat_id=chat_id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )
    bot.send_message(
        target_user_id,
        "❌ *Deposit Rejected.*\nAapka payment proof reject ho gaya hai."
        " Support: @Xenon_ask9",
    )


@bot.message_handler(func=lambda message: True)
def handle_text(message):
  global CURRENT_UPI_ID
  user_id = message.from_user.id
  text = message.text.strip()
  state = user_state.get(user_id)
  username = (
      f"@{message.from_user.username}"
      if message.from_user.username
      else message.from_user.first_name
  )

  if state == "waiting_for_broadcast" and user_id == ADMIN_ID:
    user_state.pop(user_id, None)
    success_count = 0
    for uid in active_users:
      try:
        bot.send_message(
            uid,
            f"📢 *Prime Tips Announcement:*\n\n{text}",
            parse_mode="Markdown",
        )
        success_count += 1
      except:
        pass
    bot.reply_to(
        message,
        f"✅ Broadcast sent to {success_count} users.",
        reply_markup=get_main_keyboard(user_id),
    )
    return

  if state == "waiting_for_new_upi" and user_id == ADMIN_ID:
    user_state.pop(user_id, None)
    CURRENT_UPI_ID = text
    bot.reply_to(
        message,
        f"✅ *UPI ID Updated Successfully!*\nNew UPI: `{CURRENT_UPI_ID}`",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  if state == "ai_support_chat":
    if text == "🔙 Exit AI Support":
      user_state.pop(user_id, None)
      bot.send_message(
          message.chat.id,
          "🤖 AI Support closed.",
          reply_markup=get_main_keyboard(user_id),
      )
      return
    ai_response = get_ai_response(text)
    bot.send_message(message.chat.id, ai_response, parse_mode="Markdown")
    return

  if text == "🛒 Buy Plans (Likes)":
    user_state.pop(user_id, None)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            "💎 15 Days Plan (₹59) - 220 Likes/Day", callback_data="buy_59"
        ),
        InlineKeyboardButton(
            "💎 30 Days Plan (₹99) - 220 Likes/Day", callback_data="buy_99"
        ),
    )
    bot.send_message(
        message.chat.id,
        "📦 *Subscription Plans:*\n• **₹59:** 15 Days\n• **₹99:** 30 Days",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  elif text == "💰 Add Money (Wallet)":
    user_state[user_id] = "waiting_for_amount"
    bot.send_message(
        message.chat.id,
        "💰 *Wallet Deposit*\nEnter amount (e.g., `59` or `99`):",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text == "💼 My Wallet":
    user_state.pop(user_id, None)
    bal = user_balances.get(user_id, 0)
    bot.send_message(
        message.chat.id,
        f"💼 *Wallet Balance:* `₹{bal}`",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text == "🔍 Free Fire UID Info":
    user_state[user_id] = "waiting_for_info_uid"
    bot.send_message(
        message.chat.id,
        "🔍 Enter target player **UID**:",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text == "👥 Refer & Earn":
    user_state.pop(user_id, None)
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    bot.send_message(
        message.chat.id,
        f"👥 *Refer & Earn*\nShare link & earn ₹5 per join!\n🔗 `{ref_link}`",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text == "📜 History":
    user_state.pop(user_id, None)
    history_list = user_history.get(user_id, [])
    history_text = (
        "\n".join([f"▫️ {item}" for item in history_list])
        if history_list
        else "No history found."
    )
    bot.send_message(
        message.chat.id,
        f"📜 *Activity History:*\n\n{history_text}",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text == "🤖 AI Support Assistant":
    user_state[user_id] = "ai_support_chat"
    ai_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    ai_markup.add(KeyboardButton("🔙 Exit AI Support"))
    bot.send_message(
        message.chat.id,
        "🤖 *AI Support Active.*\nContact support: @Xenon_ask9",
        reply_markup=ai_markup,
        parse_mode="Markdown",
    )
    return

  elif text == "👑 Admin Panel" and user_id == ADMIN_ID:
    user_state.pop(user_id, None)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📊 System Analytics", callback_data="admin_stats"),
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_bc"),
        InlineKeyboardButton("⚙️ Change UPI ID", callback_data="admin_change_upi"),
    )
    bot.send_message(
        message.chat.id,
        "👑 *Admin Command Center*",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  if state == "waiting_for_amount":
    if not text.isdigit():
      bot.reply_to(message, "❌ Numbers only please!")
      return
    user_state[user_id] = f"waiting_for_ss_{text}"
    bot.reply_to(
        message,
        f"💳 *UPI Gateway*\nUPI ID: `{CURRENT_UPI_ID}`\nAmount:"
        f" `₹{text}`\n\nSend Transaction ID / Screenshot detail:",
        parse_mode="Markdown",
    )

  elif state and state.startswith("waiting_for_ss_"):
    amount = state.split("_")[3]
    user_state.pop(user_id, None)
    bot.reply_to(
        message,
        "⏳ *Verification Pending.*",
        reply_markup=get_main_keyboard(user_id),
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(
            "✅ Approve", callback_data=f"approve_{user_id}_{amount}"
        ),
        InlineKeyboardButton(
            "❌ Reject", callback_data=f"reject_{user_id}_{amount}"
        ),
    )
    bot.send_message(
        ADMIN_ID,
        f"🔔 *New Deposit!*\n👤 {username} (`{user_id}`)\n💰 `₹{amount}`\nProof:"
        f" {text}",
        reply_markup=markup,
        parse_mode="Markdown",
    )

  elif state and state.startswith("waiting_for_plan_uid_"):
    days = int(state.split("_")[4])
    uid = text
    user_state.pop(user_id, None)
    if not uid.isdigit():
      bot.reply_to(message, "❌ Invalid UID!")
      return

    expiry_time_sec = time.time() + (days * 86400)
    add_history(
        user_id,
        f"Plan: {days} Days for UID: {uid} at"
        f" {datetime.datetime.now().strftime('%d-%m-%Y')}",
    )
    bot.reply_to(
        message,
        f"🎉 *Plan Deployed Successfully!* 🚀\nUID: `{uid}`\nDuration:"
        f" `{days} Days`",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )

  elif state == "waiting_for_info_uid":
    uid = text
    user_state.pop(user_id, None)
    if not uid.isdigit():
      bot.reply_to(message, "❌ Invalid UID!")
      return
    try:
      api_url = f"https://ff-info-ro45.vercel.app/api?uid={uid}&key=Anurag"
      res = requests.get(api_url, timeout=15).json()
      basic = res.get("basicInfo", {})
      info_text = (
          f"🎮 *PROFILE*\nName: `{basic.get('nickname', 'N/A')}`\nUID:"
          f" `{uid}`\nLikes: `{basic.get('liked', 'N/A')}`"
      )
      bot.reply_to(message, info_text, parse_mode="Markdown")
    except Exception as e:
      bot.reply_to(message, f"❌ Error: {e}")


@bot.callback_query_handler(
    func=lambda call: call.data in [
        "admin_stats",
        "admin_bc",
        "admin_change_upi",
    ]
)
def handle_admin_inline(call):
  if call.from_user.id != ADMIN_ID:
    bot.answer_callback_query(call.id, "❌ Unauthorized", show_alert=True)
    return
  if call.data == "admin_stats":
    bot.edit_message_text(
        f"📊 Total Users: {len(active_users)}",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
    )
  elif call.data == "admin_bc":
    user_state[call.from_user.id] = "waiting_for_broadcast"
    bot.edit_message_text(
        "📢 Enter message to broadcast:",
        call.message.chat.id,
        call.message.message_id,
    )
  elif call.data == "admin_change_upi":
    user_state[call.from_user.id] = "waiting_for_new_upi"
    bot.edit_message_text(
        f"⚙️ Current UPI: `{CURRENT_UPI_ID}`\nSend new UPI:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
    )


def run_bot():
  bot.infinity_polling(none_stop=True, interval=0)


if __name__ == "__main__":
  # Background thread for bot polling
  threading.Thread(target=run_bot, daemon=True).start()
  # Start Flask app for Render Web Service port requirement
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
        

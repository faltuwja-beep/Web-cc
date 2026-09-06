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

# Dynamic UPI Variable
CURRENT_UPI_ID = "sima6241@ptaxis"

# Bot & Flask Initialization
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)


@app.route("/")
def home():
  return "⚡ Prime Tips Bot is Online & Running Smoothly! 🚀"


# In-Memory Storage Databases
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
  return f"⏳ {days} Din {hours} Ghante {minutes} Minute baaki hain 🔥"


def get_ai_response(prompt_text):
  try:
    time.sleep(0.5)
    query = prompt_text.lower()
    if "like" in query or "likes" in query:
      return (
          "🤖 *Prime Tips AI Assistant:*\n\n🔥 Free Fire profile me likes"
          " badhane ke liye aap hamare **15 Days (₹59)** ya **30 Days (₹99)**"
          " wale VIP plans kharid sakte hain, jisme daily 220+ likes milte hain!"
          " ⚡"
      )
    elif "wallet" in query or "paisa" in query or "balance" in query:
      return (
          f"💳 *Prime Tips AI Assistant:*\n\nApne wallet me balance add karne ke"
          f" liye niche menu se **'Add Money (Wallet)'** par click karein aur"
          f" di gayi UPI ID (`{CURRENT_UPI_ID}`) par payment karke UTR/Screenshot"
          f" bhej dein. 💰"
      )
    elif "refer" in query or "dost" in query:
      return (
          "🎁 *Prime Tips AI Assistant:*\n\nAap **'Refer & Earn'** section se"
          " apna unique link dosto ke sath share karke har successful join par"
          " instant **₹5** kama sakte hain! 🚀"
      )
    else:
      return (
          f"🤖 *Prime Tips AI Assistant:*\n\nAapne pucha: *'{prompt_text}'*.\nMain"
          " aapka smart assistant hoon. Free Fire plans, wallet ya likes se"
          " judi kisi bhi sahayta ke liye aap niche diye gaye buttons ka use"
          " kar sakte hain! 🌟"
      )
  except Exception:
    return (
        "🤖 Namaste! Aapka sandesh mil gaya hai. Main aapki kya sahayta kar"
        " sakta hoon? ✨"
    )


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
            "🎉 *Referral Reward Mil Gaya!*\n🎁 Naye user ke judne par aapke"
            " wallet me **₹5** add kar diye gaye hain! 💰✨",
            parse_mode="Markdown",
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
        "⚠️ *Access Restricted!* 🛑\n\nPrime Tips ki sari services use karne ke"
        " liye pehle hamara official channel join karna anivarya hai. Join"
        " karne ke baad niche **'Verify Subscription'** par click karein! 👇",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  bot.send_message(
      message.chat.id,
      "🌟 *Swagat hai aapka Prime Tips Free Fire Utility Bot me!* 🎮🔥\n\nAapka"
      " personal gaming hub tayar hai. Neeche diye gaye options me se chunein"
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
          "✨ *Prime Tips Hub Successfully Unlock Ho Gaya!* 🚀🔥",
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
        f"✅ *Payment Successful!* (₹{plan_cost} cut ho gaye 💳)\n\nAb apna target"
        " **Free Fire UID** bhejein jisme likes shuru karni hain: 🎮✨",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )

  elif call.data.startswith("approve_"):
    if user_id != ADMIN_ID:
      return
    _, target_user_id, amount = call.data.split("_")
    target_user_id = int(target_user_id)
    amount = int(amount)

    user_balances[target_user_id] = (
        user_balances.get(target_user_id, 0) + amount
    )
    add_history(target_user_id, f"Added ₹{amount} via Admin approval ✅")
    bot.answer_callback_query(call.id, f"Approved! ₹{amount} added.")
    bot.edit_message_text(
        f"✅ *Deposit Approve Ho Gaya!*\nUser ID: `{target_user_id}` | Added:"
        f" `₹{amount}` 💰",
        chat_id=chat_id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )
    bot.send_message(
        target_user_id,
        f"🎉 *Deposit Confirmed!*\nAdmin ne aapka ₹{amount} ka payment approve"
        " kar diya hai. Wallet check karein! 🚀💵",
    )

  elif call.data.startswith("reject_"):
    if user_id != ADMIN_ID:
      return
    _, target_user_id, amount = call.data.split("_")
    target_user_id = int(target_user_id)
    amount = int(amount)

    bot.answer_callback_query(call.id, "Deposit rejected.")
    bot.edit_message_text(
        f"❌ *Deposit Reject Ho Gaya!*\nUser ID: `{target_user_id}` | Amount:"
        f" `₹{amount}`",
        chat_id=chat_id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )
    bot.send_message(
        target_user_id,
        "❌ *Deposit Rejected.*\nAapka payment proof admin dwara reject kar"
        " diya gaya hai. Kripya sahi details ke sath dobara try karein. ⚠️",
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
            f"📢 *Prime Tips Special Announcement:*\n\n{text} ✨",
            parse_mode="Markdown",
        )
        success_count += 1
      except Exception:
        pass
    bot.reply_to(
        message,
        f"✅ Broadcast successfully {success_count} active users tak bhej"
        " diya gaya hai! 🚀",
        reply_markup=get_main_keyboard(user_id),
    )
    return

  if state == "waiting_for_new_upi" and user_id == ADMIN_ID:
    user_state.pop(user_id, None)
    CURRENT_UPI_ID = text
    bot.reply_to(
        message,
        f"✅ *UPI ID Successfully Updated!*\n\nNew UPI ID: `{CURRENT_UPI_ID}` 💳",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  if state == "ai_support_chat":
    if text == "🔙 Exit AI Support":
      user_state.pop(user_id, None)
      bot.send_message(
          message.chat.id,
          "🤖 AI Support session safely band kar diya gaya hai. ✨",
          reply_markup=get_main_keyboard(user_id),
      )
      return

    ai_response = get_ai_response(text)
    bot.send_message(message.chat.id, ai_response, parse_mode="Markdown")
    return

  if text.startswith("🛒 Buy Plans (Likes)"):
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
        "📦 *Prime Tips VIP Subscription Plans:*\n\n• **₹59 Plan:** 15 Days"
        " Plan | 220 Likes/Day ⚡\n• **₹99 Plan:** 30 Days Plan | 220 Likes/Day"
        " 🔥\n\n*(Note: Plan kharidne se pehle Wallet me balance add karein)* 💳",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  elif text.startswith("💰 Add Money (Wallet)"):
    user_state[user_id] = "waiting_for_amount"
    bot.send_message(
        message.chat.id,
        "💰 *Wallet Deposit Center* 💳\n\nAap apne wallet me kitna amount add karna"
        " chahte hain? (Example: `59` ya `99`)\nKripya sirf numeric value"
        " enter karein: 👇",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text.startswith("💼 My Wallet"):
    user_state.pop(user_id, None)
    bal = user_balances.get(user_id, 0)
    bot.send_message(
        message.chat.id,
        f"💼 *Wallet Balance Ledger* 📊\n\n• Available Balance: `₹{bal}`"
        " 💵✨",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text.startswith("🔍 Free Fire UID Info"):
    user_state[user_id] = "waiting_for_info_uid"
    bot.send_message(
        message.chat.id,
        "🔍 *Free Fire UID Telemetry* 🎮\n\nKripya jis player ki info nikalni"
        " hai uska exact **UID** type karke bhejein: 👇",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text.startswith("👥 Refer & Earn"):
    user_state.pop(user_id, None)
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    bot.send_message(
        message.chat.id,
        "👥 *Refer & Earn Program* 🎁\n\nApna personal link dosto ke sath share"
        " karein. Har successful referral par instant **₹5** ka reward paye!"
        f"\n\n🔗 *Your Referral Link:*\n`{ref_link}` 🚀",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text.startswith("📜 History"):
    user_state.pop(user_id, None)
    history_list = user_history.get(user_id, [])
    if not history_list:
      history_text = "Abhi tak aapki koi activity record nahi hai. ✨"
    else:
      history_text = "\n".join([f"▫️ {item}" for item in history_list])

    bot.send_message(
        message.chat.id,
        f"📜 *Detailed Activity & Plan History:* 📊\n\n{history_text}",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text.startswith("🤖 AI Support Assistant"):
    user_state[user_id] = "ai_support_chat"
    ai_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    ai_markup.add(KeyboardButton("🔙 Exit AI Support"))
    bot.send_message(
        message.chat.id,
        "🤖 *AI Support Active (Hindi Mode)* 🧠✨\n\nAapko jo bhi doubt ho ya"
        " jankari chahiye, yahan message bhejein. (Support contact:"
        " @Xenon_ask9) 👇",
        reply_markup=ai_markup,
        parse_mode="Markdown",
    )
    return

  elif text.startswith("👑 Admin Panel") and user_id == ADMIN_ID:
    user_state.pop(user_id, None)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            "📊 System Analytics (Users) 📈", callback_data="admin_stats"
        ),
        InlineKeyboardButton("📢 Broadcast Message 🚀", callback_data="admin_bc"),
        InlineKeyboardButton(
            "⚙️ Change UPI ID 💳", callback_data="admin_change_upi"
        ),
    )
    bot.send_message(
        message.chat.id,
        "👑 *Prime Tips Admin Command Center* ⚡\n\nSelect an administrative"
        " action:",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  if state == "waiting_for_amount":
    if not text.isdigit():
      bot.reply_to(message, "❌ Invalid input! Kripya sirf numbers enter karein.")
      return

    user_state[user_id] = f"waiting_for_ss_{text}"
    bot.reply_to(
        message,
        f"💳 *UPI Payment Gateway* ⚡\n\nScan / Pay to UPI ID:"
        f" `{CURRENT_UPI_ID}`\nAmount: `₹{text}`\n\nPayment complete karne ke"
        " baad uska **Transaction ID / UTR number** ya screenshot detail yahan"
        " submit karein: 👇",
        parse_mode="Markdown",
    )

  elif state and state.startswith("waiting_for_ss_"):
    amount = state.split("_")[3]
    user_state.pop(user_id, None)

    bot.reply_to(
        message,
        "⏳ *Verification Pending...*\nAapka payment proof admin ke paas bhej"
        " diya gaya hai. Kripya sanyam banaye rakhein! 👍",
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
        f"🔔 *New Wallet Deposit Request!* 💰\n\n👤 User Name: {username}\n🆔 User"
        f" ID: `{user_id}`\n💰 Amount: `₹{amount}`\n\nProof Details:"
        f" `{text}`",
        reply_markup=markup,
        parse_mode="Markdown",
    )

  elif state and state.startswith("waiting_for_plan_uid_"):
    days = int(state.split("_")[4])
    uid = text
    user_state.pop(user_id, None)

    if not uid.isdigit():
      bot.reply_to(message, "❌ Invalid UID! Kripya sahi numbers wala UID dalein.")
      return

    start_time = datetime.datetime.now()
    expiry_time_sec = time.time() + (days * 86400)
    expiry_datetime = start_time + datetime.timedelta(days=days)

    start_str = start_time.strftime("%d-%m-%Y | %I:%M %p")
    expiry_str = expiry_datetime.strftime("%d-%m-%Y | %I:%M %p")

    user_timers[user_id] = {
        "uid": uid,
        "days": days,
        "expires": expiry_time_sec,
    }

    history_log = (
        f"🛒 Plan: {days} Days (220 Likes/Day)\n🆔 UID: {uid}\n📥 Liya gaya:"
        f" {start_str}\n⌛ Khatm hoga: {expiry_str}"
    )
    add_history(user_id, history_log)

    anim_msg = bot.reply_to(
        message,
        "✨ 🔄 *Connecting to Free Fire Secure Server...* ⚡ 🎮",
        parse_mode="Markdown",
    )
    time.sleep(0.6)
    bot.edit_message_text(
        "🔥 🔍 *Fetching Player Profile & Activating Live Timer...* ⏱️ 🚀",
        chat_id=message.chat.id,
        message_id=anim_msg.message_id,
        parse_mode="Markdown",
    )
    time.sleep(0.6)

    try:
      api_url = f"https://ff-info-ro45.vercel.app/api?uid={uid}&key=Anurag"
      response = requests.get(api_url, timeout=15)
      data = response.json()
      basic = data.get("basicInfo", {})
      nickname = basic.get("nickname", "N/A")
      likes = basic.get("liked", "N/A")
    except Exception:
      nickname = "N/A"
      likes = "N/A"

    countdown_str = format_countdown(expiry_time_sec)

    final_card = (
        f"🎉 *Plan Successfully Deployed!* 🚀✨\n\n"
        f"👤 *Player Name:* `{nickname}`\n"
        f"🆔 *UID:* `{uid}`\n"
        f"❤️ *Current Likes:* `{likes}`\n"
        f"📅 *Duration:* `{days} Days`\n"
        f"⚡ *Daily Quota:* `220 Likes/Day`\n"
        f"📥 *Start Time:* `{start_str}`\n"
        f"⌛ *Expiry Time:* `{expiry_str}`\n\n"
        f"⏱️ *Live Timer Status:* `{countdown_str}` 🔥"
    )

    bot.edit_message_text(
        final_card,
        chat_id=message.chat.id,
        message_id=anim_msg.message_id,
        parse_mode="Markdown",
    )
    bot.send_message(
        message.chat.id,
        "Aap niche menu se dusra option select kar sakte hain: 👇",
        reply_markup=get_main_keyboard(user_id),
    )

  elif state == "waiting_for_info_uid":
    uid = text
    user_state.pop(user_id, None)

    if not uid.isdigit():
      bot.reply_to(message, "❌ Invalid UID pattern format!")
      return

    anim_msg = bot.reply_to(
        message,
        "✨ ⏳ *Fetching player telemetry data with animations...* 🎮 🔥",
        parse_mode="Markdown",
    )
    time.sleep(0.8)

    try:
      api_url = f"https://ff-info-ro45.vercel.app/api?uid={uid}&key=Anurag"
      response = requests.get(api_url, timeout=15)
      data = response.json()

      basic = data.get("basicInfo", {})
      clan = data.get("clanBasicInfo", {})

      formatted_text = (
          f"┏━━━━ 🎮 *PLAYER PROFILE* ━━━━┓\n"
          f"┃\n"
          f"┣ 👤 *Name:* `{basic.get('nickname', 'N/A')}`\n"
          f"┣ 🆔 *UID:* `{uid}`\n"
          f"┣ 📊 *Level:* `{basic.get('level', 'N/A')}` | 🌐 *Region:*"
          f" `{basic.get('region', 'N/A')}`\n"
          f"┣ ❤️ *Likes:* `{basic.get('liked', 'N/A')}`\n"
          f"┣ 🏆 *BR Rank:* `{basic.get('rank', 'N/A')}`\n"
          f"┣ ⚔️ *CS Rank:* `{basic.get('csRank', 'N/A')}`\n"
          f"┣ 🛡️ *Guild:* `{clan.get('clanName', 'N/A')}`\n"
          f"┃\n"
          f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ⚡"
      )
      add_history(
          user_id,
          f"Queried UID: {uid} at"
          f" {datetime.datetime.now().strftime('%d-%m-%Y | %I:%M %p')}",
      )
      bot.edit_message_text(
          formatted_text,
          chat_id=message.chat.id,
          message_id=anim_msg.message_id,
          parse_mode="Markdown",
      )
      bot.send_message(
          message.chat.id,
          "Neeche diye gaye buttons se dusra task select karein: 👇",
          reply_markup=get_main

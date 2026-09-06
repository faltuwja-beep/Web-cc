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

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)


@app.route("/")
def home():
  return "⚡ Prime Tips Ultimate Bot is Online & Operating 24/7! 🚀"


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
            "🎉 *Referral Reward Unlocked!*\n\n🎁 Ek naya dost judne par"
            " aapke wallet me **₹5** ka bonus safalpurvak credit kar diya gaya"
            " hai! 💰✨",
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
        "⚠️ *Access Restricted!* 🛑\n\nPrime Tips ki sari premium services use"
        " karne ke liye pehle hamara official channel join karna anivarya hai."
        " Channel join karne ke baad niche diye gaye button par click karein!",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  bot.send_message(
      message.chat.id,
      "🌟 *Welcome to Prime Tips Utility Bot* 🚀🔥\n\nAapka personal"
      " high-performance gaming hub tayar hai. Neeche diye gaye menu me se"
      " apna manpasand option chunein 👇",
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
          "✨ *Prime Tips Hub Successfully Unlocked!* 🚀🔥",
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
          f"❌ Insufficient Balance! Required: ₹{plan_cost}",
          show_alert=True,
      )
      return

    user_balances[user_id] -= plan_cost
    user_state[user_id] = "waiting_for_plan_uid_" + str(days)

    bot.send_message(
        chat_id,
        "✅ *Plan Order Initialized!* 💳\n(₹"
        + str(plan_cost)
        + " successfully deducted)\n\nAb apna target **Free Fire UID**"
        + " bhejein jisme likes shuru karni hain: 🎮✨",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )

  elif call.data.startswith("approve_"):
    if user_id != ADMIN_ID:
      return
    parts = call.data.split("_")
    target_user_id = int(parts[1])
    amount = int(parts[2])

    user_balances[target_user_id] = (
        user_balances.get(target_user_id, 0) + amount
    )
    add_history(target_user_id, "Added ₹" + str(amount) + " via Admin approval")
    bot.answer_callback_query(call.id, "Approved! ₹" + str(amount) + " added.")
    bot.edit_message_text(
        "✅ *Deposit Approved Successfully!* 💳\nUser ID: `"
        + str(target_user_id)
        + "` | Credited Ledger: `₹"
        + str(amount)
        + "` 💰",
        chat_id=chat_id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )
    bot.send_message(
        target_user_id,
        "🎉 *Deposit Confirmed!* 🚀\nAapka ₹"
        + str(amount)
        + " ka payment admin dwara safalpurvak approve kar diya gaya hai. Wallet"
        + " check karein! 💵✨",
        parse_mode="Markdown",
    )

  elif call.data.startswith("reject_"):
    if user_id != ADMIN_ID:
      return
    parts = call.data.split("_")
    target_user_id = int(parts[1])
    amount = int(parts[2])

    bot.answer_callback_query(call.id, "Deposit rejected.")
    bot.edit_message_text(
        "❌ *Deposit Rejected!* ⚠️\nUser ID: `"
        + str(target_user_id)
        + "` | Amount: `₹"
        + str(amount)
        + "`",
        chat_id=chat_id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )
    bot.send_message(
        target_user_id,
        "❌ *Deposit Rejected.*\nAapka payment proof administration dwara"
        " reject kar diya gaya hai. Agar koi query hai toh @Xenon_ask9 par"
        " sampark karein. 🛑",
    )


@bot.message_handler(func=lambda message: True)
def handle_text(message):
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
    success_count = 0
    for uid in active_users:
      try:
        bot.send_message(
            uid,
            "📢 *Prime Tips Official Announcement:*\n\n" + text + " ✨",
            parse_mode="Markdown",
        )
        success_count += 1
      except Exception:
        pass
    bot.reply_to(
        message,
        "✅ Broadcast safalpurvak "
        + str(success_count)
        + " active users tak bhej diya gaya hai! 🚀",
        reply_markup=get_main_keyboard(user_id),
    )
    return

  if state == "ai_support_chat":
    if text == "🔙 Exit AI Support":
      user_state.pop(user_id, None)
      bot.send_message(
          message.chat.id,
          "🤖 AI Support session safely close kar diya gaya hai. ✨",
          reply_markup=get_main_keyboard(user_id),
      )
      return

    ai_reply = (
        "🤖 *Prime Tips AI Assistant:*\n\nAapka sawal mil gaya hai: *"
        + text
        + "*.\n\n⚡ Fast execution ke liye niche diye gaye buttons ka use"
        + " karein ya wallet me funds add karke plans activate karein. Kisi bhi"
        + " samasya ke liye @Xenon_ask9 par sampark karein! 🌟"
    )
    bot.send_message(message.chat.id, ai_reply, parse_mode="Markdown")
    return

  if text.startswith("🛒 Buy Plans (Likes)"):
    user_state.pop(user_id, None)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            "💎 15 Days Plan (₹59) - 220 Likes/Day", callback_data="buy_59"
        ),
        InlineKeyboardButton(
            "💎 30 Days Plan (₹99) - Full VIP Package", callback_data="buy_99"
        ),
    )
    bot.send_message(
        message.chat.id,
        "┏━━━━ 💎 *VIP LIKES PLANS* ━━━━┓\n┃\n┣ ⚡ **₹59 Plan:** 15 Days Active"
        " Timer (220 Likes daily)\n┣ 🔥 **₹99 Plan:** 30 Days Complete VIP"
        " Package\n┃\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n*(Pehle Wallet me balance"
        " add karna anivarya hai)* 💳",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  elif text.startswith("💰 Add Money"):
    user_state[user_id] = "waiting_for_amount"
    bot.send_message(
        message.chat.id,
        "💰 *Wallet Deposit Center* 💳\n\nAap apne wallet me kitna amount add karna"
        " chahte hain? (Example: `59` ya `100`)\nKripya sirf numeric value"
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
        "┏━━━━ 💼 *WALLET LEDGER* ━━━━┓\n┃\n┣ 💵 Available Balance: `₹"
        + str(bal)
        + "` ✨\n┃\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text.startswith("🔍 Free Fire UID Info"):
    user_state[user_id] = "waiting_for_info_uid"
    bot.send_message(
        message.chat.id,
        "🔍 *Free Fire UID Info Gateway* 🎮\n\nKripya target player ka exact"
        " **UID** type karke bhejein: 👇",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text.startswith("👥 Refer & Earn"):
    user_state.pop(user_id, None)
    bot_info = bot.get_me()
    ref_link = "https://t.me/" + bot_info.username + "?start=ref_" + str(user_id)
    bot.send_message(
        message.chat.id,
        "👥 *Refer & Earn Program* 🎁\n\nApna personal link dosto ke sath share"
        + " karein. Har successful referral par instant **₹5** ka reward paye!\n\n🔗"
        + " *Your Referral Link:*\n`"
        + ref_link
        + "` 🚀",
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
      history_text = "\n".join(["▫️ " + str(item) for item in history_list])

    bot.send_message(
        message.chat.id,
        "📜 *Transaction & Activity History:* 📊\n\n" + history_text,
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
        + " sahayta chahiye, yahan message bhejein. Support contact:"
        + " @Xenon_ask9 👇",
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
        InlineKeyboardButton(
            "📢 Broadcast Global Message 🚀", callback_data="admin_bc"
        ),
    )
    bot.send_message(
        message.chat.id,
        "👑 *Prime Tips Admin Command Center* ⚡\n\nChoose an administrative"
        + " action below:",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  if state == "waiting_for_amount":
    if not text.isdigit():
      bot.reply_to(message, "❌ Invalid input! Kripya sirf numbers enter karein.")
      return

    user_state[user_id] = "waiting_for_ss_" + text
    bot.reply_to(
        message,
        "💳 *UPI Payment Gateway* ⚡\n\nUPI ID: `sima6241@ptaxis`\nAmount: `₹"
        + text
        + "`\n\nPayment safal karne ke baad apna **Transaction ID / Screenshot"
        + " details** yahan submit karein: 👇",
        parse_mode="Markdown",
    )

  elif state and state.startswith("waiting_for_ss_"):
    amount = state.split("_")[3]
    user_state.pop(user_id, None)

    bot.reply_to(
        message,
        "⏳ *Verification Pending...*\nAapka payment proof safalpurvak admin ke"
        " paas verification ke liye bhej diya gaya hai. Kripya sanyam banaye"
        " rakhein! 👍",
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
        "🔔 *New Wallet Deposit Request!* 💰\n\n👤 User Name: "
        + username
        + "\n🆔 User ID: `"
        + str(user_id)
        + "`\n💰 Amount: `₹"
        + amount
        + "`\n\nProof Details: "
        + text,
        reply_markup=markup,
        parse_mode="Markdown",
    )

  elif state and state.startswith("waiting_for_plan_uid_"):
    days = state.split("_")[4]
    uid = text
    user_state.pop(user_id, None)

    if not uid.isdigit():
      bot.reply_to(message, "❌ Invalid UID format! Kripya sahi numbers dalein.")
      return

    add_history(user_id, "Subscribed " + days + "-Days Plan for UID: " + uid)

    anim_msg = bot.reply_to(
        message,
        "✨ 🔄 *Initializing Secure Handshake with FF Server...* ⚡ 🎮",
        parse_mode="Markdown",
    )
    time.sleep(0.6)
    bot.edit_message_text(
        "🔐 📡 *Bypassing Gateway & Verifying Player Profile...* ⏱️ 🚀",
        chat_id=message.chat.id,
        message_id=anim_msg.message_id,
        parse_mode="Markdown",
    )
    time.sleep(0.6)
    bot.edit_message_text(
        "🔥 ⚡ *Injecting Daily Likes Quota & Activating Timer...* 💎 ✨",
        chat_id=message.chat.id,
        message_id=anim_msg.message_id,
        parse_mode="Markdown",
    )
    time.sleep(0.6)

    try:
      api_url = "https://ff-info-ro45.vercel.app/api?uid=" + uid + "&key=Anurag"
      response = requests.get(api_url, timeout=15)
      data = response.json()
      basic = data.get("basicInfo", {})
      nickname = basic.get("nickname", "N/A")
      likes = basic.get("liked", "N/A")
    except Exception:
      nickname = "N/A"
      likes = "N/A"

    final_card = (
        "┏━━━━ 🎉 *PLAN DEPLOYED* ━━━━┓\n"
        + "┃\n"
        + "┣ 👤 *Player Name:* `"
        + str(nickname)
        + "`\n"
        + "┣ 🆔 *UID:* `"
        + uid
        + "`\n"
        + "┣ ❤️ *Current Likes:* `"
        + str(likes)
        + "`\n"
        + "┣ 📅 *Duration:* `"
        + days
        + " Days`\n"
        + "┣ ⚡ *Daily Quota:* `220 Likes/Day`\n"
        + "┃\n"
        + "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        + "⏱️ *Active timer successfully initiated!* 🔥"
    )

    bot.edit_message_text(
        final_card,
        chat_id=message.chat.id,
        message_id=anim_msg.message_id,
        parse_mode="Markdown",
    )
    bot.send_message(
        message.chat.id,
        "Neeche diye gaye buttons se dusra option select karein: 👇",
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
      api_url = "https://ff-info-ro45.vercel.app/api?uid=" + uid + "&key=Anurag"
      response = requests.get(api_url, timeout=15)
      data = response.json()

      basic = data.get("basicInfo", {})
      clan = data.get("clanBasicInfo", {})

      formatted_text = (
          "┏━━━━ 🎮 *PLAYER PROFILE* ━━━━┓\n"
          + "┃\n"
          + "┣ 👤 *Name:* `"
          + str(basic.get("nickname", "N/A"))
          + "`\n"
          + "┣ 🆔 *UID:* `"
          + uid
          + "`\n"
          + "┣ 📊 *Level:* `"
          + str(basic.get("level", "N/A"))
          + "` | 🌐 *Region:* `"
          + str(basic.get("region", "N/A"))
          + "`\n"
          + "┣ ❤️ *Likes:* `"
          + str(basic.get("liked", "N/A"))
          + "`\n"
          + "┣ 🏆 *BR Rank:* `"
          + str(basic.get("rank", "N/A"))
          + "`\n"
          + "┣ ⚔️ *CS Rank:* `"
          + str(basic.get("csRank", "N/A"))
          + "`\n"
          + "┣ 🛡️ *Guild:* `"
          + str(clan.get("clanName", "N/A"))
          + "`\n"
          + "┃\n"
          + "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ ⚡"
      )
      add_history(user_id, "Queried UID: " + uid)
      bot.edit_message_text(
          formatted_text,
          chat_id=message.chat.id,
          message_id=anim_msg.message_id,
          parse_mode="Markdown",
      )
      bot.send_message(
          message.chat.id,
          "Select another service using the buttons below:",
          reply_markup=get_main_keyboard(user_id),
      )
    except Exception as e:
      bot.edit_message_text(
          "❌ API Retrieval Error: `" + str(e) + "`",
          chat_id=message.chat.id,
          message_id=anim_msg.message_id,
          parse_mode="Markdown",
      )


@bot.callback_query_handler(
    func=lambda call: call.data in [
        "admin_stats",
        "admin_bc",
        "main_menu",
        "check_join",
        "buy_59",
        "buy_99",
    ]
)
def handle_admin_inline(call):
  chat_id = call.message.chat.id
  user_id = call.from_user.id

  if call.data == "main_menu":
    bot.delete_message(chat_id, call.message.message_id)
    bot.send_message(
        chat_id,
        "🌟 *Prime Tips Menu*",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  if call.data in ["check_join", "buy_59", "buy_99"]:
    return

  if user_id != ADMIN_ID:
    bot.answer_callback_query(call.id, "❌ Unauthorized access!", show_alert=True)
    return

  if call.data == "admin_stats":
    total_users = len(active_users)
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔙 Return to Main 🏠", callback_data="main_menu")
    )
    bot.edit_message_text(
        "📊 *Prime Tips System Analytics* 📈\n\n• Total Active Users: `"
        + str(total_users)
        + "` 👥",
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown",
    )

  elif call.data == "admin_bc":
    user_state[user_id] = "waiting_for_broadcast"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔙 Return to Main 🏠", callback_data="main_menu")
    )
    bot.edit_message_text(
        "📢 *Global Broadcast Engine* 🚀\n\nEnter text payload to broadcast"
    

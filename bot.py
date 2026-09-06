import time
import requests
import telebot
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
  except:
    pass
  return False


# Professional Prime Tips Keyboard Layout
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
            "🎉 *Referral Reward Unlocked!*\n🎁 New referral joined. **₹5** added"
            " to your wallet!",
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
        "⚠️ *Access Restricted!*\n\nPlease join our official channel to use"
        " Prime Tips services. Click 'Verify Subscription' after joining.",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  bot.send_message(
      message.chat.id,
      "🌟 *Welcome to Prime Tips Utility Bot*\n\nSelect an option below to"
      " begin:",
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
          "✨ *Prime Tips Hub Unlocked!*",
          reply_markup=get_main_keyboard(user_id),
          parse_mode="Markdown",
      )
    else:
      bot.answer_callback_query(
          call.id, "❌ Please join the channel first!", show_alert=True
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
    user_state[user_id] = f"waiting_for_plan_uid_{days}"

    bot.send_message(
        chat_id,
        f"✅ *Plan Order Initialized!*\n(₹{plan_cost} deducted)\n\nEnter target"
        " **Free Fire UID**:",
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
    add_history(target_user_id, f"Added ₹{amount} via Admin approval")
    bot.answer_callback_query(call.id, f"Approved! ₹{amount} added.")
    bot.edit_message_text(
        f"✅ *Deposit Approved!*\nUser ID: `{target_user_id}` | Credited:"
        f" `₹{amount}`",
        chat_id=chat_id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )
    bot.send_message(
        target_user_id,
        f"🎉 *Deposit Confirmed!*\nYour payment of ₹{amount} has been approved"
        " by admin.",
    )

  elif call.data.startswith("reject_"):
    if user_id != ADMIN_ID:
      return
    _, target_user_id, amount = call.data.split("_")
    target_user_id = int(target_user_id)
    amount = int(amount)

    bot.answer_callback_query(call.id, f"Deposit of ₹{amount} rejected.")
    bot.edit_message_text(
        f"❌ *Deposit Rejected!*\nUser ID: `{target_user_id}` | Amount:"
        f" `₹{amount}`",
        chat_id=chat_id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )
    bot.send_message(
        target_user_id,
        "❌ *Deposit Rejected.*\nYour payment submission was declined by"
        " administration. Contact support if this is an error.",
    )


@bot.message_handler(func=lambda message: True)
def handle_text(message):
  user_id = message.from_user.id
  text = message.text.strip()
  state = user_state.get(user_id)
  username = (
      f"@{message.from_user.username}"
      if message.from_user.username
      else message.from_user.first_name
  )

  # Admin Broadcast Handler
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
        f"✅ Broadcast sent successfully to {success_count} users.",
        reply_markup=get_main_keyboard(user_id),
    )
    return

  # Functional AI Assistant Support Handler (Automatic Auto-Response Bot)
  if state == "ai_support_chat":
    if text == "🔙 Exit AI Support":
      user_state.pop(user_id, None)
      bot.send_message(
          message.chat.id,
          "🤖 AI Support closed.",
          reply_markup=get_main_keyboard(user_id),
      )
      return

    ai_reply = (
        f"🤖 *Prime Tips AI Assistant:*\n\nI have processed your query:"
        f" *'{text}'*.\n\nFor instant service execution, use the navigation"
        " options below or deposit funds to purchase plans. If you encounter"
        " verification issues, please reach out via admin support channels!"
    )
    bot.send_message(message.chat.id, ai_reply, parse_mode="Markdown")
    return

  # Menu Actions
  if text == "🛒 Buy Plans (Likes)":
    user_state.pop(user_id, None)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            "💎 15 Days Plan (₹59) - 220 Likes/Day", callback_data="buy_59"
        ),
        InlineKeyboardButton(
            "💎 30 Days Plan (₹99) - Full Package", callback_data="buy_99"
        ),
    )
    bot.send_message(
        message.chat.id,
        "📦 *Prime Tips Subscription Plans:*\n\n• **₹59 Plan:** 15 Days Active"
        " Timer (220 Likes daily)\n• **₹99 Plan:** 30 Days Complete"
        " Package\n\n*(Ensure sufficient wallet balance before purchasing)*",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  elif text == "💰 Add Money (Wallet)":
    user_state[user_id] = "waiting_for_amount"
    bot.send_message(
        message.chat.id,
        "💰 *Wallet Deposit Center*\n\nEnter the amount you want to add"
        " (Example: `59` or `100`):",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text == "💼 My Wallet":
    user_state.pop(user_id, None)
    bal = user_balances.get(user_id, 0)
    bot.send_message(
        message.chat.id,
        f"💼 *Wallet Balance Ledger*\n\n• Available Balance: `₹{bal}`",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text == "🔍 Free Fire UID Info":
    user_state[user_id] = "waiting_for_info_uid"
    bot.send_message(
        message.chat.id,
        "🔍 *Free Fire UID Info*\n\nEnter player target **UID**:",
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
        "👥 *Refer & Earn Program*\n\nShare your link with friends. Earn an"
        " instant **₹5** bonus for every user who joins!\n\n🔗 *Your Referral"
        f" Link:*\n`{ref_link}`",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )
    return

  elif text == "📜 History":
    user_state.pop(user_id, None)
    history_list = user_history.get(user_id, [])
    if not history_list:
      history_text = "No recent transaction logs found."
    else:
      history_text = "\n".join([f"▫️ {item}" for item in history_list])

    bot.send_message(
        message.chat.id,
        f"📜 *Transaction & Activity History:*\n\n{history_text}",
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
        "🤖 *AI Support Active!*\n\nType any query or inquiry below for"
        " automated assistance.",
        reply_markup=ai_markup,
        parse_mode="Markdown",
    )
    return

  elif text == "👑 Admin Panel" and user_id == ADMIN_ID:
    user_state.pop(user_id, None)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            "📊 System Analytics (Users)", callback_data="admin_stats"
        ),
        InlineKeyboardButton(
            "📢 Broadcast Global Message", callback_data="admin_bc"
        ),
    )
    bot.send_message(
        message.chat.id,
        "👑 *Prime Tips Admin Command Center*\n\nChoose an administrative"
        " action:",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  # States
  if state == "waiting_for_amount":
    if not text.isdigit():
      bot.reply_to(message, "❌ Invalid input! Please enter numbers only.")
      return

    user_state[user_id] = f"waiting_for_ss_{text}"
    bot.reply_to(
        message,
        f"💳 *UPI Payment Gateway*\n\nUPI ID: `sima6241@ptaxis`\nAmount:"
        f" `₹{text}`\n\nAfter payment completion, submit your **Transaction ID /"
        " Screenshot details** here:",
        parse_mode="Markdown",
    )

  elif state and state.startswith("waiting_for_ss_"):
    amount = state.split("_")[3]
    user_state.pop(user_id, None)

    bot.reply_to(
        message,
        "⏳ *Verification Pending.*\nYour deposit proof has been routed to"
        " admin for verification.",
        reply_markup=get_main_keyboard(user_id),
    )

    # Admin Notification with Username, User ID, and Approval/Rejection buttons
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
        f"🔔 *New Wallet Deposit Request!*\n\n👤 User Name: {username}\n🆔 User"
        f" ID: `{user_id}`\n💰 Amount: `₹{amount}`\n\nProof Details:"
        f" {text}",
        reply_markup=markup,
        parse_mode="Markdown",
    )

  elif state and state.startswith("waiting_for_plan_uid_"):
    days = state.split("_")[4]
    uid = text
    user_state.pop(user_id, None)

    if not uid.isdigit():
      bot.reply_to(message, "❌ Invalid UID format! Enter numbers only.")
      return

    expiry_time = time.time() + (int(days) * 86400)
    user_timers[user_id] = {"uid": uid, "days": days, "expires": expiry_time}
    add_history(user_id, f"Subscribed {days}-Days Plan for UID: {uid}")

    try:
      api_url = f"https://ff-info-ro45.vercel.app/api?uid={uid}&key=Anurag"
      response = requests.get(api_url, timeout=15)
      data = response.json()
      basic = data.get("basicInfo", {})
      nickname = basic.get("nickname", "N/A")
      likes = basic.get("liked", "N/A")
    except:
      nickname = "N/A"
      likes = "N/A"

    bot.reply_to(
        message,
        f"🎉 *Plan Deployed Successfully!*\n\n• Player Name:"
        f" `{nickname}`\n• UID: `{uid}`\n• Likes: `{likes}`\n• Duration:"
        f" `{days} Days`\n• Daily Quota: `220 Likes/Day`\n\n⏱️ Active timer"
        f" successfully initiated!",
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown",
    )

  elif state == "waiting_for_info_uid":
    uid = text
    user_state.pop(user_id, None)

    if not uid.isdigit():
      bot.reply_to(message, "❌ Invalid UID pattern!")
      return

    msg = bot.reply_to(message, "⏳ *Fetching player telemetry...*")
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
          f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
      )
      add_history(user_id, f"Queried UID: {uid}")
      bot.edit_message_text(
          formatted_text,
          chat_id=message.chat.id,
          message_id=msg.message_id,
          parse_mode="Markdown",
      )
      bot.send_message(
          message.chat.id,
          "Select another service using the buttons below:",
          reply_markup=get_main_keyboard(user_id),
      )
    except Exception as e:
      bot.edit_message_text(
          f"❌ API Retrieval Error: `{str(e)}`",
          chat_id=message.chat.id,
          message_id=msg.message_id,
          parse_mode="Markdown",
      )


@bot.callback_query_handler(
    func=lambda call: call.data in ["admin_stats", "admin_bc"]
)
def handle_admin_inline(call):
  chat_id = call.message.chat.id
  user_id = call.from_user.id

  if user_id != ADMIN_ID:
    bot.answer_callback_query(call.id, "❌ Unauthorized access!", show_alert=True)
    return

  if call.data == "admin_stats":
    total_users = len(active_users)
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔙 Return to Main", callback_data="main_menu")
    )
    bot.edit_message_text(
        f"📊 *Prime Tips System Analytics*\n\n• Total Active Users:"
        f" `{total_users}`",
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown",
    )

  elif call.data == "admin_bc":
    user_state[user_id] = "waiting_for_broadcast"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔙 Return to Main", callback_data="main_menu")
    )
    bot.edit_message_text(
        "📢 *Global Broadcast Engine*\n\nEnter text payload to broadcast across"
        " all active users:",
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown",
    )


if __name__ == "__main__":
  print("🚀 Prime Tips Professional Bot with Username Deposit & AI Support Online!")
  bot.infinity_polling()
    

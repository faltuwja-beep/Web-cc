import requests
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# =====================================
# CONFIG
# =====================================

TOKEN = "8765709173:AAGGxm08W3vCr2sN_5g8OZ34rFZqrYNSl6M"

API_URL = "https://info.leadershadman.online/wishlist?uid={uid}"

EMOTE_API = (
    "https://cdn.jsdelivr.net/gh/"
    "ShahGCreator/icon@main/PNG/{}.png"
)

INFO_API = (
    "https://info.leadershadman.online/"
    "player-info?uid={uid}"
)

BASE_URL = "https://info.leadershadman.online"

IMAGE_URL = "https://image.leadershadman.online"


bot = telebot.TeleBot(TOKEN)


# =====================================
# USER STATE
# =====================================

user_state = {}


# =====================================
# MAIN KEYBOARD
# =====================================

def main_keyboard():

    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    markup.add(
        KeyboardButton("🔍 Player Info"),
        KeyboardButton("❤️ Wishlist")
    )

    markup.add(
        KeyboardButton("ℹ️ Help")
    )

    return markup


# =====================================
# START
# =====================================

@bot.message_handler(commands=["start"])
def start(message):

    user_state.pop(
        message.from_user.id,
        None
    )

    bot.send_message(
        message.chat.id,

        "🎮 *Free Fire Player Tool*\n\n"
        "Select a service below.",

        reply_markup=main_keyboard(),

        parse_mode="Markdown"
    )


# =====================================
# PLAYER INFO BUTTON
# =====================================

@bot.message_handler(
    func=lambda message:
    message.text == "🔍 Player Info"
)
def ask_player_uid(message):

    user_state[
        message.from_user.id
    ] = "player_info"

    bot.send_message(
        message.chat.id,

        "🔍 *Player Info*\n\n"
        "Send the Free Fire UID.",

        parse_mode="Markdown"
    )


# =====================================
# WISHLIST BUTTON
# =====================================

@bot.message_handler(
    func=lambda message:
    message.text == "❤️ Wishlist"
)
def ask_wishlist_uid(message):

    user_state[
        message.from_user.id
    ] = "wishlist"

    bot.send_message(
        message.chat.id,

        "❤️ *Wishlist Info*\n\n"
        "Send the Free Fire UID.",

        parse_mode="Markdown"
    )


# =====================================
# HELP
# =====================================

@bot.message_handler(
    func=lambda message:
    message.text == "ℹ️ Help"
)
def help_command(message):

    bot.send_message(
        message.chat.id,

        "ℹ️ *How To Use*\n\n"
        "1️⃣ Select Player Info\n"
        "2️⃣ Send UID\n"
        "3️⃣ Get player details\n\n"
        "OR\n\n"
        "1️⃣ Select Wishlist\n"
        "2️⃣ Send UID\n"
        "3️⃣ Get wishlist information",

        reply_markup=main_keyboard(),

        parse_mode="Markdown"
    )


# =====================================
# SAFE GET VALUE
# =====================================

def get_value(data, *keys, default="N/A"):

    for key in keys:

        if isinstance(data, dict) and key in data:
            value = data.get(key)

            if value is not None:
                return value

    return default


# =====================================
# PLAYER INFO FUNCTION
# =====================================

def get_player_info(message, uid):

    loading = bot.send_message(
        message.chat.id,

        "⏳ *Fetching player information...*",

        parse_mode="Markdown"
    )

    try:

        url = INFO_API.format(uid=uid)

        response = requests.get(
            url,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        # Some APIs return data inside "data"
        if isinstance(data, dict):

            player = data.get(
                "basicInfo",
                data.get(
                    "data",
                    data
                )
            )

        else:
            player = {}

        # Common fields
        name = get_value(
            player,
            "nickname",
            "name",
            "playerName"
        )

        account_id = get_value(
            player,
            "accountId",
            "uid",
            "playerId",
            default=uid
        )

        region = get_value(
            player,
            "region"
        )

        level = get_value(
            player,
            "level"
        )

        exp = get_value(
            player,
            "exp"
        )

        likes = get_value(
            player,
            "liked",
            "likes"
        )

        rank = get_value(
            player,
            "rank"
        )

        cs_rank = get_value(
            player,
            "csRank"
        )

        ranking_points = get_value(
            player,
            "rankingPoints"
        )

        result = (
            "🎮 *FREE FIRE PLAYER INFO*\n\n"

            "━━━━━━━━━━━━━━━━━━\n"

            f"👤 *Name:* `{name}`\n"
            f"🆔 *UID:* `{account_id}`\n"
            f"🌍 *Region:* `{region}`\n"
            f"📊 *Level:* `{level}`\n"
            f"✨ *EXP:* `{exp}`\n"
            f"❤️ *Likes:* `{likes}`\n\n"

            "━━━━━━━━━━━━━━━━━━\n\n"

            f"🏆 *BR Rank:* `{rank}`\n"
            f"⚔️ *CS Rank:* `{cs_rank}`\n"
            f"🎯 *Rank Points:* `{ranking_points}`\n\n"

            "━━━━━━━━━━━━━━━━━━"
        )

        bot.edit_message_text(
            result,

            chat_id=message.chat.id,

            message_id=loading.message_id,

            parse_mode="Markdown"
        )

        bot.send_message(
            message.chat.id,

            "Choose another service:",

            reply_markup=main_keyboard()
        )

    except requests.exceptions.Timeout:

        bot.edit_message_text(
            "❌ *API Timeout!*\n\n"
            "Server response is taking too long.",

            chat_id=message.chat.id,

            message_id=loading.message_id,

            parse_mode="Markdown"
        )

    except requests.exceptions.RequestException:

        bot.edit_message_text(
            "❌ *API Connection Error!*\n\n"
            "Unable to connect to the API server.",

            chat_id=message.chat.id,

            message_id=loading.message_id,

            parse_mode="Markdown"
        )

    except ValueError:

        bot.edit_message_text(
            "❌ *Invalid API Response!*\n\n"
            "The server did not return valid JSON.",

            chat_id=message.chat.id,

            message_id=loading.message_id,

            parse_mode="Markdown"
        )

    except Exception as e:

        bot.edit_message_text(
            f"❌ *Error!*\n\n`{str(e)}`",

            chat_id=message.chat.id,

            message_id=loading.message_id,

            parse_mode="Markdown"
        )


# =====================================
# WISHLIST FUNCTION
# =====================================

def get_wishlist(message, uid):

    loading = bot.send_message(
        message.chat.id,

        "⏳ *Fetching wishlist information...*",

        parse_mode="Markdown"
    )

    try:

        url = API_URL.format(uid=uid)

        response = requests.get(
            url,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        # API can return a dictionary
        # or list of wishlist/emote IDs

        if isinstance(data, dict):

            # Check common list names
            items = (
                data.get("wishlist")
                or data.get("data")
                or data.get("items")
                or data.get("emotes")
                or []
            )

        elif isinstance(data, list):

            items = data

        else:

            items = []

        # If API response is not a list
        if not isinstance(items, list):

            items = [items]

        count = len(items)

        result = (
            "❤️ *FREE FIRE WISHLIST*\n\n"

            f"🆔 *UID:* `{uid}`\n"
            f"📦 *Total Items:* `{count}`\n\n"

            "━━━━━━━━━━━━━━━━━━\n"
        )

        # Show first 20 items
        for index, item in enumerate(
            items[:20],
            start=1
        ):

            if isinstance(item, dict):

                item_id = (
                    item.get("id")
                    or item.get("itemId")
                    or item.get("emoteId")
                    or "N/A"
                )

                item_name = (
                    item.get("name")
                    or item.get("itemName")
                    or item.get("emoteName")
                    or "Unknown"
                )

                result += (
                    f"{index}. `{item_name}`\n"
                    f"   ID: `{item_id}`\n\n"
                )

            else:

                result += (
                    f"{index}. `{item}`\n"
                )

        result += (
            "\n━━━━━━━━━━━━━━━━━━"
        )

        bot.edit_message_text(
            result,

            chat_id=message.chat.id,

            message_id=loading.message_id,

            parse_mode="Markdown"
        )

        bot.send_message(
            message.chat.id,

            "Choose another service:",

            reply_markup=main_keyboard()
        )

    except requests.exceptions.Timeout:

        bot.edit_message_text(
            "❌ *Wishlist API Timeout!*",

            chat_id=message.chat.id,

            message_id=loading.message_id,

            parse_mode="Markdown"
        )

    except requests.exceptions.RequestException:

        bot.edit_message_text(
            "❌ *Wishlist API Connection Error!*",

            chat_id=message.chat.id,

            message_id=loading.message_id,

            parse_mode="Markdown"
        )

    except Exception as e:

        bot.edit_message_text(
            f"❌ *Error!*\n\n`{str(e)}`",

            chat_id=message.chat.id,

            message_id=loading.message_id,

            parse_mode="Markdown"
        )


# =====================================
# UID INPUT HANDLER
# =====================================

@bot.message_handler(func=lambda message: True)
def handle_uid(message):

    user_id = message.from_user.id

    text = message.text.strip()

    state = user_state.get(user_id)

    # Ignore if user has not selected a service
    if state is None:

        bot.send_message(
            message.chat.id,

            "Please select a service first.",

            reply_markup=main_keyboard()
        )

        return

    # UID validation
    if not text.isdigit():

        bot.send_message(
            message.chat.id,

            "❌ Invalid UID!\n\n"
            "UID should contain numbers only."
        )

        return

    user_state.pop(
        user_id,
        None
    )

    # Player info
    if state == "player_info":

        get_player_info(
            message,
            text
        )

    # Wishlist
    elif state == "wishlist":

        get_wishlist(
            message,
            text
        )


# =====================================
# RUN BOT
# =====================================

if __name__ == "__main__":

    print(
        "🚀 Free Fire Info Bot Started!"
    )

    bot.infinity_polling(
        skip_pending=True
    )

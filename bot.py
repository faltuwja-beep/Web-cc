import requests
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# =========================
# CONFIG
# =========================

TOKEN = "8765709173:AAGGxm08W3vCr2sN_5g8OZ34rFZqrYNSl6M"

API_KEY = "Anurag"

bot = telebot.TeleBot(TOKEN)


# =========================
# KEYBOARD
# =========================

def main_keyboard():
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.add(
        KeyboardButton("🔍 Free Fire UID Info")
    )

    markup.add(
        KeyboardButton("ℹ️ Bot Info")
    )

    return markup


# =========================
# START COMMAND
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    bot.send_message(
        message.chat.id,

        "🎮 *Welcome to Free Fire UID Info Bot!*\n\n"
        "🔍 Click the button below and send a Free Fire UID.",

        reply_markup=main_keyboard(),

        parse_mode="Markdown"
    )


# =========================
# BUTTON HANDLER
# =========================

@bot.message_handler(
    func=lambda message:
    message.text == "🔍 Free Fire UID Info"
)
def ask_uid(message):

    bot.send_message(
        message.chat.id,

        "🎮 *Send Free Fire UID*\n\n"
        "Example:\n`14307670967`",

        parse_mode="Markdown"
    )

    bot.register_next_step_handler(
        message,
        get_uid_info
    )


# =========================
# GET UID INFO
# =========================

def get_uid_info(message):

    uid = message.text.strip()

    # UID validation
    if not uid.isdigit():

        bot.send_message(
            message.chat.id,

            "❌ Invalid UID!\n\n"
            "Please send numbers only.",

            reply_markup=main_keyboard()
        )

        return

    # Loading message
    loading = bot.send_message(
        message.chat.id,

        "⏳ *Fetching Free Fire player info...*",

        parse_mode="Markdown"
    )

    try:

        # API URL
        api_url = (
            "https://ff-info-ro45.vercel.app/api"
            f"?uid={uid}&key={API_KEY}"
        )

        response = requests.get(
            api_url,
            timeout=20
        )

        # Check HTTP error
        response.raise_for_status()

        data = response.json()

        # Basic Info
        basic = data.get(
            "basicInfo",
            {}
        )

        # Pet Info
        pet = data.get(
            "petInfo",
            {}
        )

        # Clan Info
        clan = data.get(
            "clanBasicInfo",
            {}
        )

        # Player Details
        nickname = basic.get(
            "nickname",
            "Not Found"
        )

        account_id = basic.get(
            "accountId",
            uid
        )

        region = basic.get(
            "region",
            "N/A"
        )

        level = basic.get(
            "level",
            "N/A"
        )

        exp = basic.get(
            "exp",
            "N/A"
        )

        likes = basic.get(
            "liked",
            "N/A"
        )

        rank = basic.get(
            "rank",
            "N/A"
        )

        rank_points = basic.get(
            "rankingPoints",
            "N/A"
        )

        cs_rank = basic.get(
            "csRank",
            "N/A"
        )

        max_rank = basic.get(
            "maxRank",
            "N/A"
        )

        cs_max_rank = basic.get(
            "csMaxRank",
            "N/A"
        )

        version = basic.get(
            "releaseVersion",
            "N/A"
        )

        # Clan
        clan_name = clan.get(
            "clanName",
            "No Guild"
        )

        # Pet
        pet_id = pet.get(
            "id",
            "N/A"
        )

        pet_level = pet.get(
            "level",
            "N/A"
        )

        # Diamond
        diamond = data.get(
            "diamondCostRes",
            {}
        )

        diamond_cost = diamond.get(
            "diamondCost",
            "N/A"
        )

        # Profile message
        result = f"""
🎮 *FREE FIRE PLAYER INFO*

━━━━━━━━━━━━━━━━━━

👤 *Name:* `{nickname}`

🆔 *UID:* `{account_id}`

🌍 *Region:* `{region}`

📊 *Level:* `{level}`

✨ *EXP:* `{exp}`

❤️ *Likes:* `{likes}`

━━━━━━━━━━━━━━━━━━

🏆 *BR Rank:* `{rank}`

🎯 *Rank Points:* `{rank_points}`

⚔️ *CS Rank:* `{cs_rank}`

🥇 *Max BR Rank:* `{max_rank}`

🥇 *Max CS Rank:* `{cs_max_rank}`

━━━━━━━━━━━━━━━━━━

🛡️ *Guild:* `{clan_name}`

🐾 *Pet ID:* `{pet_id}`

📈 *Pet Level:* `{pet_level}`

💎 *Diamond Cost:* `{diamond_cost}`

━━━━━━━━━━━━━━━━━━

🎮 *Game Version:* `{version}`
"""

        bot.delete_message(
            message.chat.id,
            loading.message_id
        )

        bot.send_message(
            message.chat.id,

            result,

            parse_mode="Markdown",

            reply_markup=main_keyboard()
        )

    except requests.exceptions.Timeout:

        bot.edit_message_text(

            "❌ *API Timeout!*\n\n"
            "Server is taking too long. Try again.",

            message.chat.id,

            loading.message_id,

            parse_mode="Markdown"
        )

    except requests.exceptions.RequestException as e:

        bot.edit_message_text(

            "❌ *API Error!*\n\n"
            "Unable to connect to the server.",

            message.chat.id,

            loading.message_id,

            parse_mode="Markdown"
        )

    except Exception as e:

        bot.edit_message_text(

            "❌ *Error!*\n\n"
            f"`{str(e)}`",

            message.chat.id,

            loading.message_id,

            parse_mode="Markdown"
        )


# =========================
# BOT INFO
# =========================

@bot.message_handler(
    func=lambda message:
    message.text == "ℹ️ Bot Info"
)
def bot_info(message):

    bot.send_message(
        message.chat.id,

        "🤖 *Free Fire UID Info Bot*\n\n"
        "Send any Free Fire UID to get player information.",

        parse_mode="Markdown"
    )


# =========================
# RUN BOT
# =========================

print("🚀 Free Fire UID Info Bot Started!")

bot.infinity_polling(
    skip_pending=True
)

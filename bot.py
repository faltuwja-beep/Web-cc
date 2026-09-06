import requests
import telebot

# =========================
# CONFIG
# =========================

TOKEN = "8765709173:AAGGxm08W3vCr2sN_5g8OZ34rFZqrYNSl6M"

EMOTE_API = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG/{}.png"

bot = telebot.TeleBot(TOKEN)


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    bot.send_message(
        message.chat.id,
        "🎮 *Free Fire Emote Image Bot*\n\n"
        "🖼️ Mujhe Emote/Image ID bhejo.\n\n"
        "Example:\n"
        "`16`",
        parse_mode="Markdown"
    )


# =========================
# IMAGE ID HANDLER
# =========================

@bot.message_handler(func=lambda message: True)
def send_emote(message):

    image_id = message.text.strip()

    # Only numbers
    if not image_id.isdigit():

        bot.send_message(
            message.chat.id,
            "❌ Invalid ID!\n\n"
            "Sirf number bhejo.\n"
            "Example: `16`",
            parse_mode="Markdown"
        )
        return

    url = EMOTE_API.format(image_id)

    loading = bot.send_message(
        message.chat.id,
        "⏳ Image fetch ho rahi hai..."
    )

    try:

        response = requests.get(
            url,
            timeout=15
        )

        if response.status_code != 200:

            bot.edit_message_text(
                "❌ Is ID ki image nahi mili.",
                message.chat.id,
                loading.message_id
            )

            return

        # Telegram ko direct URL se photo bhejne ki koshish
        bot.send_photo(
            message.chat.id,
            url,
            caption=f"🎮 Free Fire Image\n🆔 ID: `{image_id}`",
            parse_mode="Markdown"
        )

        bot.delete_message(
            message.chat.id,
            loading.message_id
        )

    except Exception as e:

        try:
            bot.delete_message(
                message.chat.id,
                loading.message_id
            )
        except:
            pass

        bot.send_message(
            message.chat.id,
            "❌ Image send nahi ho payi.\n\n"
            f"Error: `{e}`",
            parse_mode="Markdown"
        )


# =========================
# RUN
# =========================

print("🚀 Emote Image Bot Started!")

bot.infinity_polling(
    skip_pending=True
)

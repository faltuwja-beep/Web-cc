import telebot
import threading
from PIL import Image
import requests
from datetime import datetime
from io import BytesIO
import time
import json
import os

# ================= LOAD .env FILE (no need to export manually) =================
def load_env_file(path=".env"):
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

load_env_file()

# ================= CONFIG =================
TOKEN = os.environ.get("8765709173:AAGGxm08W3vCr2sN_5g8OZ34rFZqrYNSl6M")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")
bot = telebot.TeleBot(TOKEN)

# ========= API LINKS =========
API_URL = "https://info.leadershadman.online/wishlist?uid={uid}"
EMOTE_API = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG/{}.png"
INFO_API = "https://info.leadershadman.online/player-info?uid={uid}"
# ========= NEW APIs =========
BASE_URL = "https://info.leadershadman.online"
IMAGE_URL = "https://image.leadershadman.online"

def banner_to_sticker(image_data):

    img = Image.open(image_data)

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    img.thumbnail((512, 512))

    output = BytesIO()
    output.name = "sticker.png"

    img.save(output, format="PNG")

    output.seek(0)

    return output

# ========= SAFE REQUEST =========
def safe_get_url(url):
    response = requests.get(url, timeout=150)

    if response.status_code != 200:
        raise Exception("API Error")

    return response


# ========= FETCH PLAYER DATA =========
def fetch_player_data_by_uid_or_name(search_parameter):

    if search_parameter.isdigit():
        url = f"{BASE_URL}/player-info?uid={search_parameter}"
    else:
        url = f"{BASE_URL}/player-info?name={search_parameter}"

    response = requests.get(url, timeout=150)

    if response.status_code != 200:
        return None

    data = response.json()

    basic_info = data.get("basicInfo", {})

    return (
        basic_info.get("accountId"),
        basic_info.get("nickname"),
        basic_info.get("region", "Not Found"),
        data
    )


# ========= FETCH BANNER =========
def fetch_banner_image(player_data):

    basic_information = player_data.get("basicInfo", {})
    clan_information = player_data.get("clanBasicInfo", {})

    frame = "true" if basic_information.get(
        "primeLevel", {}
    ).get("level") == 8 else "false"

    url = (
        f"{IMAGE_URL}/banner-image?"
        f"headPic={basic_information.get('headPic','')}"
        f"&bannerId={basic_information.get('bannerId','')}"
        f"&name={basic_information.get('nickname','').replace('#','%23').replace('&','%26')}"
        f"&level={basic_information.get('level',2)}"
        f"&guild={clan_information.get('clanName','').replace('#','%23').replace('&','%26')}"
        f"&pinId={basic_information.get('pinId','900000012')}"
        f"&celebrity={basic_information.get('celebrityStatus',0)}"
        f"&primeLevel={basic_information.get('primeLevel',{}).get('level',0)}"
        f"&frame={frame}"
    )

    response = safe_get_url(url)

    return response.content


# ========= FETCH OUTFIT =========
def fetch_outfit_image(player_data):

    basic_information = player_data.get("basicInfo", {})
    profile_information = player_data.get("profileInfo", {})

    equipped_weapons = basic_information.get(
        "weaponSkinShows", []
    )

    equipped_outfits = profile_information.get(
        "clothes", []
    )

    character_id = profile_information.get(
        "avatarId",
        "102000007"
    )

    outfit_ids = ",".join(
        str(item)
        for item in (equipped_outfits + equipped_weapons)
    ) if (equipped_outfits or equipped_weapons) else ""

    url = (
        f"{IMAGE_URL}/outfit-image?"
        f"avatar_id={character_id}"
        f"&clothes={outfit_ids}"
    )

    response = safe_get_url(url)

    return response.content
    
def convert_time(ts):
    try:
        if not ts:
            return "Not Found"

        ts = int(str(ts).strip())

        if ts > 1000000000000:  # milliseconds check
            ts = ts / 1000

        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Not Found"         
              
# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    text = """
<b><tg-emoji emoji-id='5372981976804366741'>🤖</tg-emoji> FREE FIRE PLAYER INFO BOT <tg-emoji emoji-id='5372981976804366741'>🤖</tg-emoji>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id='6100170496077204999'>⚡</tg-emoji> BOT FEATURES <tg-emoji emoji-id='6100170496077204999'>⚡</tg-emoji>

PLAYER INFO
View level, likes, rank, account info, activity and more
PLAYER SYSTEM
Get complete player information using UID with fast response and accurate data processing
REAL TIME DATA
All data is fetched live from API ensuring up to date and reliable information
MULTIPLE API INTEGRATION
Uses multiple APIs simultaneously for faster performance and better results
FAST API DATA
Optimized system with parallel requests for instant output
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id='6221914376329237010'>🆘</tg-emoji> MAIN COMMANDS <tg-emoji emoji-id='6221914376329237010'>🆘</tg-emoji>

/get &lt;uid&gt; - Full player info with all personal details  
/bancheck &lt;uid&gt; - Account status  
/banner &lt;uid&gt; - give banner image
/outfit &lt;region&gt; &lt;uid&gt; - give Outfit image
/region &lt;uid&gt; - Region information  
/token &lt;uid&gt; &lt;password&gt; - Generate login JWT token  
/wishlist &lt;uid&gt; - Get wishlist data in JSON   
/level &lt;uid&gt; - Get level data with EXP and next level progress  
/events &lt;region&gt; - Give events images 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type /help to get all commands
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id='6237905016313615867'>💫</tg-emoji> PLAYER INFO DATA

Get full player data  
Player guild information  
Ban check status  
Get wishlist items  
Update guest account bio  
Region information  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id='5796157163084718357'>🌏</tg-emoji> GLOBAL REGION SUPPORT  
IND, BD, US, VN, SG  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id='6100674965755924191'>👑</tg-emoji> BOT POWERED BY 𝗦𝗛𝗔𝗗𝗠𝗔𝗡 𝗖𝗢𝗗𝗘𝗥
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"""
    bot.send_message(
    chat_id=message.chat.id,
    text=text,
    parse_mode="HTML",
    reply_to_message_id=message.message_id
)

# ================= HELP =================
@bot.message_handler(commands=['help'])
def help(message):
    text = """
<b><tg-emoji emoji-id='6235722567336859128'>📖</tg-emoji> FREE FIRE PLAYER INFO BOT HELP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id='6221914376329237010'>🆘</tg-emoji> COMMAND GUIDE <tg-emoji emoji-id='6221914376329237010'>🆘</tg-emoji>

/get &lt;uid&gt;
Get complete player information including level, rank, likes and account data
/bancheck &lt;uid&gt;
Check if the account is banned or safe
/region &lt;uid&gt;
Detect the player region using UID
/token &lt;uid&gt; &lt;password&gt;
Generate JWT login token for account access
/wishlist &lt;uid&gt;
Get player wishlist items directly from API
/banner &lt;uid&gt; - give banner image
/outfit &lt;region&gt; &lt;uid&gt; - give Outfit image
/level &lt;uid&gt;
Get player level details including EXP and level progress
/events &lt;region&gt; - Give events images 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id='5431577498364158238'>📊</tg-emoji> DATA PROVIDED BY BOT

ACCOUNT INFORMATION
Player name, UID, level, likes, region and signature
ACCOUNT ACTIVITY
Rank details, fire pass status and last login
GUILD INFORMATION
Guild name, guild ID, guild level and leader details
PET DETAILS
Pet name, type, level and experience
IMAGE DATA
Banner image and outfit image sent directly from API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<tg-emoji emoji-id='6100674965755924191'>👑</tg-emoji> BOT POWERED BY 𝗦𝗛𝗔𝗗𝗠𝗔𝗡 𝗖𝗢𝗗𝗘𝗥
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>
"""
    bot.send_message(
    chat_id=message.chat.id,
    text=text,
    parse_mode="HTML",
    reply_to_message_id=message.message_id
)
    

# ========= FORMAT FUNCTION =========
def format_info(data):
    return f"""<b>ACCOUNT INFORMATION:
┌ Basic Information:
├─ Prime Level: {data.get('basicInfo', {}).get('primeLevel', {}).get('level', 'Not Found')}
├─ Name: {data.get('basicInfo', {}).get('nickname', 'Not Found')}
├─ UID: {data.get('basicInfo', {}).get('accountId', 'Not Found')}
├─ Level: {data.get('basicInfo', {}).get('level', 'Not Found')} (Exp: {data.get('basicInfo', {}).get('exp', 'Not Found')})
├─ Region: {data.get('basicInfo', {}).get('region', 'Not Found')}
├─ Likes: {data.get('basicInfo', {}).get('liked', 'Not Found')}
├─ Honor Score: {data.get('creditScoreInfo', {}).get('creditScore', 'Not Found')}
├─ Celebrity Status: {data.get('basicInfo', {}).get('badgeId', 'Not Found')}
├─ Title Name: {data.get('basicInfo', {}).get('title', 'Not Found')}
└─ Signature: {data.get('socialInfo', {}).get('signature', 'Not Found')}

┌ Activity Information:
├─ Most Recent OB: {data.get('basicInfo', {}).get('releaseVersion', 'Not Found')}
├─ Fire Pass: {data.get('basicInfo', {}).get('seasonId', 'Not Found')}
├─ Current Bp Badges: {data.get('basicInfo', {}).get('badgeCnt', 'Not Found')}
├─ Br Rank: {data.get('basicInfo', {}).get('rank', 'Not Found')} ({data.get('basicInfo', {}).get('rankingPoints', 'Not Found')})
├─ Cs Rank: {data.get('basicInfo', {}).get('csRank', 'Not Found')} ({data.get('basicInfo', {}).get('csRankingPoints', 'Not Found')} Star)
├─ Gender: {data.get('socialInfo', {}).get('gender', 'Not Found')}
├─ Show Rank: {data.get('socialInfo', {}).get('rankShow', 'Not Found')}
├─ Show Br Rank: {data.get('basicInfo', {}).get('showBrRank', 'Not Found')}
├─ Show Cs Rank: {data.get('basicInfo', {}).get('showCsRank', 'Not Found')}
├─ Created At: {convert_time(data.get('basicInfo', {}).get('createAt'))}
└─ Last Login: {convert_time(data.get('basicInfo', {}).get('lastLoginAt'))}

┌ Overview Information:
├─ Avatar ID: {data.get('profileInfo', {}).get('avatarId', 'Not Found')}
├─ Banner ID: {data.get('basicInfo', {}).get('bannerId', 'Not Found')}
├─ Pin ID: {data.get('profileInfo', {}).get('pinId', 'Default')}
├─ Active Time: {data.get('socialInfo', {}).get('activeTime', 'Flexible')}
├─ Active Days: {data.get('socialInfo', {}).get('activeDays', 'Flexible')}
├─ Mode Prefer: {data.get('socialInfo', {}).get('rankShow', 'No Preference')}
├─ Equipped Skills: {data.get('profileInfo', {}).get('equippedSkills', 'Not Found')}
├─ Language: {data.get('socialInfo', {}).get('language', 'Not Found')}
├─ Equipped Battle Card ID: {data.get('profileInfo', {}).get('battleCardId', 'Not Equipped')}
├─ Equipped Gun ID: {data.get('profileInfo', {}).get('gunId', 'Not Equipped')}
├─ Equipped Animation ID: {data.get('profileInfo', {}).get('animationId', 'Not Equipped')}
├─ Transform Animation ID: {data.get('profileInfo', {}).get('transformAnimationId', 'Not Equipped')}
└─ Outfits: {data.get('profileInfo', {}).get('clothes', 'Graphically Presented Below')}

┌ Pet Details:
├─ Equipped?: {data.get('petInfo', {}).get('isSelected', 'Not Found')}
├─ Pet Name: {data.get('petInfo', {}).get('name', 'Not Found')}
├─ Pet Type: {data.get('petInfo', {}).get('id', 'Not Found')}
├─ Pet Exp: {data.get('petInfo', {}).get('exp', 'Not Found')}
└─ Pet Level: {data.get('petInfo', {}).get('level', 'Not Found')}

┌ Guild Information:
├─ Guild Name: {data.get('clanBasicInfo', {}).get('clanName', 'Not Found')}
├─ Guild ID: {data.get('clanBasicInfo', {}).get('clanId', 'Not Found')}
├─ Guild Level: {data.get('clanBasicInfo', {}).get('clanLevel', 'Not Found')}
├─ Live Members: {data.get('clanBasicInfo', {}).get('memberNum', 'Not Found')}/{data.get('clanBasicInfo', {}).get('capacity', 'Not Found')}
└─ Leader Information:
    ├─ Leader Name: {data.get('captainBasicInfo', {}).get('nickname', 'Not Found')}
    ├─ Leader UID: {data.get('captainBasicInfo', {}).get('accountId', 'Not Found')}
    ├─ Leader Level: {data.get('captainBasicInfo', {}).get('level', 'Not Found')} (Exp: {data.get('captainBasicInfo', {}).get('exp', 'Not Found')})
    ├─ Leader Region: {data.get('captainBasicInfo', {}).get('region', 'Not Found')}
    ├─ Leader Fire Pass: {data.get('captainBasicInfo', {}).get('seasonId', 'Not Found')}
    ├─ Leader Created At: {convert_time(data.get('captainBasicInfo', {}).get('createAt'))}
    ├─ Leader Last Login: {convert_time(data.get('captainBasicInfo', {}).get('lastLoginAt'))}
    ├─ Leader Most Recent OB: {data.get('captainBasicInfo', {}).get('releaseVersion', 'Not Found')}
    ├─ Leader Title Name: {data.get('captainBasicInfo', {}).get('title', 'Not Found')}
    ├─ Leader Current Bp Badges: {data.get('captainBasicInfo', {}).get('badgeCnt', 'Not Found')}
    ├─ Leader Br Rank: {data.get('captainBasicInfo', {}).get('rank', 'Not Found')} ({data.get('captainBasicInfo', {}).get('rankingPoints', 'Not Found')})
    └─ Leader Cs Rank: {data.get('captainBasicInfo', {}).get('csRank', 'Not Found')} ({data.get('captainBasicInfo', {}).get('csRankingPoints', 'Not Found')} Star)

┌ Public Craftland Maps
{data.get('craftlandInfo', 'Not Found')}</b>"""

# ========= COMMAND =========
@bot.message_handler(commands=["get"])
def get_info(message):
    parts = message.text.split()

    # <tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> UID check
    if len(parts) < 2:
        bot.reply_to(message, "<b><tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> Use: /get UID</b>", parse_mode="HTML")
        return

    uid = parts[1]

    # ⏳ Processing message
    processing = bot.reply_to(
        message,
        f"<b>⏳ Fetching {uid} details, please wait...</b>",
        parse_mode="HTML"
    )

    try:
        res = requests.get(INFO_API.format(uid=uid)).json()

        # <tg-emoji emoji-id='6224430136243000396'>🔴</tg-emoji> API error check
        if not res or "error" in res:
            try:
                bot.delete_message(message.chat.id, processing.message_id)
            except:
                pass

            error_msg = res.get("error", "Invalid UID or server error.")
            bot.reply_to(message, f"<b><tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> Info Error: {error_msg}</b>", parse_mode="HTML")
            return

        # <tg-emoji emoji-id='6224390807227470978'>✅</tg-emoji> Normal data
        text = format_info(res)

        try:
            bot.delete_message(message.chat.id, processing.message_id)
        except:
            pass

        bot.reply_to(message, text, parse_mode="HTML")

    except Exception as e:
        try:
            bot.delete_message(message.chat.id, processing.message_id)
        except:
            pass

        bot.reply_to(message, f"<b><tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> Info Error: {e}</b>", parse_mode="HTML")
        
   # ===== FETCH PLAYER DATA =====
    try:
        player = fetch_player_data_by_uid_or_name(uid)

        if not player:
            bot.send_message(
                message.chat.id,
                "<b><tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> Player Not Found</b>",
                parse_mode="HTML"
            )
            return

        account_id, nickname, region, player_data = player

    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"<b><tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> Player Fetch Error:</b> {e}",
            parse_mode="HTML"
        )
        return

    # ===== BANNER STICKER =====
    try:
        banner_bytes = fetch_banner_image(player_data)

        sticker = banner_to_sticker(
            BytesIO(banner_bytes)
        )

        bot.send_sticker(
            message.chat.id,
            sticker,
            reply_to_message_id=message.message_id
        )

    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"<b><tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> Banner Error:</b> {e}",
            parse_mode="HTML"
        )


    # ===== OUTFIT IMAGE =====
    try:
        outfit_bytes = fetch_outfit_image(player_data)

        photo = BytesIO(outfit_bytes)
        photo.name = "outfit.jpg"

        bot.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                reply_to_message_id=message.message_id,
                timeout=120
            )

    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"<b><tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> Outfit Error:</b> {e}",
            parse_mode="HTML"
        )
       
# ================= WISHLIST =================
def animate(msg, stop):
    dots = ["⏳ Processing", "⏳ Processing.", "⏳ Processing..", "⏳ Processing..."]
    i = 0
    while not stop["stop"]:
        try:
            bot.edit_message_text(
                f"<b>{dots[i % len(dots)]}</b>",
                msg.chat.id,
                msg.message_id,
                parse_mode="HTML"
            )
            i += 1
            time.sleep(0.5)
        except:
            break


@bot.message_handler(commands=["wishlist"])
def wishlist(message):
    parts = message.text.split()

    if len(parts) < 2:
        bot.reply_to(message, "<b><tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> Use: /wishlist UID</b>", parse_mode="HTML")
        return

    uid = parts[1]

    msg = bot.reply_to(message, "<b>⏳ Processing...</b>", parse_mode="HTML")

    stop_flag = {"stop": False}
    threading.Thread(target=animate, args=(msg, stop_flag)).start()

    # <tg-emoji emoji-id='6235234890980269200'>🔗</tg-emoji> API CALL
    try:
        res = requests.get(API_URL.format(uid), timeout=15).json()
    except:
        stop_flag["stop"] = True
        bot.edit_message_text("<b><tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> API Error</b>", message.chat.id, msg.message_id, parse_mode="HTML")
        return

    stop_flag["stop"] = True

    # <tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> FAIL CHECK
    if not res.get("success"):
        bot.edit_message_text("<b><tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> Failed to fetch data</b>", message.chat.id, msg.message_id, parse_mode="HTML")
        return

    player = res.get("player_info", {})

    # <tg-emoji emoji-id='6224390807227470978'>✅</tg-emoji> PLAYER INFO HEADER
    info = f"""<b>WISHLIST INFORMATION    
┌ PLAYER INFO
├─ Nickname' {player.get("name", "Not Found")}
├─ UID: {player.get("uid", uid)}
├─ Region: {player.get("region", "Not Found")}
└─ STATUS: SUCCESS <tg-emoji emoji-id='6224390807227470978'>✅</tg-emoji>
</b>"""

    bot.edit_message_text(info, message.chat.id, msg.message_id, parse_mode="HTML")

    wishlist = res.get("wishlist", [])

    if not wishlist:
        bot.send_message(message.chat.id, "<b><tg-emoji emoji-id='6224185666704511761'>❌</tg-emoji> Wishlist Not Found</b>", parse_mode="HTML")
        return

    # ================= ITEMS =================
    for item in wishlist:
        name = item.get("name", "Unknown Item")
        item_id = item.get("item_id")
        icon = item.get("icon", "")
        image_link = item.get("item_image_link")

        # <tg-emoji emoji-id='6222206124867718480'>🎯</tg-emoji> PERFECT EMOTE DETECTION
        if icon and "emote" in icon.lower():
            image = EMOTE_API.format(item_id) if item_id else image_link
        elif name and "emote" in name.lower():
            image = EMOTE_API.format(item_id) if item_id else image_link
        else:
            image = image_link

        # <tg-emoji emoji-id='6235620067942341623'>🧾</tg-emoji> CAPTION
        caption = f"""<b>┌ ITEM DETAILS
├─ Name: {name}
├─ ID: {item_id}
└─ TYPE: {"EMOTE <tg-emoji emoji-id='5323300526723469658'>🎭</tg-emoji>" if "e

from flask import Flask, render_template, request
import requests
import os
from datetime import datetime

app = Flask(__name__)

API_URL = "https://ff-info-ro45.vercel.app/api"
LIKE_API_BASE = "https://two0likeapifreebyzexxyh4x.onrender.com/like"

# Daily limit tracker: { "UID": "YYYY-MM-DD" }
daily_limit_tracker = {}


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/check-uid", methods=["POST"])
def check_uid():
    uid = request.form.get("uid", "").strip()
    player = None
    error = None

    if not uid.isdigit():
        error = "❌ Please enter a valid Free Fire UID"
    else:
        try:
            response = requests.get(
                API_URL,
                params={
                    "uid": uid,
                    "key": "Anurag"
                },
                timeout=20
            )
            response.raise_for_status()
            data = response.json()

            basic = data.get("basicInfo", {})
            clan = data.get("clanBasicInfo", {})
            pet = data.get("petInfo", {})

            current_likes = int(basic.get("liked", 0))

            player = {
                "nickname": basic.get("nickname", "N/A"),
                "uid": basic.get("accountId", uid),
                "level": basic.get("level", "N/A"),
                "region": basic.get("region", "N/A"),
                "likes": current_likes,
                "rank": basic.get("rank", "N/A"),
                "cs_rank": basic.get("csRank", "N/A"),
                "exp": basic.get("exp", "N/A"),
                "guild": clan.get("clanName", "No Guild"),
                "pet": pet.get("id", "N/A")
            }

        except requests.exceptions.RequestException:
            error = "❌ API connection error. Try again."
        except ValueError:
            error = "❌ Invalid API response."
        except Exception:
            error = "❌ Something went wrong."

    return render_template("index.html", player=player, error=error)


@app.route("/send-likes", methods=["POST"])
def send_likes():
    uid = request.form.get("uid", "").strip()
    region = request.form.get("region", "ind").strip()
    
    if not uid.isdigit():
        return render_template("index.html", error="❌ Please enter a valid Free Fire UID for likes")

    old_likes = 0
    nickname = "Player"
    try:
        info_resp = requests.get(API_URL, params={"uid": uid, "key": "Anurag"}, timeout=20)
        if info_resp.status_code == 200:
            data = info_resp.json()
            basic = data.get("basicInfo", {})
            old_likes = int(basic.get("liked", 0))
            nickname = basic.get("nickname", "Player")
    except Exception:
        pass

    today_date = datetime.now().strftime("%Y-%m-%d")

    if daily_limit_tracker.get(uid) == today_date:
        result_data = {
            "uid": uid,
            "nickname": nickname,
            "old_likes": old_likes,
            "new_likes": old_likes,
            "added_likes": 0,
            "success": False,
            "message": "⚠️ Is UID par aaj ke free likes already bhej diye gaye hain! (1 day limit)"
        }
        return render_template("index.html", result_data=result_data)

    like_api_url = f"{LIKE_API_BASE}?key=20LikeFreeApiByzexxyh4x&uid={uid}&region={region}"

    new_likes = old_likes
    status_success = False
    
    try:
        like_resp = requests.get(like_api_url, timeout=20)
        
        info_resp_after = requests.get(API_URL, params={"uid": uid, "key": "Anurag"}, timeout=20)
        if info_resp_after.status_code == 200:
            data_after = info_resp_after.json()
            basic_after = data_after.get("basicInfo", {})
            new_likes = int(basic_after.get("liked", old_likes))

        if new_likes > old_likes:
            status_success = True
            daily_limit_tracker[uid] = today_date
            added = new_likes - old_likes
        elif like_resp.status_code == 200:
            status_success = True
            daily_limit_tracker[uid] = today_date
            added = new_likes - old_likes if new_likes > old_likes else 0
        else:
            status_success = False
            added = 0

    except Exception:
        status_success = False
        added = 0

    result_data = {
        "uid": uid,
        "nickname": nickname,
        "old_likes": old_likes,
        "new_likes": new_likes,
        "added_likes": added,
        "success": status_success,
        "message": "Likes successfully sent!" if status_success else "Like nahi gaye / Failed."
    }

    return render_template("index.html", result_data=result_data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
    

from flask import Flask, render_template, request
import requests
import os
from datetime import datetime

app = Flask(__name__)

API_URL = "https://ff-info-ro45.vercel.app/api"
LIKE_API_BASE = "https://two0likeapifreebyzexxyh4x.onrender.com/like"

# Daily limit tracker: { "UID": "YYYY-MM-DD" }
daily_limit_tracker = {}


@app.route("/", methods=["GET", "POST"])
def home():
    player = None
    error = None

    if request.method == "POST":
        uid = request.form.get("uid", "").strip()

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

    return render_template(
        "index.html",
        player=player,
        error=error
    )


@app.route("/send-likes", methods=["POST"])
def send_likes():
    uid = request.form.get("uid", "").strip()
    region = request.form.get("region", "ind").strip()
    old_likes = int(request.form.get("old_likes", 0))
    nickname = request.form.get("nickname", "Player")

    today_date = datetime.now().strftime("%Y-%m-%d")

    # 1 UID = 1 day limit check
    if daily_limit_tracker.get(uid) == today_date:
        error_msg = "⚠️ Is UID par aaj ke free likes already bhej diye gaye hain! Aap ab kal dobara try karein."
        player = {
            "nickname": nickname, "uid": uid, "region": region, "likes": old_likes,
            "level": "N/A", "rank": "N/A", "cs_rank": "N/A", "exp": "N/A", "guild": "N/A", "pet": "N/A"
        }
        return render_template("index.html", player=player, error=error_msg)

    like_api_url = f"{LIKE_API_BASE}?key=20LikeFreeApiByzexxyh4x&uid={uid}&region={region}"

    new_likes = old_likes
    status_success = False
    
    try:
        # Like API Hit karein
        like_resp = requests.get(like_api_url, timeout=20)
        
        # Real likes check karne ke liye dobara profile fetch karein
        info_resp = requests.get(API_URL, params={"uid": uid, "key": "Anurag"}, timeout=20)
        if info_resp.status_code == 200:
            data = info_resp.json()
            basic = data.get("basicInfo", {})
            new_likes = int(basic.get("liked", old_likes))
            nickname = basic.get("nickname", nickname)

        # Agar real likes badhe hain ya API successfully hit ho gayi hai
        if new_likes > old_likes or like_resp.status_code == 200:
            status_success = True
            daily_limit_tracker[uid] = today_date
        else:
            status_success = False

    except Exception:
        status_success = False

    result_data = {
        "uid": uid,
        "nickname": nickname,
        "old_likes": old_likes,
        "new_likes": new_likes,
        "added_likes": new_likes - old_likes if new_likes >= old_likes else 0,
        "success": status_success
    }

    return render_template("index.html", result_data=result_data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
    

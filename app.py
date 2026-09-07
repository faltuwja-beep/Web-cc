from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

API_URL = "https://ff-info-ro45.vercel.app/api"


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

                player = {
                    "nickname": basic.get("nickname", "N/A"),
                    "uid": basic.get("accountId", uid),
                    "level": basic.get("level", "N/A"),
                    "region": basic.get("region", "N/A"),
                    "likes": int(basic.get("liked", 0)),
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

    like_api = f"https://two0likeapifreebyzexxyh4x.onrender.com/link?key=20LikeFreeApiByzexxyh4x&uid={uid}&region={region}"
    # Note: Aapki di gayi URL path (/like ya /link) ke mutabiq adjust kiya gaya hai

    # Pehle player ki current details fir se fetch karte hain taaki updated likes mil sakein
    new_likes = old_likes
    nickname = request.form.get("nickname", "Player")
    
    try:
        # Pehle Like API hit karein
        requests.get(like_api, timeout=20)
        
        # Thoda gap dekar ya turant profile API se naye likes check karein
        info_resp = requests.get(API_URL, params={"uid": uid, "key": "Anurag"}, timeout=20)
        if info_resp.status_code == 200:
            data = info_resp.json()
            basic = data.get("basicInfo", {})
            new_likes = int(basic.get("liked", old_likes))
            nickname = basic.get("nickname", nickname)
    except Exception:
        pass

    result_data = {
        "uid": uid,
        "nickname": nickname,
        "old_likes": old_likes,
        "new_likes": new_likes
    }

    return render_template("index.html", result=result_data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
    

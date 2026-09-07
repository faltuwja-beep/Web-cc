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
            error = "Please enter a valid Free Fire UID"

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
                    "likes": basic.get("liked", "N/A"),
                    "rank": basic.get("rank", "N/A"),
                    "cs_rank": basic.get("csRank", "N/A"),
                    "exp": basic.get("exp", "N/A"),
                    "guild": clan.get("clanName", "No Guild"),
                    "pet_id": pet.get("id", "N/A")
                }

            except requests.exceptions.RequestException:
                error = "API connection error. Please try again."

            except ValueError:
                error = "API returned invalid data."

            except Exception:
                error = "Something went wrong."

    return render_template(
        "index.html",
        player=player,
        error=error
    )


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )

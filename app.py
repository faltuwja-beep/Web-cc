from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "sonu_super_secret_key_store"

API_URL = "https://ff-info-ro45.vercel.app/api"
LIKE_API_BASE = "https://two0likeapifreebyzexxyh4x.onrender.com/like"

site_stats = {
    "total_checks": 0,
    "total_likes_sent": 0
}
daily_limit_tracker = {}

def init_db():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        balance REAL DEFAULT 0.0,
                        is_admin INTEGER DEFAULT 0)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        category TEXT,
                        price REAL,
                        details TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        amount REAL,
                        utr TEXT,
                        status TEXT DEFAULT 'Pending')''')

    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, balance, is_admin) VALUES ('admin', 'admin123', 0.0, 1)")

    cursor.execute("SELECT * FROM products")
    if not cursor.fetchone():
        default_items = [
            ("Google Play Redeem Code ₹699", "Redeem Code", 699.0, "Instant Delivery Code"),
            ("Demo Visa Card", "CC Card", 399.0, "Working Test CC Info"),
            ("Mastercard VIP", "CC Card", 1099.0, "High Balance Mastercard")
        ]
        cursor.executemany("INSERT INTO products (name, category, price, details) VALUES (?, ?, ?, ?)", default_items)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("shop"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("❌ Please fill in all fields", "error")
            return render_template("login.html")

        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = user[1]
            session["is_admin"] = user[4]
            return redirect(url_for("shop"))
        else:
            flash("❌ Invalid Username or Password", "error")
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("❌ Please fill in all fields", "error")
            return render_template("register.html")

        try:
            conn = sqlite3.connect('store.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            flash("✅ Account created successfully! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("❌ Username already taken! Choose another.", "error")
            
    return render_template("register.html")

@app.route("/shop")
def shop():
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance, is_admin FROM users WHERE username = ?", (session["username"],))
    user_data = cursor.fetchone()
    balance = user_data[0] if user_data else 0.0
    is_admin = user_data[1] if user_data else 0

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    history = session.get("search_history", [])
    return render_template("shop.html", username=session["username"], balance=balance, is_admin=is_admin, products=products, history=history, stats=site_stats)

@app.route("/check-uid", methods=["POST"])
def check_uid():
    if "username" not in session:
        return redirect(url_for("login"))
        
    uid = request.form.get("uid", "").strip()
    player = None
    error = None

    if not uid.isdigit():
        error = "❌ Please enter a valid Free Fire UID"
    else:
        try:
            response = requests.get(API_URL, params={"uid": uid, "key": "Anurag"}, timeout=20)
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

            site_stats["total_checks"] += 1

            history = session.get("search_history", [])
            search_item = {"uid": uid, "name": player["nickname"]}
            if search_item not in history:
                history.insert(0, search_item)
                session["search_history"] = history[:5]

        except Exception:
            error = "❌ API connection error or Invalid UID."

    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance, is_admin FROM users WHERE username = ?", (session["username"],))
    user_data = cursor.fetchone()
    balance = user_data[0] if user_data else 0.0
    is_admin = user_data[1] if user_data else 0
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    return render_template("shop.html", username=session["username"], balance=balance, is_admin=is_admin, products=products, player=player, error=error, history=session.get("search_history", []), stats=site_stats)

@app.route("/send-likes", methods=["POST"])
def send_likes():
    if "username" not in session:
        return redirect(url_for("login"))
        
    uid = request.form.get("uid", "").strip()
    region = request.form.get("region", "ind").strip()
    
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance, is_admin FROM users WHERE username = ?", (session["username"],))
    user_data = cursor.fetchone()
    balance = user_data[0] if user_data else 0.0
    is_admin = user_data[1] if user_data else 0
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    if not uid.isdigit():
        return render_template("shop.html", username=session["username"], balance=balance, is_admin=is_admin, products=products, error="❌ Please enter a valid Free Fire UID", history=session.get("search_history", []), stats=site_stats)

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
            "uid": uid, "nickname": nickname, "old_likes": old_likes, "new_likes": old_likes,
            "added_likes": 0, "success": False, "message": "⚠️ Is UID par aaj ke free likes already bhej diye gaye hain! (1 day limit)"
        }
        return render_template("shop.html", username=session["username"], balance=balance, is_admin=is_admin, products=products, result_data=result_data, history=session.get("search_history", []), stats=site_stats)

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
            site_stats["total_likes_sent"] += added
        elif like_resp.status_code == 200:
            status_success = True
            daily_limit_tracker[uid] = today_date
            added = 20
            site_stats["total_likes_sent"] += added
            new_likes = old_likes + added
        else:
            status_success = False
            added = 0
    except Exception:
        status_success = False
        added = 0

    result_data = {
        "uid": uid, "nickname": nickname, "old_likes": old_likes, "new_likes": new_likes,
        "added_likes": added, "success": status_success,
        "message": "Likes successfully sent!" if status_success else "Like nahi gaye / Failed."
    }

    return render_template("shop.html", username=session["username"], balance=balance, is_admin=is_admin, products=products, result_data=result_data, history=session.get("search_history", []), stats=site_stats)

@app.route("/add-money", methods=["POST"])
def add_money():
    if "username" not in session:
        return redirect(url_for("login"))
    try:
        amount = float(request.form.get("amount", 0))
    except ValueError:
        amount = 0.0
    utr = request.form.get("utr", "").strip()

    if amount <= 0 or not utr:
        flash("❌ Please enter valid amount and UTR number", "error")
        return redirect(url_for("shop"))

    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO payments (username, amount, utr, status) VALUES (?, ?, ?, 'Pending')", 
                   (session["username"], amount, utr))
    conn.commit()
    conn.close()
    flash("⏳ Payment request submitted! Admin will verify and approve soon.", "success")
    return redirect(url_for("shop"))

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if "username" not in session:
        return redirect(url_for("login"))
        
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE username = ?", (session["username"],))
    res = cursor.fetchone()
    if not res or res[0] != 1:
        conn.close()
        return redirect(url_for("shop"))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_product":
            name = request.form.get("name")
            category = request.form.get("category")
            price = float(request.form.get("price", 0))
            details = request.form.get("details")
            cursor.execute("INSERT INTO products (name, category, price, details) VALUES (?, ?, ?, ?)", (name, category, price, details))
        elif action == "edit_product":
            pid = request.form.get("pid")
            price = float(request.form.get("price", 0))
            cursor.execute("UPDATE products SET price = ? WHERE id = ?", (price, pid))
        elif action == "delete_product":
            pid = request.form.get("pid")
            cursor.execute("DELETE FROM products WHERE id = ?", (pid,))
        elif action == "approve_payment":
            pay_id = request.form.get("pay_id")
            cursor.execute("SELECT username, amount FROM payments WHERE id = ?", (pay_id,))
            pay_data = cursor.fetchone()
            if pay_data:
                uname, amt = pay_data
                cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amt, uname))
                cursor.execute("UPDATE payments SET status = 'Approved' WHERE id = ?", (pay_id,))
        conn.commit()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.execute("SELECT * FROM payments")
    payments = cursor.fetchall()
    conn.close()
    return render_template("admin.html", products=products, payments=payments)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
            

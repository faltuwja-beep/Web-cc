from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import requests
import random
import string
from datetime import datetime

app = Flask(__name__)
app.secret_key = "xenon_store_secret_key"

TELEGRAM_BOT_TOKEN = "8822410482:AAEgv8CYy3VKHn6sv6Rezsw9BSQna5vsUJo"
TELEGRAM_CHAT_ID = "7161571409"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_db_connection():
    conn = sqlite3.connect('store.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(users)")
    columns = [row["name"] for row in cursor.fetchall()]
    if columns and "referral_code" not in columns:
        cursor.execute("DROP TABLE users")

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        balance REAL DEFAULT 0.0,
                        referral_code TEXT UNIQUE,
                        referred_by TEXT,
                        referral_count INTEGER DEFAULT 0,
                        is_admin INTEGER DEFAULT 0)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        category TEXT,
                        price REAL,
                        description TEXT,
                        secret_data TEXT,
                        image_url TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        amount REAL,
                        utr TEXT,
                        status TEXT DEFAULT 'Pending')''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        product_name TEXT,
                        price REAL,
                        secret_data TEXT,
                        purchase_date TEXT)''')

    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, balance, referral_code, referral_count, is_admin) VALUES ('admin', 'admin123', 0.0, 'ADMIN1', 0, 1)")

    cursor.execute("SELECT * FROM products")
    if not cursor.fetchone():
        default_items = [
            ("Google Play Redeem Code", "Redeem Code", 699.0, "Balance: ₹5,000 | Instant Delivery", "Your Code: GPR-9982-XYZ-2026", "https://cdn-icons-png.flaticon.com/512/888/888857.png"),
            ("Demo Visa Card", "CC Card", 399.0, "Balance: ₹10,000 | Working Test CC", "Card Number: 4532 8822 1048 2026\nExpiry Date: 09/28\nCVV: 123", "https://upload.wikimedia.org/wikipedia/commons/4/41/Visa_Logo.png"),
            ("Mastercard VIP", "CC Card", 1099.0, "Balance: ₹25,000 | High Balance Card", "Card Number: 5412 7161 5714 0099\nExpiry Date: 11/27\nCVV: 456", "https://cdn-icons-png.flaticon.com/512/349/349228.png"),
            ("Blackmarket Visa", "CC Card", 499.0, "Balance: ₹15,000 | Bitcoin Visa Card", "Card Number: 4000 1234 5678 9010\nExpiry Date: 05/29\nCVV: 789", "https://cdn-icons-png.flaticon.com/512/349/349230.png")
        ]
        cursor.executemany("INSERT INTO products (name, category, price, description, secret_data, image_url) VALUES (?, ?, ?, ?, ?, ?)", default_items)

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

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()

        if user:
            session["username"] = user["username"]
            session["is_admin"] = user["is_admin"] if "is_admin" in user.keys() else 0
            return redirect(url_for("shop"))
        else:
            flash("❌ Invalid Username or Password", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    ref_code_param = request.args.get("ref", "").strip()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        ref_input = request.form.get("ref_code", "").strip()

        if not username or not password:
            flash("❌ Please fill in all fields", "error")
            return render_template("register.html", ref_code=ref_code_param)

        my_ref = generate_referral_code()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            referrer = None
            if ref_input:
                ref_user = cursor.execute("SELECT username FROM users WHERE referral_code = ?", (ref_input,)).fetchone()
                if ref_user:
                    referrer = ref_user["username"]

            cursor.execute("INSERT INTO users (username, password, balance, referral_code, referred_by, referral_count, is_admin) VALUES (?, ?, 0.0, ?, ?, 0, 0)", 
                           (username, password, my_ref, referrer))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            send_telegram_alert(f"👤 *New User Registered in Xenon Store!*\n🆔 User ID: `#{user_id}`\n📛 Username: `{username}`\n🔗 Referred By: `{referrer if referrer else 'Direct'}`")

            flash("✅ Account created successfully! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("❌ Username already taken! Choose another.", "error")
            
    return render_template("register.html", ref_code=ref_code_param)

@app.route("/shop")
def shop():
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    user_data = conn.execute("SELECT id, balance, referral_code, referral_count, is_admin FROM users WHERE username = ?", (session["username"],)).fetchone()
    
    if not user_data:
        conn.close()
        session.clear()
        return redirect(url_for("login"))

    user_id = user_data["id"]
    balance = user_data["balance"] if user_data["balance"] is not None else 0.0
    referral_code = user_data["referral_code"] if user_data["referral_code"] else ""
    referral_count = user_data["referral_count"] if user_data["referral_count"] is not None else 0
    is_admin = user_data["is_admin"] if user_data["is_admin"] is not None else 0

    products = conn.execute("SELECT * FROM products").fetchall()
    my_payments = conn.execute("SELECT amount, utr, status FROM payments WHERE username = ? ORDER BY id DESC LIMIT 5", (session["username"],)).fetchall()
    
    my_purchases = conn.execute("SELECT id, product_name, price, secret_data, purchase_date FROM purchases WHERE username = ? ORDER BY id DESC", (session["username"],)).fetchall()
    
    today_date = datetime.now().strftime("%Y-%m-%d")
    today_purchases = conn.execute("SELECT id, product_name, price, secret_data, purchase_date FROM purchases WHERE username = ? AND purchase_date LIKE ? ORDER BY id DESC", (session["username"], f"{today_date}%")).fetchall()

    conn.close()

    referral_link = request.host_url + "register?ref=" + referral_code
    return render_template("shop.html", user_id=user_id, username=session["username"], balance=balance, referral_code=referral_code, referral_count=referral_count, referral_link=referral_link, is_admin=is_admin, products=products, my_payments=my_payments, my_purchases=my_purchases, today_purchases=today_purchases)

@app.route("/update-settings", methods=["POST"])
def update_settings():
    if "username" not in session:
        return redirect(url_for("login"))
    
    new_username = request.form.get("new_username", "").strip()
    new_password = request.form.get("new_password", "").strip()
    old_username = session["username"]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if new_username and new_username != old_username:
            cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, old_username))
            cursor.execute("UPDATE payments SET username = ? WHERE username = ?", (new_username, old_username))
            cursor.execute("UPDATE purchases SET username = ? WHERE username = ?", (new_username, old_username))
            session["username"] = new_username

        if new_password:
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, session["username"]))

        conn.commit()
        conn.close()
        flash("✅ Settings updated successfully!", "success")
    except sqlite3.IntegrityError:
        conn.close()
        flash("❌ Username already taken! Choose another.", "error")

    return redirect(url_for("shop"))

@app.route("/buy/<int:product_id>")
def buy_product(product_id):
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user_res = cursor.execute("SELECT id, balance, referred_by FROM users WHERE username = ?", (session["username"],)).fetchone()
    user_id = user_res["id"]
    balance = user_res["balance"] if user_res["balance"] is not None else 0.0
    referred_by = user_res["referred_by"]

    prod = cursor.execute("SELECT name, price, secret_data FROM products WHERE id = ?", (product_id,)).fetchone()

    if not prod:
        conn.close()
        flash("❌ Product not found!", "error")
        return redirect(url_for("shop"))

    p_name, p_price, secret_data = prod["name"], prod["price"], prod["secret_data"]
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if balance >= p_price:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (p_price, session["username"]))
        cursor.execute("INSERT INTO purchases (username, product_name, price, secret_data, purchase_date) VALUES (?, ?, ?, ?, ?)", (session["username"], p_name, p_price, secret_data, current_time))
        
        if referred_by:
            cursor.execute("UPDATE users SET balance = balance + 50.0, referral_count = referral_count + 1 WHERE username = ?", (referred_by,))
            send_telegram_alert(f"💸 *Referral Commission Paid!*\n👤 Referrer: `{referred_by}` received ₹50 because their referral `{session['username']}` made a purchase!")

        conn.commit()
        conn.close()

        send_telegram_alert(f"🛍️ *Product Purchased on Xenon Store!*\n🆔 User ID: `#{user_id}`\n👤 User: `{session['username']}`\n📦 Item: `{p_name}`\n💵 Price: `₹{p_price}`")

        flash("🎉 Purchase Successful! Check 'My Purchases' to view your secure credentials.", "success")
    else:
        conn.close()
        shortfall = p_price - balance
        flash(f"⚠️ Insufficient balance! You need ₹{shortfall} more. Please add money via QR.", "error")

    return redirect(url_for("shop"))

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

    conn = get_db_connection()
    conn.execute("INSERT INTO payments (username, amount, utr, status) VALUES (?, ?, ?, 'Pending')", 
                 (session["username"], amount, utr))
    conn.commit()
    conn.close()

    send_telegram_alert(f"🔔 *New Payment Proof submitted on Xenon Store!*\n👤 User: `{session['username']}`\n💰 Amount: `₹{amount}`\n🔢 UTR: `{utr}`\n\n*Aap /admin panel me jaakar approve/reject karein.*")

    flash("⏳ Payment proof submitted! Admin will verify and approve soon.", "success")
    return redirect(url_for("shop"))

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if "username" not in session:
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    res = conn.execute("SELECT is_admin FROM users WHERE username = ?", (session["username"],)).fetchone()
    if not res or res["is_admin"] != 1:
        conn.close()
        return redirect(url_for("shop"))

    if request.method == "POST":
        action = request.form.get("action")
        cursor = conn.cursor()
        if action == "add_product":
            name = request.form.get("name")
            category = request.form.get("category", "Redeem Code")
            price = float(request.form.get("price", 0))
            description = request.form.get("description")
            secret_data = request.form.get("secret_data")
            image_url = request.form.get("image_url", "").strip()
            if not image_url:
                image_url = "https://cdn-icons-png.flaticon.com/512/888/888857.png"
            cursor.execute("INSERT INTO products (name, category, price, description, secret_data, image_url) VALUES (?, ?, ?, ?, ?, ?)", (name, category, price, description, secret_data, image_url))
        elif action == "edit_product":
            pid = request.form.get("pid")
            price = float(request.form.get("price", 0))
            description = request.form.get("description")
            secret_data = request.form.get("secret_data")
            image_url = request.form.get("image_url", "").strip()
            cursor.execute("UPDATE products SET price = ?, description = ?, secret_data = ?, image_url = ? WHERE id = ?", (price, description, secret_data, image_url, pid))
        elif action == "delete_product":
            pid = request.form.get("pid")
            cursor.execute("DELETE FROM products WHERE id = ?", (pid,))
        elif action == "approve_payment":
            pay_id = request.form.get("pay_id")
            pay_data = cursor.execute("SELECT username, amount, status FROM payments WHERE id = ?", (pay_id,)).fetchone()
            if pay_data and pay_data["status"] == 'Pending':
                uname, amt = pay_data["username"], pay_data["amount"]
                cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amt, uname))
                cursor.execute("UPDATE payments SET status = 'Approved' WHERE id = ?", (pay_id,))
        elif action == "reject_payment":
            pay_id = request.form.get("pay_id")
            cursor.execute("UPDATE payments SET status = 'Rejected' WHERE id = ?", (pay_id,))
        conn.commit()

    products = conn.execute("SELECT * FROM products").fetchall()
    payments = conn.execute("SELECT * FROM payments ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", products=products, payments=payments)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
    

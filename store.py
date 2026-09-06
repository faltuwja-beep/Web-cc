cat << 'EOF' > store.py
import time, os
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)
users_db, pending_deposits = {}, {}

# Packs Data with Categories & Out of Stock items
packs_db = {
    "cc_99": {"cat": "cc", "name": "₹1,000 CC Balance Card", "price": 99, "rating": "4.7/5", "sold": "850+", "codes": []},
    "cc_199": {"cat": "cc", "name": "₹2,000 VIP CC Balance Card", "price": 199, "rating": "4.9/5", "sold": "1,420+", "codes": ["CARD-4312-9982 | PIN: 9021"]},
    "cc_599": {"cat": "cc", "name": "₹10,000 Elite CC Balance Card", "price": 599, "rating": "5.0/5", "sold": "3,890+", "codes": ["CARD-7712-4431 | PIN: 8810"]},
    "cc_799": {"cat": "cc", "name": "₹15,000 Ultra CC Balance Card", "price": 799, "rating": "4.9/5", "sold": "450+", "codes": []},
    "ps_79": {"cat": "ps", "name": "Google Play ₹100 Code", "price": 79, "rating": "4.8/5", "sold": "2,150+", "codes": []},
    "p100": {"cat": "ps", "name": "Google Play ₹100 Code", "price": 79, "rating": "5.0/5", "sold": "5,600+", "codes": ["CODE-3KL9-PX82 | PIN: 1122"]},
    "ps_799": {"cat": "ps", "name": "Google Play ₹2,000 Code", "price": 799, "rating": "5.0/5", "sold": "120+", "codes": []}
}

HTML_UI = """<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CYBER GAMING VIP STORE</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: #050814; color: #f8fafc; min-height: 100vh; padding: 12px; padding-bottom: 90px; }
    .container { max-width: 420px; margin: 0 auto; }
    .ticker { background: linear-gradient(135deg, rgba(2,132,199,0.2), rgba(14,165,233,0.1)); border: 1px solid rgba(56, 189, 248, 0.4); padding: 10px; border-radius: 14px; font-size: 0.8rem; color: #38bdf8; text-align: center; font-weight: 800; margin-bottom: 12px; box-shadow: 0 4px 15px rgba(2,132,199,0.15); }
    .card { background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 18px; padding: 18px; margin-bottom: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.7); backdrop-filter: blur(10px); }
    .title { text-align: center; font-size: 1.8rem; color: #38bdf8; font-weight: 900; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 1px; text-shadow: 0 0 15px rgba(56,189,248,0.4); }
    .sub { text-align: center; font-size: 0.82rem; color: #94a3b8; margin-bottom: 16px; font-weight: 700; }
    .tabs-row { display: flex; gap: 8px; margin-bottom: 14px; background: #030712; padding: 4px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }
    .tab-btn { flex: 1; padding: 12px; background: transparent; color: #94a3b8; border: none; border-radius: 8px; font-weight: 900; font-size: 0.9rem; cursor: pointer; text-align: center; text-decoration: none; display: block; }
    .tab-btn.active { background: #0284c7; color: #fff; box-shadow: 0 4px 15px rgba(2,132,199,0.4); }
    .cat-row { display: flex; gap: 10px; margin-bottom: 14px; }
    .cat-btn { flex: 1; padding: 14px; background: #1e293b; border: 2px solid #334155; border-radius: 14px; color: #fff; font-weight: 900; font-size: 0.95rem; text-align: center; text-decoration: none; display: block; }
    .cat-btn.active { background: linear-gradient(135deg, #0284c7, #0369a1); border-color: #38bdf8; box-shadow: 0 4px 15px rgba(2,132,199,0.3); }
    .inp { width: 100%; padding: 14px; margin-bottom: 12px; background: #030712; border: 1px solid #334155; border-radius: 12px; color: #fff; font-size: 1rem; font-weight: 700; outline: none; }
    .inp:focus { border-color: #38bdf8; box-shadow: 0 0 10px rgba(56,189,248,0.3); }
    .btn-glow { width: 100%; padding: 14px; background: linear-gradient(135deg, #0284c7, #0369a1); color: #fff; font-weight: 900; border: none; border-radius: 12px; cursor: pointer; font-size: 1.05rem; box-shadow: 0 4px 15px rgba(2,132,199,0.4); }
    .item-card { background: #070913; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
    .item-card.soldout { opacity: 0.4; filter: grayscale(1); pointer-events: none; }
    .b-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(9, 13, 26, 0.95); border-top: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-around; padding: 10px 0; z-index: 1000; backdrop-filter: blur(10px); }
    .b-tab { color: #94a3b8; text-decoration: none; font-size: 0.75rem; font-weight: 900; text-align: center; }
    .b-tab.active { color: #38bdf8; text-shadow: 0 0 10px rgba(56,189,248,0.6); }
    .code-box { background: #030712; border: 1px dashed #34d399; padding: 14px; border-radius: 10px; margin: 10px 0; word-break: break-all; color: #34d399; font-family: monospace; font-weight: 900; font-size: 1.05rem; text-shadow: 0 0 8px rgba(52,211,153,0.3); }
    .timer { font-size: 2.4rem; font-weight: 900; color: #f59e0b; text-align: center; margin: 10px 0; font-family: monospace; text-shadow: 0 0 15px rgba(245,158,11,0.4); }
  </style>
</head>
<body>
<div class="container">
  <div class="ticker" id="live-ticker">⚡ Live: Rahul bought ₹2,000 VIP CC Balance Card 1 min ago!</div>
  
  {% if msg %}<div style="background:#0f172a; border:1px solid #38bdf8; color:#38bdf8; padding:10px; margin-bottom:14px; text-align:center; border-radius:12px; font-size:0.9rem; font-weight:900;">{{ msg }}</div>{% endif %}

  {% if not session_user %}
  <div class="card">
    <div class="title">CYBER VAULT</div>
    <div class="sub">Gaming Store & Instant Digital Delivery</div>
    
    <div class="tabs-row">
      <a href="/?tab=login" class="tab-btn {% if tab!='reg' %}active{% endif %}">LOGIN</a>
      <a href="/?tab=reg" class="tab-btn {% if tab=='reg' %}active{% endif %}">REGISTER</a>
    </div>

    {% if tab == 'reg' %}
    <form method="POST" action="/register">
      <input type="text" name="name" class="inp" placeholder="Full Name" required>
      <input type="text" name="username" class="inp" placeholder="Username" required>
      <input type="password" name="password" class="inp" placeholder="Password" required>
      <button type="submit" class="btn-glow" style="background:linear-gradient(135deg,#10b981,#059669);">Create Account</button>
    </form>
    {% else %}
    <form method="POST" action="/login">
      <input type="text" name="username" class="inp" placeholder="Username (admin for panel)" required>
      <input type="password" name="password" class="inp" placeholder="Password (123)" required>
      <button type="submit" class="btn-glow">Login to Store</button>
    </form>
    {% endif %}
  </div>

  {% elif session_user == 'admin' %}
  <div class="card" style="border-color:#38bdf8;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
      <b style="color:#38bdf8; font-size:1.15rem;">👑 ADMIN DASHBOARD</b>
      <a href="/logout" style="color:#f87171; text-decoration:none; font-weight:900; font-size:0.85rem;">Logout</a>
    </div>
    
    <h4 style="color:#34d399; margin-bottom:10px; font-size:0.95rem;">Pending Deposits (Approval)</h4>
    {% if not pending_deposits %}<div style="color:#64748b; font-size:0.85rem; margin-bottom:14px; font-weight:700;">No pending deposits right now.</div>{% endif %}
    {% for did, d in pending_deposits.items() %}
    <div style="background:#030712; padding:12px; border-radius:10px; margin-bottom:10px; font-size:0.88rem; border:1px solid #1e293b;">
      User: <b>{{ d.username }}</b> | Amt: <b style="color:#34d399;">₹{{ d.amount }}</b><br>
      UTR: <code style="color:#38bdf8; font-weight:bold;">{{ d.utr }}</code><br>
      <div style="display:flex; gap:8px; margin-top:10px;">
        <a href="/admin/approve/{{ did }}" style="flex:1; background:#10b981; color:#fff; text-align:center; padding:8px; border-radius:8px; text-decoration:none; font-weight:900;">Accept / Approve</a>
        <a href="/admin/reject/{{ did }}" style="flex:1; background:#ef4444; color:#fff; text-align:center; padding:8px; border-radius:8px; text-decoration:none; font-weight:900;">Reject</a>
      </div>
    </div>
    {% endfor %}

    <h4 style="color:#38bdf8; margin:18px 0 10px 0; font-size:0.95rem;">Stock Management</h4>
    {% for pid, p in packs.items() %}
    <div style="background:#030712; padding:12px; border-radius:10px; margin-bottom:10px; font-size:0.88rem; border:1px solid #1e293b;">
      <b>{{ p.name }}</b> (<code>{{ pid }}</code>) | Stock: <b>{{ p.codes|length }}</b>
      <form method="POST" action="/admin/add_stock" style="margin-top:8px; display:flex; gap:8px;">
        <input type="hidden" name="pid" value="{{ pid }}">
        <input type="text" name="new_codes" class="inp" placeholder="Add codes comma separated" style="margin:0; font-size:0.8rem; padding:8px;" required>
        <button type="submit" style="background:#0284c7; color:#fff; border:none; padding:8px 12px; border-radius:8px; font-weight:900;">Add</button>
      </form>
    </div>
    {% endfor %}
  </div>

  {% else %}
  <div class="card" style="padding:14px;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <div>
        <div style="font-size:0.75rem; color:#94a3b8; font-weight:700;">Welcome,</div>
        <b style="color:#38bdf8; font-size:1.15rem;">{{ session_user }}</b>
      </div>
      <div style="background:rgba(16,185,129,0.15); border:1px solid #10b981; color:#34d399; padding:6px 14px; border-radius:14px; font-weight:900; font-size:1rem;">₹{{ "%.2f"|format(user_bal) }}</div>
      <a href="/logout" style="color:#f87171; text-decoration:none; font-weight:900; font-size:0.85rem;">Logout</a>
    </div>
  </div>

  {% if view == 'store' %}
  <div class="card">
    <div class="cat-row">
      <a href="/?view=store&cat=cc" class="cat-btn {% if cat=='cc' %}active{% endif %}">💳 CC Cards</a>
      <a href="/?view=store&cat=ps" class="cat-btn {% if cat=='ps' %}active{% endif %}">🎁 Play Store</a>
    </div>

    <div style="font-weight:900; margin-bottom:12px; color:#38bdf8; font-size:1.1rem;">
      {{ '💳 CC Balance Cards' if cat=='cc' else '🎁 Play Store Redeem Codes' }}
    </div>

    {% for pid, p in packs.items() %}
      {% if p.cat == cat %}
        {% set stock = p.codes|length %}
        <div class="item-card {% if stock == 0 %}soldout{% endif %}">
          <div>
            <div style="font-weight:900; font-size:1rem; color:#fff;">{{ p.name }}</div>
            <div style="font-size:0.78rem; color:#f59e0b; margin:4px 0; font-weight:800;">⭐ {{ p.rating }} | Sold: {{ p.sold }} | Stock: {{ stock }}</div>
            <div style="color:#38bdf8; font-weight:900; font-size:1.2rem;">₹{{ p.price }}</div>
          </div>
          {% if stock > 0 %}
          <form method="POST" action="/buy" style="margin:0;">
            <input type="hidden" name="pid" value="{{ pid }}">
            <button type="submit" style="background:#10b981; color:#fff; border:none; padding:10px 18px; border-radius:10px; font-weight:900; font-size:0.95rem; cursor:pointer;">Buy</button>
          </form>
          {% else %}
          <button disabled style="background:#334155; color:#94a3b8; border:none; padding:10px 12px; border-radius:10px; font-size:0.8rem; font-weight:900;">OUT OF STOCK</button>
          {% endif %}
        </div>
      {% endif %}
    {% endfor %}
  </div>
  {% if bought_data %}
  <div class="card" style="border-color:#34d399; text-align:center;">
    <h3 style="color:#34d399; margin-bottom:6px; font-size:1.2rem;">🎉 Item Unlocked Successfully!</h3>
    <div class="code-box">{{ bought_data }}</div>
    <a href="/" class="btn-glow" style="text-decoration:none; display:inline-block; padding:12px; margin-top:6px;">Back to Store</a>
  </div>
  {% endif %}

  {% elif view == 'dep' %}
  <div class="card" style="text-align:center;">
    <h3 style="margin-bottom:10px; font-size:1.2rem;">Scan QR & Add Money</h3>
    <div style="background:#030712; padding:16px; border-radius:16px; margin-bottom:14px; border:1px dashed #334155;">
      <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=upi://pay?pa=sima6241@ptaxis%26pn=Sima%20Devi" style="width:160px; height:160px; background:#fff; padding:6px; border-radius:12px;">
      <div style="margin-top:8px; font-weight:900; font-size:1.1rem;">Sima Devi</div>
      <div style="font-size:0.9rem; color:#38bdf8; font-weight:800;">sima6241@ptaxis</div>
    </div>
    {% set st = user_dep_status %}
    {% if not st or st.status == 'none' or st.status == 'rejected' or st.status == 'approved' %}
    <form method="POST" action="/deposit">
      <input type="number" name="amt" class="inp" placeholder="Amount Paid (₹)" required>
      <input type="text" name="utr" class="inp" placeholder="12-Digit UTR Number" required>
      <button type="submit" class="btn-glow">Submit UTR for Verification</button>
    </form>
    {% else %}
    <div style="background:#030712; border:1px solid #38bdf8; border-radius:14px; padding:18px;">
      <div style="color:#38bdf8; font-size:1rem; font-weight:900;">⏳ Payment Verification in Progress</div>
      <div class="timer" id="t-display">10:00</div>
      <div style="font-size:0.85rem; color:#f59e0b; font-weight:800;">Status: Pending in History</div>
    </div>
    <script>
      let rem = {{ st.rem | default(600) }};
      const el = document.getElementById('t-display');
      const intr = setInterval(() => {
        rem--;
        if(rem <= 0) { clearInterval(intr); el.innerText = "00:00"; return; }
        let m = Math.floor(rem / 60), s = rem % 60;
        el.innerText = (m < 10 ? '0' : '') + m + ":" + (s < 10 ? '0' : '') + s;
      }, 1000);
    </script>
    {% endif %}
  </div>

  {% elif view == 'wth' %}
  <div class="card">
    <h3 style="margin-bottom:14px; font-size:1.2rem;">Withdrawal Request</h3>
    <form method="POST" action="/withdraw">
      <input type="number" name="amt" class="inp" placeholder="Amount (₹)" required>
      <input type="text" name="upi" class="inp" placeholder="UPI ID / Paytm" required>
      <button type="submit" class="btn-glow" style="background:linear-gradient(135deg,#ea580c,#c2410c);">Request Withdrawal</button>
    </form>
  </div>

  {% elif view == 'hist' %}
  <div class="card">
    <h3 style="margin-bottom:14px; font-size:1.2rem;">Order & Wallet History</h3>
    {% if not user_history %}<div style="color:#64748b; font-size:0.9rem; font-weight:700;">No activity yet.</div>{% endif %}
    {% for h in user_history %}
    <div style="padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.08); font-size:0.9rem;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <b style="font-size:0.95rem;">{{ h.title }}</b>
        <div style="color:{{ '#34d399' if h.amount > 0 else '#f87171' }}; font-weight:900;">
          {{ '+' if h.amount > 0 else '' }}₹{{ "%.2f"|format(h.amount|abs) }}
          {% if h.status %} <span style="background:#f59e0b; color:#000; padding:2px 8px; border-radius:6px; font-size:0.72rem; font-weight:900; margin-left:6px;">{{ h.status.upper() }}</span> {% endif %}
        </div>
      </div>
      {% if h.code_data %}
      <div style="margin-top:8px; background:#030712; border:1px dashed #34d399; padding:10px; border-radius:8px; color:#34d399; font-family:monospace; font-weight:900; font-size:0.95rem;">
        🔑 Unlocked Code: {{ h.code_data }}
      </div>
      {% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <div class="b-nav">
    <a href="/?view=store&cat=cc" class="b-tab {% if view=='store' %}active{% endif %}">🛒<br>Store</a>
    <a href="/?view=dep" class="b-tab {% if view=='dep' %}active{% endif %}">💳<br>Deposit</a>
    <a href="/?view=wth" class="b-tab {% if view=='wth' %}active{% endif %}">💸<br>Withdraw</a>
    <a href="/?view=hist" class="b-tab {% if view=='hist' %}active{% endif %}">📜<br>History</a>
  </div>
  {% endif %}
</div>
<script>
  const tickers = [
    "⚡ Aman bought ₹2,000 VIP CC Balance Card 1 min ago!",
    "⚡ Rahul bought Google Play ₹500 Redeem Code just now!",
    "⚡ Karan added ₹599 to wallet successfully!",
    "⚡ Vicky unlocked ₹10,000 Elite CC Balance Card!"
  ];
  let tIdx = 0;
  setInterval(() => {
    tIdx = (tIdx + 1) % tickers.length;
    const el = document.getElementById('live-ticker');
    if(el) el.innerText = tickers[tIdx];
  }, 4000);
</script>
</body>
</html>
"""

current_session = {"user": None}
last_bought = {}

@app.route('/')
def home():
    u = current_session["user"]
    bal, hist, dep_st = 0.0, [], {'status': 'none'}
    if u and u in users_db:
        bal = users_db[u].get('balance', 0.0)
        hist = users_db[u].get('history', [])
        dep_st = users_db[u].get('deposit_status', {'status': 'none'})
    if dep_st.get('status') == 'pending':
        dep_st['rem'] = max(0, int(600 - (time.time() - dep_st.get('time', time.time()))))
    b_data = last_bought.pop(u, None) if u in last_bought else None
    return render_template_string(HTML_UI, session_user=u, user_bal=bal, user_history=hist, user_dep_status=dep_st, packs=packs_db, bought_data=b_data, tab=request.args.get('tab', 'login'), view=request.args.get('view', 'store'), cat=request.args.get('cat', 'cc'), msg=request.args.get('msg', ''))

@app.route('/register', methods=['POST'])
def register():
    name, u, p = request.form.get('name','').strip(), request.form.get('username','').strip(), request.form.get('password','').strip()
    if not u or not p: return redirect('/?tab=reg&msg=Fill+all+fields')
    if u == 'admin' or u in users_db: return redirect('/?tab=reg&msg=Username+taken')
    users_db[u] = {'name': name, 'password': p, 'balance': 0.0, 'history': [], 'deposit_status': {'status': 'none'}}
    return redirect('/?tab=login&msg=Account+Created!+Login+Now')

@app.route('/login', methods=['POST'])
def login():
    u, p = request.form.get('username','').strip(), request.form.get('password','').strip()
    if u == 'admin' and p == '123':
        current_session["user"] = 'admin'
        return redirect('/')
    if u in users_db and users_db[u]['password'] == p:
        current_session["user"] = u
        return redirect('/')
    return redirect('/?tab=login&msg=Wrong+Credentials')

@app.route('/logout')
def logout():
    current_session["user"] = None
    return redirect('/')

@app.route('/buy', methods=['POST'])
def buy():
    u, pid = current_session["user"], request.form.get('pid', '')
    if not u or u == 'admin' or u not in users_db or pid not in packs_db: return redirect('/')
    it = packs_db[pid]
    if not it['codes']: return redirect('/?msg=Out+of+stock')
    if users_db[u]['balance'] < it['price']: return redirect('/?msg=Low+balance')
    code = it['codes'].pop(0)
    users_db[u]['balance'] -= it['price']
    users_db[u]['history'].insert(0, {'title': it['name'], 'amount': -it['price'], 'code_data': code})
    last_bought[u] = code
    return redirect('/')

@app.route('/deposit', methods=['POST'])
def deposit():
    u = current_session["user"]
    amt, utr = float(request.form.get('amt', 0)), request.form.get('utr', '')
    if u and u in users_db:
        did = str(len(pending_deposits) + 101)
        pending_deposits[did] = {'username': u, 'amount': amt, 'utr': utr, 'time': time.time()}
        users_db[u]['deposit_status'] = {'status': 'pending', 'time': time.time()}
        users_db[u]['history'].insert(0, {'title': f"Deposit (UTR: {utr})", 'amount': amt, 'status': 'pending'})
    return redirect('/?view=dep&msg=Deposit+Submitted!')

@app.route('/withdraw', methods=['POST'])
def withdraw():
    u, amt, upi = current_session["user"], float(request.form.get('amt', 0)), request.form.get('upi', '')
    if u and u in users_db:
        if users_db[u]['balance'] < amt: return redirect('/?view=wth&msg=Low+balance')
        users_db[u]['balance'] -= amt
        users_db[u]['history'].ins

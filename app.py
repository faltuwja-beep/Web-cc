import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-before-production"
)

database_url = os.environ.get("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = (
    database_url or "sqlite:///store.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


UPI_ID = "sima6241@ptaxis"
SUPPORT_USERNAME = "@Xenon_ask9"

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "admin123"
)


# =====================
# DATABASE MODELS
# =====================

class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    balance = db.Column(
        db.Float,
        default=0
    )

    is_admin = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Category(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    icon = db.Column(
        db.String(30),
        default="🎁"
    )


class Product(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        default=""
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    image = db.Column(
        db.String(500),
        default=""
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id")
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    category = db.relationship(
        "Category",
        backref="products"
    )


class ProductCode(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )

    code = db.Column(
        db.String(500),
        unique=True,
        nullable=False
    )

    sold = db.Column(
        db.Boolean,
        default=False
    )

    product = db.relationship(
        "Product",
        backref="codes"
    )


class Purchase(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    product_name = db.Column(
        db.String(150),
        nullable=False
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    delivered_code = db.Column(
        db.Text,
        default=""
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref="purchases"
    )


class Payment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    utr = db.Column(
        db.String(150),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref="payments"
    )


class Transaction(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    transaction_type = db.Column(
        db.String(50),
        nullable=False
    )

    note = db.Column(
        db.String(300),
        default=""
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =====================
# DECORATORS
# =====================

def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first")
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper


def admin_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if not session.get("is_admin"):
            flash("Admin access required")
            return redirect("/shop")

        return func(*args, **kwargs)

    return wrapper


# =====================
# HOME
# =====================

@app.route("/")
def home():

    if session.get("user_id"):
        return redirect("/shop")

    return redirect("/login")


# =====================
# REGISTER
# =====================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if len(username) < 3:
            flash("Username must have 3+ characters")
            return redirect("/register")

        if len(password) < 4:
            flash("Password must have 4+ characters")
            return redirect("/register")

        if User.query.filter_by(
            username=username
        ).first():

            flash("Username already exists")
            return redirect("/register")

        user = User(
            username=username,
            password=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully!")

        return redirect("/login")

    return render_template("register.html")


# =====================
# LOGIN
# =====================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if not user:

            flash("Wrong username or password")
            return redirect("/login")

        if not check_password_hash(
            user.password,
            password
        ):

            flash("Wrong username or password")
            return redirect("/login")

        session["user_id"] = user.id
        session["username"] = user.username
        session["is_admin"] = user.is_admin

        return redirect("/shop")

    return render_template("login.html")


# =====================
# LOGOUT
# =====================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =====================
# SHOP
# =====================

@app.route("/shop")
@login_required
def shop():

    user = db.session.get(
        User,
        session["user_id"]
    )

    products = Product.query.filter_by(
        active=True
    ).order_by(
        Product.id.desc()
    ).all()

    categories = Category.query.all()

    return render_template(
        "home.html",
        user=user,
        products=products,
        categories=categories
    )


# =====================
# WALLET
# =====================

@app.route("/wallet")
@login_required
def wallet():

    user = db.session.get(
        User,
        session["user_id"]
    )

    transactions = Transaction.query.filter_by(
        user_id=user.id
    ).order_by(
        Transaction.id.desc()
    ).limit(30).all()

    return render_template(
        "wallet.html",
        user=user,
        transactions=transactions
    )


# =====================
# ADD MONEY
# =====================

@app.route(
    "/add-money",
    methods=["GET", "POST"]
)
@login_required
def add_money():

    if request.method == "POST":

        try:
            amount = float(
                request.form.get("amount", 0)
            )
        except ValueError:
            amount = 0

        if amount <= 0:
            flash("Enter valid amount")
            return redirect("/add-money")

        session["payment_amount"] = amount

        return redirect("/payment")

    return render_template("add_money.html")


# =====================
# PAYMENT
# =====================

@app.route(
    "/payment",
    methods=["GET", "POST"]
)
@login_required
def payment():

    amount = session.get("payment_amount")

    if not amount:
        return redirect("/add-money")

    if request.method == "POST":

        utr = request.form.get(
            "utr",
            ""
        ).strip()

        if len(utr) < 6:
            flash("Enter a valid UTR / Transaction ID")
            return redirect("/payment")

        payment_data = Payment(
            user_id=session["user_id"],
            amount=amount,
            utr=utr
        )

        db.session.add(payment_data)
        db.session.commit()

        session.pop(
            "payment_amount",
            None
        )

        flash(
            "Payment submitted for admin verification"
        )

        return redirect("/wallet")

    return render_template(
        "payment.html",
        amount=amount,
        upi_id=UPI_ID
    )


# =====================
# HISTORY
# =====================

@app.route("/history")
@login_required
def history():

    purchases = Purchase.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Purchase.id.desc()
    ).all()

    return render_template(
        "history.html",
        purchases=purchases
    )


# =====================
# HELP
# =====================

@app.route("/help")
@login_required
def help_page():

    return render_template(
        "help.html",
        support=SUPPORT_USERNAME
    )


# =====================
# ADMIN PANEL
# =====================

@app.route("/admin")
@login_required
@admin_required
def admin():

    return render_template(
        "admin.html",
        users=User.query.order_by(User.id.desc()).all(),
        products=Product.query.order_by(Product.id.desc()).all(),
        categories=Category.query.all(),
        payments=Payment.query.filter_by(
            status="pending"
        ).order_by(
            Payment.id.desc()
        ).all(),
        purchases=Purchase.query.order_by(
            Purchase.id.desc()
        ).limit(50).all()
    )


# =====================
# ADD CATEGORY
# =====================

@app.route(
    "/admin/category/add",
    methods=["POST"]
)
@login_required
@admin_required
def add_category():

    name = request.form.get(
        "name",
        ""
    ).strip()

    icon = request.form.get(
        "icon",
        "🎁"
    ).strip()

    if name:

        db.session.add(
            Category(
                name=name,
                icon=icon or "🎁"
            )
        )

        db.session.commit()

        flash("Category added!")

    return redirect("/admin")


# =====================
# ADD PRODUCT
# =====================

@app.route(
    "/admin/product/add",
    methods=["POST"]
)
@login_required
@admin_required
def add_product():

    name = request.form.get(
        "name",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    image = request.form.get(
        "image",
        ""
    ).strip()

    category_id = request.form.get(
        "category_id"
    )

    try:
        price = float(
            request.form.get("price", 0)
        )
    except ValueError:
        price = 0

    if not name or price <= 0:

        flash("Enter product name and valid price")

        return redirect("/admin")

    product = Product(
        name=name,
        description=description,
        image=image,
        price=price,
        category_id=int(category_id)
        if category_id
        else None
    )

    db.session.add(product)
    db.session.commit()

    flash("Product added!")

    return redirect("/admin")


# =====================
# ADD PRODUCT CODES
# =====================

@app.route(
    "/admin/code/add",
    methods=["POST"]
)
@login_required
@admin_required
def add_codes():

    product_id = request.form.get("product_id")

    codes_text = request.form.get(
        "codes",
        ""
    ).strip()

    if not product_id or not codes_text:

        flash("Select product and enter codes")

        return redirect("/admin")

    added = 0

    for code_text in codes_text.splitlines():

        code_text = code_text.strip()

        if code_text and not ProductCode.query.filter_by(
            code=code_text
        ).first():

            db.session.add(
                ProductCode(
                    product_id=int(product_id),
                    code=code_text
                )
            )

            added += 1

    db.session.commit()

    flash(f"{added} codes added!")

    return redirect("/admin")


# =====================
# APPROVE PAYMENT
# =====================

@app.route(
    "/admin/payment/approve/<int:payment_id>"
)
@login_required
@admin_required
def approve_payment(payment_id):

    payment_data = db.session.get(
        Payment,
        payment_id
    )

    if not payment_data:

        flash("Payment not found")

        return redirect("/admin")

    if payment_data.status != "pending":

        flash("Payment already processed")

        return redirect("/admin")

    user = db.session.get(
        User,
        payment_data.user_id
    )

    user.balance += payment_data.amount

    payment_data.status = "approved"

    db.session.add(
        Transaction(
            user_id=user.id,
            amount=payment_data.amount,
            transaction_type="deposit",
            note=f"Approved payment | UTR: {payment_data.utr}"
        )
    )

    db.session.commit()

    flash(
        f"₹{payment_data.amount} added successfully"
    )

    return redirect("/admin")


# =====================
# REJECT PAYMENT
# =====================

@app.route(
    "/admin/payment/reject/<int:payment_id>"
)
@login_required
@admin_required
def reject_payment(payment_id):

    payment_data = db.session.get(
        Payment,
        payment_id
    )

    if payment_data and payment_data.status == "pending":

        payment_data.status = "rejected"

        db.session.commit()

        flash("Payment rejected")

    return redirect("/admin")


# =====================
# CREATE DATABASE
# =====================

with app.app_context():

    db.create_all()

    admin_user = User.query.filter_by(
        username=ADMIN_USERNAME
    ).first()

    if not admin_user:

        db.session.add(
            User(
                username=ADMIN_USERNAME,
                password=generate_password_hash(
                    ADMIN_PASSWORD
                ),
                is_admin=True
            )
        )

        db.session.commit()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get("PORT", 8080)
        )
  )

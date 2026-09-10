import os
from datetime import datetime
from decimal import Decimal

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)

database_url = os.environ.get("DATABASE_URL")

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )
else:
    database_url = "sqlite:///shop.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =====================================
# DATABASE MODELS
# =====================================

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

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    balance = db.Column(
        db.Numeric(12, 2),
        default=Decimal("0.00")
    )

    is_admin = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
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
        db.Numeric(12, 2),
        nullable=False
    )

    image = db.Column(
        db.String(500),
        default=""
    )

    stock = db.Column(
        db.Integer,
        default=0
    )

    category = db.Column(
        db.String(100),
        default="Redeem Code"
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class RedeemCode(db.Model):

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

    used = db.Column(
        db.Boolean,
        default=False
    )

    used_by = db.Column(
        db.Integer,
        nullable=True
    )

    used_at = db.Column(
        db.DateTime,
        nullable=True
    )


class PaymentRequest(db.Model):

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
        db.Numeric(12, 2),
        nullable=False
    )

    utr = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="PENDING"
    )

    admin_note = db.Column(
        db.String(500),
        default=""
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
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

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )

    product_name = db.Column(
        db.String(150),
        nullable=False
    )

    amount = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    redeem_code = db.Column(
        db.String(500),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =====================================
# HELPER FUNCTIONS
# =====================================

def current_user():

    user_id = session.get("user_id")

    if not user_id:
        return None

    return db.session.get(
        User,
        user_id
    )


def login_required(func):

    def wrapper(*args, **kwargs):

        if not current_user():
            flash("Please login first.", "error")

            return redirect(
                url_for("login")
            )

        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__

    return wrapper


def admin_required(func):

    def wrapper(*args, **kwargs):

        user = current_user()

        if not user or not user.is_admin:

            flash(
                "Admin access required.",
                "error"
            )

            return redirect(
                url_for("index")
            )

        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__

    return wrapper


# =====================================
# CREATE ADMIN
# =====================================

def create_admin():

    admin_username = os.environ.get(
        "ADMIN_USERNAME",
        "admin"
    )

    admin_password = os.environ.get(
        "ADMIN_PASSWORD",
        "Admin@12345"
    )

    admin = User.query.filter_by(
        username=admin_username
    ).first()

    if admin:
        # Existing user ko admin bana do
        admin.is_admin = True
        admin.password = generate_password_hash(
            admin_password
        )
        db.session.commit()

    else:
        # Admin user create karo
        admin = User(
            username=admin_username,
            email="admin@store.local",
            password=generate_password_hash(
                admin_password
            ),
            balance=Decimal("0.00"),
            is_admin=True
        )

        db.session.add(admin)
        db.session.commit()



# =====================================
# HOME
# =====================================

@app.route("/")
def index():

    products = Product.query.filter_by(
        active=True
    ).order_by(
        Product.id.desc()
    ).limit(6).all()

    return render_template(
        "index.html",
        products=products,
        user=current_user()
    )


# =====================================
# REGISTER
# =====================================

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

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if len(username) < 3:

            flash(
                "Username minimum 3 characters.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        if "@" not in email:

            flash(
                "Enter valid email.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        if len(password) < 6:

            flash(
                "Password minimum 6 characters.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        existing_user = User.query.filter(
            (User.username == username) |
            (User.email == email)
        ).first()

        if existing_user:

            flash(
                "Username or email already exists.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(
                password
            )
        )

        db.session.add(user)

        db.session.commit()

        flash(
            "Account created! Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# =====================================
# LOGIN
# =====================================

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

        if not user or not check_password_hash(
            user.password,
            password
        ):

            flash(
                "Invalid username or password.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        session["user_id"] = user.id

        flash(
            f"Welcome {user.username}!",
            "success"
        )

        return redirect(
            url_for("index")
        )

    return render_template(
        "login.html"
    )


# =====================================
# LOGOUT
# =====================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Logged out successfully.",
        "success"
    )

    return redirect(
        url_for("index")
    )


# =====================================
# PRODUCTS
# =====================================

@app.route("/products")
def products():

    product_list = Product.query.filter_by(
        active=True
    ).order_by(
        Product.id.desc()
    ).all()

    return render_template(
        "products.html",
        products=product_list
    )


# =====================================
# BUY PRODUCT
# =====================================

@app.route("/buy/<int:product_id>")
@login_required
def buy_product(product_id):

    user = current_user()

    product = db.session.get(
        Product,
        product_id
    )

    if not product or not product.active:

        flash(
            "Product not available.",
            "error"
        )

        return redirect(
            url_for("products")
        )

    available_code = RedeemCode.query.filter_by(
        product_id=product.id,
        used=False
    ).first()

    if not available_code:

        flash(
            "Product out of stock.",
            "error"
        )

        return redirect(
            url_for("products")
        )

    if user.balance < product.price:

        flash(
            "Insufficient wallet balance.",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    user.balance -= product.price

    available_code.used = True

    available_code.used_by = user.id

    available_code.used_at = datetime.utcnow()

    purchase = Purchase(
        user_id=user.id,
        product_id=product.id,
        product_name=product.name,
        amount=product.price,
        redeem_code=available_code.code
    )

    db.session.add(purchase)

    db.session.commit()

    flash(
        "Purchase successful! Check History.",
        "success"
    )

    return redirect(
        url_for("history")
    )


# =====================================
# WALLET
# =====================================

@app.route("/wallet")
@login_required
def wallet():

    user = current_user()

    payments = PaymentRequest.query.filter_by(
        user_id=user.id
    ).order_by(
        PaymentRequest.id.desc()
    ).limit(5).all()

    return render_template(
        "wallet.html",
        user=user,
        payments=payments
    )


# =====================================
# ADD MONEY
# =====================================

@app.route(
    "/add-money",
    methods=["GET", "POST"]
)
@login_required
def add_money():

    user = current_user()

    upi_id = os.environ.get(
        "UPI_ID",
        "sima6241@ptaxis"
    )

    upi_name = os.environ.get(
        "UPI_NAME",
        "Redeem Store"
    )

    if request.method == "POST":

        amount_text = request.form.get(
            "amount",
            ""
        )

        utr = request.form.get(
            "utr",
            ""
        ).strip()

        try:

            amount = Decimal(
                amount_text
            )

        except:

            flash(
                "Enter valid amount.",
                "error"
            )

            return redirect(
                url_for("add_money")
            )

        if amount < Decimal("10"):

            flash(
                "Minimum add money ₹10.",
                "error"
            )

            return redirect(
                url_for("add_money")
            )

        if len(utr) < 6:

            flash(
                "Enter valid UTR number.",
                "error"
            )

            return redirect(
                url_for("add_money")
            )

        duplicate = PaymentRequest.query.filter_by(
            utr=utr
        ).first()

        if duplicate:

            flash(
                "This UTR already submitted.",
                "error"
            )

            return redirect(
                url_for("add_money")
            )

        payment = PaymentRequest(
            user_id=user.id,
            amount=amount,
            utr=utr,
            status="PENDING"
        )

        db.session.add(payment)

        db.session.commit()

        flash(
            "Payment request submitted!",
            "success"
        )

        return redirect(
            url_for("wallet")
        )

    return render_template(
        "add_money.html",
        upi_id=upi_id,
        upi_name=upi_name
    )


# =====================================
# HISTORY
# =====================================

@app.route("/history")
@login_required
def history():

    user = current_user()

    purchases = Purchase.query.filter_by(
        user_id=user.id
    ).order_by(
        Purchase.id.desc()
    ).all()

    payments = PaymentRequest.query.filter_by(
        user_id=user.id
    ).order_by(
        PaymentRequest.id.desc()
    ).all()

    return render_template(
        "history.html",
        purchases=purchases,
        payments=payments
    )


# =====================================
# PROFILE
# =====================================

@app.route("/profile")
@login_required
def profile():

    return render_template(
        "profile.html",
        user=current_user()
    )


# =====================================
# ADMIN DASHBOARD
# =====================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    total_users = User.query.count()

    total_products = Product.query.count()

    pending_payments = PaymentRequest.query.filter_by(
        status="PENDING"
    ).count()

    total_sales = db.session.query(
        db.func.coalesce(
            db.func.sum(Purchase.amount),
            0
        )
    ).scalar()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_products=total_products,
        pending_payments=pending_payments,
        total_sales=total_sales
    )


# =====================================
# ADMIN PRODUCTS
# =====================================

@app.route(
    "/admin/products",
    methods=["GET", "POST"]
)
@admin_required
def admin_products():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price_text = request.form.get(
            "price",
            ""
        )

        image = request.form.get(
            "image",
            ""
        ).strip()

        category = request.form.get(
            "category",
            "Redeem Code"
        ).strip()

        try:

            price = Decimal(
                price_text
            )

        except:

            flash(
                "Invalid price.",
                "error"
            )

            return redirect(
                url_for("admin_products")
            )

        if not name or price <= 0:

            flash(
                "Enter valid product details.",
                "error"
            )

            return redirect(
                url_for("admin_products")
            )

        product = Product(
            name=name,
            description=description,
            price=price,
            image=image,
            category=category
        )

        db.session.add(product)

        db.session.commit()

        flash(
            "Product created!",
            "success"
        )

        return redirect(
            url_for("admin_products")
        )

    product_list = Product.query.order_by(
        Product.id.desc()
    ).all()

    return render_template(
        "admin/products.html",
        products=product_list
    )


# =====================================
# ADMIN ADD REDEEM CODE
# =====================================

@app.route(
    "/admin/product/<int:product_id>/code",
    methods=["POST"]
)
@admin_required
def admin_add_code(product_id):

    code = request.form.get(
        "code",
        ""
    ).strip()

    product = db.session.get(
        Product,
        product_id
    )

    if not product:

        flash(
            "Product not found.",
            "error"
        )

        return redirect(
            url_for("admin_products")
        )

    if not code:

        flash(
            "Enter redeem code.",
            "error"
        )

        return redirect(
            url_for("admin_products")
        )

    existing = RedeemCode.query.filter_by(
        code=code
    ).first()

    if existing:

        flash(
            "Code already exists.",
            "error"
        )

        return redirect(
            url_for("admin_products")
        )

    redeem = RedeemCode(
        product_id=product.id,
        code=code
    )

    db.session.add(redeem)

    db.session.commit()

    flash(
        "Redeem code added!",
        "success"
    )

    return redirect(
        url_for("admin_products")
    )


# =====================================
# ADMIN DELETE PRODUCT
# =====================================

@app.route(
    "/admin/product/<int:product_id>/delete"
)
@admin_required
def admin_delete_product(product_id):

    product = db.session.get(
        Product,
        product_id
    )

    if product:

        codes = RedeemCode.query.filter_by(
            product_id=product.id
        ).all()

        for code in codes:

            db.session.delete(code)

        db.session.delete(product)

        db.session.commit()

        flash(
            "Product deleted.",
            "success"
        )

    return redirect(
        url_for("admin_products")
    )


# =====================================
# ADMIN PAYMENTS
# =====================================


@app.route("/admin/payments")
@admin_required
def admin_payments():

    payments = PaymentRequest.query.order_by(
        PaymentRequest.id.desc()
    ).all()

    return render_template(
        "admin/payments.html",
        payments=payments
    )




# =====================================
# ADMIN APPROVE PAYMENT
# =====================================

@app.route(
    "/admin/payment/<int:payment_id>/approve",
    methods=["POST"]
)
@admin_required
def approve_payment(payment_id):

    payment = db.session.get(
        PaymentRequest,
        payment_id
    )

    if not payment:

        flash(
            "Payment not found.",
            "error"
        )

        return redirect(
            url_for("admin_payments")
        )

    if payment.status != "PENDING":

        flash(
            "Payment already processed.",
            "error"
        )

        return redirect(
            url_for("admin_payments")
        )

    user = db.session.get(
        User,
        payment.user_id
    )

    if not user:

        flash(
            "User not found.",
            "error"
        )

        return redirect(
            url_for("admin_payments")
        )

    user.balance += payment.amount

    payment.status = "APPROVED"

    payment.admin_note = "Payment verified and approved."

    db.session.commit()

    flash(
        "Payment approved and wallet updated!",
        "success"
    )

    return redirect(
        url_for("admin_payments")
    )


# =====================================
# ADMIN REJECT PAYMENT
# =====================================

@app.route(
    "/admin/payment/<int:payment_id>/reject",
    methods=["POST"]
)
@admin_required
def reject_payment(payment_id):

    payment = db.session.get(
        PaymentRequest,
        payment_id
    )

    if not payment:

        flash(
            "Payment not found.",
            "error"
        )

        return redirect(
            url_for("admin_payments")
        )

    if payment.status != "PENDING":

        flash(
            "Payment already processed.",
            "error"
        )

        return redirect(
            url_for("admin_payments")
        )

    note = request.form.get(
        "note",
        ""
    ).strip()

    payment.status = "REJECTED"

    payment.admin_note = (
        note or
        "Payment could not be verified."
    )

    db.session.commit()

    flash(
        "Payment rejected.",
        "success"
    )

    return redirect(
        url_for("admin_payments")
    )


# =====================================
# ADMIN USERS
# =====================================

@app.route("/admin/users")
@admin_required
def admin_users():

    users = User.query.order_by(
        User.id.desc()
    ).all()

    return render_template(
        "admin/users.html",
        users=users
    )


# =====================================
# CONTEXT
# =====================================

@app.context_processor
def inject_user():

    return {
        "current_user_data": current_user()
    }


# =====================================
# START
# =====================================

with app.app_context():

    db.create_all()

    create_admin()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )

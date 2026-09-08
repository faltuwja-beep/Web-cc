const express = require("express");
const path = require("path");
const fs = require("fs");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const app = express();

const PORT = process.env.PORT || 3000;
const SECRET = process.env.JWT_SECRET || "xenon-secret-change-me";

const ADMIN_EMAIL =
  process.env.ADMIN_EMAIL || "admin@xenon.shop";

const ADMIN_PASSWORD =
  process.env.ADMIN_PASSWORD || "ChangeMe123!";

const DATA_DIR = path.join(__dirname, "data");
const DATA_FILE = path.join(DATA_DIR, "db.json");

app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

function readData() {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  if (!fs.existsSync(DATA_FILE)) {
    fs.writeFileSync(
      DATA_FILE,
      JSON.stringify({
        users: [],
        products: [
          {
            id: 1,
            name: "₹500 Redeem Code",
            price: 500,
            description: "₹500 digital redeem code",
            icon: "🎟️"
          },
          {
            id: 2,
            name: "₹1000 Redeem Code",
            price: 1000,
            description: "₹1000 digital redeem code",
            icon: "💳"
          },
          {
            id: 3,
            name: "₹5000 Redeem Code",
            price: 5000,
            description: "₹5000 premium redeem code",
            icon: "💎"
          }
        ],
        coupons: [],
        deposits: [],
        orders: [],
        support: [],
        nextId: 10
      }, null, 2)
    );
  }

  return JSON.parse(
    fs.readFileSync(DATA_FILE, "utf8")
  );
}

function saveData(data) {
  fs.writeFileSync(
    DATA_FILE,
    JSON.stringify(data, null, 2)
  );
}

function publicUser(user) {
  return {
    id: user.id,
    uid: user.uid,
    name: user.name,
    email: user.email,
    wallet: user.wallet,
    referralCode: user.referralCode,
    membership: "VIP PRIME PROFESSIONAL"
  };
}

function tokenFor(user) {
  return jwt.sign(
    { id: user.id },
    SECRET,
    { expiresIn: "7d" }
  );
}

function auth(req, res, next) {
  try {
    const header =
      req.headers.authorization || "";

    const token =
      header.startsWith("Bearer ")
        ? header.substring(7)
        : "";

    const decoded =
      jwt.verify(token, SECRET);

    req.user = decoded;
    next();

  } catch {
    res.status(401).json({
      error: "Login required"
    });
  }
}

function adminAuth(req, res, next) {
  if (
    req.headers["x-admin-email"] !==
      ADMIN_EMAIL ||
    req.headers["x-admin-password"] !==
      ADMIN_PASSWORD
  ) {
    return res.status(401).json({
      error: "Invalid admin login"
    });
  }

  next();
}

/* REGISTER */

app.post("/api/register", async (req, res) => {
  const data = readData();

  const name =
    String(req.body.name || "").trim();

  const email =
    String(req.body.email || "")
      .trim()
      .toLowerCase();

  const password =
    String(req.body.password || "");

  const referralCode =
    String(req.body.referralCode || "")
      .trim();

  if (!name || !email || !password) {
    return res.status(400).json({
      error: "All fields are required"
    });
  }

  if (password.length < 6) {
    return res.status(400).json({
      error: "Password must be at least 6 characters"
    });
  }

  if (
    data.users.some(
      user => user.email === email
    )
  ) {
    return res.status(400).json({
      error: "Email already registered"
    });
  }

  const referrer =
    data.users.find(
      user =>
        user.referralCode ===
        referralCode
    );

  const user = {
    id: Date.now(),

    uid:
      "XENON-" +
      Math.random()
        .toString(36)
        .substring(2, 8)
        .toUpperCase(),

    name,
    email,

    password:
      await bcrypt.hash(password, 10),

    wallet: 0,

    referralCode:
      "REF-" +
      Math.random()
        .toString(36)
        .substring(2, 8)
        .toUpperCase(),

    referredBy:
      referrer ? referrer.id : null,

    referralRewardGiven: false
  };

  data.users.push(user);
  saveData(data);

  res.json({
    token: tokenFor(user),
    user: publicUser(user)
  });
});

/* LOGIN */

app.post("/api/login", async (req, res) => {
  const data = readData();

  const email =
    String(req.body.email || "")
      .trim()
      .toLowerCase();

  const password =
    String(req.body.password || "");

  const user =
    data.users.find(
      x => x.email === email
    );

  if (
    !user ||
    !(await bcrypt.compare(
      password,
      user.password
    ))
  ) {
    return res.status(401).json({
      error: "Invalid email or password"
    });
  }

  res.json({
    token: tokenFor(user),
    user: publicUser(user)
  });
});

/* CURRENT USER */

app.get("/api/me", auth, (req, res) => {
  const data = readData();

  const user =
    data.users.find(
      x => x.id === req.user.id
    );

  if (!user) {
    return res.status(404).json({
      error: "User not found"
    });
  }

  res.json(publicUser(user));
});

/* PRODUCTS */

app.get("/api/products", (req, res) => {
  const data = readData();

  res.json(data.products);
});

/* ADD MONEY */

app.post("/api/deposits", auth, (req, res) => {
  const data = readData();

  const amount =
    Number(req.body.amount);

  const utr =
    String(req.body.utr || "").trim();

  if (
    !Number.isFinite(amount) ||
    amount < 10
  ) {
    return res.status(400).json({
      error: "Minimum amount is ₹10"
    });
  }

  if (!utr) {
    return res.status(400).json({
      error: "UTR required"
    });
  }

  const deposit = {
    id: Date.now(),
    userId: req.user.id,
    amount,
    utr,
    status: "PENDING",
    createdAt:
      new Date().toISOString()
  };

  data.deposits.push(deposit);
  saveData(data);

  res.json(deposit);
});

/* HISTORY */

app.get("/api/history", auth, (req, res) => {
  const data = readData();

  res.json({
    deposits:
      data.deposits.filter(
        x => x.userId === req.user.id
      ),

    orders:
      data.orders.filter(
        x => x.userId === req.user.id
      )
  });
});

/* COUPON CHECK */

app.post(
  "/api/coupon/check",
  auth,
  (req, res) => {

    const data = readData();

    const product =
      data.products.find(
        x =>
          x.id == req.body.productId
      );

    const code =
      String(req.body.code || "")
        .trim()
        .toUpperCase();

    const coupon =
      data.coupons.find(
        x =>
          x.code === code &&
          x.active === true
      );

    if (!product || !coupon) {
      return res.status(400).json({
        error: "Invalid coupon"
      });
    }

    const discount =
      Math.floor(
        product.price *
        coupon.percent /
        100
      );

    res.json({
      discount,
      final:
        Math.max(
          0,
          product.price - discount
        )
    });
  }
);

/* BUY PRODUCT */

app.post(
  "/api/orders",
  auth,
  (req, res) => {

    const data = readData();

    const user =
      data.users.find(
        x => x.id === req.user.id
      );

    const product =
      data.products.find(
        x =>
          x.id == req.body.productId
      );

    if (!user || !product) {
      return res.status(404).json({
        error: "Product not found"
      });
    }

    const couponCode =
      String(req.body.coupon || "")
        .trim()
        .toUpperCase();

    const coupon =
      data.coupons.find(
        x =>
          x.code === couponCode &&
          x.active === true
      );

    let price = product.price;

    if (coupon) {
      price =
        Math.max(
          0,
          product.price -
          Math.floor(
            product.price *
            coupon.percent /
            100
          )
        );
    }

    if (user.wallet < price) {
      return res.status(400).json({
        error: "Insufficient wallet balance"
      });
    }

    user.wallet -= price;

    const code =
      "XENON-" +
      Math.random()
        .toString(36)
        .substring(2, 12)
        .toUpperCase();

    data.orders.push({
      id: Date.now(),
      userId: user.id,
      product: product.name,
      amount: price,
      code,
      createdAt:
        new Date().toISOString()
    });

    /* ₹50 referral reward after purchase */

    if (
      user.referredBy &&
      !user.referralRewardGiven
    ) {
      const parent =
        data.users.find(
          x =>
            x.id === user.referredBy
        );

      if (parent) {
        parent.wallet += 50;
        user.referralRewardGiven = true;
      }
    }

    saveData(data);

    res.json({
      success: true,
      code,
      wallet: user.wallet
    });
  }
);

/* SUPPORT */

app.post(
  "/api/support",
  auth,
  (req, res) => {

    const data = readData();

    data.support.push({
      id: Date.now(),
      userId: req.user.id,
      message:
        String(
          req.body.message || ""
        ),
      createdAt:
        new Date().toISOString()
    });

    saveData(data);

    res.json({
      success: true
    });
  }
);

/* ADMIN PAYMENT LIST */

app.get(
  "/api/admin/deposits",
  adminAuth,
  (req, res) => {

    const data = readData();

    res.json(
      data.deposits.map(deposit => {

        const user =
          data.users.find(
            x =>
              x.id === deposit.userId
          );

        return {
          ...deposit,
          email:
            user
              ? user.email
              : "Unknown"
        };
      })
    );
  }
);

/* ADMIN ACCEPT / REJECT */

app.post(
  "/api/admin/deposits/:id",
  adminAuth,
  (req, res) => {

    const data = readData();

    const deposit =
      data.deposits.find(
        x =>
          x.id ==
          req.params.id
      );

    if (!deposit) {
      return res.status(404).json({
        error: "Payment not found"
      });
    }

    if (
      deposit.status !==
      "PENDING"
    ) {
      return res.status(400).json({
        error: "Already reviewed"
      });
    }

    const user =
      data.users.find(
        x =>
          x.id === deposit.userId
      );

    if (
      req.body.action ===
      "ACCEPT"
    ) {

      deposit.status =
        "ACCEPTED";

      if (user) {
        user.wallet

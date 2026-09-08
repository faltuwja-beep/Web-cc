const express = require("express");
const path = require("path");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const app = express();

const PORT = process.env.PORT || 3000;
const SECRET =
  process.env.JWT_SECRET || "change-this-secret";

const ADMIN_EMAIL =
  process.env.ADMIN_EMAIL || "admin@xenon.shop";

const ADMIN_PASSWORD =
  process.env.ADMIN_PASSWORD || "change-this-password";

const UPI_ID =
  process.env.UPI_ID || "yourupi@upi";

app.use(express.json({ limit: "5mb" }));

app.use(
  express.static(path.join(__dirname, "public"))
);

/* ---------------- DATABASE ---------------- */

let data = {
  users: [],
  deposits: [],
  purchases: [],
  products: [
    {
      id: 1,
      name: "Premium Account",
      price: 99,
      description:
        "Premium digital package.",
      image: "",
      icon: "⭐"
    },
    {
      id: 2,
      name: "VIP Package",
      price: 199,
      description:
        "VIP digital package.",
      image: "",
      icon: "💎"
    }
  ]
};

/* ---------------- HELPERS ---------------- */

function createToken(user) {
  return jwt.sign(
    {
      id: user.id,
      email: user.email
    },
    SECRET,
    {
      expiresIn: "30d"
    }
  );
}

function publicUser(user) {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    balance: user.balance,
    referralCode: user.referralCode,
    referralBonus: user.referralBonus
  };
}

function makeReferralCode() {
  return (
    "XENON" +
    Math.random()
      .toString(36)
      .substring(2, 8)
      .toUpperCase()
  );
}

/* ---------------- AUTH ---------------- */

function auth(req, res, next) {
  const header =
    req.headers.authorization || "";

  if (!header.startsWith("Bearer ")) {
    return res.status(401).json({
      error: "Login required"
    });
  }

  try {
    const token = header.substring(7);

    req.user = jwt.verify(
      token,
      SECRET
    );

    next();
  } catch (error) {
    return res.status(401).json({
      error: "Session expired"
    });
  }
}

function adminOnly(req, res, next) {
  if (
    !req.user ||
    req.user.email !== ADMIN_EMAIL
  ) {
    return res.status(403).json({
      error: "Admin only"
    });
  }

  next();
}

/* ---------------- REGISTER ---------------- */

app.post("/api/register", async (req, res) => {
  try {
    const name =
      String(req.body.name || "").trim();

    const email =
      String(req.body.email || "")
        .trim()
        .toLowerCase();

    const password =
      String(req.body.password || "");

    const referralCode =
      String(
        req.body.referralCode || ""
      )
        .trim()
        .toUpperCase();

    if (
      !name ||
      !email ||
      !password
    ) {
      return res.status(400).json({
        error:
          "Name, email and password required"
      });
    }

    if (password.length < 6) {
      return res.status(400).json({
        error:
          "Password minimum 6 characters hona chahiye"
      });
    }

    const exists =
      data.users.find(
        user => user.email === email
      );

    if (exists) {
      return res.status(400).json({
        error:
          "Email already registered"
      });
    }

    const hashedPassword =
      await bcrypt.hash(
        password,
        10
      );

    const user = {
      id: Date.now().toString(),

      name,

      email,

      passwordHash:
        hashedPassword,

      balance: 0,

      referralCode:
        makeReferralCode(),

      referralBonus: 0,

      referredBy: null
    };

    const referrer =
      data.users.find(
        user =>
          user.referralCode ===
          referralCode
      );

    if (referrer) {
      user.referredBy =
        referrer.id;
    }

    data.users.push(user);

    res.json({
      token: createToken(user),
      user: publicUser(user)
    });

  } catch (error) {
    console.error(error);

    res.status(500).json({
      error: "Registration failed"
    });
  }
});

/* ---------------- LOGIN ---------------- */

app.post("/api/login", async (req, res) => {
  try {
    const email =
      String(req.body.email || "")
        .trim()
        .toLowerCase();

    const password =
      String(req.body.password || "");

    const user =
      data.users.find(
        user =>
          user.email === email
      );

    if (!user) {
      return res.status(401).json({
        error:
          "Wrong email or password"
      });
    }

    const correct =
      await bcrypt.compare(
        password,
        user.passwordHash
      );

    if (!correct) {
      return res.status(401).json({
        error:
          "Wrong email or password"
      });
    }

    res.json({
      token: createToken(user),
      user: publicUser(user)
    });

  } catch (error) {
    res.status(500).json({
      error: "Login failed"
    });
  }
});

/* ---------------- CURRENT USER ---------------- */

app.get("/api/me", auth, (req, res) => {
  const user =
    data.users.find(
      user =>
        user.id === req.user.id
    );

  if (!user) {
    return res.status(404).json({
      error: "User not found"
    });
  }

  res.json(
    publicUser(user)
  );
});

/* ---------------- PRODUCTS ---------------- */

app.get(
  "/api/products",
  (req, res) => {
    res.json(data.products);
  }
);

/* ---------------- PAYMENT INFO ---------------- */

app.get(
  "/api/payment-info",
  (req, res) => {
    res.json({
      upiId: UPI_ID
    });
  }
);

/* ---------------- ADD MONEY ---------------- */

app.post(
  "/api/deposits",
  auth,
  (req, res) => {

    const amount =
      Number(req.body.amount);

    const utr =
      String(
        req.body.utr || ""
      ).trim();

    if (
      !amount ||
      amount <= 0
    ) {
      return res.status(400).json({
        error:
          "Valid amount enter karo"
      });
    }

    if (!utr) {
      return res.status(400).json({
        error:
          "UTR enter karo"
      });
    }

    const deposit = {
      id: Date.now().toString(),

      userId:
        req.user.id,

      amount,

      utr,

      status:
        "PENDING",

      createdAt:
        new Date().toISOString()
    };

    data.deposits.push(
      deposit
    );

    res.json({
      message:
        "Payment submitted",

      deposit
    });
  }
);

/* ---------------- USER DEPOSITS ---------------- */

app.get(
  "/api/deposits",
  auth,
  (req, res) => {

    const deposits =
      data.deposits
        .filter(
          deposit =>
            deposit.userId ===
            req.user.id
        )
        .reverse();

    res.json(deposits);
  }
);

/* ---------------- BUY PRODUCT ---------------- */

app.post(
  "/api/buy",
  auth,
  (req, res) => {

    const user =
      data.users.find(
        user =>
          user.id ===
          req.user.id
      );

    const product =
      data.products.find(
        product =>
          product.id ===
          Number(
            req.body.productId
          )
      );

    if (!user) {
      return res.status(404).json({
        error:
          "User not found"
      });
    }

    if (!product) {
      return res.status(404).json({
        error:
          "Product not found"
      });
    }

    if (
      user.balance <
      product.price
    ) {
      return res.status(400).json({
        error:
          "Insufficient balance"
      });
    }

    user.balance -=
      product.price;

    const purchase = {
      id: Date.now().toString(),

      userId:
        user.id,

      productId:
        product.id,

      amount:
        product.price,

      status:
        "COMPLETED",

      createdAt:
        new Date().toISOString()
    };

    data.purchases.push(
      purchase
    );

    res.json({
      message:
        "Purchase successful",

      user:
        publicUser(user)
    });
  }
);

/* ---------------- LIVE ACTIVITY ---------------- */

app.get(
  "/api/activity",
  (req, res) => {

    const activity =
      data.purchases
        .slice(-15)
        .reverse()
        .map(
          purchase => {

            const user =
              data.users.find(
                user =>
                  user.id ===
                  purchase.userId
              );

            const product =
              data.products.find(
                product =>
                  product.id ===
                  purchase.productId
              );

            return {
              name:
                user
                  ? user.name
                  : "Customer",

              product:
                product
                  ? product.name
                  : "Product",

              amount:
                purchase.amount,

              createdAt:
                purchase.createdAt
            };
          }
        );

    res.json(activity);
  }
);

/* ---------------- REFERRALS ---------------- */

app.get(
  "/api/referrals",
  auth,
  (req, res) => {

    const user =
      data.users.find(
        user =>
          user.id ===
          req.user.id
      );

    if (!user) {
      return res.status(404).json({
        error:
          "User not found"
      });
    }

    const referrals =
      data.users.filter(
        other =>
          other.referredBy ===
          user.id
      );

    res.json({
      referralCode:
        user.referralCode,

      bonus:
        user.referralBonus,

      total:
        referrals.length
    });
  }
);

/* ---------------- ADMIN LOGIN ---------------- */

app.post(
  "/api/admin/login",
  (req, res) => {

    const email =
      String(
        req.body.email || ""
      ).trim();

    const password =
      String(
        req.body.password || ""
      );

    if (
      email !==
        ADMIN_EMAIL ||
      password !==
        ADMIN_PASSWORD
    ) {
      return res.status(401).json({
        error:
          "Invalid admin login"
      });
    }

    const token =
      jwt.sign(
        {
          id: "admin",
          email:
            ADMIN_EMAIL
        },
        SECRET,
        {
          expiresIn:
            "30d"
        }
      );

    res.json({
      token
    });
  }
);

/* ---------------- ADMIN DEPOSITS ---------------- */

app.get(
  "/api/admin/deposits",
  auth,
  adminOnly,
  (req, res) => {

    const deposits =
      data.deposits
        .map(deposit => {

          const user =
            data.users.find(
              user =>
                user.id ===
                deposit.userId
            );

          return {
            ...deposit,

            user:
              user
                ? user.email
                : "Unknown",

            userName:
              user
                ? user.name
                : "Unknown"
          };
        })
        .reverse();

    res.json(deposits);
  }
);

/* ---------------- ADMIN APPROVE / REJECT ---------------- */

app.post(
  "/api/admin/deposits/:id",
  auth,
  adminOnly,
  (req, res) => {

    const deposit =
      data.deposits.find(
        deposit =>
          deposit.id ===
          req.params.id
      );

    if (!deposit) {
      return res.status(404).json({
        error:
          "Deposit not found"
      });
    }

    if (
      deposit.status !==
      "PENDING"
    ) {
      return res.status(400).json({
        error:
          "Payment already processed"
      });
    }

    const status =
      req.body.status;

    if (
      status !==
        "APPROVED" &&
      status !==
        "REJECTED"
    ) {
      return res.status(400).json({
        error:
          "Invalid status"
      });
    }

    deposit.status =
      status;

    if (
      status ===
      "APPROVED"
    ) {

      const user =
        data.users.find(
          user =>

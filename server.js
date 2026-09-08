const express = require("express");
const path = require("path");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const app = express();
const PORT = process.env.PORT || 3000;

const SECRET =
  process.env.JWT_SECRET || "xenon-change-this-secret";

const ADMIN_EMAIL =
  process.env.ADMIN_EMAIL || "admin@xenon.shop";

const ADMIN_PASSWORD =
  process.env.ADMIN_PASSWORD || "change-this-password";

const UPI_ID =
  process.env.UPI_ID || "yourupi@upi";

app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

const db = {
  users: [],
  deposits: [],
  purchases: [],
  referrals: [],

  products: [
    {
      id: 1,
      name: "Premium Account",
      price: 99,
      description: "Premium digital package",
      icon: "⭐"
    },
    {
      id: 2,
      name: "VIP Package",
      price: 199,
      description: "VIP digital package",
      icon: "💎"
    },
    {
      id: 3,
      name: "Pro Package",
      price: 299,
      description: "Professional package",
      icon: "🚀"
    }
  ]
};

function makeToken(user) {
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

function auth(req, res, next) {
  const header = req.headers.authorization || "";

  if (!header.startsWith("Bearer ")) {
    return res.status(401).json({
      error: "Login required"
    });
  }

  try {
    req.user = jwt.verify(
      header.substring(7),
      SECRET
    );

    next();
  } catch {
    return res.status(401).json({
      error: "Session expired"
    });
  }
}

function admin(req, res, next) {
  if (req.user.email !== ADMIN_EMAIL) {
    return res.status(403).json({
      error: "Admin only"
    });
  }

  next();
}

/* REGISTER */

app.post("/api/register", async (req, res) => {
  const name = String(req.body.name || "").trim();
  const email = String(req.body.email || "")
    .trim()
    .toLowerCase();

  const password = String(
    req.body.password || ""
  );

  const referralCode = String(
    req.body.referralCode || ""
  )
    .trim()
    .toUpperCase();

  if (!name || !email || password.length < 6) {
    return res.status(400).json({
      error:
        "Name, email and password of at least 6 characters are required"
    });
  }

  if (
    db.users.some(
      user => user.email === email
    )
  ) {
    return res.status(400).json({
      error: "Email already registered"
    });
  }

  const user = {
    id: Date.now().toString(),

    name,

    email,

    passwordHash:
      await bcrypt.hash(password, 10),

    balance: 0,

    referralCode:
      makeReferralCode(),

    referralBonus: 0,

    referredBy: null
  };

  if (referralCode) {
    const referrer = db.users.find(
      user =>
        user.referralCode ===
        referralCode
    );

    if (referrer) {
      user.referredBy = referrer.id;
    }
  }

  db.users.push(user);

  res.json({
    token: makeToken(user),
    user: publicUser(user)
  });
});

/* LOGIN */

app.post("/api/login", async (req, res) => {
  const email = String(
    req.body.email || ""
  )
    .trim()
    .toLowerCase();

  const password = String(
    req.body.password || ""
  );

  const user = db.users.find(
    x => x.email === email
  );

  if (
    !user ||
    !(await bcrypt.compare(
      password,
      user.passwordHash
    ))
  ) {
    return res.status(401).json({
      error: "Wrong email or password"
    });
  }

  res.json({
    token: makeToken(user),
    user: publicUser(user)
  });
});

/* CURRENT USER */

app.get("/api/me", auth, (req, res) => {
  const user = db.users.find(
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
  res.json(db.products);
});

/* PAYMENT INFO */

app.get(
  "/api/payment-info",
  (req, res) => {
    res.json({
      upiId: UPI_ID
    });
  }
);

/* ADD MONEY */

app.post(
  "/api/deposits",
  auth,
  (req, res) => {
    const amount = Number(
      req.body.amount
    );

    const utr = String(
      req.body.utr || ""
    ).trim();

    if (
      !amount ||
      amount <= 0 ||
      !utr
    ) {
      return res.status(400).json({
        error: "Amount and UTR are required"
      });
    }

    const deposit = {
      id: Date.now().toString(),

      userId: req.user.id,

      amount,

      utr,

      status: "PENDING",

      createdAt:
        new Date().toISOString()
    };

    db.deposits.push(deposit);

    res.json({
      message:
        "Payment submitted successfully",
      deposit
    });
  }
);

/* USER PAYMENT HISTORY */

app.get(
  "/api/deposits",
  auth,
  (req, res) => {
    const deposits =
      db.deposits
        .filter(
          x =>
            x.userId ===
            req.user.id
        )
        .reverse();

    res.json(deposits);
  }
);

/* BUY */

app.post("/api/buy", auth, (req, res) => {
  const user = db.users.find(
    x => x.id === req.user.id
  );

  const product = db.products.find(
    x =>
      x.id ===
      Number(req.body.productId)
  );

  if (!product) {
    return res.status(404).json({
      error: "Product not found"
    });
  }

  if (user.balance < product.price) {
    return res.status(400).json({
      error: "Insufficient balance"
    });
  }

  user.balance -= product.price;

  db.purchases.push({
    id: Date.now().toString(),

    userId: user.id,

    productId: product.id,

    amount: product.price,

    status: "COMPLETED",

    createdAt:
      new Date().toISOString()
  });

  if (
    user.referredBy &&
    !db.referrals.some(
      x =>
        x.referredUserId ===
        user.id
    )
  ) {
    const referrer =
      db.users.find(
        x =>
          x.id ===
          user.referredBy
      );

    if (referrer) {
      referrer.balance += 50;

      referrer.referralBonus += 50;

      db.referrals.push({
        referrerId:
          referrer.id,

        referredUserId:
          user.id,

        amount: 50,

        status: "PAID",

        createdAt:
          new Date().toISOString()
      });
    }
  }

  res.json({
    message:
      "Purchase successful",
    user: publicUser(user)
  });
});

/* REFERRALS */

app.get(
  "/api/referrals",
  auth,
  (req, res) => {
    const user = db.users.find(
      x => x.id === req.user.id
    );

    const referrals =
      db.referrals.filter(
        x =>
          x.referrerId ===
          user.id
      );

    res.json({
      referralCode:
        user.referralCode,

      bonus:
        user.referralBonus,

      referrals
    });
  }
);

/* ADMIN LOGIN */

app.post(
  "/api/admin/login",
  (req, res) => {
    if (
      req.body.email !==
        ADMIN_EMAIL ||
      req.body.password !==
        ADMIN_PASSWORD
    ) {
      return res.status(401).json({
        error:
          "Invalid admin login"
      });
    }

    const token = jwt.sign(
      {
        id: "admin",
        email: ADMIN_EMAIL
      },
      SECRET,
      {
        expiresIn: "30d"
      }
    );

    res.json({ token });
  }
);

/* ADMIN DEPOSITS */

app.get(
  "/api/admin/deposits",
  auth,
  admin,
  (req, res) => {
    const list =
      db.deposits.map(d => ({
        ...d,

        user:
          db.users.find(
            u =>
              u.id ===
              d.userId
          )?.email ||
          "Unknown"
      }));

    res.json(list.reverse());
  }
);

/* APPROVE / REJECT */

app.post(
  "/api/admin/deposits/:id",
  auth,
  admin,
  (req, res) => {
    const deposit =
      db.deposits.find(
        x =>
          x.id ===
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
      status !== "APPROVED" &&
      status !== "REJECTED"
    ) {
      return res.status(400).json({
        error:
          "Invalid status"
      });
    }

    deposit.status = status;

    if (status === "APPROVED") {
      const user =
        db.users.find(
          x =>
            x.id ===
            deposit.userId
        );

      if (user) {
        user.balance +=
          deposit.amount;
      }
    }

    res.json(deposit);
  }
);

/* HEALTH */

app.get(
  "/api/health",
  (req, res) => {
    res.json({
      ok: true
    });
  }
);

app.listen(
  PORT,
  () => {
    console.log(
      "⚡ XENON SHOP RUNNING"
    );

    console.log(
      "🌐 Port: " + PORT
    );
  }
);

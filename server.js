const express = require("express");
const path = require("path");
const fs = require("fs");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const app = express();

const PORT = process.env.PORT || 3000;

const JWT_SECRET =
  process.env.JWT_SECRET ||
  "xenon-shop-change-this-secret";

const ADMIN_EMAIL =
  process.env.ADMIN_EMAIL ||
  "admin@xenon.shop";

const ADMIN_PASSWORD =
  process.env.ADMIN_PASSWORD ||
  "admin123";

const UPI_ID =
  process.env.UPI_ID ||
  "yourupi@upi";


/* =========================
   MIDDLEWARE
========================= */

app.use(express.json({
  limit: "2mb"
}));

app.use(express.urlencoded({
  extended: true
}));

app.use(express.static(
  path.join(__dirname, "public")
));


/* =========================
   DATABASE
========================= */

const dataDir =
  path.join(__dirname, "data");

const dataFile =
  path.join(dataDir, "db.json");


function defaultData() {
  return {
    users: [],
    deposits: [],
    products: [],
    purchases: []
  };
}


function ensureDatabase() {

  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, {
      recursive: true
    });
  }

  if (!fs.existsSync(dataFile)) {

    fs.writeFileSync(
      dataFile,
      JSON.stringify(
        defaultData(),
        null,
        2
      )
    );

  }

}


function readData() {

  ensureDatabase();

  try {

    const raw =
      fs.readFileSync(
        dataFile,
        "utf8"
      );

    const data =
      JSON.parse(raw);

    return {
      users: Array.isArray(data.users)
        ? data.users
        : [],

      deposits: Array.isArray(data.deposits)
        ? data.deposits
        : [],

      products: Array.isArray(data.products)
        ? data.products
        : [],

      purchases: Array.isArray(data.purchases)
        ? data.purchases
        : []
    };

  } catch (error) {

    console.error(
      "Database read error:",
      error
    );

    return defaultData();

  }

}


function saveData(data) {

  ensureDatabase();

  fs.writeFileSync(
    dataFile,
    JSON.stringify(
      data,
      null,
      2
    )
  );

}


ensureDatabase();


/* =========================
   HELPERS
========================= */

function makeId() {

  return Date.now().toString() +
    Math.random()
      .toString(36)
      .slice(2, 8);

}


function makeReferralCode(name) {

  const clean =
    String(name || "USER")
      .replace(
        /[^a-zA-Z0-9]/g,
        ""
      )
      .toUpperCase()
      .slice(0, 5);

  return (
    clean +
    Math.random()
      .toString(36)
      .slice(2, 7)
      .toUpperCase()
  );

}


function publicUser(user) {

  return {
    id: user.id,
    name: user.name,
    email: user.email,
    balance: Number(user.balance || 0),

    referralCode:
      user.referralCode || "",

    referralCount:
      Number(user.referralCount || 0),

    referralEarnings:
      Number(user.referralEarnings || 0),

    createdAt:
      user.createdAt
  };

}


function createToken(user) {

  return jwt.sign(
    {
      id: user.id
    },
    JWT_SECRET,
    {
      expiresIn: "30d"
    }
  );

}


/* =========================
   AUTH MIDDLEWARE
========================= */

function auth(req, res, next) {

  const header =
    req.headers.authorization || "";

  if (!header.startsWith("Bearer ")) {

    return res.status(401).json({
      error: "Login required"
    });

  }


  const token =
    header.slice(7);


  try {

    const decoded =
      jwt.verify(
        token,
        JWT_SECRET
      );

    req.user = decoded;

    next();

  } catch (error) {

    return res.status(401).json({
      error: "Invalid or expired token"
    });

  }

}


function admin(req, res, next) {

  const data =
    readData();

  const user =
    data.users.find(
      x => x.id === req.user.id
    );


  if (
    !user ||
    user.role !== "admin"
  ) {

    return res.status(403).json({
      error: "Admin access required"
    });

  }


  next();

}


/* =========================
   HEALTH CHECK
========================= */

app.get(
  "/api/health",
  (req, res) => {

    res.json({
      ok: true,
      message: "Xenon Shop is running"
    });

  }
);


/* =========================
   CONFIG
========================= */

app.get(
  "/api/config",
  (req, res) => {

    res.json({
      upiId: UPI_ID
    });

  }
);


/* =========================
   REGISTER
========================= */

app.post(
  "/api/register",
  async (req, res) => {

    try {

      const {
        name,
        email,
        password,
        referral
      } = req.body;


      const cleanName =
        String(name || "").trim();

      const cleanEmail =
        String(email || "")
          .trim()
          .toLowerCase();

      const cleanPassword =
        String(password || "");


      if (!cleanName) {

        return res.status(400).json({
          error: "Name is required"
        });

      }


      if (!cleanEmail) {

        return res.status(400).json({
          error: "Email is required"
        });

      }


      if (
        cleanPassword.length < 6
      ) {

        return res.status(400).json({
          error:
            "Password must be at least 6 characters"
        });

      }


      const data =
        readData();


      const exists =
        data.users.find(
          x =>
            x.email ===
            cleanEmail
        );


      if (exists) {

        return res.status(400).json({
          error:
            "Email already registered"
        });

      }


      const passwordHash =
        await bcrypt.hash(
          cleanPassword,
          10
        );


      let referralCode =
        makeReferralCode(
          cleanName
        );


      while (
        data.users.some(
          x =>
            x.referralCode ===
            referralCode
        )
      ) {

        referralCode =
          makeReferralCode(
            cleanName
          );

      }


      const user = {

        id: makeId(),

        name: cleanName,

        email: cleanEmail,

        password:
          passwordHash,

        balance: 0,

        referralCode,

        referralCount: 0,

        referralEarnings: 0,

        role: "user",

        referredBy:
          String(
            referral || ""
          ).trim(),

        createdAt:
          new Date().toISOString()

      };


      /* Referral count */

      if (user.referredBy) {

        const referrer =
          data.users.find(
            x =>
              x.referralCode ===
              user.referredBy
          );


        if (referrer) {

          referrer.referralCount =
            Number(
              referrer.referralCount ||
              0
            ) + 1;

        }

      }


      data.users.push(
        user
      );

      saveData(data);


      const token =
        createToken(
          user
        );


      res.status(201).json({

        token,

        user:
          publicUser(user)

      });


    } catch (error) {

      console.error(
        "Register error:",
        error
      );

      res.status(500).json({
        error:
          "Registration failed"
      });

    }

  }
);


/* =========================
   LOGIN
========================= */

app.post(
  "/api/login",
  async (req, res) => {

    try {

      const email =
        String(
          req.body.email || ""
        )
          .trim()
          .toLowerCase();

      const password =
        String(
          req.body.password || ""
        );


      const data =
        readData();


      const user =
        data.users.find(
          x =>
            x.email ===
            email
        );


      if (!user) {

        return res.status(401).json({
          error:
            "Invalid email or password"
        });

      }


      const valid =
        await bcrypt.compare(
          password,
          user.password
        );


      if (!valid) {

        return res.status(401).json({
          error:
            "Invalid email or password"
        });

      }


      const token =
        createToken(
          user
        );


      res.json({

        token,

        user:
          publicUser(user)

      });


    } catch (error) {

      console.error(
        "Login error:",
        error
      );

      res.status(500).json({
        error:
          "Login failed"
      });

    }

  }
);


/* =========================
   CURRENT USER
========================= */

app.get(
  "/api/me",
  auth,
  (req, res) => {

    const data =
      readData();


    const user =
      data.users.find(
        x =>
          x.id ===
          req.user.id
      );


    if (!user) {

      return res.status(404).json({
        error:
          "User not found"
      });

    }


    res.json(
      publicUser(user)
    );

  }
);


/* =========================
   PRODUCTS
========================= */

app.get(
  "/api/products",
  (req, res) => {

    const data =
      readData();


    res.json(
      data.products.map(
        product => ({

          id: product.id,

          name:
            product.name,

          price:
            Number(
              product.price
            ),

          description:
            product.description ||
            "",

          icon:
            product.icon ||
            "📦",

          image:
            product.image ||
            ""

        })
      )
    );

  }
);


/* =========================
   BUY PRODUCT
========================= */

app.post(
  "/api/buy",
  auth,
  (req, res) => {

    const productId =
      String(
        req.body.productId || ""
      );


    const data =
      readData();


    const user =
      data.users.find(
        x =>
          x.id ===
          req.user.id
      );


    if (!user) {

      return res.status(404).json({
        error:
          "User not found"
      });

    }


    const product =
      data.products.find(
        x =>
          String(x.id) ===
          productId
      );


    if (!product) {

      return res.status(404).json({
        error:
          "Product not found"
      });

    }


    const price =
      Number(
        product.price
      );


    if (
      !Number.isFinite(price) ||
      price <= 0
    ) {

      return res.status(400).json({
        error:
          "Invalid product price"
      });

    }


    if (
      Number(user.balance || 0) <
      price
    ) {

      return res.status(400).json({
        error:
          "Insufficient wallet balance"
      });

    }


    user.balance =
      Number(user.balance || 0) -
      price;


    const purchase = {

      id: makeId(),

      userId:
        user.id,

      name:
        user.name,

      product:
        product.name,

      productId:
        product.id,

      amount:
        price,

      createdAt:
        new Date().toISOString()

    };


    data.purchases.push(
      purchase
    );


    saveData(data);


    res.json({

      success: true,

      message:
        "Purchase successful",

      purchase,

      balance:
        user.balance

    });

  }
);


/* =========================
   PUBLIC ACTIVITY
========================= */

app.get(
  "/api/activity",
  (req, res) => {

    const data =
      readData();


    const list =
      data.purchases
        .slice(-30)
        .reverse()
        .map(
          item => ({

            id:
              item.id,

            name:
              item.name,

            product:
              item.product,

            amount:
              item.amount,

            createdAt:
              item.createdAt

          })
        );


    res.json(list);

  }
);


/* =========================
   ADD MONEY
========================= */

app.post(
  "/api/deposits",
  auth,
  (req, res) => {

    const amount =
      Number(
        req.body.amount
      );

    const utr =
      String(
        req.body.utr || ""
      ).trim();


    if (
      !Number.isFinite(amount) ||
      amount <= 0
    ) {

      return res.status(400).json({
        error:
          "Invalid amount"
      });

    }


    if (!utr) {

      return res.status(400).json({
        error:
          "UTR is required"
      });

    }


    const data =
      readData();


    const user =
      data.users.find(
        x =>
          x.id ===
          req.user.id
      );


    if (!user) {

      return res.status(404).json({
        error:
          "User not found"
      });

    }


    const deposit = {

      id: makeId(),

      userId:
        user.id,

      userName:
        user.name,

      userEmail:
        user.email,

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


    saveData(data);


    res.status(201).json({

      success: true,

      deposit

    });

  }
);


/* =========================
   USER DEPOSITS
========================= */

app.get(
  "/api/deposits",
  auth,
  (req, res) => {

    const data =
      readData();


    const deposits =
      data.deposits.filter(
        x =>
          x.userId ===
          req.user.id
      );


    res.json(
      deposits
    );

  }
);


/* =========================
   ADMIN LOGIN
========================= */

app.post(
  "/api/admin/login",
  async (req, res) => {

    const email =
      String(
        req.body.email || ""
      )
        .trim()
        .toLowerCase();

    const password =
      String(
        req.body.password || ""
      );


    if (
      email !==
      ADMIN_EMAIL.toLowerCase() ||
      password !==
      ADMIN_PASSWORD
    ) {

      return res.status(401).json({
        error:
          "Invalid admin login"
      });

    }


    const data =
      readData();


    let adminUser =
      data.users.find(
        x =>
          x.email ===
          ADMIN_EMAIL.toLowerCase()
      );


    if (!adminUser) {

      adminUser = {

        id: "admin",

        name: "Xenon Admin",

        email:
          ADMIN_EMAIL.toLowerCase(),

        password:
          await bcrypt.hash(
            ADMIN_PASSWORD,
            10
          ),

        balance: 0,

        referralCode:
          "ADMIN",

        referralCount: 0,

        referralEarnings: 0,

        role: "admin",

        createdAt:
          new Date().toISOString()

      };


      data.users.push(
        adminUser
      );

      saveData(data);

    }


    adminUser.role =
      "admin";


    const token =
      createToken(
        adminUser
      );


    res.json({

      token,

      user:
        publicUser(
          adminUser
        )

    });

  }
);


/* =========================
   ADMIN DEPOSITS
========================= */

app.get(
  "/api/admin/deposits",
  auth,
  admin,
  (req, res) => {

    const data =
      readData();


    res.json(
      data.deposits
        .slice()
        .reverse()
    );

  }
);


/* =========================
   APPROVE / REJECT DEPOSIT
========================= */

app.post(
  "/api/admin/deposits/:id",
  auth,
  admin,
  (req, res) => {

    const depositId =
      String(
        req.params.id
      );


    const status =
      String(
        req.body.status || ""
      ).toUpperCase();


    if (
      status !==
      "APPROVED" &&
      status !==
      "REJECTED"
    ) {

      return res.status(400).json({
        error:
          "Status must be APPROVED or REJECTED"
      });

    }


    const data =
      readData();


    const deposit =
      data.deposits.find(
        x =>
          String(x.id) ===
          depositId
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
          "Deposit already processed"
      });

    }


    deposit.status =
      status;


    deposit.updatedAt =
      new Date().toISOString();


    /* Add wallet money only once */

    if (
      status ===
      "APPROVED"
    ) {

      const user =
        data.users.find(
          x =>
            x.id ===
            deposit.userId
        );


      if (!user) {

        return res.status(404).json({
          error:
            "User not found"
        });

      }


      user.balance =
        Number(
          user.balance || 0
        ) +
        Number(
          deposit.amount
        );

    }


    saveData(data);


    res.json({

      success: true,

      deposit

    });

  }
);


/* =========================
   ADMIN PRODUCTS
========================= */

app.post(
  "/api/admin/products",
  auth,
  admin,
  (req, res) => {

    const {
      name,
      price,
      description,
      image,
      icon
    } = req.body;


    const cleanName =
      String(
        name || ""
      ).trim();


    const productPrice =
      Number(price);


    if (!cleanName) {

      return res.status(400).json({
        error:
          "Product name required"
      });

    }


    if (
      !Number.isFinite(
        productPrice
      ) ||
      productPrice <= 0
    ) {

      return res.status(400).json({
        error:
          "Valid product price required"
      });

    }


    const data =
      readData();


    const product = {

      id: makeId(),

      name:
        cleanName,

      price:
        productPrice,

      description:
        String(
          description || ""
        ).trim(),

      image:
        String(
          image || ""
        ).trim(),

      icon:
        String(
          icon || "📦"
        ).trim(),

      createdAt:
        new Date().toISOString()

    };


    data.products.push(
      product
    );


    saveData(data);


    res.status(201).json({

      success: true,

      product

    });

  }
);


/* =========================
   ADMIN PRODUCT DELETE
========================= */

app.delete(
  "/api/admin/products/:id",
  auth,
  admin,
  (req, res) => {

    const id =
      String(
        req.params.id
      );


    const data =
      readData();


    const index =
      data.products.findIndex(
        x =>
          String(x.id) ===
          id
      );


    if (index === -1) {

      return res.status(404).json({
        error:
          "Product not found"
      });

    }


    const deleted =
      data.products.splice(
        index,
        1
      )[0];


    saveData(data);


    res.json({

      success: true,

      product:
        deleted

    });

  }
);


/* =========================
   ADMIN PRODUCT UPDATE
========================= */

app.put(
  "/api/admin/products/:id",
  auth,
  admin,
  (req, res) => {

    const id =
      String(
        req.params.id
      );


    const data =
      readData();


    const product =
      data.products.find(
        x =>
          String(x.id) ===
          id
      );


    if (!product) {

      return res.status(404).json({
        error:
          "Product not found"
      });

    }


    if (
      req.body.name !==
      undefined
    ) {

      product.name =
        String(
          req.body.name
        ).trim();

    }


    if (
      req.body.price !==
      undefined
    ) {

      const price =
        Number(
          req.body.price
        );


      if (
        !Number.isFinite(price) ||
        price <= 0
      ) {

        return res.status(400).json({
          error:
            "Invalid price"
        });

      }


      product.price =
        price;

    }


    if (
      req.body.description !==
      undefined
    ) {

      product.description =
        String(
          req.body.description
        ).trim();

    }


    if (
      req.body.image !==
      undefined
    ) {

      product.image =
        String(
          req.body.image
        ).trim();

    }


    if (
      req.body.icon !==
      undefined
    ) {

      product.icon

import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash


from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure database connection
conn = sqlite3.connect('finance.db', check_same_thread=False)
# function to make fetchone and fetchall to return dictionary instead of tuple


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


conn.row_factory = dict_factory
# assigning sqlite3.Row to the row_factory of connection creates a 'dictionary cursor'
# instead of tuples it starts returning 'dictionary' rows after fetchall or fetchone.
db = conn.cursor()

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    user_id = session["user_id"]

    # create transactions table if not exists
    db.execute(
        "CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL, action TEXT NOT NULL CHECK(action IN ('BUY', 'SELL')), symbol TEXT NOT NULL, name TEXT NOT NULL, price NUMERIC NOT NULL, shares INTEGER NOT NULL, datetime TEXT NOT NULL DEFAULT (datetime('now', 'localtime')))")

    # create index on user_id in transactions table for future search/where
    db.execute(
        "CREATE INDEX IF NOT EXISTS user_id ON transactions (user_id)")

    # get stock symbol, total_shares owned from db
    stocks = db.execute(
        "SELECT symbol, name, SUM(CASE WHEN action = 'BUY' THEN shares ELSE shares * -1 END) as total_shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0", (user_id, ))
    stocks = stocks.fetchall()

    # add current stock price and total_value to the dictonary
    for stock in stocks:
        quote = lookup(stock["symbol"])
        # stock["name"] = quote["name"]
        stock["price"] = quote["price"]
        stock["total_value"] = stock["price"] * stock["total_shares"]

    # get user's cash balance
    cash = db.execute("SELECT cash FROM users WHERE id = ?", (user_id, ))
    cash = cash.fetchall()
    cash = cash[0]["cash"]

    return render_template("index.html", stocks=stocks, cash=float(cash))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # define BUY action
    action = "BUY"

    # GET
    if request.method != "POST":
        return render_template("buy.html", action=action)

    # POST
    symbol = request.form.get("symbol")
    shares = request.form.get("shares", type=int)

    # if symbol or shares are empty
    if not symbol or not shares:
        return apology("stock symbol and number of shares must not be empty.")

    # if user manually changed shares to 0 or negative int
    if shares <= 0:
        return apology("number of shares must be a positive integer")

    quote = lookup(symbol)
    # if quote is null
    if not quote:
        return apology("stock symbol does not exist.")

    user_id = session["user_id"]
    price = quote["price"]
    name = quote["name"]
    # check cash balance
    cash = db.execute(
        "SELECT cash FROM users WHERE id = ?", (user_id, ))
    cash = cash.fetchall()
    cash = cash[0]["cash"]

    # check stock purchase total cost
    cost = price * shares

    # balance has to be >= 0
    balance = cash - cost

    # if total cost exceeds cash balance, return error message
    if balance < 0:
        return apology("you do not have enough cash balance. current balance: " + usd(cash) + ". total cost to buy stock: " + usd(cost), 403)

    # insert buy transaction
    db.execute(
        "INSERT INTO transactions (user_id, action, symbol, name, price, shares) VALUES (?, ?, ?, ?, ?, ?)", (user_id, action, symbol, name, price, shares))
    conn.commit()

    # update user table with new cash balance
    db.execute(
        "UPDATE users SET cash = ? WHERE id = ?", (balance, user_id))
    conn.commit()

    # display message that stock bought
    flash("Stock bought!", "information")

    return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # get this user's transactions
    trades = db.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY symbol, datetime", (session["user_id"], ))
    trades = trades.fetchall()

    return render_template("history.html", trades=trades)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          (request.form.get("username"), ))
        rows = rows.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # display message
        flash("Logged in!", "information")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # POST
    if request.method == "POST":
        symbol = request.form.get("symbol")
        # stock symbol should not be empty
        if len(symbol) > 0:
            quote = lookup(symbol)
            # if cannot find this stock symbol
            if not quote:
                return apology("stock symbol does not exist.")
            else:  # if stock symbol is found
                return render_template("quote.html", quote=quote)
        else:
            return apology("stock symbol must not be empty.")
    # GET
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    session.clear()

    # POST
    if request.method == "POST":

        # get all user inputs
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("username must not be empty.")

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", (username, ))
        rows = rows.fetchall()
        if len(rows) > 0:
            return apology("username already exists.")

        if not password or not confirmation:
            return apology("password and confirm password must not be empty.")

        if password != confirmation:
            return apology("passwords do not match")

        # hash the password
        hash_pw = generate_password_hash(password)

        # register new user
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                   (username, hash_pw))
        conn.commit()

        # display message user is registered
        flash("User registered!", "information")

        return render_template("login.html")

    # GET
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # define SELL action
    action = "SELL"

    user_id = session["user_id"]
    # get user_id, symbol, total_shares owned by user from db
    stocks = db.execute(
        "SELECT user_id, symbol, name, (SUM(CASE WHEN action = 'BUY' THEN shares ELSE shares * -1 END)) AS total_shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0", (user_id, ))
    stocks = stocks.fetchall()

    # GET
    if request.method != "POST":
        return render_template("sell.html", stocks=stocks)

    # POST
    symbol = request.form.get("symbol")
    shares = request.form.get("shares", type=int)

    # if symbol or shares are empty
    if not symbol or not shares:
        return apology("stock symbol and number of shares must not be empty.")

    # if share input is not a positive integer
    if shares <= 0:
        return apology("number of shares must be a positive integer")

    # total shares owned for chosen symbol
    shares_owned = 0
    for stock in stocks:
        if stock['symbol'] == symbol:
            shares_owned = stock['total_shares']

    # user does not own that many shares
    if shares > shares_owned:
        return apology("you do not own that many shares of this stock")

    quote = lookup(symbol)
    price = quote["price"]
    name = quote["name"]
    # insert sell transactions
    db.execute(
        "INSERT INTO transactions (user_id, action, symbol, name, price, shares) VALUES (?, ?, ?, ?, ?, ?)", (user_id, action, symbol, name, price, shares))
    conn.commit()

    # update user cash balance
    cash = db.execute("SELECT cash FROM users WHERE id = ?", (user_id, ))
    cash = cash.fetchall()
    cash = cash[0]["cash"]

    db.execute("UPDATE users SET cash = ? WHERE id = ?",
               ((cash + price * shares), user_id))
    conn.commit()

    # display message that stock sold
    flash("Stock sold!", "information")

    return redirect("/")

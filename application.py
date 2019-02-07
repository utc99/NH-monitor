from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from passlib.context import CryptContext
from helpers import *
from flask_jsglue import JSGlue
import schedule
import time
from apscheduler.schedulers.background import BackgroundScheduler
import string
import gc


# configure application
app = Flask(__name__)
JSGlue(app)
app.config['DEBUG'] = False


# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///monitor.db")

# Initiate the cron for constant refresh of data
@app.before_first_request
def initialize():

    apsched = BackgroundScheduler()
    apsched.start()
    apsched.add_job(backround_tasks, 'interval', seconds=40)

# Show Index page
#-------------------------------------------------------------------------
@app.route("/", methods=["GET"])
@login_required
def index():
    """Index page with balance"""

    return render_template("index.html")

# Give workers details
#-------------------------------------------------------------------------
@app.route("/display_data", methods=["GET"])
@login_required
def display_data():

    id=session["user_id"]

    # Get the address of the workers
    addr = request.args.get("addr")

    # Select this address only if it belongs to the user
    address = db.execute("SELECT wallet_address FROM wallets WHERE user_id=:id AND wallet_address=:addr", id=id, addr=addr)

    # If the user has no BTC addreses assigned
    if not address:
        return jsonify('no data')

    address = address[0]['wallet_address']
    #Return all workers data with the names of the algos, not just id's
    data =  db.execute("SELECT worker_name,accepted,rejected,diff,last_seen,time,suffix,algo_name FROM workers JOIN algos ON workers.algo = algos.algo_nr WHERE wallet_address =:address ORDER BY worker_name,last_seen ASC", address=address)

    return jsonify(data)

# Give all wallets of the user
#-------------------------------------------------------------------------
@app.route("/show_wallets", methods=["GET"])
@login_required
def show_wallets():

        id=session["user_id"]

        # Select all user's wallets and return a JSON
        wallets = db.execute("SELECT wallet_address FROM wallets WHERE user_id=:id", id=id)
        return jsonify(wallets)

# Give wallet details of specified address
#-------------------------------------------------------------------------
@app.route("/give_wallet", methods=["GET"])
@login_required
def give_wallet():

    if "user_id" in session:
        addr = request.args.get("addr")
        id=session["user_id"]

        data =  db.execute("SELECT * FROM wallets WHERE user_id =:id AND wallet_address=:addr", id=id, addr=addr)

        # If the user has no wallets
        if not data:
            return jsonify('no data')

        return jsonify(data)
    else:
        destination = url_for('login')
        return jsonify({"status":"fail","url":destination})

#-------------------------------------------------------------------------
@app.route("/give_user", methods=["GET"])
@login_required
def give_user():

    if "user_id" in session:
        id=session["user_id"]

        data =  db.execute("SELECT * FROM users WHERE id =:id", id=id)
        return jsonify(data)
    else:
        destination = url_for('login')
        return jsonify({"status":"fail","url":destination})

# Give newest exchange rates of the currency in user profile
#-------------------------------------------------------------------------
@app.route("/give_exchange_rate", methods=["GET"])
@login_required
def give_exchange_rate():

    id=session["user_id"]

    data =  db.execute("SELECT rate,symbol FROM exchange_rates JOIN users ON exchange_rates.currency = users.currency WHERE users.id=:id", id=id)
    return jsonify(data)

# Give currency list
#-------------------------------------------------------------------------
@app.route("/give_currency", methods=["GET"])
@login_required
def give_currency():

    id=session["user_id"]

    data =  db.execute("SELECT currency FROM exchange_rates WHERE 1")
    return jsonify(data)

# tasks to be ran in background for constant update
#-------------------------------------------------------------------------
def backround_tasks():

    start = time.time()

    set_exchange_rate()
    update_algo_profitability()
    update_workers()

    gc.collect()

    #Count the time spent for the tasks
    print ("it took", time.time() - start, "seconds.")

# user settings page
#-------------------------------------------------------------------------
@app.route("/settings", methods=["GET"])
@login_required
def settings():

    return render_template("settings.html")      # initial change password page

# Manual rows deletion in index page
#-------------------------------------------------------------------------
@app.route("/deleteIndexRows", methods=["GET", "POST"])
@login_required
def deleteIndexRows():

        id=session["user_id"]

        data = request.get_json()

        if 'worker' in data:
            address = db.execute("SELECT wallet_address FROM wallets WHERE user_id=:id AND wallet_address=:addr", id=id, addr=data['address'])
            is_found = len(address)
            address = address[0]['wallet_address']
            algo = db.execute("SELECT algo_nr FROM algos WHERE algo_name=:algo_name", algo_name=data['algo'])
            algo = algo[0]['algo_nr']
            if is_found == 1:
                db.execute("DELETE FROM workers WHERE wallet_address =:address AND worker_name=:worker AND algo =:algo", address=address, worker=data['worker'],algo=algo)

            return jsonify( {  "status": "ok" })
        else:
            return jsonify( {  "status": "failed" })

# Change user password
#-------------------------------------------------------------------------
@app.route("/change_password", methods=["POST"])
@login_required
def change_password():
    """Change a password."""

    # get the user input
    data = request.get_json()
    currentpass = data["current_password"]
    newpass1 = data["new_password_1"]
    newpass2 = data["new_password_2"]

    #Check for forbiden characters
    if symbol_check(currentpass) == True or symbol_check(newpass1) == True  or symbol_check(newpass2) == True:
        return jsonify( {  "status": "Invalid characters were found" })

    # ensure current password was submitted
    if not currentpass:
        return jsonify( {  "status": "Current password is required" })

    # ensure a new password was submitted
    elif not newpass1:
        return jsonify( {  "status": "New password is required" })

    # ensure a new password was confirmed
    elif not newpass2:
        return jsonify( {  "status": "Password is too short, at least 4 characters" })

    # check if passwords do match
    if newpass1 != newpass2:
        return jsonify( {  "status": "Passwords do not match" })

    # limit password length
    elif len(newpass1) > 32 :
        return jsonify( {  "status": "Password is too long, max - 32 characters" })

    # minimum password length
    elif len(newpass1) < 4 :
        return jsonify( {  "status": "Password is too short, at least 4 characters" })

    else:
    # hash the password and insert a new user into the database
        if changepass(currentpass,newpass1) == "success":
            return jsonify( {  "status": "Password was successfully updated" })
        else:
            return jsonify( {  "status": "Incorrect password" })

#Login route
#-------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return alert_user("Username is required", "alert-danger", "login.html")

        # ensure password was submitted
        elif not request.form.get("password"):
            return alert_user("Password is required", "alert-danger", "login.html")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return alert_user("Invalid username and/or password", "alert-danger", "login.html")
        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

#Logout route
#-------------------------------------------------------------------------
@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

#Register a new user
#-------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])            # NO illegal symbols, spaces check                  #########
def register():
    """Register user."""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # get user input
        username = request.form.get("username")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        # ensure username was submitted
        if not username:
            return alert_user("Username is required", "alert-danger", "register.html")

        if not email:
            return alert_user("Email is required", "alert-danger", "register.html")

        # ensure password was submitted
        elif not password1:
            return alert_user("Password is required", "alert-danger", "register.html")

        # ensure password was confirmed
        elif not password2:
            return alert_user("Password was not confirmed", "alert-danger", "register.html")

        # Check for forbiden characters
        if symbol_check(username) == True or symbol_check(password1) == True  or symbol_check(password2) == True or symbol_check(email) == True:
            return alert_user("Forbiden characters not allowed", "alert-danger", "register.html")

        # limit username length
        elif len(username) > 32 :
            return alert_user("Username is too long", "alert-danger", "register.html")

        # limit password length
        elif len(password1) > 32 :
            return alert_user("Username is too long, maximum 32 characters", "alert-danger", "register.html")

        # minimum password length
        elif len(password1) < 4 :
            return alert_user("Password is too short, at least 4 characters", "alert-danger", "register.html")
        # check if passwords do match
        if password1 != password2:
            return alert_user("Passwords do not match", "alert-danger", "register.html")
        else:
        # hash the password and insert a new user into the database, a new user gets redirected to index
            return create_user(username, email, password1)

    else:
        return render_template("register.html")


# Update wallets in user settings
#-------------------------------------------------------------------------
@app.route("/update_wallets", methods=["GET"])
def update_wallets():

        id=session["user_id"]

        # set new wallet addresses
        addr1 = request.args.get("addr1")
        my_list = addr1.split(",")

        #delete old wallets
        db.execute("DELETE FROM wallets WHERE user_id =:id", id=id)

        for item in my_list:
            if item != "":
                db.execute("INSERT INTO wallets (user_id, wallet_address) VALUES(:id, :wallet_address)",
                id=id, wallet_address=item)

        return jsonify("success")

# Update user summary information
#-------------------------------------------------------------------------
@app.route("/update_summary", methods=["POST"])
@login_required
def update_summary():
    """Change a password."""

    id=session["user_id"]

    # get the user input
    data = request.get_json()

    # if json is correct, double check for existing currency
    if 'currency' in data:
        email = data["email"]
        currency = db.execute("SELECT currency FROM exchange_rates WHERE currency=:currency", currency=data["currency"])
        if len(currency) == 1:
            # If currency is valid, update currency and user email
            db.execute("UPDATE users SET currency = :currency, email = :email WHERE id = :id", currency=currency[0]['currency'], email=email, id=id)
            return jsonify( {  "status": "User profile successfully updated." })

    return jsonify( {  "status": "Failed to update currency" })
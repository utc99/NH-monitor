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
#from apscheduler.scheduler import Scheduler
from apscheduler.schedulers.background import BackgroundScheduler

# configure application
app = Flask(__name__)
JSGlue(app)
app.config['DEBUG'] = True


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


@app.before_first_request
def initialize():
    apsched = BackgroundScheduler()

    apsched.start()
    apsched.add_job(backround_tasks, 'interval', seconds=40)


#-------------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Index page with balance"""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # apply the buy/sell actions through index page
        return(index_apply())
    else:
        # refresh and show balance in index page
        #balance = show_balance()
        return render_template("index.html")


#-------------------------------------------------------------------------
@app.route("/quote", methods=["GET", "POST"])
#@login_required
def quote():


    if request.method == "POST":
        return render_template("quote.html")
    else:
        return render_template("quote.html")

#-------------------------------------------------------------------------
@app.route("/display_data", methods=["GET"])
def display_data():

    if "user_id" in session:
        id=session["user_id"]
        address = db.execute("SELECT wallet_address FROM wallets WHERE user_id=:id", id=id)
        address = address[0]['wallet_address']

        data =  db.execute("SELECT worker_name,accepted,rejected,diff,last_seen,time,suffix,algo_name FROM workers JOIN algos ON workers.algo = algos.algo_nr WHERE wallet_address =:address ORDER BY worker_name,last_seen ASC", address=address)
        return jsonify(data)
    else:
        destination = url_for('login')
        return jsonify({"status":"fail","url":destination})

#-------------------------------------------------------------------------
@app.route("/give_wallet", methods=["GET"])
def give_wallet():

    if "user_id" in session:
        id=session["user_id"]

        data =  db.execute("SELECT * FROM wallets WHERE user_id =:id", id=id)
        return jsonify(data)

    else:
        destination = url_for('login')
        return jsonify({"status":"fail","url":destination})

#-------------------------------------------------------------------------
@app.route("/give_exchange_rate", methods=["GET"])
def give_exchange_rate():

    if "user_id" in session:
        id=session["user_id"]

        data =  db.execute("SELECT rate FROM exchange_rates JOIN users ON exchange_rates.currency = users.currency WHERE users.id=:id", id=id)
        return jsonify(data)

    else:
        destination = url_for('login')
        return jsonify({"status":"fail","url":destination})

#-------------------------------------------------------------------------
def backround_tasks():
    set_exchange_rate()
    update_algo_profitability()
    update_workers()

#-------------------------------------------------------------------------
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        print("POST")
    else:
        return render_template("settings.html")      # initial change password page


#-------------------------------------------------------------------------
@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change a password."""

    # get the user input
    currentpass = request.form.get("current_password")
    newpass1 = request.form.get("new_password_1")
    newpass2 = request.form.get("new_password_2")

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Check for forbiden characters
    #    if symbol_check(currentpass) == True or symbol_check(newpass1) == True  or symbol_check(newpass2) == True:
    #        return alert_user("Forbiden characters", "alert-danger","change_password.html")

        # ensure current password was submitted
        if not currentpass:
            return alert_user("Current password is required", "alert-danger","change_password.html")

        # ensure a new password was submitted
        elif not newpass1:
            return alert_user("New password is required", "alert-danger", "change_password.html")

        # ensure a new password was confirmed
        elif not newpass2:
            return alert_user("New password was not confirmed", "alert-danger", "change_password.html")

        # check if passwords do match
        if newpass1 != newpass2:
            return alert_user("Passwords do not match", "alert-danger","change_password.html")

        # limit password length
        elif len(newpass1) > 32 :
            return alert_user("Password is too long, max - 32 characters", "alert-danger","change_password.html")

        # minimum password length
        elif len(newpass1) < 4 :
            return alert_user("Password is too short, at least 4 characters", "alert-danger", "change_password.html")

        else:
        # hash the password and insert a new user into the database
            return changepass(currentpass,newpass1)

    else:
        return render_template("change_password.html")      # initial change password page


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

#-------------------------------------------------------------------------
@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

#-------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])            # NO illegal symbols, spaces check                  #########
def register():
    """Register user."""

    # get user input
    username = request.form.get("username")
    password1 = request.form.get("password1")
    password2 = request.form.get("password2")

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not username:
            return alert_user("Username is required", "alert-danger", "register.html")

        # ensure password was submitted
        elif not password1:
            return alert_user("Password is required", "alert-danger", "register.html")

        # ensure password was confirmed
        elif not password2:
            return alert_user("Password was not confirmed", "alert-danger", "register.html")

#FIX    # Check for forbiden characters
        if 1!=1:
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
            return create_user(username,password1)

    else:
        return render_template("register.html")

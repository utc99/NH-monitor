import csv
#import urllib.request
from urllib.request import Request, urlopen
from urllib.error import  URLError
import json
import feedparser
import urllib.parse
import logging

from flask import redirect, render_template, request, session, url_for
from functools import wraps
from flask_jsglue import JSGlue

from passlib.apps import custom_app_context as pwd_context
from passlib.context import CryptContext
from cs50 import SQL

db = SQL("sqlite:///monitor.db")

#-------------------------------------------------------------------------
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

#-------------------------------------------------------------------------
def create_user(username,password1):
    """Hashes the password and inserts a new user into database"""

    # define hashing parameters
    hasher = CryptContext(schemes=["sha256_crypt"])

    # hash the user password
    hash1 = hasher.hash(password1)

    # check if the username is not already taken
    rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
    if len(rows) == 1:
        return alert_user("Username already exists", "alert-danger", "register.html")
    else:
        # insert a new user to the database and redirect to the index page with the current balance
        db.execute("INSERT INTO users (username,hash) VALUES(:username, :hash)", username=username, hash=hash1)
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        session["user_id"] = rows[0]["id"]
        return alert_user("A new user was created successfuly!", "alert-success", "index.html")

#-------------------------------------------------------------------------
def changepass(currentpass,newpass1):
    """Hashes the password and inserts into database"""

    # check if the current password is valid
    id=session["user_id"]
    passwordrow = db.execute("SELECT hash FROM users WHERE id = :id", id=id)
    if len(passwordrow) != 1 or not pwd_context.verify(currentpass, passwordrow[0]["hash"]):
            return alert_user("Invalid password", "alert-danger", "change_password.html")


    # hash the new password
    hasher = CryptContext(schemes=["sha256_crypt"])
    hash1 = hasher.hash(newpass1)

    # update the pasword
    db.execute("UPDATE users SET hash = :hash WHERE id = :id", hash=hash1, id=id)

    return alert_user("Password was changed!", "alert-success", "index.html")

#-------------------------------------------------------------------------

def get_JSON(link,address=0):
        try:
            if address != 0:
                with urllib.request.urlopen(link.format(urllib.parse.quote(address, safe=""))) as url:
                    data = json.loads(url.read().decode())
            else:
                #with urllib.request.urlopen("{}".format(urllib.parse.quote(link, safe=""))) as url:
                with urllib.request.urlopen(link) as url:
                    data = json.loads(url.read().decode())
        except URLError as e:
            if hasattr(e, 'reason'):
                print('We failed to reach a server.')
                print('Reason: ', e.reason)
                return -1
            elif hasattr(e, 'code'):
                print('The server couldn\'t fulfill the request.')
                print('Error code: ', e.code)
                return -1

        # everything is fine
        return data

def get_worker_data(address):
    return get_JSON("https://api.nicehash.com/api?method=stats.provider.workers&addr={}", address)

def get_exchange_rate():
    return get_JSON("https://blockchain.info/ticker")

def get_new_algo(address):
    return get_JSON("https://api.nicehash.com/api?method=stats.provider.ex&addr={}", address)

def get_new_profitability():
    return get_JSON("https://api.nicehash.com/api?method=simplemultialgo.info")

def get_wallet_stats(address):
    return get_JSON("https://api.nicehash.com/api?method=stats.provider&addr={}", address)

def set_exchange_rate():

    new_rates = get_exchange_rate()
    if new_rates == -1:
        return

    for key,value in new_rates.items():

        currency = key
        rate = value['last']
        symbol = value ['symbol']

        old_rates =  db.execute("SELECT NULL FROM exchange_rates WHERE currency =:currency", currency=currency)
        if len(old_rates) != 1:
            db.execute("INSERT INTO exchange_rates (currency,rate,symbol) VALUES(:currency, :rate, :symbol)",
            currency=currency, rate=rate,symbol=symbol)
        else:
            db.execute("UPDATE exchange_rates SET rate=:rate WHERE currency =:currency", rate = rate, currency=currency)

#-------------------------------------------------------------------------
def alert_user(message, alert_type, page):
    return render_template(page,
    title = '<div class="alert ' + alert_type + '" role="alert">' + message + '</div>')

#-------------------------------------------------------------------------
def update_algo_profitability():

    algo_data = get_new_profitability()
    if algo_data == -1:
        return
    algo_data = algo_data['result']['simplemultialgo']
    for item in algo_data:
        algo_nr = item['algo']
        rows =  db.execute("SELECT suffix FROM algos WHERE :algo_nr=algo_nr", algo_nr=algo_nr)
        if len(rows) == 1:
            suffix = rows[0]['suffix']
            if suffix == "GH":
                divider = 11
            elif suffix == "MH":
                divider = 1000
            elif suffix == "kH":
                divider = 1000000
            else:
                divider = 1000000000

            profitability = float(item['paying']) / divider
            profitability = "{:.10f}".format(profitability)

            db.execute("UPDATE algos SET profitability=:profitability WHERE algo_nr =:algo_nr",
            profitability=profitability, algo_nr=algo_nr)

#-------------------------------------------------------------------------
def update_workers():

    db.execute("DELETE FROM history")

    wallets = db.execute("SELECT wallet_address FROM wallets WHERE 1")
    for item in wallets:

        wallet = item['wallet_address']
        workers = get_worker_data(wallet)         # retrieve and show data
        if workers == -1:
            return
        workers = workers['result']['workers']
        get_unpaid_balance(wallet)
        total_profit = 0.0

        for worker in workers:

            profitability = 0.0

            worker_name = worker[0]
            time = worker[2]
            diff = worker[4]
            location = worker[5]
            algo_nr = worker[6]

            rejected = 0.0
            accepted = 0.0

            for key,value in worker[1].items():  # `items()` for python3 `iteritems()` for python2
                if key == "a":
                    accepted = float(value)
                elif key == "rs":
                    rejected += float(value)

            rows1 =  db.execute("SELECT NULL FROM workers WHERE wallet_address =:wallet AND worker_name =:worker_name AND algo =:algo_nr",
            worker_name=worker_name, algo_nr=algo_nr,wallet=wallet)
            if len(rows1) < 1:
                db.execute("INSERT INTO workers (wallet_address,worker_name,accepted,rejected,time,diff,location,algo) VALUES(:wallet, :worker_name, :accepted, :rejected, :time, :diff, :location, :algo_nr)",
                wallet=wallet, worker_name=worker_name,accepted=accepted,rejected=rejected,time=time,diff=diff,location=location,algo_nr=algo_nr)
            else:
                db.execute("UPDATE workers SET accepted=:accepted, rejected=:rejected, time=:time, last_seen=0, timestamp = CURRENT_TIMESTAMP WHERE wallet_address =:wallet AND worker_name=:worker_name AND algo=:algo_nr",
                accepted=accepted, rejected = rejected, time=time, worker_name=worker_name, algo_nr=algo_nr, wallet=wallet)


            db.execute("INSERT INTO history (wallet_address,worker_name,algo) VALUES(:wallet, :worker_name, :algo_nr)",
                wallet=wallet, worker_name=worker_name, algo_nr=algo_nr)

            algos =  db.execute("SELECT NULL FROM algos WHERE algo_nr =:algo_nr", algo_nr=algo_nr)
            if len(algos) != 1:
                get_new_algo_data(wallet)


            profitability = db.execute("SELECT profitability FROM algos WHERE algo_nr =:algo_nr", algo_nr=algo_nr)

            profitability = profitability[0]['profitability']
            total_profit += float(profitability) * accepted

        total_profit = "{:.4f}".format(total_profit)
        db.execute('UPDATE wallets SET total_profitability=:total_profit WHERE wallet_address =:wallet',total_profit=total_profit, wallet=wallet)

    db.execute('UPDATE workers SET last_seen = CAST ((JulianDay(CURRENT_TIMESTAMP) - JulianDay(timestamp)) * 24 * 60 AS Integer ) WHERE NOT EXISTS ( SELECT NULL FROM history WHERE workers.worker_name = history.worker_name AND workers.algo = history.algo)')
    return


#-------------------------------------------------------------------------
def get_new_algo_data(address):

    result = get_new_algo(address)         # retrieve data.
    if result == -1:
        return

    current_data = result['result']['current']

    for item in current_data:

        algo_nr = item['algo']
        name = item['name']
        suffix = item['suffix']
        data = item['data']

        rows1 =  db.execute("SELECT NULL FROM algos WHERE :algo_nr=algo_nr", algo_nr=algo_nr)
        if len(rows1) < 1:
            db.execute("INSERT INTO algos (algo_nr,algo_name,suffix) VALUES(:algo_nr,:algo_name,:suffix)",
            algo_nr=algo_nr, algo_name=name,suffix=suffix)

    update_algo_profitability()

    return

#-------------------------------------------------------------------------
def get_unpaid_balance(address):

    result = get_wallet_stats(address)         # retrieve data.
    if result == -1:
        return
    current_data = result['result']['stats']
    unpaid_balance = 0.0
    for item in current_data:
        unpaid_balance += float(item['balance'])

    unpaid_balance = "{:.4f}".format(unpaid_balance)
    db.execute('UPDATE wallets SET unpaid_balance=:unpaid_balance WHERE wallet_address =:address',unpaid_balance=unpaid_balance, address=address)
    return
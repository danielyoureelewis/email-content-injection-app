#! /usr/local/bin/python
from flask import Flask, render_template, jsonify, request, session
from flask_session import Session
import sys
import os
import re
import math
import random
import urllib
import smtplib
import json
from email.mime.text import MIMEText
from email import policy
from email.parser import BytesParser
from email.mime.multipart import MIMEMultipart
import sqlite3

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

EMAILS_DIR = "emails"  # Directory where .eml files are stored
DB_PATH = "users.db"



def init_db():
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                email TEXT UNIQUE NOT NULL,
                                username TEXT NOT NULL,
                                password TEXT NOT NULL,
                                mfa INTEGER,
                                verified BOOL NOT NULL,
                                verification_code TEXT NOT NULL,
                                cart INTEGER)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS carts (
                                user_id INTEGER PRIMARY KEY,
                                items TEXT DEFAULT '[]',
                                FOREIGN KEY (user_id) REFERENCES users(id))''')
            conn.commit()
            print("[INFO] Database initialized.")

# Call this on startup
init_db()


def create_eml_file(sender, recipient, subject, body, filename="email.eml"):
    """Creates an EML file.

    Args:
        sender (str): Sender's email address.
        recipient (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        filename (str, optional): Name of the EML file to be created. Defaults to "email.eml".
    """
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))
    filename = 'emails/' + filename
    with open(filename, 'w') as f:
        f.write(msg.as_string())

@app.route("/")
def home():
    with open('./index.html') as page:
        return page.read()

@app.route("/signup", methods=['POST'])
def signup():
    print(request.host)
    if request.method == 'POST':
        content = f'Thank you for signing up for our newsletter!<br>Click <a href="http://{request.host}/unsubscribe/{urllib.parse.quote(request.json["email"])}">here</a> to unsubscribe.'
        subject = f'{request.host} Newsletter Signup'
        create_eml_file("noreply@online.store", request.json["email"], subject, content, filename='signup.eml')
        with open('./signUpThanks.html') as page:
            return page.read()
    else:
        print('else')

# New /results page to list and view .eml files
@app.route("/results")
def results():
    """Render the results page where users can pick an email to view."""
    email_files = [f for f in os.listdir(EMAILS_DIR) if f.endswith(".eml")]
    return render_template("results.html", emails=email_files)


@app.route("/get_email")
def get_email():
    """Fetch and parse an .eml file."""
    filename = request.args.get("filename")
    file_path = os.path.join(EMAILS_DIR, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    with open(file_path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)

    email_data = {
        "subject": msg["subject"],
        "from": msg["from"],
        "to": msg["to"],
        "date": msg["date"],
        "body": msg.get_body(preferencelist=("plain", "html")).get_content(),
    }

    return jsonify(email_data)

@app.route("/account")
def account():
    """Render the results page where users can pick an email to view."""
    with open('./account.html') as page:
        return page.read()

def generateOTP() :
 
    # Declare a digits variable  
    # which stores all digits 
    digits = "0123456789"
    OTP = ""
 
   # length of password can be changed
   # by changing value in range
    for i in range(6) :
        OTP += digits[math.floor(random.random() * 10)]
 
    return OTP

@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        data = request.get_json()
        
        username = data["username"]
        email = data["email"]
        password = data["password"]


        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                verfication_code = generateOTP()
                cursor.execute("INSERT INTO users (username, email, password, verified, verification_code) VALUES (?, ?, ?, ?, ?)", 
                               (username, email, password, False, verfication_code))

                user_id = cursor.lastrowid

                # Create an empty cart for the user
                cursor.execute("INSERT INTO carts (user_id, items) VALUES (?, '[]')", (user_id,))
                conn.commit()

                body = f"Welcome to online.store {username}! We are so glad to have you as a customer. Verify your email by clicking on this <a href='127.0.0.1:5000/{verfication_code}'>link</a>. If you need support, contact our support team  <a href='127.0.0.1:5000'>here</a>."
                create_eml_file("noreply@online.store", email, "Welcome to online.store!", body, filename="register.eml")
                return f'{{"message":"Signup successful! Welcome, {username}!"}}'
            except sqlite3.IntegrityError:
                return "username already exists!"

# Sign-In Route
@app.route("/signin", methods=["POST"])
def signin():
    if request.method == "POST":
        data = request.get_json()
        username = data["username"]
        password = data["password"]

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()
        if user:
            email = user[2]
            username = user[1]
            session["user_id"] = user[0]  # Store user_id in session
            session["username"] = username
            session["token"] = generateOTP()
            session["level"] = 0
            
            body = f"Hello, {username} Your token is {session["token"]}"
            create_eml_file("noreply@online.store", email, "online.store Login Token", body, filename="MFA.eml")
            return jsonify({"successful":"200"})
        else:
            return "Invalid username or password."


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    if "user_id" not in session:
        return "You must be signed in to add to cart.", 401

    data = request.get_json()
    item = data.get("item")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Fetch current cart items
        cursor.execute("SELECT items FROM carts WHERE user_id = ?", (session["user_id"],))
        cart = cursor.fetchone()

        if cart:
            items = json.loads(cart[0])
            items.append(item)  # Add new item
            cursor.execute("UPDATE carts SET items = ? WHERE user_id = ?", 
                           (json.dumps(items), session["user_id"]))
            conn.commit()
            return f"Item '{item}' added to cart."
        else:
            return "Cart not found.", 404

# View cart
@app.route("/cart", methods=["GET"])
def view_cart():
    if "user_id" not in session:
        return "You must be signed in to view your cart.", 401

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT items FROM carts WHERE user_id = ?", (session["user_id"],))
        cart = cursor.fetchone()

    if cart:
        return {"cart": json.loads(cart[0])}
    else:
        return "Cart not found.", 404

@app.route("/cart/view")
def view_cart_page():
    if "user_id" not in session:
        return "You must be signed in to view your cart.", 401
    return render_template("cart.html")

@app.route("/support", methods=["POST"])
def support():
    data = request.get_json()
    support_email = data["variables"]["email_addr"]
    email_body = data["variables"]["body"]
    email_subject = data["variables"]["subject"]
    create_eml_file("support@online.store", support_email, email_subject, email_body, filename="support.eml")
    return jsonify({"successful":"200"})

@app.route("/products", methods=["GET"])
def products():
    return render_template("products.html")

@app.route("/mfa", methods=["POST"])
def mfa():
    data = request.get_json()
    mfa = data["mfa"]
    print(session['token'])
    print(mfa)
    if session['token'] == mfa:
        session['level'] = 1
        return jsonify({"successful":"200"})
    else:
        return jsonify({"unsuccessful":"200"})

if __name__ == "__main__":
    
    app.run(debug=True)

#! /usr/local/bin/python
from flask import Flask, render_template, jsonify, request
import sys
import os
import re
import math
import random
import urllib
import smtplib
from email.mime.text import MIMEText
from email import policy
from email.parser import BytesParser
from email.mime.multipart import MIMEMultipart
import sqlite3
app = Flask(__name__)

EMAILS_DIR = "emails"  # Directory where .eml files are stored
DB_PATH = "users.db"

def init_db():
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT UNIQUE NOT NULL,
                                name TEXT NOT NULL,
                                password TEXT NOT NULL,
                                verified BOOL NOT NULL,
                                verification_code TEXT NOT NULL)''')
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
        
        name = data["name"]
        username = data["email"]
        password = data["password"]


        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                verfication_code = generateOTP()
                cursor.execute("INSERT INTO users (name, username, password, verified, verification_code) VALUES (?, ?, ?, ?, ?)", 
                               (name, username, password, False, verfication_code))
                conn.commit()
                body = f"Welcome to online.store {name}! We are so glad to have you as a customer. Verify your email by clicking on this <a href='127.0.0.1:5000/{verfication_code}'>link</a>. If you need support, contact our support team  <a href='127.0.0.1:5000'>here</a>."
                create_eml_file("noreply@online.store", username, "Welcome to online.store!", body, filename="register.eml")
                return f'{{"message":"Signup successful! Welcome, {name}!"}}'
            except sqlite3.IntegrityError:
                return "Username already exists!"

if __name__ == "__main__":
    
    app.run(debug=True)

#! /usr/local/bin/python
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
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
from datetime import datetime
import uuid
import base64
import bcrypt
from dotenv import load_dotenv
from config import DB_PATH, EMAILS_DIR, CHALLENGE_DB_PATH
from crypto_utils import hash_password, encrypt_card, decrypt_card

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

load_dotenv()

PASSWORD_PEPPER = os.getenv("PASSWORD_PEPPER")
AES_KEY = os.getenv("AES_KEY").encode()
AES_IV = os.getenv("AES_IV").encode()

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


from db_setup import initialize
initialize()


@app.context_processor
def inject_request():
    return dict(request=request)


# Helper function to get a connection to the database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn


@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()

    search_term = request.args.get('search')
    suspicious = False
    products_data = []

    if search_term:
        query = f"SELECT id, name, description, price, image FROM products WHERE name LIKE '%{search_term}%'"
    else:
        query = "SELECT id, name, description, price, image FROM products"

    try:
        cursor.execute(query)
        products = cursor.fetchall()

        products_data = [{
            'id': product['id'],
            'name': product['name'],
            'description': product['description'],
            'price': product['price'],
            'image': product['image']
        } for product in products]

        # ✅ Detection logic: SQLi pattern AND leaked user data
        if search_term:
            search_term = urllib.parse.unquote(search_term)  # URL decode the search term
            if "'" in search_term and "--" in search_term:
                for product in products_data:
                    if "tentaclemail" in product['name'].lower() or "tentaclemail" in product['description'].lower():
                        suspicious = True
                        break
        # ✅ Mark challenge as solved using global "solved" flag
        if suspicious:
            try:
                with sqlite3.connect(CHALLENGE_DB_PATH) as chal_conn:
                    chal_cursor = chal_conn.cursor()
                    chal_cursor.execute("SELECT solved FROM challenges WHERE uuid = '54460c30-2852-4880-bc98-6494d5b31dbe'")
                    row = chal_cursor.fetchone()
                    if row and not row[0]:  # not already solved
                        chal_cursor.execute("UPDATE challenges SET solved = 1 WHERE uuid = '54460c30-2852-4880-bc98-6494d5b31dbe'")
                        chal_conn.commit()
            except sqlite3.Error as e:
                print("[CHALLENGE DB ERROR]", e)
    except Exception as e:
        pass
        #print("[SQL ERROR]", e)

    conn.close()
    return jsonify(products_data)

def create_eml_file(sender, recipients, subject, body, filename="email"):
    if isinstance(recipients, str):
        recipients = [recipients]
    for recipient in recipients:
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
        created_file = 'emails/' + filename + '_' + convertEmailRecipient(recipient) + '.eml'
        print(created_file)
        with open(created_file, 'w') as f:
            f.write(msg.as_string())

def convertEmailRecipient(email):
    #converts an email address to a string that can be used in a file name
    email = re.sub(r'@', '_', email)
    email = re.sub(r'\.', '_', email)
    return email

@app.route("/")
def home():
    if session and session["level"] > 0:
        return render_template("index.html")
    elif session and session["level"] == 0:
        #send the user to the login page
        return render_template("account.html", mfa_level=session["level"])
    else:
        return render_template("account.html", mfa_level=99)

@app.route("/signup", methods=['POST'])
def signup():
    print(request.host)

    template_path = os.path.join(os.path.dirname(__file__), 'email_templates', 'newsletter_welcome.html')
    with open(template_path, 'r') as file:
        body_template = file.read()

    request_data = request.get_json()
    email = request_data["email"]
    username = request_data.get("username", "")
    safe_username = username if username else "there"

    body = body_template.format(
        username=safe_username,
        email_encoded=email,
        request=request
    )

    subject = f'{request.host} Newsletter Signup'
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y_%m_%d_%H_%M_%S")
    filename = formatted_date + '_signup'

    create_eml_file("noreply@tenticleandthrow.local", email, subject, body, filename=filename)

    # 🚨 Detection #1: Host header manipulation
    if request.host not in ["127.0.0.1", "localhost", "tentacleandthrow.local"]:
        with sqlite3.connect(CHALLENGE_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT solved FROM challenges WHERE uuid = '1f8aea60-7fbe-40f5-ae07-2cb720960d34'")
            row = cursor.fetchone()
            if row and not row[0]:
                cursor.execute("UPDATE challenges SET solved = 1 WHERE uuid = '1f8aea60-7fbe-40f5-ae07-2cb720960d34'")
                conn.commit()

    # 🚨 Detection #2: HTML in username (Email Content Injection)
    if "<" in username or ">" in username:
        with sqlite3.connect(CHALLENGE_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT solved FROM challenges WHERE uuid = 'b90cd1c8-09f2-4b9a-93a1-7e62f071551a'")
            row = cursor.fetchone()
            if row and not row[0]:
                cursor.execute("UPDATE challenges SET solved = 1 WHERE uuid = 'b90cd1c8-09f2-4b9a-93a1-7e62f071551a'")
                conn.commit()

    return render_template("signUpThanks.html")



from flask import request

@app.route('/unsubscribe')
def unsubscribe():
    email = request.args.get('email')
    if not email:
        return "Missing email parameter.", 400
    
    # validate email format maybe here
    # perform unsubscribe logic
    return f"Email {email} has been unsubscribed.", 200

# New /results page to list and view .eml files
@app.route("/results")
def results():
    """Render the results page where users can pick an email to view."""
    email_files = [f for f in os.listdir(EMAILS_DIR) if f.endswith(".eml")]
    email_files.sort(reverse=True)  # Sort files by name in reverse order
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
    if session and session.get("level") == 1:
        return render_template("profile.html")
    elif session and session["level"] == 0:
        #send the user to the login page
        return render_template("account.html", mfa_level=session["level"])
    else:
        return render_template("account.html", mfa_level=99)

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
        raw_password = data["password"]
        password = hash_password(raw_password)  # Securely hashed

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                verification_code = generateOTP()

                # Insert user
                cursor.execute('''
                    INSERT INTO users (username, email, password, verified, verification_code)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, email, password, False, verification_code))
                user_id = cursor.lastrowid

                # Create an empty cart for the user
                cursor.execute('''
                    INSERT INTO carts (user_id) VALUES (?)
                ''', (user_id,))
                cart_id = cursor.lastrowid

                # Link user to cart
                cursor.execute('''
                    UPDATE users
                    SET cart = ?
                    WHERE id = ?
                ''', (cart_id, user_id))

                conn.commit()

                # Send verification email
                current_date = datetime.now()
                formatted_date = current_date.strftime("%Y_%m_%d_%H_%M_%S")
                filename = formatted_date + '_register'
                
                template_path = os.path.join(os.path.dirname(__file__), 'email_templates', 'verify.html')
                with open(template_path, 'r') as file:
                    body = file.read()
                    body = body.format(verification_code=verification_code, username=username)

                create_eml_file("noreply@tenticleandthrow.local", email, "Welcome to Tenticle & Throw!", body, filename=filename)

                session["user_id"] = user_id
                session["username"] = username
                session["level"] = 0

                profile_pics_dir = os.path.join("static", "profile_pics", username)
                os.makedirs(profile_pics_dir, exist_ok=True)

                return jsonify({"message": f"Signup successful! Welcome, {username}!"})

            except sqlite3.IntegrityError:
                return jsonify({"message": "Username or email already exists!"}), 400




# Sign-In Route
@app.route("/signin", methods=["POST"])
def signin():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Fetch user, including seeded flag
        cursor.execute("SELECT id, username, email, verified, password, seeded FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            return f'{{"message":"Invalid username."}}', 401

        stored_hash = user[4]  # This is the hashed password from DB
        print('here1')
        if not bcrypt.checkpw((PASSWORD_PEPPER + password).encode(), stored_hash.encode()):
            print("Invalid password")
            return jsonify({"message": "Invalid username or password."}), 401
        print('here')
        if user[3] == 0:
            return f'{{"message":"Please check your email for the verification address"}}', 401    

        # ✅ Account Takeover Detection
        if user[5]:  # seeded == 1
            with sqlite3.connect(CHALLENGE_DB_PATH) as chal_conn:
                chal_cursor = chal_conn.cursor()
                chal_cursor.execute("SELECT solved FROM challenges WHERE uuid = 'ac0f5a78-70ab-44e2-91e7-2875df3f2a63'")
                row = chal_cursor.fetchone()
                if row and not row[0]:
                    chal_cursor.execute("UPDATE challenges SET solved = 1 WHERE uuid = 'ac0f5a78-70ab-44e2-91e7-2875df3f2a63'")
                    chal_conn.commit()

        # Proceed with session
        session["user_id"] = user[0]
        session["username"] = user[1]
        session["token"] = generateOTP()
        session["level"] = 0

        current_date = datetime.now()
        formatted_date = current_date.strftime("%Y_%m_%d_%H_%M_%S")
        filename = formatted_date + '_mfa'

        with open('email_templates/mfa.html', 'r') as file:
            body = file.read()
            token = session['token']
            body = body.format(**locals())

        create_eml_file("noreply@tenticleandthrow.local", user[2], "Tenticle & Throw Login Token", body, filename=filename)

        session.modified = True
        return jsonify({"message": "successful!"}), 200


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    print('/cart/add')
    print(session)
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    product_id = data.get("item")  # item should be product_id

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        print(session["user_id"])
        # Get user's cart_id
        cursor.execute("SELECT id FROM carts WHERE user_id = ?", (session["user_id"],))
        result = cursor.fetchone()
        print(result)

        if not result:
            return jsonify({"error": "Cart not found."}), 404

        cart_id = result[0]

        # Check if item is already in cart_items
        cursor.execute('''
            SELECT quantity FROM cart_items
            WHERE cart_id = ? AND product_id = ?
        ''', (cart_id, product_id))
        item = cursor.fetchone()

        if item:
            # Item already in cart – increment quantity
            new_quantity = item[0] + 1
            cursor.execute('''
                UPDATE cart_items
                SET quantity = ?
                WHERE cart_id = ? AND product_id = ?
            ''', (new_quantity, cart_id, product_id))
        else:
            # Insert new item into cart_items
            cursor.execute('''
                INSERT INTO cart_items (cart_id, product_id, quantity)
                VALUES (?, ?, 1)
            ''', (cart_id, product_id))

        conn.commit()
        return jsonify({"message": f"Product {product_id} added to cart."})


@app.route("/cart", methods=["GET"])
def view_cart():
    if "user_id" not in session:
        return render_template("account.html", mfa_level=99)

    # 🚨 Detection: Forced browsing without completing MFA
    if session.get("level", 0) == 0:
        with sqlite3.connect(CHALLENGE_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT solved FROM challenges WHERE uuid = '2ba998c0-d788-4a85-97ff-61e14ec08993'")
            row = cursor.fetchone()
            if row and not row[0]:
                cursor.execute("UPDATE challenges SET solved = 1 WHERE uuid = '2ba998c0-d788-4a85-97ff-61e14ec08993'")
                conn.commit()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        print(session["user_id"])

        # Get the user's cart ID
        cursor.execute("SELECT id FROM carts WHERE user_id = ?", (session["user_id"],))
        cart_row = cursor.fetchone()
        print(cart_row)
        if not cart_row:
            return jsonify({"error": "Cart not found."}), 404

        cart_id = cart_row["id"]

        # Get all items in the cart with product info
        cursor.execute('''
            SELECT 
                p.id AS product_id,
                p.name,
                p.description,
                p.price,
                p.image,
                ci.quantity
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.cart_id = ?
        ''', (cart_id,))

        items = [dict(row) for row in cursor.fetchall()]
        return jsonify(items)


@app.route("/cart/view")
def view_cart_page():
    if "user_id" not in session:
        return render_template("account.html", mfa_level=99)
    return render_template("cart.html")

@app.route("/support", methods=["POST"])
def support():
    data = request.get_json()
    support_email = data["variables"]["email_addr"]
    email_body = data["variables"]["body"]
    email_subject = data["variables"]["subject"]

    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y_%m_%d_%H_%M_%S")
    filename = formatted_date + '_support'

    create_eml_file("support@tenticleandthrow.local", support_email, email_subject, email_body, filename=filename)

    # 🚨 Detection: attacker has changed the recipient
    if support_email.strip().lower() != "support@tentacleandthrow.local":
        with sqlite3.connect(CHALLENGE_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT solved FROM challenges WHERE uuid = 'ea3dccb4-9ce3-49ae-a042-4b105e0a4cb0'")
            row = cursor.fetchone()
            if row and not row[0]:
                cursor.execute("UPDATE challenges SET solved = 1 WHERE uuid = 'ea3dccb4-9ce3-49ae-a042-4b105e0a4cb0'")
                conn.commit()

    return jsonify({"successful": "200"})


@app.route("/products", methods=["GET"])
def products():
    if session and session["level"] > 0:
        return render_template("products.html")
    elif session and session["level"] == 0:
        #send the user to the login page
        return render_template("account.html", mfa_level=session["level"])
    else:
        return render_template("account.html", mfa_level=99)

@app.route("/mfa", methods=["GET", "POST"])
def mfa():
    print('mfa')
    data = request.get_json()
    mfa_input = data.get("mfa", "")

    if "mfa_attempts" not in session:
        session["mfa_attempts"] = 0

    session["mfa_attempts"] += 1
    print("MFA attempt count:", session["mfa_attempts"])
    
    if session["token"] == mfa_input:
        # ✅ Detection: excessive attempts (e.g., >5)
        if session["mfa_attempts"] > 5:
            with sqlite3.connect(CHALLENGE_DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT solved FROM challenges WHERE uuid = '8e8efb73-1d72-4f23-bac0-79bb567876b1'")
                row = cursor.fetchone()
                if row and not row[0]:
                    cursor.execute("UPDATE challenges SET solved = 1 WHERE uuid = '8e8efb73-1d72-4f23-bac0-79bb567876b1'")
                    conn.commit()

        session["level"] = 1
        session.pop("mfa_attempts", None)  # Reset
        return jsonify({"successful": "200"})
    else:
        return jsonify({"unsuccessful": "200"})


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    reset_code = request.args.get("reset_code")

    if request.method == "GET":
        if not reset_code:
            return "Missing reset code", 400

        # Verify the reset_code is valid before showing the form
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            print(type(reset_code))
            cursor.execute("SELECT id, email FROM users WHERE forgot_password_code = ?", (reset_code,))
            user = cursor.fetchone()

        if not user:
            return "Invalid reset link", 400

        user_id, email = user  # Unpack user information

        return render_template("reset_password_form.html", email=email, reset_code=reset_code)

    elif request.method == "POST":
        #get new_password from JSON
        data = request.get_json()
        new_password = data.get("new_password")
        email = data.get("email")
        reset_code = data.get("reset_code")

        if not new_password:
            return "Password cannot be empty", 400

        # Optional: Hash password here
        #hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
        hashed_password = new_password
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET password = ?, forgot_password_code = ''
                WHERE email = ? AND forgot_password_code = ?
            """, (hashed_password, email, reset_code))
            conn.commit()
        
        # return {"success": "Password reset successful!"}
        return jsonify({"success": "Password reset successful!"})

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        data = request.get_json()
        email = data["email"]

        if not email:
            return "Email is required.", 400

        reset_code = generateOTP()  # 6-digit random number

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

            if not user:
                return "Email not found.", 404

            # Save the reset code
            cursor.execute('''
                UPDATE users
                SET forgot_password_code = ?
                WHERE email = ?
            ''', (reset_code, email))
            conn.commit()

        # Build the reset link
        reset_link = f"{request.host_url}reset_password?email={urllib.parse.quote(email)}&reset_code={reset_code}"

        # Load the HTML template
        template_path = os.path.join(os.path.dirname(__file__), 'email_templates', 'reset_password.html')
        with open(template_path, 'r') as file:
            body_template = file.read()

        # Insert the reset link into the template
        body = body_template.format(reset_link=reset_link)

        # Save it as a .eml file
        current_date = datetime.now()
        formatted_date = current_date.strftime("%Y_%m_%d_%H_%M_%S")
        filename = f"{formatted_date}_password_reset"

        create_eml_file(
            sender="noreply@tentacleandthrow.local",
            recipients=email,
            subject="Tentacle & Throw Password Reset",
            body=body,
            filename=filename
        )

        # return {success: "200"}
        return jsonify({"success": "Password reset email sent!"})

    return render_template("forgot_password.html")


@app.route('/verify')
def verify():
    code = request.args.get('verfication_code')  # note typo: 'verfication_code'
    if not code:
        return "Invalid or missing verification code.", 400

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, verified FROM users WHERE verification_code = ?", (code,))
        user = cursor.fetchone()
        print(user)
        if user:
            if user[1]:
                return "Your email has already been verified."
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                # Update the user's verified status
                
                cursor.execute("UPDATE users SET verified = 1 WHERE id = ?", (user[0],))
                conn.commit()
                #redirect to the app root
                #this counts as mfa update the session level
                session["level"] = 1
                return redirect('/')
        else:
            return "Invalid verification code.", 404


@app.route("/update_cart", methods=["POST"])
def update_cart():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    product_id = data.get("product_id")
    action = data.get("action")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Get user's cart_id
        cursor.execute("SELECT id FROM carts WHERE user_id = ?", (session["user_id"],))
        cart_row = cursor.fetchone()
        if not cart_row:
            return jsonify({"error": "Cart not found"}), 404

        cart_id = cart_row[0]

        # Get current quantity
        cursor.execute("SELECT quantity FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, product_id))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Item not in cart"}), 404

        current_qty = row[0]
        new_qty = current_qty + 1 if action == "increase" else max(1, current_qty - 1)
        print(new_qty)
        cursor.execute("UPDATE cart_items SET quantity = ? WHERE cart_id = ? AND product_id = ?", (new_qty, cart_id, product_id))
        conn.commit()

        return jsonify({"new_quantity": new_qty})

@app.route("/cart/delete", methods=["POST"])
def delete_cart_item():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    product_id = data.get("product_id")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM carts WHERE user_id = ?", (session["user_id"],))
        cart = cursor.fetchone()
        if not cart:
            return jsonify({"error": "Cart not found"}), 404

        cart_id = cart[0]

        cursor.execute("DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, product_id))
        conn.commit()

        return jsonify({"success": True})

def sanitize_comment(text):
    # Strip dangerous tags
    text = re.sub(r'</?(script|img|iframe|object|embed|link|style|svg|math|base)[^>]*?>', '', text, flags=re.IGNORECASE)
    
    # Strip on* event handlers (like onclick=, onload=, etc.)
    text = re.sub(r'\son\w+\s*=\s*"[^"]*"', '', text, flags=re.IGNORECASE)
    text = re.sub(r"\son\w+\s*=\s*'[^']*'", '', text, flags=re.IGNORECASE)

    # Remove style and javascript: or data: URLs
    text = re.sub(r'style\s*=\s*["\'].*?["\']', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(src|href)\s*=\s*["\']\s*(javascript|data):[^"\']*["\']', '', text, flags=re.IGNORECASE)

    return text


@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_page(product_id):
    if session and session["level"] == 0:
        mfa_level = session.get("level", 0)
        return render_template("account.html", mfa_level=mfa_level)
    if request.method == 'POST':
        commenter_name = request.form['commenter_name']
        comment_text = request.form['comment_text']
        # Sanitize the comment text
        comment_text = sanitize_comment(comment_text)
        commenter_name = sanitize_comment(commenter_name)
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO comments (product_id, name, text) VALUES (?, ?, ?)
            ''', (product_id, commenter_name, comment_text))

        return redirect(f'/product/{product_id}')

    # On GET, load the product and its comments
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT name, text FROM comments WHERE product_id = ?', (product_id,))
        comments = cursor.fetchall()

        cursor.execute('SELECT id, name, price, description, image FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()

    return render_template('product.html', product=product, comments=comments)


# --- Stub for Luhn algorithm card validation ---
def validate_card_number(card_number):
    print(card_number)
    def luhn_checksum(card_number):
        def digits_of(n):
            return [int(d) for d in str(n)]
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10

    return luhn_checksum(card_number) == 0

# --- Checkout Route ---
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "GET":
        return render_template("checkout.html")

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in."}), 401

    data = request.get_json()
    shipping_address = data.get('shipping_address')
    billing_address = data.get('billing_address')

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Fetch user info
            cursor.execute('SELECT username, email, cart FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "User not found."}), 404

            full_name = user['username']
            email = user['email']
            cart_id = user['cart']
            if not cart_id:
                return jsonify({"error": "No cart found for user."}), 400

            # Get cart items
            cursor.execute('''
                SELECT products.id, products.name, products.price, cart_items.quantity
                FROM cart_items
                JOIN products ON cart_items.product_id = products.id
                WHERE cart_items.cart_id = ?
            ''', (cart_id,))
            cart_items = cursor.fetchall()
            if not cart_items:
                return jsonify({"error": "Your cart is empty."}), 400

            # Insert new order
            cursor.execute('''
                INSERT INTO orders (user_id, full_name, email, shipping_address, billing_address)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, full_name, email, shipping_address, billing_address))
            order_id = cursor.lastrowid

            # Insert order items
            for item in cart_items:
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    order_id,
                    item['id'],
                    item['name'],
                    item['quantity'],
                    item['price']
                ))

            # Clear the cart
            cursor.execute('DELETE FROM cart_items WHERE cart_id = ?', (cart_id,))
            conn.commit()

            return jsonify({"message": "Checkout successful!"})

    except Exception as e:
        print("[ERROR] Checkout failed:", e)
        return jsonify({"error": "Checkout failed. Please try again."}), 500

@app.route("/test", methods=["GET"])
def profile_v2():
    return render_template("profile2.html")

@app.route('/api/profile')
def get_profile():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, email, shipping_address, billing_address,
                   card_number, card_expiration, profile_picture_url
            FROM users WHERE id = ?
        ''', (user_id,))
        row = cursor.fetchone()

    if not row:
        return jsonify({"error": "User not found"}), 404

    username, email, shipping, billing, encrypted_card, exp, profile_picture_url = row

    try:
        if encrypted_card:
            card = decrypt_card(encrypted_card)
        else:
            card = None
    except Exception:
        card = "[DECRYPTION FAILED]"

    pic_url = profile_picture_url or "/static/profile_pics/default.png"

    return jsonify({
        "id": user_id,
        "username": username,
        "email": email,
        "shipping_address": shipping,
        "billing_address": billing,
        "card_number": card,
        "card_expiration": exp,
        "profile_picture": pic_url
    })



@app.route("/api/orders", methods=["GET"])
def get_orders():
    user_id = session.get('user_id')

    if not user_id:
        return jsonify([])

    orders_data = []

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Step 1: Get all orders for this user
            cursor.execute('''
                SELECT id, full_name, email, shipping_address, billing_address, order_time, status
                FROM orders
                WHERE user_id = ?
                ORDER BY order_time DESC
            ''', (user_id,))
            orders = cursor.fetchall()

            for order in orders:
                order_id = order['id']

                # Step 2: Get items for this order
                cursor.execute('''
                    SELECT product_name, quantity, price
                    FROM order_items
                    WHERE order_id = ?
                ''', (order_id,))
                items = cursor.fetchall()

                orders_data.append({
                    'id': order_id,
                    'full_name': order['full_name'],
                    'email': order['email'],
                    'shipping_address': order['shipping_address'],
                    'billing_address': order['billing_address'],
                    'order_time': order['order_time'],
                    'status': order['status'],
                    'items': [
                        {
                            'product_name': item['product_name'],
                            'quantity': item['quantity'],
                            'price': item['price']
                        } for item in items
                    ],
                    'total': sum(item['price'] * item['quantity'] for item in items)
                })

        return jsonify(orders_data)

    except Exception as e:
        print("[ERROR] Failed to load orders:", e)
        return jsonify([]), 500


@app.route("/logout")
def logout():
    session.clear()  # Wipe out the session (logs user out completely)
    return redirect(url_for('account'))  # Redirect them back to your login/signup page


def get_user_from_db(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('''
            SELECT username, email, shipping_address, billing_address, card_number
            FROM users
            WHERE id = ?
        ''', (user_id,))
        return cur.fetchone()

@app.route('/api/profile/update', methods=["POST"])
def update_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({}), 401

    data = request.get_json()
    field_mapping = {
        'email': 'email',
        'shipping_address': 'shipping_address',
        'billing_address': 'billing_address',
        'card_number': 'card_number',
        'card_expiration': 'card_expiration'
    }

    field_to_update = None
    value = None

    for key, db_field in field_mapping.items():
        if key in data:
            field_to_update = db_field
            value = data[key]
            if key == "card_number":
                value = encrypt_card(value)  # Encrypt before storage
            break

    if not field_to_update:
        return jsonify({"error": "Invalid field."}), 400

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            UPDATE users
            SET {field_to_update} = ?
            WHERE id = ?
        ''', (value, user_id))
        conn.commit()

    return jsonify({"message": "Profile updated successfully!"})


import requests

@app.route('/api/profile/picture', methods=['POST'])
def upload_profile_picture():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()

    if not result:
        return jsonify({"error": "User not found"}), 404

    username = result[0]
    user_dir = os.path.join("static", "profile_pics", username)
    os.makedirs(user_dir, exist_ok=True)

    # Check if user provided a file or a URL
    if 'picture' in request.files:
        file = request.files['picture']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        filepath = os.path.join(user_dir, file.filename)
        file.save(filepath)

    elif request.is_json and 'url' in request.json:
        url = request.json['url']

        # SSRF vulnerability: the server blindly fetches the URL
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return jsonify({"error": "Could not fetch remote image"}), 400

        filename = os.path.basename(url.split("?")[0])
        filepath = os.path.join(user_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(response.content)

    else:
        return jsonify({"error": "No picture or URL provided"}), 400

    # Store path in DB
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET profile_picture_url = ?
            WHERE id = ?
        ''', (filepath, user_id))
        conn.commit()

    return jsonify({"message": f"Uploaded to {filepath}"}), 200

@app.route("/api/profile/email", methods=["GET"])
def email_profile():
    user_id = session.get("user_id")
    if not user_id:
        return "User not logged in", 403

    # Fetch user from DB
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, email, shipping_address, profile_picture_url
            FROM users WHERE id = ?
        """, (user_id,))
        row = cursor.fetchone()

    if not row:
        return "User not found", 404

    # Load injected HTML from user-controlled file path
    pic_path = row["profile_picture_url"]  # e.g. "../../static/uploads/evil.html"
    try:
        with open(pic_path, "r") as f:
            profile_pic_html = f.read()
    except Exception as e:
        profile_pic_html = f"<p>Could not load profile picture: {e}</p>"

    # Render email with raw HTML injection
    body = render_template(
        "profile.html",
        username=row["username"],
        email=row["email"],
        shipping_address=row["shipping_address"],
        profile_picture_url=profile_pic_html  # 🚨 Injecting file contents directly
    )

    # Save email to .eml using create_eml_file function
    eml_path = f"profile_email_{user_id}"

    subject = f'Your Tentacle and Throw Profile'
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y_%m_%d_%H_%M_%S")
    filename = formatted_date + '_signup'
    create_eml_file("noreply@tenticleandthrow.local", row["email"], subject, body, filename=filename)

    return f"Check your email for your profile information!", 200

@app.route('/api/challenges', methods=['GET'])
def get_challenges():
    with sqlite3.connect(CHALLENGE_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, uuid, name, description, points, category, solved FROM challenges")
        all_challenges = cursor.fetchall()

    grouped = {}
    for row in all_challenges:
        entry = {
            'id': row['id'],
            'uuid': row['uuid'],
            'name': row['name'],
            'description': row['description'],
            'points': row['points'],
            'solved': bool(row['solved'])
        }
        grouped.setdefault(row['category'], []).append(entry)

    output = []
    for category, challenges in grouped.items():
        output.append({
            'category': category,
            'solved': sum(1 for c in challenges if c['solved']),
            'total': len(challenges),
            'challenges': challenges
        })

    return jsonify(output)

@app.route('/api/submit_solution', methods=['POST'])
def submit_solution():
    data = request.get_json()
    challenge_id = data.get('challenge_id')

    if not challenge_id:
        return jsonify({'success': False, 'message': 'Missing challenge ID'}), 400

    with sqlite3.connect(CHALLENGE_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT solved FROM challenges WHERE id = ?", (challenge_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({'success': False, 'message': 'Challenge not found'}), 404

        if row[0]:  # already solved
            return jsonify({'success': False, 'message': 'Already solved'}), 400

        cursor.execute("UPDATE challenges SET solved = 1 WHERE id = ?", (challenge_id,))
        conn.commit()

    return jsonify({'success': True, 'message': 'Challenge marked as solved'})




@app.route('/scoreboard', methods=['GET'])
def scoreboard():
    with sqlite3.connect(CHALLENGE_DB_PATH) as conn:
        cursor = conn.cursor()

        # Total points possible
        cursor.execute("SELECT SUM(points) FROM challenges")
        total_possible = cursor.fetchone()[0] or 0

        # Points from solved challenges
        cursor.execute("SELECT SUM(points) FROM challenges WHERE solved = 1")
        total_solved = cursor.fetchone()[0] or 0

    return render_template("scoreboard.html", total=total_possible, solved=total_solved)


@app.route('/api/solve/<uuid>', methods=['POST'])
def solve_challenge_by_uuid(uuid):
    with sqlite3.connect(CHALLENGE_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, solved FROM challenges WHERE uuid = ?", (uuid,))
        row = cursor.fetchone()

        if not row:
            return jsonify({'success': False, 'message': 'Challenge not found'}), 404

        if row[1]:
            return jsonify({'success': False, 'message': 'Already solved'}), 400

        cursor.execute("UPDATE challenges SET solved = 1 WHERE uuid = ?", (uuid,))
        conn.commit()

    return jsonify({'success': True, 'message': 'Challenge marked as solved'})





if __name__ == "__main__":
    app.run(debug=True)

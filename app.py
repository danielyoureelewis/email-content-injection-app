#! /usr/local/bin/python
from flask import Flask, render_template, jsonify, request, session, redirect
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

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

EMAILS_DIR = "emails"  # Directory where .eml files are stored
DB_PATH = "app.db"

@app.context_processor
def inject_request():
    return dict(request=request)

def insert_initial_products():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        products = [
            (
                '/static/assets/images/products/elder_bites.png',
                'Elder Bites – Tentacly Good!',
                'Start your day with a spoonful of madness! These cosmic crunchies swirl with ancient flavor and come with a free Elder Sign Fun Pack. Tentacles not included... or are they?',
                24.99
            ),
            (
                '/static/assets/images/products/toaster.png',
                'Great Old Toaster – R’lyeh Toast!',
                'This sanity-defying toaster brings the Great Old Ones to your breakfast table. Every slice drives you a little more mad... and that\'s before the butter hits. Make mornings mythos-worthy!',
                29.99
            ),
            (
                '/static/assets/images/products/ottoman.png',
                'Esoteric Ottoman of Ulthar',
                'An ottoman that whispers secrets when you rest your feet. Lose a memory, gain forbidden knowledge. Upholstered in interdimensional feline velvet.',
                89.99
            ),
            (
                '/static/assets/images/products/coffee_press.png',
                'Cthulhu’s Coffee Press',
                'Brew eldritch espresso with this kraken-bone French press. Produces the blackest brew this side of R’lyeh. Not responsible for psychic awakenings.',
                39.99
            ),
            (
                '/static/assets/images/products/candle_set.png',
                'Necronomican Candle Set',
                '“Crypt Dust,” “Blood of Shoggoth,” and “Eldritch Gardenia.” Smells like doom, and maybe vanilla. Glyphs appear as wax melts—don’t chant them!',
                19.99
            ),
            (
                '/static/assets/images/products/throw_blanket.png',
                'Whispering Throw Blanket',
                'Soft, warm, and occasionally mumbles in long-dead languages. Not recommended for insomniacs. Do not launder lest ye anger the weave.',
                49.99
            ),
            (
                '/static/assets/images/products/storage_cubes.png',
                'Yog-Sothoth’s Modular Storage Cubes',
                'Organize your soul. Infinite configurations. Improper arrangement may cause temporal overlap. Great for tomes or cursed tchotchkes.',
                59.99
            ),
            (
                '/static/assets/images/products/shower_curtain.png',
                'Shub-Niggurath Shower Curtain',
                'Adorned with the Black Goat of the Woods. Bleeds ichor during full moons. May scream if drawn too fast.',
                34.99
            ),
            (
                '/static/assets/images/products/dishware.png',
                'Innsmouth Dishware Collection',
                'Fishy plates that evolve the longer you use them. Cups mutter sea-chants. Comes with complimentary dread.',
                74.99
            ),
            (
                '/static/assets/images/products/area_rug.png',
                'Carpet of the Crawling Chaos',
                'A rug that grows with your nightmares. Subtly moves underfoot. Excellent for summoning or lounging.',
                129.99
            ),
            (
                '/static/assets/images/products/sleep_mask.png',
                'Azathoth’s Sleep Mask',
                'Blocks light, sound, and rational thought. Dreamless, timeless sleep guaranteed. Comes in Void Black.',
                17.99
            ),
            (
                '/static/assets/images/products/air_purifier.png',
                'Eldritch Air Purifier',
                'Purifies air—and spirits. Emits a low-frequency whimper. Blessed and cursed for optimal effect.',
                99.99
            )
        ]

        cursor.executemany('''INSERT INTO products (image, name, description, price)
                              VALUES (?, ?, ?, ?)''', products)

        conn.commit()
        print("[INFO] Initial products inserted.")



def init_db():
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Create users table
            cursor.execute('''CREATE TABLE users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                email TEXT UNIQUE NOT NULL,
                                username TEXT NOT NULL,
                                password TEXT NOT NULL,
                                mfa INTEGER,
                                verified BOOL NOT NULL,
                                verification_code TEXT NOT NULL,
                                forgot_password_code TEXT,
                                cart INTEGER)''')

            # Create carts table
            cursor.execute('''CREATE TABLE IF NOT EXISTS carts (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                FOREIGN KEY (user_id) REFERENCES users(id))''')

            # Create cart_items table with quantity support
            cursor.execute('''CREATE TABLE IF NOT EXISTS cart_items (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                cart_id INTEGER NOT NULL,
                                product_id INTEGER NOT NULL,
                                quantity INTEGER NOT NULL DEFAULT 1,
                                FOREIGN KEY (cart_id) REFERENCES carts(id),
                                FOREIGN KEY (product_id) REFERENCES products(id),
                                UNIQUE(cart_id, product_id))''')

            # Create products table
            cursor.execute('''CREATE TABLE products (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                image TEXT NOT NULL,
                                name TEXT NOT NULL,
                                description TEXT NOT NULL,
                                price REAL NOT NULL)''')

            conn.commit()
            print("[INFO] Database initialized.")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products LIMIT 1")
    rows = cursor.fetchall()
    if not rows:
        insert_initial_products()

# Call this on startup
init_db()



# Helper function to get a connection to the database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn


@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the search term from the query parameters, if it exists
    search_term = request.args.get('search')  
    
    if search_term:
        # If there is a search term, filter products by name
        query = f"SELECT id, name, description, price, image FROM products WHERE name LIKE '%{search_term}%'"
    else:
        # If no search term, get all products
        query = "SELECT id, name, description, price, image FROM products"
    
    cursor.execute(query)  # Execute the query
    products = cursor.fetchall()
    
    # Format the result into a list of dictionaries
    products_data = [{
        'id': product['id'],
        'name': product['name'],
        'description': product['description'],
        'price': product['price'],
        'image': product['image']
    } for product in products]
    
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
    return render_template("index.html")

@app.route("/signup", methods=['POST'])
def signup():
    print(request.host)
    if request.method == 'POST':
        content = (
                    f'Thank you for subscribing to the Tentacle & Throw newsletter.<br><br>'
                    f'We’re excited to keep you informed about our latest updates, insights, and offerings.<br><br>'
                    f'If you prefer not to receive future communications, you may unsubscribe at any time by clicking '
                    f'<a href="http://{request.host}/unsubscribe/{urllib.parse.quote(request.json["email"])}">here</a>.<br><br>'
                    f'If you have any questions or concerns, feel free to reach out via our '
                    f'<a href="http://127.0.0.1/contact">contact page</a>.<br><br>'
                    f'<small>This email was sent by Tentacle & Throw. You are receiving this message because you opted in to receive '
                    f'communications from us. If you believe this was sent in error, please unsubscribe or contact us. '
                    f'Please do not reply to this email. For full details, see our terms and privacy policy on our website.</small>'
                )
        subject = f'{request.host} Newsletter Signup'
        current_date = datetime.now()
        formatted_date = current_date.strftime("%Y_%m_%d_%H_%M_%S")
        filename = formatted_date + '_signup'
        create_eml_file("noreply@tenticleandthrow.local", request.json["email"], subject, content, filename=filename)
        return render_template("signUpThanks.html")
    else:
        print('else')

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
    return render_template("account.html")

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

                conn.commit()

                # Create verification email
                current_date = datetime.now()
                formatted_date = current_date.strftime("%Y_%m_%d_%H_%M_%S")
                filename = formatted_date + '_register'
                
                template_path = os.path.join(os.path.dirname(__file__), '..', 'email_templates', 'verify.html')
                with open(template_path, 'r') as file:
                    body = file.read()
                    body = body.format(**locals())

                create_eml_file("noreply@tenticleandthrow.local", email, "Welcome to Tenticle & Throw!", body, filename=filename)

                return jsonify({"message": f"Signup successful! Welcome, {username}!"})
            
            except sqlite3.IntegrityError:
                return jsonify({"message": f"Username or email already exists!"}), 400


# Sign-In Route
@app.route("/signin", methods=["POST"])
def signin():
    if request.method == "POST":
        data = request.get_json()
        username = data["username"]
        password = data["password"]

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email, verified FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()
            if user[3] == 0:
                return f'{{"message":"Please verify your email address."}}', 401    
        if user:
            email = user[2]
            username = user[1]
            session["user_id"] = user[0]  # Store user_id in session
            session["username"] = username
            session["token"] = generateOTP()
            session["level"] = 0
            current_date = datetime.now()
            formatted_date = current_date.strftime("%Y_%m_%d_%H_%M_%S")
            filename = formatted_date + '_mfa'
            with open('email_templates/mfa.html', 'r') as file:
                body = file.read()
                token = session['token']
                body = body.format(**locals())
                print(body)
            create_eml_file("noreply@tenticleandthrow.local", email, "Tenticle & Throw Login Token", body, filename=filename)
            return jsonify({"successful":"200"})
        else:
            return f'{{"message":"Invalid username or password."}}', 401

@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    print('/cart/add')
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    product_id = data.get("item")  # item should be product_id

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Get user's cart_id
        cursor.execute("SELECT id FROM carts WHERE user_id = ?", (session["user_id"],))
        result = cursor.fetchone()
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
        return jsonify({"error": "You must be signed in to view your cart."}), 401

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the user's cart ID
        cursor.execute("SELECT id FROM carts WHERE user_id = ?", (session["user_id"],))
        cart_row = cursor.fetchone()
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
        return "You must be signed in to view your cart.", 401
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

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    
    reset_code = request.args.get("reset_code")

    if request.method == "GET":
        if not reset_code:
            return "Missing email or reset code", 400

        # Optionally, verify the reset_code is valid before showing the form
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE forgot_password_code = ?", (reset_code))
            user = cursor.fetchone()

        if not user:
            return "Invalid reset link", 400

        return render_template("reset_password_form.html", email=email, reset_code=reset_code)

    elif request.method == "POST":
        new_password = request.form.get("new_password")

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

        return redirect(url_for("login"))  # or return a message like "Password reset!"


@app.route('/verify')
def verify():
    code = request.args.get('verfication_code')  # note typo: 'verfication_code'
    if not code:
        return "Invalid or missing verification code.", 400

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE verification_code = ?", (code,))
    user = cursor.fetchone()

    if user:
        if user['verified']:
            return "Your email has already been verified."
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Update the user's verified status
            cursor.execute("UPDATE users SET verified = 1 WHERE id = ?", (user['id'],))
            db.commit()
            #redirect to the app root
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


@app.route('/product/<int:product_id>')
def product_view(product_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, image, name, description, price FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()

    if product:
        product_data = {
            "id": product[0],
            "image": product[1],
            "name": product[2],
            "description": product[3],
            "price": product[4],
        }
        return render_template('product.html', product=product_data)
    else:
        return "Product not found", 404


if __name__ == "__main__":
    
    app.run(debug=True)

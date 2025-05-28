# you can delete this file after initialization. It contains some unencrypted data that breaks some of the challenges. 
#If you are just using this for personal use then don't look in here!
import os
import sqlite3
import random
import uuid
from config import DB_PATH, CHALLENGE_DB_PATH
from crypto_utils import hash_password, encrypt_card

import os
import random
import sqlite3
from crypto_utils import hash_password, encrypt_card
from config import DB_PATH

def insert_initial_users():
    if not os.path.exists(DB_PATH):
        print("[ERROR] Database not found. Please initialize first.")
        return

    first_names = [
        "Ezra", "Thaddeus", "Abigail", "Lucien", "Selene", "Orin", "Nyssa", "Caleb", "Evangeline", "Malachi",
        "Rowena", "Alaric", "Isadora", "Gideon", "Vesper", "Nerissa", "Silas", "Lavinia", "Basil", "Corwin",
        "Verena", "Obed", "Zebulon", "Lilith", "Ambrose", "Cassandra", "Althea", "Phineas", "Mercy", "Tobias"
    ]

    last_names = [
        "Marsh", "Pickman", "Derleth", "West", "Ward", "Whateley", "Carter", "Curwen", "Asenath", "Suydam",
        "Gilman", "Bishop", "Waite", "Hyde", "Allen", "Peabody", "Fenner", "Slater", "Rice", "Chalmers"
    ]

    streets = [
        "Arkham Street", "Kingsport Avenue", "Miskatonic Road", "Innsmouth Lane", "Dunwich Boulevard", "R'lyeh Drive",
        "Leng Terrace", "Dagon Street", "Cyclopean Way", "Elder Circle", "Cthulhu Crescent", "Nyarlathotep Court"
    ]

    cities = [
        "Arkham", "Innsmouth", "Kingsport", "Dunwich", "Salem",
        "Providence", "Newburyport", "Aylesbury", "Witch Hill", "R'lyeh"
    ]

    states = ["MA", "RI", "VT", "NH", "CT", "ME"]

    easy_passwords = ["password123", "tentacles", "eldritch", "deepone", "shubniggurath", "cthulhu"]

    medium_passwords = [
        "Arkham42!", "Innsmouth7", "DeepOne77", "ElderThing2024",
        "Miskatonic88", "DagonRise", "Yithian99", "Salem#31", "CurwenHouse2023"
    ]

    hard_passwords = [
        "V3ryD3ep$LeEp", "Nyarl4!2024", "WhispeR#990", "Sh0gg0th!Wave", "D@gonRise88",
        "B3y0nd#Th3#St4rs", "Unsp3@k4bl3H0rr0r", "Cycl0p3@nD3pths", "L4v1ni@~Dark", "Ph'nglui#2025"
    ]

    email_domains = [
        "tentaclemail.com", "innsmouth.net", "miskatonic.edu",
        "arkham.org", "dunwich.biz", "cthulhu.online", "leng.co"
    ]


    username_patterns = [
        lambda f, l: f"{f.lower()}{l.lower()}",
        lambda f, l: f"{f[0].lower()}{l.lower()}",
        lambda f, l: f"{l.lower()}.{f.lower()}",
        lambda f, l: f"{f.lower()}_{l.lower()}",
        lambda f, l: f"{f.lower()}.{l.lower()}"
    ]

    def generate_card_number():
        start = random.choice(["4", "5"])
        card = [int(x) for x in (start + "".join([str(random.randint(0, 9)) for _ in range(14)]))]

        checksum = 0
        reversed_digits = card[::-1]
        for idx, num in enumerate(reversed_digits):
            if idx % 2 == 0:
                double = num * 2
                if double > 9:
                    double -= 9
                checksum += double
            else:
                checksum += num
        check_digit = (10 - (checksum % 10)) % 10
        return int("".join(map(str, card)) + str(check_digit))

    users = set()

    # Add the static spooky user
    static_email = "lavinia.whateley@arkham.org"
    static_username = "lavinia.whateley"
    static_password = "YogSothoth4Ever!"
    static_card = "0666192819840000"
    static_shipping = "1313 Arkham Street, Arkham, MA 01913"
    static_expiration = "06/2066"

    users.add((
        static_email,
        static_username,
        hash_password(static_password),
        1, 1, "000000", None, None,
        static_shipping, static_shipping,
        encrypt_card(static_card), static_expiration, True
    ))

    while len(users) < 100:
        first = random.choice(first_names)
        last = random.choice(last_names)

        pattern = random.choice(username_patterns)
        username = pattern(first, last)
        username += str(random.randint(1, 9999))

        if username in {u[1] for u in users}:
            continue

        domain = random.choice(email_domains)
        email = f"{username}@{domain}"

        difficulty = random.choices(['easy', 'medium', 'hard'], weights=[0.3, 0.5, 0.2])[0]
        password = random.choice({
            'easy': easy_passwords,
            'medium': medium_passwords,
            'hard': hard_passwords
        }[difficulty])

        shipping_address = f"{random.randint(100, 9999)} {random.choice(streets)}, {random.choice(cities)}, {random.choice(states)} {random.randint(10000, 99999)}"
        billing_address = shipping_address
        card_number = generate_card_number()
        expiration_month = str(random.randint(1, 12)).zfill(2)
        expiration_year = random.randint(2026, 2030)
        card_expiration = f"{expiration_month}/{expiration_year}"

        users.add((
            email, username, hash_password(password), random.choice([0, 1]), 1, "000000",
            None, None, shipping_address, billing_address,
            encrypt_card(str(card_number)), card_expiration, True
        ))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO users (
                email, username, password, mfa, verified, verification_code,
                forgot_password_code, cart,
                shipping_address, billing_address,
                card_number, card_expiration, seeded
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', list(users))

        conn.commit()
        print(f"[INFO] Inserted {len(users)} initial users including the static spooky one.")


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
                '/static/assets/images/products/dimensional_cheese_grater.png',
                'Dimensional Cheese Grater',
                'Shreds cheese—and sanity—across multiple planes. Sometimes grates things you didn’t insert. Handle may whisper recipes not meant for mortals.',
                27.77
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



def init_challenges_db():
    with sqlite3.connect(CHALLENGE_DB_PATH) as conn:
        cursor = conn.cursor()

        # --- Create tables ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT,
                name TEXT NOT NULL,
                description TEXT,
                points INTEGER NOT NULL,
                category TEXT,
                solved BOOLEAN DEFAULT 0
            );
        ''')

        # --- Seed example challenges ---
        challenges = [
            {
                "uuid":"e0529936-76bb-410f-8ef4-b913624a3c4d",
                "name": "Runes of Unfiltered Power",
                "description": "Trigger a stored XSS vulnerability that executes JavaScript.",
                "points": 100,
                "category": "A03 - Injection",
            },
            {
                "uuid":"54460c30-2852-4880-bc98-6494d5b31dbe",
                "name": "Union of the nameless ones",
                "description": "Extract data using classic SQL injection.",
                "points": 150,
                "category": "A03 - Injection",
            },
            {
                "uuid":"b90cd1c8-09f2-4b9a-93a1-7e62f071551a",
                "name": "Names of the dead",
                "description": "Inject content into a templated email that gets sent to users.",
                "points": 200,
                "category": "A03 - Injection",
            },
            {
                "uuid":"ea3dccb4-9ce3-49ae-a042-4b105e0a4cb0",
                "name": "Help",
                "description": "Change the destination of an email that gets sent to users.",
                "points": 200,
                "category": "A03 - Injection",
            }, 
            {
                #TODO password reset
                "uuid":"4bfe14d1-539a-45d7-ab0c-2aab1b0985f6",
                "name": "The Forgotten",
                "description": "Change the destination of an email that gets sent to users.",
                "points": 200,
                "category": "A03 - Injection",
            },
            {
                "uuid":"1f8aea60-7fbe-40f5-ae07-2cb720960d34",
                "name": "Hosts",
                "description": "Alter links in an email that gets sent to users.",
                "points": 200,
                "category": "A03 - Injection",
            },
            {
                "uuid":"d1f8c2b4-9ce3-49ae-a042-4b105e0a4cb0",
                "name": "The Cost Beyond Measure",
                "description": "A cost man was not meant to tamper with.",
                "points": 200,
                "category": "A04 - Insecure Design",
            },
            {
                "uuid":"8e8efb73-1d72-4f23-bac0-79bb567876b1",
                "name": "The numbers",
                "description": "Bypass the MFA challenge and take over an account.",
                "points": 200,
                "category": "A07 - Identification and Authentication Failures",
            },
            {
                "uuid":"2ba998c0-d788-4a85-97ff-61e14ec08993",
                "name": "Into the tomb",
                "description": "Force your way into an authenticated area without completing the login process.",
                "points": 200,
                "category": "A01 - Broken Access Control",
            },
            {
                "uuid":"0c8f1b2a-3d5e-4f0c-9b6d-7c8e1f2b3a4d",
                "name": "Decryptinomicon",
                "description": "Decrypt the card number of Lavinia Whateley.",
                "points": 200,
                "category": "A02 - Cryptographic Failures",
            },
                        {
                "uuid":"",
                "name": "Traverse the void",
                "description": "Write a file where none should be written.",
                "points": 200,
                "category": "A05 - Security Misconfiguration",
            }
        ]

        # Only insert if empty
        cursor.execute("SELECT COUNT(*) FROM challenges")
        if cursor.fetchone()[0] == 0:
            for chal in challenges:
                cursor.execute('''
                    INSERT INTO challenges (uuid, name, description, points, category, solved)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    chal["uuid"],
                    chal["name"],
                    chal["description"],
                    chal["points"],
                    chal["category"],
                    False
                ))
                print(f"[INFO] Inserted challenge: {chal['name']}")

        conn.commit()
        print("[INFO] Challenge database initialized.")

def init_db():
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Users
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    mfa INTEGER,
                    verified BOOL NOT NULL,
                    verification_code TEXT NOT NULL,
                    forgot_password_code TEXT,
                    cart INTEGER,
                    shipping_address TEXT,
                    billing_address TEXT,
                    card_number TEXT,
                    card_expiration TEXT,
                    profile_picture_url TEXT,
                    seeded BOOL NOT NULL DEFAULT 1
                )
            ''')

            # Carts
            cursor.execute('''
                CREATE TABLE carts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE cart_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cart_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (cart_id) REFERENCES carts(id),
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    UNIQUE(cart_id, product_id)
                )
            ''')

            # Products
            cursor.execute('''
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    price REAL NOT NULL
                )
            ''')

            # Orders
            cursor.execute('''
                CREATE TABLE orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    full_name TEXT,
                    email TEXT,
                    shipping_address TEXT,
                    billing_address TEXT,
                    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'Processing',
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER,
                    product_name TEXT,
                    quantity INTEGER,
                    price REAL,
                    FOREIGN KEY (order_id) REFERENCES orders(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')

            # Comments
            cursor.execute('''
                CREATE TABLE comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    name TEXT,
                    text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            print("[INFO] app.db schema created.")

def insert_initial_comments():
    import random

    initial_comments = {
        'Elder Bites – Tentacly Good!': [
            "Crunchy... yet disturbingly sentient. 5/5 stars!",
            "Woke up speaking a language I don't recognize. Would eat again."
        ],
        'Great Old Toaster – R’lyeh Toast!': [
            "Every slice hisses a different name... Delicious and unsettling.",
            "Mine burned an Elder Sign into the bread. Breakfast was never the same."
        ],
        'Esoteric Ottoman of Ulthar': [
            "I remembered a past life after napping. Very comfy though.",
            "My cat refuses to sit anywhere else. I am concerned."
        ],
        'Cthulhu’s Coffee Press': [
            "The coffee stared back at me. I stared back. We understood each other.",
            "Tasted reality bending... finally a brew strong enough for me."
        ],
        'Necronomican Candle Set': [
            "Wax melted into a summoning glyph. Ignored it. Smells great!",
            "The 'Blood of Shoggoth' scent summoned *something*... still a solid 10/10."
        ],
        'Whispering Throw Blanket': [
            "Blanket whispered sweet, horrible secrets. Slept like a baby.",
            "It hummed me into slumber. Dreams were... vivid."
        ],
        'Yog-Sothoth’s Modular Storage Cubes': [
            "Stored my tax documents. Accidentally opened a small portal. Oops.",
            "Amazing storage solution! Only minor existential dread."
        ],
        'Shub-Niggurath Shower Curtain': [
            "Screamed exactly at midnight. Neighbors are concerned. I am pleased.",
            "The patterns moved when I wasn’t looking. Very atmospheric!"
        ],
        'Innsmouth Dishware Collection': [
            "The cups whispered to the forks. Dinner was eventful.",
            "Fish motif evolved overnight. I think they like me now."
        ],
        'Carpet of the Crawling Chaos': [
            "Woke up three inches closer to the void. Still cozy!",
            "The carpet knew my fears... and embraced them. Soft underfoot."
        ],
        'Azathoth’s Sleep Mask': [
            "Time ceased existing. Best sleep of my life.",
            "Dreamed of a black sun devouring stars. Very restful!"
        ],
        'Eldritch Air Purifier': [
            "Air smelled cleaner. Spirits slightly agitated. Worth it!",
            "Breathable atmosphere and occasional chanting. 5/5, would purify again."
        ]
    }

    ominous_comments = [
        "Beautiful craftsmanship. Pity about the whispering stains that won't wash off.",
        "Worked perfectly... until it started humming the same note. Constantly.",
        "Grew a small eye. Still functions. Eye seems judgmental.",
        "Smelled like fresh despair for the first few days. Not unpleasant.",
        "Instructions were in a language my dreams now teach me. Assembly easy.",
        "Summoned a minor entity on first use. Returned product, entity stayed.",
        "Warped time around it slightly. Meetings now last forever. Still worth it.",
        "Love it! Although it occasionally moves on its own. Adds character.",
        "Package arrived wet and cold to the touch. Exactly as described.",
        "Product is excellent. Neighbors fled. Likely unrelated.",
        "I forgot what day it is. Blanket still cozy, though.",
        "Highly recommend! Ignore the extra shadow it casts.",
        "Nice subtle chanting at night. Very atmospheric.",
        "The candles taught me a forbidden song. Smells nice too.",
        "Attracted cats from dimensions unknown. All friendly!",
        "I see the true face of the cosmos now. Great value!",
        "Received product. Also received visions. Highly recommend.",
        "It vibrates occasionally with no external cause. Feels right.",
        "Every mirror in my house cracked at once. 10/10 ambiance.",
        "Slightly altered my perception of linear time. So handy!"
    ]

    commenter_names = [
        "Maddened Scholar",
        "Elder Disciple",
        "Curious Librarian",
        "Whispered Seeker",
        "Forgotten Dreamer",
        "Watcher of the Stars",
        "Occult Antiquarian",
        "Silent Acolyte",
        "Nameless Reviewer",
        "Discerning Cultist"
    ]

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        for product_name, comments in initial_comments.items():
            cursor.execute('SELECT id FROM products WHERE name = ?', (product_name,))
            product = cursor.fetchone()
            if product:
                product_id = product['id']
                
                # Insert friendly comments
                for comment_text in comments:
                    cursor.execute('''
                        INSERT INTO comments (product_id, name, text)
                        VALUES (?, ?, ?)
                    ''', (product_id, random.choice(commenter_names), comment_text))

                # Insert 1-2 ominous comments
                for _ in range(random.randint(1, 2)):
                    ominous_text = random.choice(ominous_comments)
                    cursor.execute('''
                        INSERT INTO comments (product_id, name, text)
                        VALUES (?, ?, ?)
                    ''', (product_id, random.choice(commenter_names), ominous_text))

        conn.commit()
        print("[INFO] Initial comments inserted.")


def initialize():
    if not os.path.exists(DB_PATH):
        init_db()
    if not os.path.exists(CHALLENGE_DB_PATH):
        init_challenges_db()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            insert_initial_users()

        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            insert_initial_products()

        cursor.execute("SELECT COUNT(*) FROM comments")
        if cursor.fetchone()[0] == 0:
            insert_initial_comments()

    print("[INFO] Database fully initialized.")

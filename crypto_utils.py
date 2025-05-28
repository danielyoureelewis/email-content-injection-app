import os
import bcrypt
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

PASSWORD_PEPPER = os.environ.get("PASSWORD_PEPPER", "default_pepper")
AES_KEY = os.environ.get("AES_KEY", "badkey1234567890").encode()
AES_IV = os.environ.get("AES_IV", "iviviviviviviviv").encode()

def hash_password(password):
    combined = (PASSWORD_PEPPER + password).encode()
    return bcrypt.hashpw(combined, bcrypt.gensalt()).decode()

def encrypt_card(card_number):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    padded = pad(card_number.encode(), AES.block_size)
    return base64.b64encode(cipher.encrypt(padded)).decode()

def decrypt_card(encrypted):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return unpad(cipher.decrypt(base64.b64decode(encrypted)), AES.block_size).decode()

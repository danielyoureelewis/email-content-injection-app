import sqlite3

def dump_cart_table(db_path='app.db'):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM carts")
        rows = cursor.fetchall()
        print("Carts Table:")
        for row in rows:
            print(row)

        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        print("Users Table:")
        for row in rows:
            print(row)

        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        print("Products Table:")
        for row in rows:
            print(row)

        cursor.execute("SELECT id, name, description, price, image FROM products WHERE id == 1")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    dump_cart_table()


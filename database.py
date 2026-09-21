import sqlite3

def init_db():
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    
    # Do'kon sozlamalari (kanal, filial, lokatsiya)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Mahsulotlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price TEXT,
            description TEXT,
            photo_id TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def set_setting(key, value):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def add_product(name, price, description, photo_id):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, price, description, photo_id)
        VALUES (?, ?, ?, ?)
    """, (name, price, description, photo_id))
    conn.commit()
    conn.close()

def get_products():
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, description, photo_id FROM products")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_product(product_id):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

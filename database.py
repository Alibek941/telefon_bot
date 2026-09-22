import sqlite3

def get_db():
    conn = sqlite3.connect("shop.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            subcategory TEXT,
            model TEXT,
            name TEXT,
            memory TEXT,
            battery TEXT,
            color TEXT,
            condition TEXT,
            price TEXT,
            quantity INTEGER,
            photo_id TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    
    conn.commit()
    conn.close()

# --- SOZLAMALAR VA XODIMLAR ---
def set_setting(key, value):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_setting(key):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else None

def add_staff(name, phone):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO staff (name, phone) VALUES (?, ?)", (name, phone))
    conn.commit()
    conn.close()

def get_staff_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone FROM staff")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_staff(staff_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
    conn.commit()
    conn.close()

# --- MAHSULOTLAR ---
def add_product(category, subcategory, model, name, memory, battery, color, condition, price, quantity, photo_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (category, subcategory, model, name, memory, battery, color, condition, price, quantity, photo_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (category, subcategory, model, name, memory, battery, color, condition, price, quantity, photo_id))
    conn.commit()
    conn.close()

def get_products_by_category(category):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE category = ?", (category,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_products_by_subcategory(category, subcategory):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE category = ? AND subcategory = ?", (category, subcategory))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_products_by_model(category, subcategory, model):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE category = ? AND subcategory = ? AND model = ?", (category, subcategory, model))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_products():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

# --- FOYDALANUVCHILAR VA STATISTIKA ---
def add_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_users_count():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

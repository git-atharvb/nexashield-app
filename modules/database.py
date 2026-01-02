import sqlite3
import hashlib

class DatabaseManager:
    def __init__(self, db_name="nexashield.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        """Initialize the users table."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                phone TEXT,
                address TEXT
            )
        """)
        # Migration: Add columns if they don't exist (for existing databases)
        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
            self.cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")
        except sqlite3.OperationalError:
            pass  # Columns likely already exist
        self.conn.commit()

    def register_user(self, username, password, phone, address):
        """Register a new user with a hashed password."""
        try:
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            self.cursor.execute("INSERT INTO users (username, password, phone, address) VALUES (?, ?, ?, ?)", 
                                (username, hashed_pw, phone, address))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username, password):
        """Verify user credentials."""
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
        return self.cursor.fetchone() is not None

    def get_user_phone(self, username):
        """Retrieve phone number for a user."""
        self.cursor.execute("SELECT phone FROM users WHERE username=?", (username,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def update_password(self, username, new_password):
        """Update user password."""
        hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
        self.cursor.execute("UPDATE users SET password=? WHERE username=?", (hashed_pw, username))
        self.conn.commit()
        return True
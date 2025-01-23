import sqlite3
db_lp = sqlite3.connect('login_password.db')
cursor_db = db_lp.cursor()
cursor_db.execute('''DROP TABLE passwords''')

sql_create = '''CREATE TABLE IF NOT EXISTS passwords (
    login TEXT PRIMARY KEY,
    password TEXT NOT NULL
);'''

cursor_db.execute(sql_create)

cursor_db.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                role TEXT DEFAULT 'user',
                login TEXT NOT NULL,
                FOREIGN KEY (login) REFERENCES passwords(login) ON DELETE CASCADE
)
''')

cursor_db.execute('PRAGMA foreign_keys = ON')
db_lp.commit()

cursor_db.close()
db_lp.close()
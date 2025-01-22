import sqlite3
db_lp = sqlite3.connect('login_password.db')
cursor_db = db_lp.cursor()

sql_create = '''CREATE TABLE IF NOT EXISTS passwords (
    login TEXT PRIMARY KEY,
    password TEXT NOT NULL
);'''

cursor_db.execute(sql_create)
cursor_db.execute('''ALTER TABLE passwords ADD COLUMN role TEXT''')

sql_create2 = '''CREATE TABLE IF NOT EXISTS tags (
    name TEXT PRIMARY KEY,
    count TEXT NOT NULL
);'''
cursor_db.execute(sql_create2)
db_lp.commit()

cursor_db.close()
db_lp.close()
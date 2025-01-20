import sqlite3

db_lp = sqlite3.connect('login_password.db')
cursor_db = db_lp.cursor()
sql_create = '''CREATE TABLE passwords(
login TEXT PRIMARY KEY,
password TEXT NOT NULL);'''

cursor_db.execute(sql_create)
db_lp.commit()

cursor_db.close()
db_lp.close()
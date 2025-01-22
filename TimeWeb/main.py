import os

from flask import Flask, request, render_template, session, redirect, url_for, flash
import sqlite3

app = Flask(__name__)

app.secret_key = os.urandom(24)
def get_db_connection():
    conn = sqlite3.connect('login_password.db')
    # Возвращаем строки как "словари"
    conn.row_factory = sqlite3.Row
    return conn
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/users")
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM passwords').fetchall()
    conn.close()
    return render_template('users.html', users=users)
@app.route('/create_user', methods=('GET', 'POST'))
def create_user():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')

        conn = get_db_connection()
        conn.execute('INSERT INTO passwords (login, password) VALUES (?, ?)', (login, password))
        conn.commit()
        conn.close()

        return redirect(url_for('get_users'))

    return render_template('create.html')

@app.route('/create_tag', methods=('GET', 'POST'))
def create_tag():
    if request.method == 'POST':
        tag = request.form.get('tag')

        conn = get_db_connection()
        conn.execute('INSERT INTO tags (name, count) VALUES (?, ?)', (tag, 0))
        conn.commit()
        conn.close()

        return redirect(url_for('get_tags'))

    return render_template('create_tag.html')

@app.route("/tags")
def get_tags():
    conn = get_db_connection()
    tags = conn.execute('SELECT * FROM tags').fetchall()
    conn.close()
    return render_template('tags.html', tags=tags)

@app.route('/authorization', methods=['GET', 'POST'])
def form_authorization():
   if request.method == 'POST':
       Login = request.form.get('Login')
       Password = request.form.get('Password')

       db_lp = sqlite3.connect('login_password.db')
       cursor_db = db_lp.cursor()

       cursor_db.execute(('SELECT password FROM passwords WHERE login = ?'), (Login,))
       result = cursor_db.fetchone()


       if not result:
           return render_template("authorization.html", error_message='Пользователя с таким логином не существует!')
       if result[0] != Password:
           return render_template("authorization.html", error_message='Неверный пароль!')

       cursor_db.execute('SELECT role FROM passwords WHERE login = ?', (Login,))
       role = cursor_db.fetchone()[0]

       session['username'] = Login
       session['role'] = role

       # Закрываем подключение к базе данных
       cursor_db.close()

       return redirect(url_for('home'))
   return render_template('authorization.html')

@app.route('/logout')
def logout():
    # Удаляем имя пользователя из сессии (выход из аккаунта)
    session.pop('username', None)
    session.clear()  # Очистка всех данных сессии
    return redirect(url_for('home'))

@app.route('/account', methods=('GET', 'POST'))
def account():
    return render_template('account.html')

@app.route('/registration', methods=['GET', 'POST'])
def form_registration():
   if request.method == 'POST':
       Login = request.form.get('Login')
       Password = request.form.get('Password')

       db_lp = sqlite3.connect('login_password.db')
       cursor_db = db_lp.cursor()
       sql_insert = '''INSERT INTO passwords VALUES('{}','{}');'''.format(Login, Password)
       cursor_db.execute(sql_insert)
       cursor_db.close()
       db_lp.commit()
       db_lp.close()
       return render_template('successfulregis.html')
   return render_template('registration.html')

if __name__ == "__main__":
    app.run(port=5001)
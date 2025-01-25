import os

from flask import Flask, request, render_template, session, redirect, url_for, flash
import sqlite3

from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def get_db_connection():
    conn = sqlite3.connect('login_password.db')
    # Возвращаем строки как "словари"
    conn.row_factory = sqlite3.Row
    return conn
@app.route("/")
def home():
    conn = get_db_connection()
    posts_data = conn.execute('''
                        SELECT posts.post_id, title, content, image_path, user_profile.login
                        FROM posts
                        INNER JOIN user_profile ON posts.user_id = user_profile.user_id
                    ''').fetchall()
    conn.close()
    return render_template('index.html', posts=posts_data)

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

@app.route("/user_posts")
def get_user_posts():
    conn = get_db_connection()

    post_data = conn.execute('''
                SELECT posts.post_id, title, content, image_path, user_profile.login
                FROM posts
                INNER JOIN user_profile ON posts.user_id = user_profile.user_id
                WHERE user_profile.login = ?
                ''', (session['username'],)).fetchall()
    conn.close()
    return render_template('user_posts.html', posts=post_data)

@app.route('/create_user', methods=('GET', 'POST'))
def create_user():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')

        conn = get_db_connection()
        conn.execute('INSERT INTO passwords (login, password) VALUES (?, ?)', (login, password))
        conn.execute(('INSERT INTO user_profile (login) VALUES (?)'), (login,))
        conn.commit()
        conn.close()

        return redirect(url_for('get_users'))

    return render_template('create.html')

@app.route('/<string:login>/edit_user', methods=('GET', 'POST'))
def edit_user(login):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM passwords WHERE login = ?', (login,)).fetchone()

    if request.method == 'POST':
        new_login = request.form.get('login')
        new_password = request.form.get('password')

        conn.execute('UPDATE passwords SET login = ?, password = ? WHERE login = ?', (new_login, new_password, login))
        conn.commit()
        conn.close()
        return redirect(url_for('get_users'))

    return render_template('edit_user.html', user=user)
@app.route('/<login>/delete_user', methods=('POST',))
def delete_user(login):
    conn = get_db_connection()
    conn.execute('DELETE FROM passwords WHERE login = ?', (login,))
    conn.commit()
    conn.close()
    flash('Пользователь был удален.')
    return redirect(url_for('get_users'))

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

       cursor_db.execute('SELECT role FROM user_profile WHERE login = ?', (Login,))
       role = cursor_db.fetchone()[0]
       # print(role)

       cursor_db.execute('SELECT user_id FROM user_profile WHERE login = ?', (Login,))
       user_id = cursor_db.fetchone()[0]

       # Сохраняем данные в сессии только после успешной авторизации
       session['username'] = Login
       session['role'] = role
       session['user_id'] = user_id

       # Закрываем подключение к базе данных
       cursor_db.close()

       return redirect(url_for('home'))
   return render_template('authorization.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create_user_post', methods=('GET', 'POST'))
def create_user_post():
    # conn = sqlite3.connect('blog.db')
    # cursor = conn.cursor()
    #
    # # Получение списка тегов из таблицы "tags"
    # tags = cursor.execute('SELECT tag_id, name FROM tags').fetchall()  # Возвращает список кортежей (id, name)
    #
    # conn.close()

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        tag = request.form.get('tag')
        user_id = session['user_id']
        file = request.files.get('image')
        image_path = None
        if file and allowed_file(file.filename):

            safe_filename = secure_filename(file.filename)
            upload_path = f'static/uploads/{safe_filename}'

            file.save(upload_path)
            image_path = upload_path
        try:
            conn = sqlite3.connect('blog.db')
            cursor = conn.cursor()
            cursor.execute('''
                            INSERT INTO posts (user_id, title, content, image_path, tag)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (user_id, title, content, image_path, tag))

            conn.commit()
            conn.close()

            flash('Пост успешно добавлен!', 'success')
            return redirect(url_for('get_user_posts'))
        except Exception as e:
            flash(f'Ошибка при добавлении поста: {str(e)}', 'danger')
    return render_template('create_user_post.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.clear()
    return redirect(url_for('home'))

@app.route('/account', methods=('GET', 'POST'))
def account():
    conn = get_db_connection()
    current_login = session['username']
    user = conn.execute('SELECT login, name, email FROM user_profile WHERE login = ?', (current_login,)).fetchone()

    if request.method == 'POST':
        # login = request.form.get('login')
        name = request.form.get('name')
        email = request.form.get('email')

        conn.execute('UPDATE user_profile SET name = ?, email = ? WHERE login = ?', (name, email, current_login))
        conn.commit()
        conn.close()
        flash('Данные успешно обновлены')
        return redirect(url_for('account'))

    return render_template('account.html', user=user)

@app.route('/registration', methods=['GET', 'POST'])
def form_registration():
   if request.method == 'POST':
       Login = request.form.get('Login')
       Password = request.form.get('Password')

       db_lp = sqlite3.connect('login_password.db')
       cursor_db = db_lp.cursor()

       cursor_db.execute('INSERT INTO passwords (login, password) VALUES(?, ?)', (Login, Password))
       cursor_db.execute(('INSERT INTO user_profile (login) VALUES (?)'), (Login,))

       cursor_db.close()
       db_lp.commit()
       db_lp.close()
       session['username'] = Login
       session['role'] = 'user'
       return redirect(url_for('home'))
   return render_template('registration.html')

if __name__ == "__main__":
    app.run(port=5001)
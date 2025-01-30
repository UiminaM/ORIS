import sqlite3
db_lp = sqlite3.connect('blog.db')
cursor = db_lp.cursor()

cursor.execute('''DROP TABLE passwords''')
cursor.execute('''DROP TABLE user_profile''')
cursor.execute('''DROP TABLE tags''')
cursor.execute('''DROP TABLE post_tags''')
cursor.execute('''DROP TABLE posts''')



cursor.execute('''
                CREATE TABLE IF NOT EXISTS passwords(
                login TEXT PRIMARY KEY,
                password TEXT NOT NULL)
''')

# Включаем поддержку внешних ключей
cursor.execute('PRAGMA foreign_keys = ON')

# Связь "один к одному" между таблицами passwords и user_profile реализована через поле login.
# Каждому логину в таблице passwords соответствует ровно один профиль в таблице user_profile.
cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Уникальный ID пользователя
                name TEXT, -- Имя пользователя
                email TEXT UNIQUE, -- Email пользователя
                role TEXT DEFAULT 'user',
                login TEXT NOT NULL UNIQUE,        -- Логин, который должен быть уникальным
                FOREIGN KEY (login) REFERENCES passwords(login) ON DELETE CASCADE
)
''')

# Таблица user_profile имеет связь "один ко многим" с таблицей posts, поскольку один пользователь может создавать несколько постов,
# но каждый пост ассоциирован только с одним пользователем. Это реализуется через поле user_id в таблице posts,
# которое является внешним ключом, указывающим на уникальный идентификатор пользователя.
cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                image_path TEXT,
                FOREIGN KEY (user_id) REFERENCES user_profile (user_id) ON DELETE CASCADE
            )
''')

# Таблица тегов
# UNIQUE гарантирует отсутствие дубликатов тегов.
cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
)
''')

# Связующая таблица для posts и tags
# Связь "многие ко многим" реализуется через связующую таблицу post_tags.
# Один пост может иметь много тегов, и один тег может быть связан с многими постами.
cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_tags (
                post_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts (post_id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
                PRIMARY KEY (post_id, tag_id)
            )
''')

db_lp.commit()
db_lp.close()
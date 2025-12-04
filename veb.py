#to-do-list
from flask import Flask, render_template, redirect, url_for, flash, request, session, send_from_directory
from werkzeug.utils import secure_filename
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
DATABASE = 'tasks.db'
app.config['UPLOAD_FOLDER'] = 'profile_photos'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT FALSE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            photo TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_tasks():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks ORDER BY id DESC")
        rows = cur.fetchall()
        return rows

def add_task(title, description=''):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO tasks (title, description) VALUES (?, ?)", (title, description))
        conn.commit()

def delete_task(task_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()

def complete_task(task_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE tasks SET completed=? WHERE id=?", (True, task_id))
        conn.commit()

with app.app_context():
    init_db()

@app.route('/')
def index():
    tasks = get_tasks()
    user_name = session.get('user_name')
    user_email = session.get('user_email')
    user_photo = session.get('user_photo')
    lang = session.get('lang', 'ru')
    return render_template('index.html', tasks=tasks, user_name=user_name, user_email=user_email, user_photo=user_photo, lang=lang)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        add_task(title, description)
        flash('Задача успешно добавлена!', 'Успех')
        return redirect(url_for('index'))
    return render_template('task_form.html', action='Добавить задачу')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE tasks SET title=?, description=? WHERE id=?", (title, description, id))
            conn.commit()
        flash('Задача успешно обновлена!', 'Обновление')
        return redirect(url_for('index'))
    else:
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM tasks WHERE id=?", (id,))
            task = cur.fetchone()
        return render_template('task_form.html', action=f'Изменить задачу #{id}', task=task)

@app.route('/delete/<int:id>')
def delete(id):
    delete_task(id)
    flash('Задача удалена!', 'Предупреждение')
    return redirect(url_for('index'))

@app.route('/complete/<int:id>')
def complete(id):
    complete_task(id)
    flash('Задача отмечена как выполненная!', 'Успех')
    return redirect(url_for('index'))


# Страница "Задачи"
@app.route('/tasks')
def tasks():
    return render_template('tasks.html')

# Страница "Профиль"
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        photo = request.files.get('photo')
        photo_path = None
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            if not filename.lower().endswith('.jpg'):
                flash('Фото профиля должно быть в формате .jpg!', 'Ошибка')
                return render_template('profile.html')
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo_path = filename
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute('SELECT id FROM users WHERE email=?', (email,))
            exists = cur.fetchone()
            if exists:
                session['user_name'] = exists[1]
                session['user_email'] = exists[2]
                session['user_photo'] = exists[3].split('/')[-1] if exists[3] else None
                flash('Пользователь с таким email уже существует!', 'Ошибка')
                return render_template('profile.html')
            else:
                cur.execute('INSERT INTO users (email, name, password, photo) VALUES (?, ?, ?, ?)', (email, name, password, photo_path))
                conn.commit()
                session['user_name'] = name
                session['user_email'] = email
                session['user_photo'] = photo_path
                flash('Профиль успешно создан!', 'Успех')
        return redirect(url_for('index'))
    return render_template('profile.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        lang = request.form.get('lang')
        session['lang'] = lang
        # ... обработка остальных настроек ...
        flash('Настройки сохранены!', 'Успех')
        return redirect(url_for('settings'))
    return render_template('settings.html', lang=session.get('lang', 'ru'))

@app.route('/delete_all_users', methods=['POST'])
def delete_all_users():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM users')
        conn.commit()
    session.clear()
    flash('Все учётные записи удалены!', 'Успех')
    return redirect(url_for('index'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    email = session.get('user_email')
    if email:
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM users WHERE email=?', (email,))
            conn.commit()
        session.clear()
        flash('Учётная запись удалена!', 'Успех')
    return redirect(url_for('index'))

@app.route('/profile_photos/<filename>')
def profile_photo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)

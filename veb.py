#to-do-list
from flask import Flask, render_template, redirect, url_for, flash, request, session, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

app.config['UPLOAD_FOLDER'] = 'profile_photos'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
TASKS_FILE = os.path.join(DATA_DIR, 'tasks.json')

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def init_db():
    if not os.path.exists(USERS_FILE):
        save_json(USERS_FILE, [])
    if not os.path.exists(TASKS_FILE):
        save_json(TASKS_FILE, [])

def get_tasks(user_id):
    tasks = load_json(TASKS_FILE)
    return [task for task in tasks if task.get('user_id') == user_id]

def add_task(title, description='', user_id=None):
    tasks = load_json(TASKS_FILE)
    new_task = {
        'id': len(tasks) + 1,
        'title': title,
        'description': description,
        'completed': False,
        'user_id': user_id
    }
    tasks.append(new_task)
    save_json(TASKS_FILE, tasks)

def delete_task(task_id, user_id):
    tasks = load_json(TASKS_FILE)
    tasks = [task for task in tasks if not (task.get('id') == task_id and task.get('user_id') == user_id)]
    save_json(TASKS_FILE, tasks)

def complete_task(task_id, user_id):
    tasks = load_json(TASKS_FILE)
    for task in tasks:
        if task.get('id') == task_id and task.get('user_id') == user_id:
            task['completed'] = True
    save_json(TASKS_FILE, tasks)

def get_user_by_email(email):
    users = load_json(USERS_FILE)
    for user in users:
        if user.get('email') == email:
            return user
    return None

def add_user(email, name, password, photo=None):
    users = load_json(USERS_FILE)
    user_id = max([u.get('id', 0) for u in users]) + 1 if users else 1
    new_user = {
        'id': user_id,
        'email': email,
        'name': name,
        'password': password,
        'photo': photo
    }
    users.append(new_user)
    save_json(USERS_FILE, users)
    return new_user

def delete_user_by_email(email):
    users = load_json(USERS_FILE)
    users = [u for u in users if u.get('email') != email]
    save_json(USERS_FILE, users)

def delete_all_users_data():
    save_json(USERS_FILE, [])
    save_json(TASKS_FILE, [])


with app.app_context():
    init_db()

@app.route('/')
def index():
    user_id = session.get('user_id')
    if not user_id:
        flash('Пожалуйста, войдите или зарегистрируйтесь!', 'Ошибка')
        return redirect(url_for('profile'))
    tasks = get_tasks(user_id)
    user_name = session.get('user_name')
    user_email = session.get('user_email')
    user_photo = session.get('user_photo')
    lang = session.get('lang', 'ru')
    return render_template('index.html', tasks=tasks, user_name=user_name, user_email=user_email, user_photo=user_photo, lang=lang)

@app.route('/add', methods=['GET', 'POST'])
def add():
    user_id = session.get('user_id')
    if not user_id:
        flash('Пожалуйста, войдите или зарегистрируйтесь!', 'Ошибка')
        return redirect(url_for('profile'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        add_task(title, description, user_id)
        flash('Задача успешно добавлена!', 'Успех')
        return redirect(url_for('index'))
    return render_template('task_form.html', action='Добавить задачу')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Пожалуйста, войдите или зарегистрируйтесь!', 'Ошибка')
        return redirect(url_for('profile'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        tasks = load_json(TASKS_FILE)
        for task in tasks:
            if task.get('id') == id and task.get('user_id') == user_id:
                task['title'] = title
                task['description'] = description
        save_json(TASKS_FILE, tasks)
        flash('Задача успешно обновлена!', 'Обновление')
        return redirect(url_for('index'))
    else:
        tasks = load_json(TASKS_FILE)
        task = next((t for t in tasks if t.get('id') == id and t.get('user_id') == user_id), None)
        return render_template('task_form.html', action=f'Изменить задачу #{id}', task=task)

@app.route('/delete/<int:id>')
def delete(id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Пожалуйста, войдите или зарегистрируйтесь!', 'Ошибка')
        return redirect(url_for('profile'))
    delete_task(id, user_id)
    flash('Задача удалена!', 'Предупреждение')
    return redirect(url_for('index'))

@app.route('/complete/<int:id>')
def complete(id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Пожалуйста, войдите или зарегистрируйтесь!', 'Ошибка')
        return redirect(url_for('profile'))
    complete_task(id, user_id)
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
        
        existing_user = get_user_by_email(email)
        if existing_user:
            session['user_id'] = existing_user['id']
            session['user_name'] = existing_user['name']
            session['user_email'] = existing_user['email']
            session['user_photo'] = existing_user.get('photo')
            flash('Пользователь с таким email уже существует!', 'Ошибка')
            return render_template('profile.html')
        else:
            user = add_user(email, name, password, photo_path)
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_photo'] = user.get('photo')
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
    delete_all_users_data()
    session.clear()
    flash('Все учётные записи удалены!', 'Успех')
    return redirect(url_for('index'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    email = session.get('user_email')
    if email:
        delete_user_by_email(email)
        tasks = load_json(TASKS_FILE)
        user_id = session.get('user_id')
        tasks = [t for t in tasks if t.get('user_id') != user_id]
        save_json(TASKS_FILE, tasks)
        session.clear()
        flash('Учётная запись удалена!', 'Успех')
    return redirect(url_for('index'))

@app.route('/profile_photos/<filename>')
def profile_photo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False)


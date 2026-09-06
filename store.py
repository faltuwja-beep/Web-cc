import os
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = 'super_secret_cyber_key'

users = {"admin": "123"}
tasks = []

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username] == password:
            session['user'] = username
            return redirect('/todo')
        else:
            msg = "Galat Username ya Password!"
    return render_template('index.html', msg=msg)

@app.route('/todo', methods=['GET', 'POST'])
def todo():
    if 'user' not in session:
        return redirect('/')
    if request.method == 'POST':
        task_text = request.form.get('task')
        if task_text:
            tasks.append(task_text)
        return redirect('/todo')
    return render_template('todo.html', tasks=tasks, user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
  

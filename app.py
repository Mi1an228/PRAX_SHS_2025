from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import os

load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = os.urandom(24)

USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

login_form = '''
<!doctype html>
<title>Login</title>
<h2>Login</h2>
<form method="post">
  <input type="text" name="username" placeholder="Username" required><br>
  <input type="password" name="password" placeholder="Password" required><br>
  <input type="submit" value="Login">
</form>
<p style="color:red;">{{ error }}</p>
'''

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['user'] = username
            return redirect(url_for('homepage'))
        else:
            error = 'Nesprávne meno alebo heslo.'
    return render_template_string(login_form, error=error)

@app.route('/homepage')
def homepage():
    return render_template_string('''
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Welcome</title>
  <style>
    body { margin:0; background:#111; color:#fff; font-family:sans-serif; text-align:center; }
    h1 { margin-top: 80px; font-size: 3em; letter-spacing: 2px; }
    #particles-js { position: absolute; width: 100vw; height: 100vh; z-index: 0; top:0; left:0; }
    .content { position: relative; z-index: 1; }
    .btn-appka {
      margin-top: 40px;
      padding: 15px 40px;
      font-size: 1.2em;
      background: #00c3ff;
      color: #fff;
      border: none;
      border-radius: 30px;
      cursor: pointer;
      transition: background 0.2s;
    }
    .btn-appka:hover { background: #007fa3; }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/particles.js@2.0.0/particles.min.js"></script>
</head>
<body>
  <div id="particles-js"></div>
  <div class="content">
    <h1>WELCOME</h1>
    <a href="/app"><button class="btn-appka">Appka</button></a>
  </div>
  <script>
    particlesJS('particles-js', {
      "particles": {
        "number": {"value": 80},
        "color": {"value": "#00c3ff"},
        "shape": {"type": "circle"},
        "opacity": {"value": 0.5},
        "size": {"value": 3},
        "line_linked": {"enable": true, "distance": 150, "color": "#00c3ff", "opacity": 0.4, "width": 1},
        "move": {"enable": true, "speed": 2}
      },
      "interactivity": {
        "detect_on": "canvas",
        "events": {"onhover": {"enable": true, "mode": "repulse"}},
        "modes": {"repulse": {"distance": 100}}
      },
      "retina_detect": true
    });
  </script>
</body>
</html>
''')

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return f"<h2>Vitaj, {session['user']}!</h2><a href='/logout'>Logout</a>"
    return redirect(url_for('login'))

@app.route('/app')
def appka():
    return render_template_string('''
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Appka</title>
  <style>
    body { background: #f4f4f4; font-family: sans-serif; text-align: center; margin: 0; }
    .container { margin-top: 100px; }
    h2 { color: #222; }
    p { color: #555; }
  </style>
</head>
<body>
  <div class="container">
    <h2>Appka - úvodná obrazovka</h2>
    <p>Túto stránku môžete upravovať podľa potreby.</p>
  </div>
</body>
</html>
''')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/hello')
def hello():
    return '<h1>Hello, World!</h1>'

if __name__ == '__main__':
    app.run(debug=True)

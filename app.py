from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import json
import os

app = Flask(__name__)
app.secret_key = "guitar-practice-secret-key-2025"

SONGS_FILE = "songs.json"
USERS_FILE = "users.json"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "guitar2025"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username

@login_manager.user_loader
def load_user(username):
    users = load_users()
    if username in users:
        return User(username)
    return None

def load_songs():
    if os.path.exists(SONGS_FILE):
        with open(SONGS_FILE, "r") as f:
            return json.load(f)
    return {"beginner": [], "intermediate": [], "advanced": []}

def save_songs(songs):
    with open(SONGS_FILE, "w") as f:
        json.dump(songs, f, indent=4)


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
    else:
        users = {}

    # Always ensure admin exists
    if "admin" not in users:
        users["admin"] = {"password": "guitar2025"}
        save_users(users)

    return users

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def load_progress():
    if os.path.exists("progress.json"):
        with open("progress.json", "r") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open("progress.json", "w") as f:
        json.dump(progress, f, indent=4)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/practice")
def practice():
    return render_template("practice.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = load_users()
        if username in users and users[username]["password"] == password:
            user = User(username)
            login_user(user)
            session["admin"] = (username == ADMIN_USERNAME)
            return redirect(url_for("home"))
        else:
            error = "Wrong username or password"
    return render_template("login.html", error=error)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if not username or not password:
            error = "Please fill in all fields"
        elif password != confirm:
            error = "Passwords don't match"
        elif len(password) < 4:
            error = "Password must be at least 4 characters"
        else:
            users = load_users()
            if username in users:
                error = "Username already exists"
            elif username == ADMIN_USERNAME:
                error = "This username is reserved"
            else:
                users[username] = {"password": password}
                save_users(users)
                progress = load_progress()
                progress[username] = {"learned": [], "practicing": []}
                save_progress(progress)
                user = User(username)
                login_user(user)
                return redirect(url_for("home"))
    return render_template("signup.html", error=error)

@app.route("/logout")
def logout():
    logout_user()
    session.pop("admin", None)
    return redirect(url_for("home"))

@app.route("/api/progress", methods=["GET"])
def get_progress():
    if current_user.is_authenticated:
        progress = load_progress()
        username = current_user.username
        if username in progress:
            return progress[username]
    return {"learned": [], "practicing": []}

@app.route("/api/progress", methods=["POST"])
def save_user_progress():
    if current_user.is_authenticated:
        data = request.get_json()
        progress = load_progress()
        progress[current_user.username] = data
        save_progress(progress)
        return {"status": "ok"}
    return {"status": "not_logged_in"}

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect(url_for("login"))
    if request.method == "POST":
        name = request.form.get("name")
        artist = request.form.get("artist")
        chords = request.form.get("chords")
        difficulty = request.form.get("difficulty")
        songs = load_songs()
        chord_list = [c.strip() for c in chords.split(",") if c.strip()]
        songs[difficulty].append({
            "name": name,
            "artist": artist,
            "chords": chord_list
        })
        save_songs(songs)
        return redirect(url_for("admin"))
    songs = load_songs()
    return render_template("admin.html", songs=songs)

@app.route("/api/songs")
def api_songs():
    return load_songs()

@app.route("/api/check_admin")
def check_admin():
    return {
        "is_admin": session.get("admin", False),
        "is_logged_in": current_user.is_authenticated,
        "username": current_user.username if current_user.is_authenticated else None
    }

@app.route("/admin/delete/<difficulty>/<song_name>")
def delete_song(difficulty, song_name):
    if not session.get("admin"):
        return redirect(url_for("login"))
    songs = load_songs()
    songs[difficulty] = [s for s in songs[difficulty] if s["name"] != song_name]
    save_songs(songs)
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)
"""Movie Recommendation App (Flask + SQLite)."""
import os
import sqlite3
from functools import wraps

from flask import (Flask, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["DB_PATH"] = os.environ.get(
    "MOVIE_DB", os.path.join(BASE_DIR, "database", "movies.db"))

# title, year, genres, score, director, description, emoji
SEED_MOVIES = [
    ("The Shawshank Redemption", 1994, "Drama", 9.3, "Frank Darabont", "A banker jailed for a crime he says he didn't commit forms a lasting friendship and quietly plans his escape.", "🔓"),
    ("The Godfather", 1972, "Crime,Drama", 9.2, "Francis Ford Coppola", "The aging head of a crime family hands control to his reluctant youngest son.", "🎩"),
    ("The Dark Knight", 2008, "Action,Crime,Thriller", 9.0, "Christopher Nolan", "Batman faces a chaos-loving criminal who pushes Gotham to its limits.", "🦇"),
    ("Inception", 2010, "Action,Sci-Fi,Thriller", 8.8, "Christopher Nolan", "A thief who steals secrets from dreams is offered a chance to plant an idea instead.", "🌀"),
    ("Interstellar", 2014, "Adventure,Drama,Sci-Fi", 8.7, "Christopher Nolan", "Explorers travel through a wormhole to find a new home for humanity.", "🪐"),
    ("The Matrix", 1999, "Action,Sci-Fi", 8.7, "The Wachowskis", "A hacker discovers his world is a simulation and joins a rebellion against its machine rulers.", "💊"),
    ("Pulp Fiction", 1994, "Crime,Drama", 8.9, "Quentin Tarantino", "Several intertwined stories of hitmen, a boxer and a gangster's wife unfold in Los Angeles.", "💼"),
    ("Forrest Gump", 1994, "Drama,Romance", 8.8, "Robert Zemeckis", "A kind-hearted man drifts through decades of American history and accidentally shapes some of it.", "🍫"),
    ("Spirited Away", 2001, "Animation,Adventure,Fantasy", 8.6, "Hayao Miyazaki", "A girl wanders into a spirit world and must work at a bathhouse to free her parents.", "🐉"),
    ("Parasite", 2019, "Comedy,Drama,Thriller", 8.5, "Bong Joon-ho", "A poor family schemes its way into the lives of a wealthy household.", "🪨"),
    ("3 Idiots", 2009, "Comedy,Drama", 8.4, "Rajkumar Hirani", "Three engineering students navigate friendship, pressure and the meaning of real education.", "🎓"),
    ("Dangal", 2016, "Action,Drama,Sport", 8.3, "Nitesh Tiwari", "A former wrestler trains his daughters to become world-class champions.", "🤼"),
    ("Baahubali: The Beginning", 2015, "Action,Adventure,Fantasy", 8.0, "S. S. Rajamouli", "A young man discovers his royal lineage and is drawn into a war for a kingdom.", "⚔️"),
    ("Gladiator", 2000, "Action,Adventure,Drama", 8.5, "Ridley Scott", "A betrayed Roman general returns as a gladiator seeking revenge.", "🏛️"),
    ("The Lion King", 1994, "Animation,Adventure,Drama", 8.5, "Roger Allers", "A young lion prince flees his kingdom, then returns to reclaim it.", "🦁"),
    ("Toy Story", 1995, "Animation,Comedy,Family", 8.3, "John Lasseter", "A cowboy doll feels threatened when a space ranger toy becomes his owner's favourite.", "🤠"),
    ("Finding Nemo", 2003, "Animation,Adventure,Family", 8.2, "Andrew Stanton", "An anxious clownfish crosses the ocean to find his lost son.", "🐠"),
    ("Titanic", 1997, "Drama,Romance", 7.9, "James Cameron", "A young couple from different classes fall in love aboard the doomed ocean liner.", "🚢"),
    ("Mad Max: Fury Road", 2015, "Action,Adventure,Sci-Fi", 8.1, "George Miller", "In a desert wasteland, a rebel driver and a drifter flee a tyrant across a relentless chase.", "🔥"),
    ("Get Out", 2017, "Horror,Mystery,Thriller", 7.8, "Jordan Peele", "A visit to his girlfriend's family estate turns unnerving for a young photographer.", "☕"),
    ("The Silence of the Lambs", 1991, "Crime,Horror,Thriller", 8.6, "Jonathan Demme", "A young FBI trainee seeks help from an imprisoned cannibal to catch another killer.", "🦋"),
    ("La La Land", 2016, "Comedy,Drama,Romance", 8.0, "Damien Chazelle", "A jazz pianist and an aspiring actress chase their dreams and each other in Los Angeles.", "🎹"),
    ("Coco", 2017, "Animation,Family,Fantasy", 8.4, "Lee Unkrich", "A boy who dreams of music enters the Land of the Dead to uncover his family's history.", "🎸"),
    ("Knives Out", 2019, "Comedy,Crime,Mystery", 7.9, "Rian Johnson", "A detective investigates the death of a famous novelist surrounded by his scheming family.", "🔪"),
]


# ---------------------------------------------------------------- database
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    path = app.config["DB_PATH"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, year INTEGER, genres TEXT NOT NULL,
            score REAL, director TEXT, description TEXT, emoji TEXT);
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS ratings (
            user_id INTEGER NOT NULL, movie_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            PRIMARY KEY (user_id, movie_id));
    """)
    if db.execute("SELECT COUNT(*) FROM movies").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO movies (title, year, genres, score, director, description, emoji) "
            "VALUES (?,?,?,?,?,?,?)", SEED_MOVIES)
    db.commit()
    db.close()


# ----------------------------------------------------------------- helpers
def all_genres():
    rows = get_db().execute("SELECT genres FROM movies").fetchall()
    return sorted({g.strip() for r in rows for g in r["genres"].split(",")})


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_user():
    return {"current_user": session.get("username")}


@app.template_filter("genre_list")
def genre_list(value):
    return [g.strip() for g in value.split(",")]


def recommend_for_user(user_id, limit=8):
    """Content-based: weight genres by the user's ratings (4-5 = like, 1-2 = dislike)."""
    db = get_db()
    rated = db.execute(
        "SELECT m.id, m.genres, r.rating FROM ratings r "
        "JOIN movies m ON m.id = r.movie_id WHERE r.user_id = ?", (user_id,)).fetchall()
    if not rated:
        return [], []
    weights = {}
    for row in rated:
        for genre in row["genres"].split(","):
            weights[genre] = weights.get(genre, 0) + (row["rating"] - 3)
    seen = {row["id"] for row in rated}
    scored = []
    for m in db.execute("SELECT * FROM movies").fetchall():
        if m["id"] in seen:
            continue
        gs = m["genres"].split(",")
        match = sum(weights.get(g, 0) for g in gs) / len(gs)
        scored.append((match + m["score"] / 10, m))
    scored.sort(key=lambda t: t[0], reverse=True)
    liked = [g for g, w in sorted(weights.items(), key=lambda t: -t[1]) if w > 0][:3]
    return [m for _, m in scored[:limit]], liked


# ------------------------------------------------------------------ routes
@app.route("/")
def index():
    db = get_db()
    top = db.execute("SELECT * FROM movies ORDER BY score DESC LIMIT 8").fetchall()
    return render_template("index.html", top=top, genres=all_genres())


@app.route("/movies")
def movies():
    q = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()
    sql, params = "SELECT * FROM movies WHERE 1=1", []
    if q:
        sql += " AND title LIKE ?"
        params.append(f"%{q}%")
    if genre:
        sql += " AND (',' || genres || ',') LIKE ?"
        params.append(f"%,{genre},%")
    sql += " ORDER BY score DESC"
    rows = get_db().execute(sql, params).fetchall()
    return render_template("movies.html", movies=rows, genres=all_genres(), q=q, genre=genre)


@app.route("/movie/<int:movie_id>", methods=["GET", "POST"])
def movie_details(movie_id):
    db = get_db()
    movie = db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    if movie is None:
        return render_template("movies.html", movies=[], genres=all_genres(), q="", genre=""), 404
    if request.method == "POST":
        if "user_id" not in session:
            flash("Log in to rate movies.", "error")
            return redirect(url_for("login", next=request.path))
        try:
            rating = int(request.form.get("rating", 0))
        except ValueError:
            rating = 0
        if not 1 <= rating <= 5:
            flash("Choose a rating from 1 to 5.", "error")
        else:
            db.execute("INSERT OR REPLACE INTO ratings (user_id, movie_id, rating) VALUES (?,?,?)",
                       (session["user_id"], movie_id, rating))
            db.commit()
            flash("Rating saved!", "success")
        return redirect(url_for("movie_details", movie_id=movie_id))

    stats = db.execute("SELECT AVG(rating) AS avg, COUNT(*) AS n FROM ratings WHERE movie_id = ?",
                       (movie_id,)).fetchone()
    my_rating = None
    if "user_id" in session:
        row = db.execute("SELECT rating FROM ratings WHERE user_id = ? AND movie_id = ?",
                         (session["user_id"], movie_id)).fetchone()
        my_rating = row["rating"] if row else None
    first_genre = movie["genres"].split(",")[0]
    similar = db.execute(
        "SELECT * FROM movies WHERE id != ? AND (',' || genres || ',') LIKE ? "
        "ORDER BY score DESC LIMIT 4", (movie_id, f"%,{first_genre},%")).fetchall()
    return render_template("movie-details.html", movie=movie, stats=stats,
                           my_rating=my_rating, similar=similar)


@app.route("/recommendations")
def recommendations():
    db = get_db()
    picked = [g for g in request.args.getlist("genre") if g]
    mode, results, liked = "top", [], []
    if picked:
        mode = "genres"
        clauses = " OR ".join("(',' || genres || ',') LIKE ?" for _ in picked)
        results = db.execute(f"SELECT * FROM movies WHERE {clauses} ORDER BY score DESC LIMIT 12",
                             [f"%,{g},%" for g in picked]).fetchall()
    elif "user_id" in session:
        results, liked = recommend_for_user(session["user_id"])
        if results:
            mode = "personal"
    if not results:
        results = db.execute("SELECT * FROM movies ORDER BY score DESC LIMIT 8").fetchall()
    return render_template("recommendations.html", movies=results, mode=mode,
                           liked=liked, genres=all_genres(), picked=picked)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(username) < 3 or "@" not in email or len(password) < 6:
            flash("Username 3+ chars, valid email, password 6+ chars.", "error")
        else:
            db = get_db()
            try:
                db.execute("INSERT INTO users (username, email, password_hash) VALUES (?,?,?)",
                           (username, email, generate_password_hash(password)))
                db.commit()
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Username or email already taken.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session.clear()
            session["user_id"], session["username"] = user["id"], user["username"]
            nxt = request.args.get("next", "")
            return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else url_for("index"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("index"))


@app.route("/health")
def health():
    return jsonify(status="UP")


@app.route("/api/movies")
def api_movies():
    rows = get_db().execute("SELECT id, title, year, genres, score FROM movies ORDER BY score DESC").fetchall()
    return jsonify([dict(r) for r in rows])


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

import os
import random
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Use SECRET_KEY from the environment if set; otherwise make a random one.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32)

# food.db lives in the same folder as this file.
# Set FOOD_DB to use a different file instead (e.g. a throwaway test database).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get("FOOD_DB") or os.path.join(BASE_DIR, "food.db")


def connect():
    """Open a new connection to food.db with our standard settings."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # lets us use row["column_name"]
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite has these off by default
    return conn


def get_db():
    """Return this request's connection, opening it the first time it's needed."""
    if "db" not in g:
        g.db = connect()
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Close the connection at the end of every request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the tables if they don't exist yet."""
    conn = connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE COLLATE NOCASE,  -- "Demo" = "demo"
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS places (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            category    TEXT NOT NULL,   -- e.g. Dining hall, Cafe, Restaurant
            location    TEXT NOT NULL,   -- On campus or Off campus
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id),
            place_id   INTEGER NOT NULL REFERENCES places(id),
            rating     INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            body       TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, place_id)   -- one review per user per place
        );
    """)
    conn.close()


# ---- Sample data used by seed_db() ----

PLACES = [
    # (name, category, location, description)
    ("The Marketplace", "Dining hall", "On campus",
     "The main dining hall in Benson Center, with stations for grill, pizza, salads and more."),
    ("The Bronco", "Restaurant", "On campus",
     "Casual spot in Benson for burgers, wings and late-night snacks."),
    ("Mission Bakery", "Cafe", "On campus",
     "Coffee, pastries and grab-and-go sandwiches between classes."),
    ("Sunstream Cafe", "Cafe", "On campus",
     "Small cafe with espresso drinks, smoothies and quick bites."),
    ("Pizz'a Chicago", "Restaurant", "Off campus",
     "Deep-dish and thin-crust pizza on El Camino Real, popular for group dinners."),
    ("Mission City Coffee", "Cafe", "Off campus",
     "Roomy coffee house with good wifi, a favorite study spot."),
    ("Alameda Taqueria", "Restaurant", "Off campus",
     "Burritos, tacos and aguas frescas a short walk from campus."),
    ("Franklin Street Pho", "Restaurant", "Off campus",
     "Vietnamese noodle soups and banh mi in downtown Santa Clara."),
    ("Bronco Boba", "Cafe", "Off campus",
     "Milk tea, fruit tea and snacks with lots of topping choices."),
    ("El Camino Thai", "Restaurant", "Off campus",
     "Curries, noodles and lunch specials at student-friendly prices."),
]

USERNAMES = ["demo", "alex", "priya", "marcus", "jenny", "sam", "diego", "kayla"]

REVIEWS = [
    # (username, place name, rating, body)
    ("demo", "The Marketplace", 4, "Lots of choices and the salad bar is always fresh. Gets crowded around noon."),
    ("demo", "Pizz'a Chicago", 5, "The deep dish is worth the wait. Perfect for a group dinner."),
    ("demo", "Mission Bakery", 3, "Pastries are good but the coffee is just okay."),
    ("demo", "Bronco Boba", 4, "Great brown sugar milk tea. A little pricey for the size."),
    ("alex", "The Marketplace", 3, "Fine for a quick meal, but the menu repeats a lot during the week."),
    ("alex", "The Bronco", 5, "Best late-night burger on campus. The fries are always hot."),
    ("alex", "Alameda Taqueria", 5, "Huge burritos and really good salsa. My go-to after practice."),
    ("alex", "El Camino Thai", 4, "Pad see ew was excellent. Service was a bit slow."),
    ("alex", "Mission City Coffee", 4, "Nice place to study for a few hours. Seating fills up on weekends."),
    ("priya", "Sunstream Cafe", 4, "The smoothies are great and the line moves fast."),
    ("priya", "Mission City Coffee", 5, "Love the chai latte and the relaxed vibe."),
    ("priya", "Franklin Street Pho", 5, "Rich broth and generous portions. Perfect on a cold night."),
    ("priya", "The Marketplace", 2, "Ran out of the vegetarian entree twice this week."),
    ("priya", "Bronco Boba", 3, "Tea was too sweet even at 50% sugar."),
    ("marcus", "The Bronco", 4, "Good wings and the game is always on. Can get loud."),
    ("marcus", "Pizz'a Chicago", 4, "Solid pizza, but plan for a long wait on Fridays."),
    ("marcus", "Alameda Taqueria", 4, "Carne asada tacos are the move. Cash is faster here."),
    ("marcus", "Mission Bakery", 2, "My sandwich was soggy and the bread was stale."),
    ("jenny", "Mission Bakery", 4, "The blueberry muffins are amazing when they're warm."),
    ("jenny", "El Camino Thai", 5, "Green curry is spicy and delicious. Great lunch special."),
    ("jenny", "Sunstream Cafe", 3, "Decent coffee, but not many seats."),
    ("jenny", "Franklin Street Pho", 4, "Good banh mi for the price. Parking is tricky."),
    ("sam", "The Marketplace", 4, "Breakfast is the best meal here. The omelet station is great."),
    ("sam", "Bronco Boba", 5, "Taro milk tea with boba is perfect every time."),
    ("sam", "Pizz'a Chicago", 3, "Pizza was good but it took almost an hour to come out."),
    ("sam", "The Bronco", 2, "Burger came out cold and the line was really long."),
    ("diego", "Alameda Taqueria", 5, "Authentic and cheap. The al pastor is the best around."),
    ("diego", "Mission City Coffee", 3, "Coffee is good, but the wifi kept dropping."),
    ("diego", "El Camino Thai", 3, "Food was okay, a bit too sweet for my taste."),
    ("diego", "Sunstream Cafe", 4, "Quick iced coffee before class. Friendly staff."),
    ("diego", "Franklin Street Pho", 4, "Big bowls and fast service. Good value."),
    ("kayla", "Franklin Street Pho", 5, "The best pho near campus, hands down."),
    ("kayla", "The Marketplace", 3, "Pasta night is good, everything else is hit or miss."),
    ("kayla", "Mission Bakery", 5, "Cute spot and the croissants are flaky and buttery."),
    ("kayla", "Pizz'a Chicago", 1, "Our order was wrong and it took forever to fix."),
    ("kayla", "Bronco Boba", 4, "Fun flavors and the staff are always nice."),
]


def seed_db():
    """Fill the database with sample data, but only if there are no places yet."""
    conn = connect()
    count = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
    if count > 0:
        conn.close()
        return

    # "with conn" saves everything at once, or nothing if there's an error.
    with conn:
        conn.executemany(
            "INSERT INTO places (name, category, location, description) VALUES (?, ?, ?, ?)",
            PLACES,
        )

        # Random dates for the sample data. The fixed seed means the same
        # "random" dates (relative to today) every time.
        rng = random.Random(107)
        now = datetime.now(timezone.utc)  # CURRENT_TIMESTAMP is UTC too
        fmt = "%Y-%m-%d %H:%M:%S"  # same text format as CURRENT_TIMESTAMP

        # Every fake user's password is password123 (stored only as a hash).
        # They joined about 5 months ago (150-165 days), before any of their
        # reviews (at most 120 days old), so "member since" makes sense.
        for username in USERNAMES:
            joined = now - timedelta(seconds=rng.randint(150 * 24 * 3600, 165 * 24 * 3600))
            conn.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, generate_password_hash("password123"), joined.strftime(fmt)),
            )

        # Give each review a random date in the past 4 months.
        rows = []
        for username, place_name, rating, body in REVIEWS:
            created = now - timedelta(seconds=rng.randint(0, 120 * 24 * 3600))
            updated = created
            # About 1 in 5 reviews was edited a little later (never in the future).
            if rng.random() < 0.2:
                updated = min(created + timedelta(hours=rng.randint(1, 240)), now)
            rows.append((username, place_name, rating, body,
                         created.strftime(fmt), updated.strftime(fmt)))

        # Look up the user and place ids by name inside the INSERT.
        conn.executemany(
            """INSERT INTO reviews (user_id, place_id, rating, body, created_at, updated_at)
               VALUES ((SELECT id FROM users WHERE username = ?),
                       (SELECT id FROM places WHERE name = ?),
                       ?, ?, ?, ?)""",
            rows,
        )
    conn.close()


# Run at import time so this works with `flask run` and with gunicorn.
init_db()
seed_db()


# ---- User accounts ----

@app.before_request
def load_logged_in_user():
    """Before every request, put the logged-in user (or None) in g.user."""
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = get_db().execute(
            "SELECT id, username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if g.user is None:
            session.clear()  # the user was deleted, so forget the old login


def login_required(view):
    """Decorator for pages that need a logged-in user."""
    @wraps(view)  # keeps the view's name so url_for still works
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            flash("Please log in first.", "info")
            # Only come back to GET pages: a POST-only URL like
            # /place/3/review would give "Method Not Allowed" after logging in.
            if request.method != "GET":
                return redirect(url_for("login"))
            # full_path includes the query string; it ends in "?" if there isn't one
            return redirect(url_for("login", next=request.full_path.rstrip("?")))
        return view(*args, **kwargs)
    return wrapped_view


def is_safe_next(url):
    """Only allow redirects to paths on this site, like /place/3.

    "//evil.com" (and "/\\evil.com", which browsers treat the same way)
    would send the user to another website, so those are rejected.
    """
    return bool(url) and url.startswith("/") and not url.startswith("//") and "\\" not in url


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", username="")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm", "")

    # Check the rules one at a time and stop at the first problem.
    error = None
    if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
        error = "Username must be 3 to 20 characters: letters, digits and underscores only."
    elif len(password) < 8:
        error = "Password must be at least 8 characters."
    elif password != confirm:
        error = "Passwords don't match."

    if error is None:
        db = get_db()
        try:
            cursor = db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            # The UNIQUE rule on username failed, so the name is taken.
            error = f"The username {username} is already taken."

    if error is not None:
        flash(error, "error")
        # Re-show the form with the username filled in (never the password).
        return render_template("register.html", username=username)

    # Log the new user in right away.
    session.clear()
    session["user_id"] = cursor.lastrowid
    flash(f"Welcome, {username}! Your account is ready.", "success")
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    # "next" is the page to go back to after logging in, e.g. /place/3
    next_url = request.args.get("next", "")

    if request.method == "GET":
        return render_template("login.html", username="", next_url=next_url)

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    user = get_db().execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?", (username,)
    ).fetchone()

    # Same message whether the username or the password was wrong,
    # so nobody can use this form to find out which usernames exist.
    if user is None or not check_password_hash(user["password_hash"], password):
        flash("Invalid username or password", "error")
        return render_template("login.html", username=username, next_url=next_url)

    # clear() first so no data from before the login carries over.
    session.clear()
    session["user_id"] = user["id"]
    flash(f"Welcome back, {user['username']}!", "success")
    return redirect(next_url if is_safe_next(next_url) else url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You've been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/")
def index():
    """Home page: every place, ranked by average rating."""
    # LEFT JOIN keeps places with no reviews (their AVG is NULL, COUNT is 0).
    # "avg_rating IS NULL" is 0 for reviewed places and 1 for unreviewed,
    # so sorting on it first puts unreviewed places at the bottom.
    places = get_db().execute("""
        SELECT places.id, places.name, places.category, places.location,
               AVG(reviews.rating) AS avg_rating,
               COUNT(reviews.id)   AS review_count
        FROM places
        LEFT JOIN reviews ON reviews.place_id = places.id
        GROUP BY places.id
        ORDER BY avg_rating IS NULL, avg_rating DESC, review_count DESC, places.name
    """).fetchall()
    return render_template("index.html", places=places)


@app.route("/place/<int:place_id>")
def place(place_id):
    """Detail page for one place: info, rating summary, chart and reviews."""
    place = get_db().execute("SELECT * FROM places WHERE id = ?", (place_id,)).fetchone()
    if place is None:
        abort(404)  # handled by page_not_found() below
    return render_place_page(place)


def render_place_page(place, form=None):
    """Build the place page. save_review() also uses this to re-show the page
    after an error; then `form` holds what the user typed so it stays filled in.
    """
    db = get_db()
    place_id = place["id"]

    summary = db.execute(
        """SELECT AVG(rating) AS avg_rating, COUNT(*) AS review_count
           FROM reviews WHERE place_id = ?""",
        (place_id,),
    ).fetchone()

    # SQL only returns ratings that actually appear, e.g. {4: 2, 5: 1},
    # so start every star level at 0 and fill in the real counts.
    rows = db.execute(
        "SELECT rating, COUNT(*) AS n FROM reviews WHERE place_id = ? GROUP BY rating",
        (place_id,),
    ).fetchall()
    counts = {stars: 0 for stars in range(1, 6)}
    for row in rows:
        counts[row["rating"]] = row["n"]
    rating_counts = [counts[stars] for stars in range(1, 6)]  # [1-star, ..., 5-star]

    # Newest first; id breaks ties when two reviews have the same timestamp.
    reviews = db.execute(
        """SELECT reviews.user_id, reviews.rating, reviews.body,
                  reviews.created_at, reviews.updated_at, users.username
           FROM reviews
           JOIN users ON users.id = reviews.user_id
           WHERE reviews.place_id = ?
           ORDER BY reviews.created_at DESC, reviews.id DESC""",
        (place_id,),
    ).fetchall()

    # The logged-in user's own review of this place, if they wrote one.
    # The template uses it to pick "Write a review" vs. "Edit your review".
    my_review = None
    if g.user is not None:
        my_review = db.execute(
            "SELECT rating, body FROM reviews WHERE user_id = ? AND place_id = ?",
            (g.user["id"], place_id),
        ).fetchone()

    return render_template(
        "place.html",
        place=place,
        summary=summary,
        rating_counts=rating_counts,
        reviews=reviews,
        my_review=my_review,
        form=form,
    )


# Security note: both review routes below use g.user["id"], which comes from
# the signed session cookie, never a user id sent in the form. That is why a
# user can only ever create, edit or delete their own review.

@app.route("/place/<int:place_id>/review", methods=["POST"])
@login_required
def save_review(place_id):
    """Create a new review, or update the user's existing one."""
    db = get_db()
    place = db.execute("SELECT * FROM places WHERE id = ?", (place_id,)).fetchone()
    if place is None:
        abort(404)

    # The rating must be a whole number from 1 to 5 ("4.5" or "abc" fail int()).
    try:
        rating = int(request.form.get("rating", ""))
    except ValueError:
        rating = None

    # Browsers send line breaks as "\r\n"; count them as one character.
    body = request.form.get("body", "").replace("\r\n", "\n").strip()

    error = None
    if rating is None or not 1 <= rating <= 5:
        error = "Please choose a rating from 1 to 5 stars."
    elif len(body) == 0:
        error = "Please write something in your review."
    elif len(body) > 500:
        error = f"Reviews can be at most 500 characters (yours is {len(body)})."

    if error is not None:
        # Re-show the page (no redirect) so the typed rating and text stay
        # in the form. The flashed message shows up on this same page.
        flash(error, "error")
        return render_place_page(place, form={"rating": rating, "body": body}), 400

    # One statement for both cases: INSERT a new row, or, if this user already
    # reviewed this place (the UNIQUE rule), UPDATE that row instead.
    # "excluded" means the values we just tried to insert. created_at is left
    # alone on an edit, so updated_at > created_at marks an edited review.
    db.execute(
        """INSERT INTO reviews (user_id, place_id, rating, body)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(user_id, place_id) DO UPDATE SET
               rating = excluded.rating,
               body = excluded.body,
               updated_at = CURRENT_TIMESTAMP""",
        (g.user["id"], place_id, rating, body),
    )
    db.commit()
    flash("Review saved", "success")
    return redirect(url_for("place", place_id=place_id))


@app.route("/place/<int:place_id>/review/delete", methods=["POST"])
@login_required
def delete_review(place_id):
    """Delete the logged-in user's review of this place."""
    db = get_db()
    # Matching on both columns means this can only delete the user's own review.
    cursor = db.execute(
        "DELETE FROM reviews WHERE user_id = ? AND place_id = ?",
        (g.user["id"], place_id),
    )
    db.commit()
    if cursor.rowcount:
        flash("Your review was deleted.", "success")
    else:
        flash("There was no review to delete.", "info")
    return redirect(url_for("place", place_id=place_id))


@app.route("/user/<username>")
def user_page(username):
    """List all of one user's reviews, newest first."""
    db = get_db()
    # The username column is COLLATE NOCASE, so /user/Demo finds "demo" too.
    user = db.execute(
        "SELECT id, username, created_at FROM users WHERE username = ?", (username,)
    ).fetchone()
    if user is None:
        abort(404)

    reviews = db.execute(
        """SELECT reviews.place_id, reviews.rating, reviews.body,
                  reviews.created_at, reviews.updated_at, places.name AS place_name
           FROM reviews
           JOIN places ON places.id = reviews.place_id
           WHERE reviews.user_id = ?
           ORDER BY reviews.created_at DESC, reviews.id DESC""",
        (user["id"],),
    ).fetchall()
    return render_template("user.html", user=user, reviews=reviews)


@app.errorhandler(404)
def page_not_found(error):
    """Show a friendly page for bad URLs and missing places."""
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(error):
    """Show a friendly page when something crashes.
    (With `flask run --debug` you see the debugger instead.)"""
    return render_template("500.html"), 500

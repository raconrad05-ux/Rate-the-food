import os
import sqlite3

from flask import Flask, g
from werkzeug.security import generate_password_hash

app = Flask(__name__)

# Use SECRET_KEY from the environment if set; otherwise make a random one.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32)

# food.db lives in the same folder as this file.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "food.db")


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
            username      TEXT NOT NULL UNIQUE,
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

        # Every fake user's password is password123 (stored only as a hash).
        for username in USERNAMES:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash("password123")),
            )

        # Look up the user and place ids by name inside the INSERT.
        conn.executemany(
            """INSERT INTO reviews (user_id, place_id, rating, body)
               VALUES ((SELECT id FROM users WHERE username = ?),
                       (SELECT id FROM places WHERE name = ?),
                       ?, ?)""",
            REVIEWS,
        )
    conn.close()


# Run at import time so this works with `flask run` and with gunicorn.
init_db()
seed_db()


@app.route("/")
def index():
    """Temporary page: show how many rows are in each table."""
    db = get_db()
    users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    places = db.execute("SELECT COUNT(*) FROM places").fetchone()[0]
    reviews = db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    text = f"Users: {users}\nPlaces: {places}\nReviews: {reviews}\n"
    return text, 200, {"Content-Type": "text/plain"}

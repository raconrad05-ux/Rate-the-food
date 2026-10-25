## PROMPT 1
I’m building “Rate the Food”, a Flask app for rating places to eat on and around Santa Clara University. This is a class assignment, and I want to understand the code, so keep it simple and add short comments. Only do this step; don’t build pages or login yet.

Create app.py with:

A Flask app using Python’s built-in sqlite3 (no SQLAlchemy). The database file is food.db in the same folder as app.py (use os.path.dirname(os.path.abspath(__file__))). Use flask.g to open one connection per request, with row_factory = sqlite3.Row, and close it in a teardown_appcontext function. Turn on foreign keys with PRAGMA foreign_keys = ON.
SECRET_KEY read from the environment, falling back to os.urandom(32).
An init_db() function that creates three tables with CREATE TABLE IF NOT EXISTS:
users: id, username (unique, not null), password_hash (not null), created_at
places: id, name (unique, not null), category (e.g. “Dining hall”, “Cafe”, “Restaurant”), location (“On campus” or “Off campus”), description
reviews: id, user_id → users, place_id → places, rating (integer with a CHECK between 1 and 5), body (text), created_at, updated_at, and UNIQUE(user_id, place_id) so each user can review a place only once
A seed_db() function that runs only if the places table is empty. It inserts about 10 places (a mix of on-campus spots and off-campus restaurants near Santa Clara, with short descriptions), about 8 fake users with hashed passwords (use werkzeug.security.generate_password_hash; give all of them the password password123, and include one named demo), and 30 to 40 fake reviews spread across the places with varied ratings and realistic one- or two-sentence review text. Each user should review a place at most once. Use parameterized queries (?) everywhere.
Call init_db() and seed_db() at module level (not inside if __name__ == "__main__"), so they run when the app is imported by Flask locally and by gunicorn on Google Cloud Run.
A temporary / route that returns plain text showing how many users, places and reviews are in the database.

Don’t add any new packages; Flask and Werkzeug are already in requirements.txt.
# PROMPT 1
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

# PROMPT 2
Next step: replace the temporary / route with a real home page. Keep it simple, with short comments.

Create templates/base.html as a layout that every page extends: a header with the site name “Rate the Food” linking to /, a {% block content %}, and a footer. Show flashed messages (get_flashed_messages(with_categories=true)) above the content, since later steps will use them. For styling, link Pico CSS from a CDN (https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css) and add only a small amount of custom CSS in a <style> tag.
Create templates/index.html extending base.html. It shows all places ranked by average rating, highest first, in a table with columns: rank, name (linking to /place/<id>, a page we’ll build next), category, location, average rating (one decimal, with stars), and number of reviews.
Do the ranking in one SQL query: LEFT JOIN places to reviews so places with zero reviews still appear (show “No reviews yet” for them), GROUP BY place, AVG(rating) and COUNT(reviews.id), ordered by average descending, then review count descending, with unreviewed places last.
Don’t build the place page, login or forms yet.

# PROMPT 3
Next step: the place detail page. Keep it simple, with short comments.

Add a route /place/<int:place_id>. Look up the place; if it doesn’t exist, call abort(404).
Add a 404 error handler that renders templates/404.html (extending base.html) with a clear message like “That page or place doesn’t exist” and a link back home. Return the 404 status code.
Create templates/place.html showing:
the place’s name, category, location and description
the average rating (one decimal, with stars, using the same rounding as the home page) and the number of reviews, or “No reviews yet”
a bar chart of how many reviews gave 1, 2, 3, 4 and 5 stars. Count them in SQL with GROUP BY rating and fill in zero for missing ratings in Python, so the chart always has all five bars. Use Chart.js from https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js and pass the counts into JavaScript with Jinja’s tojson filter. Skip the chart if there are no reviews.
the list of reviews, newest first, each showing the reviewer’s username, star rating, the review text and the date. Get them with a JOIN to users.
In index.html, replace the hard-coded /place/<id> links with url_for('place', place_id=...) now that the route exists.
Don’t build login or review forms yet.

# PROMPT 4
Next step: user accounts. Keep it simple, with short comments. Don’t build review forms yet.

Register at /register: GET shows a form (username, password, confirm password); POST validates and creates the user. Rules: username 3 to 20 characters, only letters, digits and underscores; password at least 8 characters; the two passwords must match. Hash with werkzeug.security.generate_password_hash. If the username is taken, catch sqlite3.IntegrityError and show a clear message. On any error, flash the message and re-show the form with the username still filled in (never the password). On success, log the user in and redirect to the home page with a success flash.
Log in at /login: GET shows the form; POST checks the password with check_password_hash. On failure, show one generic message, “Invalid username or password”, without revealing which part was wrong. On success, store user_id in session. Support an optional next query parameter so a login can return the user to the page they came from, but only accept it if it is a relative path starting with / and not //; otherwise go home.
Log out at /logout, POST only (a small form button in the header), which clears the session.
A before_request function that loads the logged-in user into g.user (or None). If the session points to a user that no longer exists, clear the session.
A login_required decorator (using functools.wraps) that redirects to /login?next=<current path> with a flash message if nobody is logged in. We’ll use it in the next step.
In base.html, the header shows “Log in” and “Register” links when logged out, and “Logged in as <username>“ plus a Log out button when logged in.
Templates register.html and login.html extend base.html.
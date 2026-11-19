# Tests for the Rate the Food app.
# conftest.py has already pointed FOOD_DB at a temp file, so importing
# app here builds a fresh, seeded test database instead of using food.db.
from app import app


def login(client, username, password):
    """Helper: submit the login form, the same way a browser would."""
    return client.post("/login", data={"username": username, "password": password})


def test_home_page_loads():
    # The home page should load (200 OK) and show the site name from base.html.
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Rate the Food" in response.data


def test_missing_place_returns_404():
    # There is no place with id 9999, so the app should answer 404 Not Found.
    client = app.test_client()
    response = client.get("/place/9999")
    assert response.status_code == 404


def test_logged_in_user_can_post_review():
    # Log in as the seeded demo user (the client keeps the session cookie).
    client = app.test_client()
    login(client, "demo", "password123")

    # Post a valid review. On success the app redirects back to the place page.
    review_text = "Test review: the pizza station was great today."
    response = client.post("/place/1/review", data={"rating": "5", "body": review_text})
    assert response.status_code == 302

    # The new review text should now appear on the place page.
    page = client.get("/place/1")
    assert review_text.encode() in page.data


def test_rating_out_of_range_is_rejected():
    # Ratings must be 1 to 5, so a rating of 7 should be refused with 400 Bad Request.
    client = app.test_client()
    login(client, "demo", "password123")

    response = client.post("/place/1/review", data={"rating": "7", "body": "Too many stars"})
    assert response.status_code == 400
    assert b"Please choose a rating from 1 to 5 stars." in response.data


def test_wrong_password_shows_error():
    # A wrong password should not log you in; the login page shows an error instead.
    client = app.test_client()
    response = login(client, "demo", "wrong-password")
    assert b"Invalid username or password" in response.data

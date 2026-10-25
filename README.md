# Rate the Food

Rate the Food is a small web app where students rate and review places to eat on and around Santa Clara University. Anyone can browse the rankings and reviews; logged-in users can write one review per place and edit or delete it later.

## Features

- Home page that ranks every place by average rating
- Place page with details, average rating, a bar chart of 1–5 star ratings, and all reviews
- Register, log in and log out
- One review per user per place, with edit and delete
- User pages listing everything a user has reviewed
- Case-insensitive usernames ("Demo" and "demo" are the same account)
- Friendly 404 and 500 pages, and forms that keep your input when there's an error

## Run it on a laptop

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    flask --app app run --port 5001

Then open http://127.0.0.1:5001. The database (`food.db`) and sample data are created automatically on the first run.

## Demo login

- Username: `demo`
- Password: `password123`

## Live site

https://rate-the-food-746021394777.us-west1.run.app/

## Tech used

- Flask (Python web framework)
- SQLite (database)
- Jinja (HTML templates)
- Pico CSS (styling)
- Chart.js (rating chart)
- Google Cloud Run (hosting)

## Known limitations

- On Cloud Run the SQLite database resets whenever the service restarts or is redeployed. The sample data reloads automatically, but new accounts and reviews are lost.
- The Cloud Run service is limited to one instance so all visitors share the same database.
- The forms don't have CSRF protection.

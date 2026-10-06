# CineMatch - Movie Recommendation App

Flask + SQLite. Browse 24 movies, register/login, rate movies (1-5 stars) and get recommendations.

## Run locally (Windows)
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000  (the database is created and seeded automatically if missing).

## How recommendations work
- Rate movies 4-5 stars = you like their genres; 1-2 stars = dislike.
- Unrated movies are scored by your genre weights plus their critic score.
- Not logged in? Pick genres on the "For You" page.

## Tests
```
pytest tests
```

## Jenkins
Use the included `Jenkinsfile` (Pipeline script from SCM). Needs Python 3.10+ and Git on the Jenkins machine.
Stages: Checkout > Setup Python > Test > Package > Deploy (C:\movie-app, port 5000) > Smoke Test.

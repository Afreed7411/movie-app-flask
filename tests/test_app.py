import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["MOVIE_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

import app as movie_app  # noqa: E402


@pytest.fixture()
def client():
    movie_app.app.config["TESTING"] = True
    return movie_app.app.test_client()


def register_and_login(client, name="tester"):
    client.post("/register", data={"username": name, "email": f"{name}@x.com", "password": "secret1"})
    return client.post("/login", data={"username": name, "password": "secret1"}, follow_redirects=True)


def test_health(client):
    assert client.get("/health").json == {"status": "UP"}


def test_home_and_movies_pages(client):
    assert client.get("/").status_code == 200
    r = client.get("/movies?q=inception")
    assert b"Inception" in r.data and b"Titanic" not in r.data


def test_genre_filter(client):
    r = client.get("/movies?genre=Animation")
    assert b"Coco" in r.data and b"Inception" not in r.data


def test_movie_details_and_404(client):
    assert b"The Matrix" in client.get("/movie/6").data
    assert client.get("/movie/9999").status_code == 404


def test_register_login_logout(client):
    r = register_and_login(client, "alice")
    assert b"Hi, alice" in r.data
    assert b"Login" in client.get("/logout", follow_redirects=True).data


def test_bad_login(client):
    r = client.post("/login", data={"username": "nobody", "password": "x"})
    assert b"Invalid username or password" in r.data


def test_rating_requires_login(client):
    r = client.post("/movie/1", data={"rating": 5})
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_personal_recommendations(client):
    register_and_login(client, "bob")
    client.post("/movie/4", data={"rating": 5})   # Inception (Sci-Fi)
    client.post("/movie/6", data={"rating": 5})   # The Matrix (Sci-Fi)
    r = client.get("/recommendations")
    assert b"Picked for you" in r.data
    assert b"Interstellar" in r.data
    assert b"Inception" not in r.data.split(b'class="grid"')[1]


def test_genre_recommendations(client):
    r = client.get("/recommendations?genre=Horror")
    assert b"Get Out" in r.data

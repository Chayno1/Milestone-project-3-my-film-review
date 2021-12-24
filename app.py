import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_films")
def get_films():
    reviews = list(mongo.db['reviews'].find({}))
    films = list(mongo.db['films'].find({}))
    users = list(mongo.db['users'].find({}))
    return render_template("home.html", films=films, reviews=reviews)



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")




@app.route("/movies", methods=["GET", "POST"])
def movies():
    films = list(mongo.db['films'].find({}))
    return render_template("films.html", films=films)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # checks hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(request.form.get("username")))
                    return redirect(url_for("profile", username=session["user"]))
            else:
                #  if invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # if username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # get the session user's username from database
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    
    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login")) 


@app.route("/add_film", methods=["GET", "POST"])
def add_film():
    if request.method == "POST":
        # check if film already exists in db
        existing_film = mongo.db.users.find_one(
            {"title": request.form.get("title")})

        if existing_film:
            flash("Film already exists")
            return redirect(url_for("movies"))

        film = {
            "title": request.form.get("film_title"),
            "director": request.form.get("director"),
            "release_year": request.form.get("release_year"),
            "genre": request.form.getlist("genre_type[]"),
            "synopsis": request.form.get("synopsis"),
            "rating": request.form.get("rating"),
            "created_by": session["user"]
        }
        mongo.db.films.insert_one(film)
        print(film)
        flash("Film Successfully Added")
        return redirect(url_for('movies'))

    genres = mongo.db.genres.find().sort("genre", 1)
    return render_template("add_film.html", genres=genres)


@app.route("/edit_film/<films_id>", methods=["GET", "POST"])
def edit_film(films_id):
    if request.method == "POST":
        submit = {
            "title": request.form.get("film_title"),
            "director": request.form.get("director"),
            "release_year": request.form.get("release_year"),
            "genre": request.form.getlist("genre_type[]"),
            "synopsis": request.form.get("synopsis"),
            "rating": request.form.get("rating"),
            "created_by": session["user"]
        }
        mongo.db.films.update_one({"_id": ObjectId(films_id)}, {"$set": submit})
        flash("Film Successfully Updated")
        return redirect(url_for('movies'))

    films = mongo.db.films.find_one({"_id": ObjectId(films_id)})
    print("Film", films)
    genres = mongo.db.genres.find().sort("genre", 1)
    return render_template("edit_film.html", films=films, genres=genres)


@app.route("/reviews/<films_id>", methods=["GET", "POST"])
def reviews(films_id):
    film = mongo.db.films.find_one({"_id": ObjectId(films_id)})
    reviews = mongo.db.reviews.find({"title": film["title"]})
    return render_template("reviews.html", film=film, reviews=reviews)


@app.route("/add_review/<films_id>", methods=["GET", "POST"])
def add_review(films_id):
    if request.method == "POST":
        review = {
            "title": request.form.get("film_title"),
            "director": request.form.get("director"),
            "release_year": request.form.get("release_year"),
            "genre": request.form.getlist("genre_type[]"),
            "synopsis": request.form.get("synopsis"),
            "rating": request.form.get("rating"),
            "review": request.form.getlist("review[]"),
            "created_by": session["user"]
        }
        mongo.db.reviews.insert_one(review)
        flash("Review Successfully Added!")
        return redirect(url_for('movies'))

    film = mongo.db.films.find_one({"_id": ObjectId(films_id)})
    genres = mongo.db.genres.find().sort("genre", 1)
    return render_template("add_review.html", film=film, genres=genres)



if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
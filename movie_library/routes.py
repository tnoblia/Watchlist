import functools
from flask import (
    Blueprint, 
    render_template, 
    session, 
    redirect, 
    request, 
    url_for, 
    current_app, 
    abort,
    flash)
from movie_library.forms import MovieForm, ExtendeMovieForm, RegisterForm, LoginForm
import uuid
from movie_library.models import Movie, User
from dataclasses import asdict
import datetime
from passlib.hash import pbkdf2_sha256

pages = Blueprint(
    "pages",__name__, template_folder="templates",static_folder='static'
)

def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args, **kwargs):
        if not session.get('email'):
            return redirect(url_for(".login"))
        return route(*args, **kwargs)
    return route_wrapper

@pages.route('/')
@login_required
def index():
    user_data = current_app.db.users.find_one({"email": session["email"]})
    user = User(**user_data)
    movie_data = current_app.db.movies.find({"_id": {"$in": user.movies}})
    movies = [Movie(**movie) for movie in movie_data]
    return render_template(
        "index.html",
        title = "Movies watchlist",
        movies_data = movies
    )

@pages.route("/add", methods = ["GET","POST"])
@login_required
def add_movie():
    form = MovieForm()
    #if request.method == "POST":
    #Fait la même chose mais en mieux : C'est à dire que validate_on_submit regarde si le form a été soumis
    #Mais essaie de le valider également.
    if form.validate_on_submit():
        movie = Movie(
            _id= uuid.uuid4().hex,
            title= form.title.data,
            director = form.director.data,
            year = form.year.data
        )
        current_app.db.movies.insert_one(asdict(movie))
        current_app.db.users.update_one(
            {"_id" : session["user_id"]}, {"$push":{"movies":movie._id}}
        )

        return redirect(url_for('.index'))

    return render_template(
        "new_movie.html", 
        title = "Movies watchlist - Add Movie",
        form = form
        )

@pages.get('/movie/<string:_id>')
def movie(_id:str):
    movie_data = current_app.db.movies.find_one({"_id":_id})
    movie = Movie(**movie_data)
    if movie.video_link:
        video_link_embedded = movie.video_link.replace('watch?v=','embed/')
    else:
        video_link_embedded =""
    return render_template("movie_details.html", movie = movie, video_link_embedded = video_link_embedded)

@pages.get('/toggle-theme')
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session['theme'] = 'light'
    else:
        session["theme"] = 'dark'
    return redirect(request.args.get("current_page"))


@pages.get('/movie/<string:_id>/rate')
def rate_movie(_id):
    rating = int(request.args.get("rating")) 
    #Parce que l'url ressemble à ça: /movie/<string:_id>/rate?rating=4 => rating est dans l'url
    current_app.db.movies.update_one({"_id": _id}, {"$set": {"rating": rating}})
    fatal = current_app.db.movies.find_one({"title":"Fatal"}) 
    return redirect(url_for(".movie",_id = _id))


@pages.get('/movie/<string:_id>/watch')
@login_required
def watch_today(_id):
    today_date = datetime.datetime.today() 
    current_app.db.movies.update_one({"_id": _id}, {"$set": {"last_watched": today_date}})
    return redirect(url_for(".movie",_id = _id))

@pages.route("/edit/<string:_id>",methods = ["GET","POST"])
@login_required
def edit_movie(_id:str):
    movie = Movie(**current_app.db.movies.find_one({"_id":_id}))
    form = ExtendeMovieForm(obj=movie)
    if form.validate_on_submit():
        movie.title = form.title.data
        movie.director = form.director.data
        movie.year = form.year.data
        movie.cast = form.cast.data
        movie.series = form.series.data
        movie.tags = form.tags.data
        movie.description = form.description.data
        movie.video_link = form.video_link.data
        current_app.db.movies.update_one({"_id": _id}, {"$set": asdict(movie)})
        return redirect(url_for(".movie", _id = movie._id))

    
    return render_template("movie_form.html", movie = movie, form = form)

@pages.route("/register",methods = ["GET","POST"])
def register():
    if session.get("email"):
        return redirect(url_for(".index"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            _id= uuid.uuid4().hex,
            email= form.email.data,
            password = pbkdf2_sha256.hash(form.password.data),
        )
        current_app.db.users.insert_one(asdict(user))
        flash("User registered successfully", "success")
        session["email"] = user.email
        session["user_id"] = user._id
    return render_template("register.html", title = "Movies Watchlist - Register", form = form)


@pages.route("/login",methods = ["GET","POST"])
def login():
    if session.get("email"):
        return redirect(url_for(".index"))
    form = LoginForm()
    if form.validate_on_submit():
        user_data = current_app.db.users.find_one({"email":form.email.data})
        if not user_data:
            flash("Login credentials not correct", "danger")
            return redirect(url_for(".login"))
        user = User(**user_data)
        if pbkdf2_sha256.verify(form.password.data, user.password):
            session["user_id"] = user._id
            session["email"] = user.email
            return redirect(url_for(".index"))
        else:
            flash("Login credentials not correct", "danger")
    return render_template("login.html", title = "Movies Watchlist - Login", form = form)

@pages.route("/logout")
def logout():
    theme = session['theme']
    session.clear()
    session['theme'] = theme
    return  redirect(url_for(".login"))
from cs50 import SQL
from flask_session import Session
from flask import Flask, render_template, redirect, request, session, jsonify
from datetime import datetime


# Creates a connection to the database
db = SQL ( "sqlite:///login.db" )

# Instantiate Flask object named app
app = Flask(__name__)


# Configure sessions
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Define route for index page. Loads list of blog posts.
@app.route("/")
def index():
    blog = db.execute("SELECT * FROM posts ORDER BY id DESC")
    blogLen = len(blog)
    if 'user' in session:
        return render_template ( "index.html", session=session, blog=blog, blogLen=blogLen )
    return render_template ( "index.html", blog=blog, blogLen=blogLen )


# Sends user to login page
@app.route("/user/")
def user():
    return render_template ( "login.html" )


# Logs in a validated user
@app.route("/login/", methods=["POST"] )
def login():
    user = request.form["username"].lower()
    pwd = request.form["password"]

    if user == "" or pwd == "":
        return render_template ( "login.html" )

    query = "SELECT * FROM login WHERE username = :user AND password = :pwd"
    rows = db.execute ( query, user=user, pwd=pwd )

    if len(rows) == 1:
        session['user'] = user
        session['time'] = datetime.now( ).strftime('%Y-%m-%d')

    if 'user' in session:
        return redirect ( "/" )

    return render_template ( "login.html" )


# Once user is logged in, sends to user to a post form
@app.route("/post/")
def post():
    if 'user' in session:
        return render_template ("post.html", session=session)
    return redirect ('/')


# Processes a post and inserts it to the post database
@app.route("/posted/", methods=["POST"] )
def posted():
    title = request.form["title"]
    post = request.form["post"]
    db.execute ( "INSERT INTO posts (title, post, date, author) VALUES (:title, :post, :date, :author)", title=title, post=post, date=session['time'], author=session["user"] )
    return redirect('/')


# Renders a specific post. Post id is part of the URL
@app.route("/<int:id>/", methods=["GET"])
def article(id):
    art = db.execute("SELECT * FROM posts WHERE id=:id", id=id)
    return render_template ("article.html", art=art)


# Function to delete a post
@app.route("/<int:id>/delete/", methods=["GET"])
def delete(id):
    if 'user' in session:
        db.execute('DELETE FROM posts WHERE id=:id', id=id)
        return redirect("/")
    return render_template ( "404.html" ), 404


# Function to edit a post
@app.route("/<int:id>/edit/", methods=["GET"])
def edit(id):
    if 'user' in session:
        edit = db.execute('SELECT * FROM posts WHERE id=:id', id=id)
        return render_template('edit.html', edit=edit)


# Redirects user to the home page after editing a post
@app.route("/edited/", methods=["POST"] )
def edited():
    title = request.form["title"]
    post = request.form["post"]
    id = int(request.form["id"])
    db.execute ( "UPDATE posts SET title=:title, post=:post WHERE id=:id", title=title, post=post, id=id )
    return redirect('/')


# Sends new user to the registration page
@app.route("/new/")
def new_registration():
    return render_template ( "register.html", msg="All fields are required.")


# Route to an about page
@app.route("/about/")
def about():
    return render_template("about.html")


# Validates new user and inserts new user info to the user table
@app.route("/register/", methods=["POST"] )
def registration():
    username = request.form["username"]
    password = request.form["password"]
    confirm = request.form["confirm"]
    fname = request.form["fname"]
    lname = request.form["lname"]
    email = request.form["email"]

    if not username.isalnum ( ):
        return render_template ( "register.html", msg="Only alphanumeric usernames!" )

    if password != confirm:
        return render_template ( "register.html", msg="Passwords must match!" )

    rows = db.execute( "SELECT * FROM login WHERE username = :username ", username = username )
    if len( rows ) > 0:
        return render_template ( "register.html", msg="Username already exists!" )

    new = db.execute ( "INSERT INTO login (username, password) VALUES (:username, :password)",
                    username=username, password=password )

    # If the user was not added to the login table, then don't add them to the user table
    if new > 0:
        results = db.execute ( "SELECT * FROM login WHERE username=:username", username=username )
        uid = results[0]["uid"]

        db.execute ( "INSERT INTO user (uid, email, fname, lname) VALUES (:uid, :email, :fname, :lname)",
                        uid=uid, email=email, fname=fname, lname=lname )
        return render_template ( "registered.html" )

    return render_template ( "register.html", msg="Could not complete registration. Try again.")


# Route to 404 Error page
@app.errorhandler(404)
def pageNotFound( e ):
    if 'user' in session:
        return render_template ( "404.html", session=session )
    return render_template ( "404.html" ), 404


# Disallow login submission with GET method
@app.route("/login/", methods=["GET"] )
def badLogin():
    return render_template ( "405.html" ), 405


# Log user out and clear session variables. Redirect to home page
@app.route("/logout/")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to home page
    return redirect("/")


# Only needed if Flask run is not used to execute the server
#if __name__ == "__main__":
#    app.run( host='0.0.0.0', port=8080 )
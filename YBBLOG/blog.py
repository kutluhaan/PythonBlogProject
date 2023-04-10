from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

# User Log In Decorator
def login_required(f): #login decorator
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session: #logged in check
            return f(*args, **kwargs)
        else:
            flash("Please login to view this page.","danger")
            return redirect(url_for("login"))

    return decorated_function
# User Sign Up Form
class RegisterForm(Form): #form class
    name = StringField("Name-Last Name",validators=[validators.Length(min = 4,max = 25)])
    username = StringField("Username",validators=[validators.Length(min = 5,max = 35)])
    email = StringField("Email Adddress",validators=[validators.Email(message = "Lütfen Geçerli Bir Email Adresi Girin...")]) #validator
    password = PasswordField("Password:",validators=[ 
        validators.DataRequired(message = "Please enter a password"),
        validators.EqualTo(fieldname = "confirm",message="Passwords are not matching")
    ])
    confirm = PasswordField("Confirm Password")
class LoginForm(Form): #login form
    username = StringField("Username")
    password = PasswordField("Password")
app = Flask(__name__)
app.secret_key= "ybblog"
//set the SQL Database
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app) #connect SQL to app

@app.route("/") #determine the root
def index():
   return render_template("index.html") #rendering
@app.route("/about")
def about():
    return render_template("about.html")
# Article Page
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor() #create the cursor in database

    sorgu = "Select * From articles" #sorgu

    result = cursor.execute(sorgu) #execute

    if result > 0:
        articles = cursor.fetchall() #read all the rows
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")

@app.route("/dashboard") 
@login_required //if logged in
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],)) #find the username

    if result > 0:
        articles = cursor.fetchall() #read all
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")
#Sign Up
@app.route("/register",methods = ["GET","POST"]) #determine the methods
def register():
    form = RegisterForm(request.form) #take the form

    if request.method == "POST" and form.validate(): #if it is okay and correct method take the info fromm the user
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) #encrpyt the password

        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)" #insert the data

        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit() #commit changes

        cursor.close()
        flash("Succesfully signed up.","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)
# Login Process
@app.route("/login",methods =["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
       username = form.username.data
       password_entered = form.password.data

       cursor = mysql.connection.cursor()

       sorgu = "Select * From users where username = %s"

       result = cursor.execute(sorgu,(username,))

       if result > 0:
           data = cursor.fetchone()
           real_password = data["password"]
           if sha256_crypt.verify(password_entered,real_password):
               flash("Succesfully logged in","success")

               session["logged_in"] = True
               session["username"] = username

               return redirect(url_for("index"))
           else:
               flash("Wrong password.","danger")
               return redirect(url_for("login")) 

       else:
           flash("No such user.","danger") # flash messages
           return redirect(url_for("login"))

    
    return render_template("login.html",form = form)

# Deatil Page

@app.route("/article/<string:id>") #see the articles detailed
def article(id):
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * from articles where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article) # see the article
    else:
        return render_template("article.html")
# Logout Process
@app.route("/logout")
def logout():
    session.clear() #clear the login session
    return redirect(url_for("index"))
# Add Article
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():  # if okay to add take the data
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("Article succesfully added","success") # give the message

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form = form)

# Delete Article
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s and id = %s"  # select the article to be deleted

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from articles where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("No such article or you are not authorizied to do the operation.","danger")  # if no article
        return redirect(url_for("index"))
# Update Article
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
   if request.method == "GET":  # if method is okay
       cursor = mysql.connection.cursor()

       sorgu = "Select * from articles where id = %s and author = %s"
       result = cursor.execute(sorgu,(id,session["username"]))

       if result == 0:
           flash("No such article or you are not authorizied to do the operation.","danger")
           return redirect(url_for("index"))
       else:
           article = cursor.fetchone()  # just one article is taken
           form = ArticleForm()

           form.title.data = article["title"] 
           form.content.data = article["content"]
           return render_template("update.html",form = form)

   else:
       # POST REQUEST
       form = ArticleForm(request.form)

       newTitle = form.title.data
       newContent = form.content.data

       sorgu2 = "Update articles Set title = %s,content = %s where id = %s "

       cursor = mysql.connection.cursor()

       cursor.execute(sorgu2,(newTitle,newContent,id))

       mysql.connection.commit()

       flash("Article succesfully updated","success")

       return redirect(url_for("dashboard"))

       pass
# Article Form
class ArticleForm(Form):  # article form create
    title = StringField("Article Title",validators=[validators.Length(min = 5,max = 100)]) 
    content = TextAreaField("Article Content",validators=[validators.Length(min = 10)])

# Search URL
@app.route("/search",methods = ["GET","POST"])
def search(): # search the keyword
   if request.method == "GET":
       return redirect(url_for("index"))
   else:
       keyword = request.form.get("keyword")

       cursor = mysql.connection.cursor()

       sorgu = "Select * from articles where title like '%" + keyword +"%'"

       result = cursor.execute(sorgu)

       if result == 0:
           flash("The word you search is not found.","warning")
           return redirect(url_for("articles"))
       else:
           articles = cursor.fetchall()

           return render_template("articles.html",articles = articles)
if __name__ == "__main__":  # run the app
    app.run(debug=True)

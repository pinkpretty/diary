from flask import Flask,request,render_template,flash,redirect,url_for,session,logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

# Configuring MYSQL

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'gobinithya11'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#initializing MYSQL

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template("Homepage.html")

class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min =1,max=50)])
    username = StringField('UserName',[validators.Length(min=6,max=30)])
    email = StringField('Email', [validators.Length(min=6, max=100)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message = "Passwords do not match")
    ])
    confirm = PasswordField('ConfirmPassword')

@app.route('/register',methods = ['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # creating cursor to execute queries
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO USERS(name,username,password,email) VALUES (%s,%s,%s,%s)",(name,username,password,email))

        #Commit to DB
        mysql.connection.commit()

        #Close Connection
        cur.close()

        #Once rtegister say flash message
        flash('You are now registered. You can login','success')
        return redirect(url_for('index'))
    return render_template("register.html",form=form)



@app.route('/about')
def about():
    return render_template("about.html")

#user login
@app.route('/login',methods =['GET','POST'])
def login():
    if request.method == 'POST':
        # get username and password form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #create a cursor
        cur = mysql.connection.cursor()

        #selecting values from DB

        result = cur.execute("SELECT * FROM users WHERE USERNAME = %s",[username])

        if result > 0:
            # Get stored hash - if multiple rows returned, this line will fetch the first row matching
            data = cur.fetchone()
            password = data['password']

            # compare the results

            if sha256_crypt.verify(password_candidate,password):
                app.logger.info("Password match")
                session['logged_in'] = 'True'
                session['username'] = username

                flash("You are now logged in ")
                return redirect(url_for('dashboard'))
            else:
                app.logger.info("Password not matching")
                error = "Passwords do not match"
                return render_template("login.html",error=error)
        else:
            app.logger.info("No user found")
            error = "User name not registered"
            return render_template("login.html",error=error)

    return render_template('login.html')


# check user logged in or not

def is_user_logged(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash("You are not logged in. Please login")
            return redirect(url_for('index'))
    return wrap


@app.route('/articles')
@is_user_logged
def articles():
    # create a cursor
    cur = mysql.connection.cursor()

    # selecting values from DB

    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result == 0 :
        flash("There are no article! Please add article")
    else:
        return render_template("articles.html",articles=articles)
    #close the connection
    cur.close()

@app.route('/articles/<string:id>')
@is_user_logged
def article(id):
    # create a cursor
    cur = mysql.connection.cursor()

    # selecting values from DB

    result = cur.execute("SELECT * FROM articles")
    article = cur.fetchone()
    return render_template("article.html", article=article)

# Editing the articles

@app.route('/edit_article/<string:id>',methods =['GET','POST'])
@is_user_logged
def edit_article(id):

    # create a cursor
    cur = mysql.connection.cursor()

    # selecting values from DB

    result = cur.execute("SELECT * FROM articles where id = %s",[id])
    article = cur.fetchone()

    #get form
    form = ArticleForm(request.form)

    #populating value in form fields

    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():

        #fetching the form values otherwise it will fetch old title n body n table will not be updated
        title = request.form['title']
        body = request.form['body']

        # creating cursor to execute queries
        cur = mysql.connection.cursor()
        cur.execute("UPDATE articles SET title = %s , body = %s where id = %s ",(title,body,id))

        # Commit to DB
        mysql.connection.commit()

        # Close Connection
        cur.close()

        # Once rtegister say flash message
        flash('Your article is successfully Updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template("edit_article.html", form=form)

    return render_template("article.html", article=article)

# delete the article
@app.route('/delete_article/<string:id>',methods=['POST'])
@is_user_logged
def delete_article(id):

    # create a cursor
    cur = mysql.connection.cursor()

    # selecting values from DB

    result = cur.execute("DELETE FROM articles where id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    # Close Connection
    cur.close()

    flash("Article deleted")
    return redirect(url_for('dashboard'))

@app.route('/logout')
@is_user_logged
def logout():
    session.clear()
    flash("You are now logged out ")
    return redirect(url_for('index'))

@app.route('/dashboard')
@is_user_logged
def dashboard():
    # create a cursor
    cur = mysql.connection.cursor()

    # selecting values from DB

    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template("dashboard.html", articles=articles)
    else:
        flash("There are no article! Please add article")

    # close the connection
    cur.close()

    return render_template("dashboard.html")

# WTForms for adding content in the article page

class ArticleForm(Form):

    title = StringField('Title',[validators.Length(min =1,max=300)])
    body = TextAreaField('Body', [validators.Length(min=50)])


@app.route('/add_article',methods = ['GET','POST'])
@is_user_logged
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # creating cursor to execute queries
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title,body,author) VALUES (%s,%s,%s)",
                    (title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        # Close Connection
        cur.close()

        # Once rtegister say flash message
        flash('Your article is successfully posted', 'success')
        return redirect(url_for('dashboard'))
    return render_template("add_article.html", form=form)


if __name__ == "__main__":
    app.secret_key = 'Agdt@1234'
    app.run(debug=True)

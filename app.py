import os
import os.path as op
from os.path import dirname, join, realpath

from flask import (Flask, flash, redirect, render_template, request, url_for)
from flask_admin import Admin, form
from flask_admin.contrib import rediscli, sqla
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules
from flask_login import LoginManager, UserMixin
from flask_login.utils import current_user, login_user, logout_user
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from jinja2 import Markup
from sqlalchemy.event import listens_for

file_path = op.join(op.dirname(__file__), './static/files')
try:
    os.mkdir(file_path)
except OSError:
    pass


app = Flask(__name__)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
admin = Admin(app)
app.secret_key = "mailserver"

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = 'rasp.pi98@gmail.com'
app.config["MAIL_PASSWORD"] = 'MHEECHA8lamo'

mail = Mail(app)
mail.init_app(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql+psycopg2://postgres:MHEECHA1lamo@localhost:5432/projects'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://sigjzxfjrhvcxz:d3c589e50670a2c7b2dd3fb1b76db9d4eb3dc2eda9b2b2a45770a116d078e595@ec2-18-209-187-54.compute-1.amazonaws.com:5432/d9beeu0impht4s"

###########################################################################
# DATABASE CLASSES


class projects(db.Model, UserMixin):
    __tablename__ = 'p_db'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    description = db.Column(db.String())
    github = db.Column(db.String())
    link = db.Column(db.String())
    name = db.Column(db.Unicode(64))
    path = db.Column(db.Unicode(128))
    techstack = db.Column(db.String())

    def __unicode__(self):
        return self.name

    def serialize(self):
        return {
            'title': self.title,
            'description': self.description,
            'github': self.github,
            'link': self.link,
            'techstack': self.techstack,
            'path': self.path
        }


class user(db.Model, UserMixin):
    __tablename__ = 'u_db'
    _id = db.Column("id", db.Integer, primary_key=True)
    firstName = db.Column(db.String(100))
    lastName = db.Column(db.String(100))
    email = db.Column(db.String(100))
    subject = db.Column(db.String())
    message = db.Column(db.String())
    password = db.Column(db.String())

    def __init__(self,
                 firstName=None,
                 lastName=None,
                 email=None,
                 subject=None,
                 message=None,
                 password=None):
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.subject = subject
        self.message = message
        self.password = password

    def serialize(self):
        return {
            'id': self._id,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email,
            'subject': self.subject,
            'message': self.message,
            'password': self.password
        }

    def get_id(self):
        return (self._id)

###########################################################################
# ADMIN MODELS


class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and not current_user.is_anonymous


class ImageView(ModelView):
    def _list_thumbnail(view, context, model, name):
        if not model.path:
            return ''

        return Markup('<img src="%s">' % url_for('static',
                                                 filename=form.thumbgen_filename(model.path)))

    column_formatters = {
        'path': _list_thumbnail
    }

    # Alternative way to contribute field is to override it completely.
    # In this case, Flask-Admin won't attempt to merge various parameters for the field.
    form_extra_fields = {
        'path': form.ImageUploadField('Image',
                                      base_path=file_path,
                                      thumbnail_size=(100, 100, True))
    }

    def is_accessible(self):
        return current_user.is_authenticated and not current_user.is_anonymous


admin.add_view(ModelView(user, db.session))
admin.add_view(ImageView(projects, db.session))

###########################################################################
# ROUTES


@login_manager.user_loader
def load_user(user_id):
    return user.query.get(user_id)


@app.route('/login/', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        us = user.query.get(1)
        if request.form['username'] != us.firstName or request.form['password'] != us.password:
            flash("Invalid Username or Password.")
            return render_template("login.html")
        else:
            login_user(us)
            return redirect(url_for("home")+"admin")
    else:
        return render_template("login.html")


@app.route('/logout/')
def logout():

    logout_user()
    return "<h1>Logged out</h1>"


@app.route('/')
def home():
    return render_template("home.html", title="GAURAV SHILPAKAR", projects=db_projects())


@app.route('/contact/', methods=["POST", "GET"])
def contact():
    if request.method == "POST":
        firstName = request.form["firstName"]
        lastName = request.form["lastName"]
        email = request.form["email"]
        subject = request.form["subject"]
        message = request.form["message"]

        msg = Message(subject, sender=email, recipients=[
                      "gaurav.shilpakar@gmail.com"])
        msg.body = f"""
        From: <{email}>
        Subject: <{subject}>
        Message: 
        {message}
        """
        mail.send(msg)
        flash("Message Delivered!")

        u = user(firstName=firstName,
                 lastName=lastName,
                 email=email,
                 subject=subject,
                 message=message)
        db.session.add(u)
        db.session.commit()

        print(u.firstName)
        return redirect(url_for('home')+"#contact")
    else:
        return redirect(url_for('home')+"#contact")


@app.route("/api/")
def db_projects():
    pjs = projects.query.all()
    return ([e.serialize() for e in pjs])


@app.route('/resume/')
def resume():
    return url_for('static', filename='resume.pdf')


if __name__ == "__main__":
    db.create_all()

    app.secret_key = "1a3de5vefsa52vdwa42evdc2234d3ddsas"
    app.run(debug=True)

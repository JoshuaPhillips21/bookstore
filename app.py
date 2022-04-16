from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

import os

load_dotenv()

# database_url ="postgresql:" + ":".join(os.environ.get("DATABASE_URL", "").split(":")[1:])
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy(app)
ma = Marshmallow(app)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.sqlite")
CORS(app)
bcrypt = Bcrypt(app)

user_table = db.Table('users_table', 
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('lib_id', db.Integer, db.ForeignKey('librarian.lib_id'))
)

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    books = db.relationship('Book', backref='user', cascade='all, delete, delete-orphan')

    def __init__(self, username, password):
        self.username = username
        self.password = password


class Librarian(User):
    __tablename__ = 'librarian'
    
    lib_id = db.Column(db.Integer, primary_key=True)
    lib_username = db.Column(db.String, unique=True, nullable=False)
    lib_password = db.Column(db.String, nullable=False)
    canAccess = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, username, password, canAccess):
        super().__init__(username, password)
        self.lib_username = username
        self.lib_password = password
        self.canAccess = canAccess

@app.route('/user/add', methods=['POST'])
def add_user():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')

    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')
    possible_duplicate = db.session.query(User).filter(User.username == username).first()

    if possible_duplicate is not None: 
        return jsonify('Error: the username is taken.')

    encrpted_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username, encrpted_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify("Congrats, you've signed up")

@app.route('/user/verify', methods=['POST'])
def verify_user():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')
    
    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')

    user = db.session.query(User).filter(User.username == username).first()

    if user is None:
        return jsonify('User NOT verified')
    if bcrypt.check_password_hash(user.password, password) == False:
        return jsonify('User NOT verified')

    return jsonify('User has been verified')

@app.route('/user/get', methods=['GET'])
def get_user():
    all_users = db.session.query(User).all()
    return jsonify(multiple_user_schema.dump(all_users))

@app.route('/user/delete', methods=['Delete'])
def delete_users() :
    all_users = db.session.query(User).all()
    for user in all_users:
        db.session.delete(user)

    db.session.commit()
    return jsonify('All users have been deleted')

@app.route('/user/delete/<id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.query(User).filter(User.id == id).first()
    db.session.delete(user)
    db.session.commit()

    return jsonify(f'The user {user.username} has been deleted')


class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False, unique=True)
    author = db.Column(db.String, nullable=False)
    review = db.Column(db.String(144), nullable=True)
    genre = db.Column(db.String, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, title, author, review, genre, user_id):
        self.title = title
        self.author = author 
        self.review = review 
        self.genre = genre
        self.user_id = user_id


class BookSchema(ma.Schema):
    class Meta:
        fields = ("id", "title", "author", "review", "genre")

book_schema = BookSchema()
multiple_book_schema = BookSchema(many=True)


@app.route('/book/add', methods=["POST"])
def add_book():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')

    post_data = request.get_json()
    title = post_data.get('title')
    author = post_data.get('author')
    review = post_data.get('review')
    genre = post_data.get('genre')
    user_id = post_data.get('user_id')

    book = db.session.query(Book).filter(Book.title == title).first()

    if title == None:
        return jsonify("Error: data must have a 'Title' key.")
    if book:
        return jsonify("Error: title must be unique")
    if author == None:
        return jsonify("Error: data must have a 'Author' key.")

    new_book = Book(title, author, review, genre, user_id)
    db.session.add(new_book)
    db.session.commit()

    return jsonify("You've added a new book!")


@app.route('/book/get', methods={"GET"})
def get_books():
    books = db.session.query(Book).all()
    return jsonify(multiple_book_schema.dump(books))


@app.route('/book/get/<id>', methods={"GET"})
def get_book(id):
    book = db.session.query(Book).filter(Book.id == id).first()
    return jsonify(book_schema.dump(book))

@app.route('/book/get/title/<title>', methods=["GET"])
def get_book_by_title(title):
    book = db.session.query(Book).filter(Book.title == title).first()
    return jsonify(book_schema.dump(book))

@app.route('/book/get/author/<author>', methods=["GET"])
def get_book_by_author(author):
    book = db.session.query(Book).filter(Book.author == author).all()
    return jsonify(multiple_book_schema.dump(book))

@app.route('/book/get/genre/<genre>', methods=["GET"])
def get_book_by_genre(genre):
    book = db.session.query(Book).filter(Book.genre == genre).all()
    return jsonify(multiple_book_schema.dump(book))

@app.route('/book/delete/<id>', methods={"DELETE"})
def delete_book_by_id(id):
    book = db.session.query(Book).filter(Book.id == id).first()
    db.session.delete(book)
    db.session.commit()
    
    return jsonify("The book has been deleted")

@app.route('/book/update/<id>', methods={"PUT", "PATCH"})
def update_book_by_id(id):
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')

    post_data = request.get_json()
    title = post_data.get('title')
    author = post_data.get('author')
    review = post_data.get('review')
    genre = post_data.get('genre')
    
    book = db.session.query(Book).filter(Book.id == id).first()

    
    if title != None:
        book.title = title    
    if author != None:
        book.author = author
    if review != None:
        book.review = review
    if genre != None:
        book.genre = genre

    db.session.commit()
    return jsonify("Book has been updated")
    
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'password', 'books')
    books = ma.Nested(multiple_book_schema)

user_schema = UserSchema()
multiple_user_schema = UserSchema(many=True)

class LibrarianSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'canAccess')

lib_schema = LibrarianSchema()
multiple_lib_schema = LibrarianSchema(many=True)

@app.route('/lib/add', methods=['POST'])
def add_lib():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be json')

    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')
    canAccess = post_data.get('canAccess')

    if canAccess == 'True':
        canAccess = True
    else: 
        canAccess = False

    possible_duplicate = db.session.query(User).filter(User.username == username).first()

    if possible_duplicate is not None: 
        return jsonify('Error: the username is taken.')

    encrpted_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_lib = User(username, encrpted_password, canAccess)

    db.session.add(new_lib)
    db.session.commit()
    
    return jsonify("Congrats, you've signed up for a new librarian account")
    

if __name__ == "__main__":
    app.run(debug=True)
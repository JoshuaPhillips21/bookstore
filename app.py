from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS

import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy(app)
ma = Marshmallow(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.sqlite")
CORS(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False, unique=True)
    author = db.Column(db.String, nullable=False)
    review = db.Column(db.String(144), nullable=True)
    genre = db.Column(db.String, nullable=True)

    def __init__(self, title, author, review, genre):
        self.title = title
        self.author = author 
        self.review = review 
        self.genre= genre


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

    book = db.session.query(Book).filter(Book.title == title).first()

    if title == None:
        return jsonify("Error: data must have a 'Title' key.")
    if book:
        return jsonify("Error: title must be unique")
    if author == None:
        return jsonify("Error: data must have a 'Author' key.")

    new_book = Book(title, author, review, genre)
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

@app.route('/book/delete/<id>', methods={"DELETE"})
def delete_book_by_id(id):
    book = db.session.delete(book).filter(Book.id == id)
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
    

    

if __name__ == "__main__":
    app.run(debug=True)
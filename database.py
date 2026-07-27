from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    #Stores user accounts
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password = db.Column(db.String(200), nullable = False) # Hashed password
    created_at = db.Column(db.DateTime, default = datetime.utcnow)

    #Relationships, one user has many study sets
    study_sets = db.relationship('StudySet', backref='owner', lazy=True, cascade='all, delete-orphan')

class StudySet(db.Model):
    #Collection of flashcards generated from one PDF or text input
    __tablename__ = 'study_sets'

    id =  db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(200), nullable = False)
    source_text = db.Column(db.Text, nullable = False) #original text the cards were made from
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)

    #Relationships
    flashcards = db.relationship('Flashcard', backref='study_set', lazy=True, cascade='all, delete-orphan')

    quiz_results = db.relationship('QuizResult', backref='study_set', lazy=True, cascade='all, delete-orphan')

class Flashcard(db.Model):
    #A single flashcard with a question ans answer
    __tablename__ = 'flashcards'

    id = db.Column(db.Integer, primary_key = True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable = False)
    difficulty = db.Column(db.String(20), default = 'new') #new easy medium hard
    review_count = db.Column(db.Integer, default = 0) #How many times reviewed
    study_set_id = db.Column(db.Integer, db.ForeignKey('study_sets.id'), nullable = False)


class QuizResult(db.Model):
    #Stores result of a quiz attempt
    __tablename__ = 'quiz_results'

    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable = False) #number correct
    total = db.Column(db.Integer, nullable = False) #total questions
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)
    study_set_id = db.Column(db.Integer, db.ForeignKey('study_sets.id'), nullable = False)
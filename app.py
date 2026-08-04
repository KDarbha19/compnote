import os 
from flask import Flask
from dotenv import load_dotenv
from database import db
from flask_login import LoginManager

load_dotenv()

def create_app():
    app = Flask(__name__)

    #Config
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///compnote.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

    #Database
    db.init_app(app)

    #Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' #redirection if not logged in 
    login_manager.login_message = 'Please log in to access this page.'

    from database import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    #Register Blueprints 
    #Splits the app into logical modules 
    #auth.py handles login/setup, study.py handles flashcards/quizzes
    from auth import auth_bp
    from study import study_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(study_bp)

    #Table creation 
    with app.app_context():
        db.create_all()
        print("Database tables created!")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

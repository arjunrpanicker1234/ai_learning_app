from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User, Skill
from config import Config
from routes.auth import auth_bp
from routes.user import user_bp
from routes.tutor import tutor_bp
import os
from sqlalchemy.orm import Session  # Import Session


# App factory
def create_app():
    app = Flask(__name__)  # Initialize app here
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)

    # Initialize LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(tutor_bp, url_prefix='/tutor')

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
      return db.session.get(User, int(user_id)) 
    # Main route
    @app.route('/')
    def index():
        return render_template('index.html')

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Create DB tables and initial data if DB doesn't exist
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not os.path.exists(db_path):
            db.create_all()

            # Insert initial skills if the table is empty
            if Skill.query.count() == 0:
                initial_skills = [
                    Skill(name='Python', description='Python programming language'),
                    Skill(name='JavaScript', description='JavaScript programming language'),
                    Skill(name='Data Science', description='Data analysis and machine learning'),
                    Skill(name='Web Development', description='HTML, CSS, and web frameworks')
                ]
                db.session.add_all(initial_skills)
                db.session.commit()

    return app


# Run the app
if __name__ == '__main__':
    app = create_app()  # Create app here
    app.run(debug=True)

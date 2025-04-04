from app import app
from models import db, User

with app.app_context():
    # Print database URI to verify which database you're connecting to
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    users = User.query.all()
    print(f"Total users found: {len(users)}")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")
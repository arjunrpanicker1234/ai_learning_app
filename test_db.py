from app import app
from models import db, User

# Import for database file check
import os

with app.app_context():
    # Print database URI and check if file exists
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"Database URI: {db_uri}")
    
    if db_uri.startswith('sqlite:///'):
        db_file = db_uri.replace('sqlite:///', '')
        if os.path.exists(db_file):
            print(f"Database file exists: {db_file}")
            db_size = os.path.getsize(db_file)
            print(f"Database file size: {db_size} bytes")
        else:
            print(f"Database file does NOT exist: {db_file}")
    
    # Check existing users
    existing_users = User.query.all()
    print(f"Existing users: {len(existing_users)}")
    for user in existing_users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")
    
    # Try to create a test user
    try:
        test_user = User(
            username="testuser123", 
            email="test123@example.com",
            is_tutor=False
        )
        test_user.set_password("password123")
        
        db.session.add(test_user)
        db.session.commit()
        print("Test user added successfully")
        
        # Verify it was added
        user = User.query.filter_by(username="testuser123").first()
        if user:
            print(f"User found: {user.username}, Email: {user.email}")
        else:
            print("User not found after adding")
    except Exception as e:
        print(f"Error adding user: {e}")
        db.session.rollback()